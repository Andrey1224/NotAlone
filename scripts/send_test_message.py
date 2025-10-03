#!/usr/bin/env python3
"""Script to send test messages from AlisaTest to MisterAndrey."""

import asyncio
import sys

import httpx


async def send_message_from_alisa(text: str) -> None:
    """
    Send a message from AlisaTest (user_id=3, tg_id=999999999) to MisterAndrey.

    This simulates AlisaTest sending a message by calling the /chat/relay API.
    The bot will then forward the message to MisterAndrey (tg_id=1057355026).
    """
    api_url = "http://localhost:8000/chat/relay"

    payload = {"from_user": 999999999, "text": text}  # AlisaTest's fake tg_id

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(api_url, json=payload, timeout=10.0)
            response.raise_for_status()

            result = response.json()
            print("✅ Message sent successfully!")
            print(f"   Response: {result}")
            print(f"   Peer tg_id: {result.get('peer_tg_id')}")
            print(f"\n📨 MisterAndrey should receive: '✉️ АлисаТест: {text}'")

        except httpx.HTTPStatusError as e:
            print(f"❌ HTTP error: {e.response.status_code}")
            print(f"   Response: {e.response.text}")
        except Exception as e:
            print(f"❌ Error: {e}")


def main() -> None:
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python send_test_message.py <message>")
        print('Example: python send_test_message.py "Привет! Как дела?"')
        sys.exit(1)

    message_text = " ".join(sys.argv[1:])
    print(f"🤖 Sending message from АлисаТест: '{message_text}'")

    asyncio.run(send_message_from_alisa(message_text))


if __name__ == "__main__":
    main()
