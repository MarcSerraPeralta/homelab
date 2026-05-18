import json
import pathlib
import asyncio
from nio import AsyncClient, AsyncClientConfig, RoomMessageText

STORE_DIR = pathlib.Path("./store_gemini_bot-expenses")
CREDS_FILE = STORE_DIR / "credentials.json"

HOMESERVER = "https://matrix.servidoret.com"
USER_ID = "@bot-expenses:servidoret.com"


async def message_callback(room, event: RoomMessageText):
    """
    This callback triggers automatically every time a new text message
    is received and successfully decrypted by matrix-nio.
    """
    # Skip printing the bot's own messages to keep the terminal clean
    if event.sender == USER_ID:
        return

    # Fallback to room_id if the room doesn't have a human-readable name yet
    room_name = room.display_name or room.room_id

    print(f"📩 New Message in [{room_name}]")
    print(f"   👤 Sender: {event.sender}")
    print(f"   💬 Text:   {event.body}")
    print("-" * 40)


async def main():
    if not CREDS_FILE.exists():
        print("❌ Stored credentials not found. Run your preparation script first.")
        return

    with open(CREDS_FILE, "r") as f:
        creds = json.load(f)

    # Enable encryption in the config so the background engine handles decryption
    config = AsyncClientConfig(encryption_enabled=True)

    client = AsyncClient(
        HOMESERVER,
        USER_ID,
        device_id=creds["device_id"],
        store_path=str(STORE_DIR),
        config=config,
    )

    client.restore_login(
        user_id=USER_ID,
        device_id=creds["device_id"],
        access_token=creds["access_token"],
    )

    # Register the callback specifically for text messages.
    # matrix-nio will only pass successfully decrypted events to this callback.
    client.add_event_callback(message_callback, RoomMessageText)

    print("🛰️  Bot is now online and listening for encrypted messages...")
    print("Go to Element, type a message in the room, and watch this terminal.")
    print("Press Ctrl+C to stop.")

    try:
        # full_state=False prevents flooding the terminal with historical room setups
        await client.sync_forever(timeout=30000, full_state=False)
    except KeyboardInterrupt:
        print("\nStopping listener...")
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
