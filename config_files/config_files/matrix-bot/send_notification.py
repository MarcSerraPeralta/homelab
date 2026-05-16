import json
import pathlib
import asyncio
from nio import AsyncClient, AsyncClientConfig, RoomSendResponse, RoomSendError

STORE_DIR = pathlib.Path("./store_gemini_bot-expenses")
CREDS_FILE = STORE_DIR / "credentials.json"

# Configurations
HOMESERVER = "https://matrix.servidoret.com"
USER_ID = "@bot-expenses:servidoret.com"
ROOM_ID = "!GgmBycypOfQkTMrLgf:servidoret.com"  # The room ID from your logs

async def main():
    if not CREDS_FILE.exists():
        print("❌ Stored credentials not found. Run your preparation script first.")
        return

    with open(CREDS_FILE, "r") as f:
        creds = json.load(f)

    # Enable E2EE inside the client configuration
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

    # 1. Sync once downstream so nio grabs latest room encryption states
    print("Syncing encryption states...")
    await client.sync(timeout=3000)

    # 2. Send your encrypted text message
    print(f"Sending encrypted alert to room {ROOM_ID}...")
    response = await client.room_send(
        room_id=ROOM_ID,
        message_type="m.room.message",
        content={
            "msgtype": "m.text",
            "body": "🔒 Hello! This is an end-to-end encrypted notification from your home server bot."
        },
        ignore_unverified_devices=True  # <-- CRITICAL: Bypasses emoji verification check
    )

    # 3. Verify it went through smoothly
    if isinstance(response, RoomSendResponse):
        print(f"✅ Success! Message sent. Event ID: {response.event_id}")
    elif isinstance(response, RoomSendError):
        print(f"❌ Failed to send message: {response.message} (Error code: {response.status_code})")

    await client.close()

if __name__ == "__main__":
    asyncio.run(main())
