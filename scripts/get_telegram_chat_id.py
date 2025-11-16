#!/usr/bin/env python3
"""
Get your Telegram Chat ID from your bot

Instructions:
1. Message your bot on Telegram first (click START or send "hello")
2. Run this script
3. It will show you the correct chat ID

Usage:
    python3 scripts/get_telegram_chat_id.py
"""

import os
import sys

import requests

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config.config import config


def get_chat_id():
    if not config.telegram_bot_token:
        print("❌ TELEGRAM_BOT_TOKEN not found in .env file")
        return

    print("🔍 Checking for messages sent to your bot...")
    print("=" * 60)

    url = f"https://api.telegram.org/bot{config.telegram_bot_token}/getUpdates"

    try:
        response = requests.get(url, timeout=10)
        data = response.json()

        if not data.get("ok"):
            print(f"❌ Error: {data.get('description', 'Unknown error')}")
            return

        updates = data.get("result", [])

        if not updates:
            print("❌ No messages found from your bot!")
            print()
            print("📱 DO THIS:")
            print("1. Open Telegram")
            print("2. Search for your bot by username")
            print("3. Click START button")
            print("4. Run this script again")
            return

        print(f"✅ Found {len(updates)} messages\n")

        # Get all unique chat IDs
        chats = {}
        for update in updates:
            if "message" in update:
                msg = update["message"]
                chat = msg["chat"]
                chat_id = chat["id"]

                if chat_id not in chats:
                    chats[chat_id] = {
                        "id": chat_id,
                        "first_name": chat.get("first_name", ""),
                        "last_name": chat.get("last_name", ""),
                        "username": chat.get("username", ""),
                        "type": chat.get("type", "private"),
                    }

        print("📋 Chat IDs that messaged your bot:")
        print("=" * 60)

        for chat_id, info in chats.items():
            print(f"\nChat ID: {chat_id}")
            print(f"Type: {info['type']}")
            if info["first_name"]:
                print(f"Name: {info['first_name']} {info['last_name']}")
            if info["username"]:
                print(f"Username: @{info['username']}")

        print("\n" + "=" * 60)

        if len(chats) == 1:
            chat_id = list(chats.keys())[0]
            print(f"\n✅ Your Chat ID: {chat_id}")
            print("\n📝 Add this to your .env file:")
            print(f"TELEGRAM_CHAT_ID={chat_id}")

            if config.telegram_chat_id:
                current = str(config.telegram_chat_id).strip()
                correct = str(chat_id).strip()

                if current == correct:
                    print("\n✅ Your .env file is CORRECT!")
                else:
                    print(f"\n⚠️  WRONG! Your .env has: {config.telegram_chat_id}")
                    print(f"⚠️  Should be: {chat_id}")
                    print("\n🔧 Update your .env file with the correct chat ID above")
        else:
            print("\nℹ️  Multiple chats found. Use the private chat ID.")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    get_chat_id()
