import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, Tuple, List
import xgboost as xgb
from sklearn.model_selection import train_test_split, TimeSeriesSplit
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, accuracy_score
import joblib
import logging
from datetime import datetime, timedelta
import os

from .base_strategy import BaseStrategy, Signal, SignalType
from ..features.feature_engineering import FeatureEngineer

logger = logging.getLogger(__name__)


class XGBoostTradingStrategy(BaseStrategy):
    def __init__(
        self,
        params: Optional[Dict[str, Any]] = None,
        model_path: Optional[str] = None,
        retrain_frequency: int = 168  # hours (1 week)
    ):
        default_params = {
            'objective': 'multi:softprob',
            'num_class': 3,  # buy, sell, hold
            'max_depth': 6,
            'learning_rate': 0.1,
            'n_estimators': 100,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'random_state': 42,
            'n_jobs': -1
        }
        if params:
            default_params.update(params)

        super().__init__("XGBoostML", default_params)

        self.model = None
        self.scaler = StandardScaler()
        self.feature_engineer = FeatureEngineer()
        self.model_path = model_path or "models/xgboost_model.pkl"
        self.scaler_path = "models/scaler.pkl"
        self.retrain_frequency = retrain_frequency
        self.last_train_time = None
        self.feature_columns = []

        # Create models directory
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)

        # Load existing model if available
        self._load_model()

    def _load_model(self):
        """Load existing model and scaler"""
        try:
            if os.path.exists(self.model_path):
                self.model = joblib.load(self.model_path)
                logger.info("Loaded existing XGBoost model")

            if os.path.exists(self.scaler_path):
                self.scaler = joblib.load(self.scaler_path)
                logger.info("Loaded existing scaler")

        except Exception as e:
            logger.warning(f"Failed to load model: {e}")
            self.model = None

    def _save_model(self):
        """Save model and scaler"""
        try:
            joblib.dump(self.model, self.model_path)
            joblib.dump(self.scaler, self.scaler_path)
            logger.info("Saved XGBoost model and scaler")
        except Exception as e:
            logger.error(f"Failed to save model: {e}")

    def prepare_features(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
        """Prepare features and target for training"""
        # Engineer features
        df_features = self.feature_engineer.engineer_features(df)

        # Create target variable (future returns)
        df_features['future_return'] = df_features['close'].pct_change().shift(-1)

        # Create classification target
        # 0 = sell/short, 1 = hold, 2 = buy/long
        conditions = [
            df_features['future_return'] < -0.005,  # < -0.5% = sell
            df_features['future_return'] > 0.005,   # > 0.5% = buy
        ]
        choices = [0, 2]  # sell, buy
        df_features['target'] = np.select(conditions, choices, default=1)  # hold

        # Select features for training
        feature_columns = [
            col for col in df_features.columns
            if col not in ['timestamp', 'open', 'high', 'low', 'close', 'volume',
                          'future_return', 'target', 'symbol', 'timeframe', 'exchange']
            and not col.endswith('_lag_1')  # avoid look-ahead bias
        ]

        # Remove rows with NaN values
        df_clean = df_features.dropna()

        if len(df_clean) == 0:
            raise ValueError("No clean data available for training")

        X = df_clean[feature_columns]
        y = df_clean['target']

        self.feature_columns = feature_columns
        logger.info(f"Prepared {len(X)} samples with {len(feature_columns)} features")

        return X, y

    def train_model(
        self,
        df: pd.DataFrame,
        validation_split: float = 0.2,
        use_time_split: bool = True
    ) -> Dict[str, Any]:
        """Train the XGBoost model"""
        logger.info("Training XGBoost model...")

        try:
            X, y = self.prepare_features(df)

            if len(X) < 100:
                logger.warning("Insufficient data for training")
                return {'success': False, 'reason': 'insufficient_data'}

            # Split data
            if use_time_split:
                split_idx = int(len(X) * (1 - validation_split))
                X_train, X_val = X.iloc[:split_idx], X.iloc[split_idx:]
                y_train, y_val = y.iloc[:split_idx], y.iloc[split_idx:]
            else:
                X_train, X_val, y_train, y_val = train_test_split(
                    X, y, test_size=validation_split, random_state=42, stratify=y
                )

            # Scale features
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_val_scaled = self.scaler.transform(X_val)

            # Train model
            self.model = xgb.XGBClassifier(**self.params)
            self.model.fit(
                X_train_scaled, y_train,
                eval_set=[(X_val_scaled, y_val)],
                verbose=False
            )

            # Evaluate
            y_pred = self.model.predict(X_val_scaled)
            accuracy = accuracy_score(y_val, y_pred)

            # Get feature importance
            feature_importance = dict(zip(
                self.feature_columns,
                self.model.feature_importances_
            ))

            self.last_train_time = datetime.now()
            self._save_model()

            logger.info(f"Model training completed. Validation accuracy: {accuracy:.3f}")

            return {
                'success': True,
                'accuracy': accuracy,
                'feature_importance': feature_importance,
                'train_samples': len(X_train),
                'val_samples': len(X_val),
                'class_distribution': y.value_counts().to_dict()
            }

        except Exception as e:
            logger.error(f"Model training failed: {e}")
            return {'success': False, 'reason': str(e)}

    def predict(self, df: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """Make prediction using the trained model"""
        if self.model is None:
            logger.warning("No trained model available")
            return None

        try:
            # Engineer features for latest data
            df_features = self.feature_engineer.engineer_features(df)

            if len(df_features) == 0:
                return None

            # Get latest row features
            latest_features = df_features[self.feature_columns].iloc[-1:].fillna(0)

            # Scale features
            features_scaled = self.scaler.transform(latest_features)

            # Get prediction probabilities
            probabilities = self.model.predict_proba(features_scaled)[0]

            # Get prediction
            prediction = self.model.predict(features_scaled)[0]

            prediction_map = {0: 'sell', 1: 'hold', 2: 'buy'}

            return {
                'prediction': prediction_map[prediction],
                'probabilities': {
                    'sell': probabilities[0],
                    'hold': probabilities[1],
                    'buy': probabilities[2]
                },
                'confidence': max(probabilities)
            }

        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            return None

    def should_retrain(self) -> bool:
        """Check if model should be retrained"""
        if self.model is None:
            return True

        if self.last_train_time is None:
            return True

        time_since_training = datetime.now() - self.last_train_time
        return time_since_training > timedelta(hours=self.retrain_frequency)

    def generate_signal(self, df: pd.DataFrame) -> Optional[Signal]:
        """Generate trading signal using ML model"""
        if len(df) < 50:
            return None

        # Check if retrain is needed
        if self.should_retrain():
            logger.info("Retraining model...")
            train_result = self.train_model(df)
            if not train_result.get('success', False):
                logger.warning("Model retraining failed")

        # Get prediction
        prediction_result = self.predict(df)
        if prediction_result is None:
            return None

        prediction = prediction_result['prediction']
        confidence = prediction_result['confidence']
        probabilities = prediction_result['probabilities']

        # Convert to signal
        signal_map = {
            'buy': SignalType.BUY,
            'sell': SignalType.SELL,
            'hold': SignalType.HOLD
        }

        if prediction == 'hold' or confidence < 0.6:
            return None

        signal_type = signal_map[prediction]

        # Calculate strength based on probability difference
        if prediction == 'buy':
            strength = probabilities['buy'] - max(probabilities['sell'], probabilities['hold'])
        else:
            strength = probabilities['sell'] - max(probabilities['buy'], probabilities['hold'])

        strength = max(0.1, min(1.0, strength * 2))  # Scale to 0.1-1.0

        return Signal(
            signal_type=signal_type,
            strength=strength,
            confidence=confidence,
            strategy_name=self.name,
            timestamp=pd.Timestamp.now(),
            metadata={
                'probabilities': probabilities,
                'ml_confidence': confidence,
                'model_prediction': prediction
            }
        )

    def validate_signal(self, signal: Signal, df: pd.DataFrame) -> bool:
        """Validate ML signal"""
        # Basic validation - check if confidence is above threshold
        return signal.confidence > 0.6

    def calculate_signal_strength(self, df: pd.DataFrame) -> float:
        """Calculate signal strength (handled in generate_signal)"""
        return 0.5

    def calculate_confidence(self, df: pd.DataFrame) -> float:
        """Calculate confidence (handled in generate_signal)"""
        return 0.5

    def get_feature_importance(self) -> Optional[Dict[str, float]]:
        """Get feature importance from trained model"""
        if self.model is None:
            return None

        return dict(zip(self.feature_columns, self.model.feature_importances_))

    def backtest_model(
        self,
        df: pd.DataFrame,
        train_size: float = 0.7
    ) -> Dict[str, Any]:
        """Backtest the ML model performance"""
        try:
            X, y = self.prepare_features(df)

            # Time-based split for backtesting
            split_idx = int(len(X) * train_size)
            X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
            y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

            # Train model
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)

            model = xgb.XGBClassifier(**self.params)
            model.fit(X_train_scaled, y_train)

            # Predictions
            y_pred = model.predict(X_test_scaled)
            y_pred_proba = model.predict_proba(X_test_scaled)

            accuracy = accuracy_score(y_test, y_pred)

            # Calculate directional accuracy for trading
            correct_directions = 0
            total_signals = 0

            for i in range(len(y_test)):
                if y_test.iloc[i] != 1:  # Not hold
                    total_signals += 1
                    if y_pred[i] == y_test.iloc[i]:
                        correct_directions += 1

            directional_accuracy = correct_directions / total_signals if total_signals > 0 else 0

            return {
                'overall_accuracy': accuracy,
                'directional_accuracy': directional_accuracy,
                'total_samples': len(y_test),
                'trading_signals': total_signals,
                'class_report': classification_report(y_test, y_pred, output_dict=True),
                'feature_importance': dict(zip(self.feature_columns, model.feature_importances_))
            }

        except Exception as e:
            logger.error(f"Backtest failed: {e}")
            return {'error': str(e)}