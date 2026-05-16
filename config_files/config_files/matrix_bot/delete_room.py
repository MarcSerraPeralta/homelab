import json
import pathlib
import asyncio
from nio import AsyncClient, AsyncClientConfig, RoomKickResponse, RoomLeaveResponse

STORE_DIR = pathlib.Path("./store_gemini_bot-expenses")
CREDS_FILE = STORE_DIR / "credentials.json"

# Update these to match your setup
MY_USER_ID = "@marc:servidoret.com" 
ROOM_ID_TO_DELETE = "!WdvtWcojYbNGgACQrC:servidoret.com" # Put the ID of the room you want to destroy here

async def main():
    with open(CREDS_FILE, "r") as f:
        creds = json.load(f)

    config = AsyncClientConfig(encryption_enabled=True)
    client = AsyncClient(
        "https://matrix.servidoret.com",
        "@bot-expenses:servidoret.com",
        device_id=creds["device_id"],
        store_path=str(STORE_DIR),
        config=config,
    )
    client.restore_login(
        user_id="@bot-expenses:servidoret.com",
        device_id=creds["device_id"],
        access_token=creds["access_token"],
    )

    print("🔄 Connecting bot to homeserver...")
    await client.sync(timeout=3000)

    print(f"🥾 Step 1: Bot is kicking {MY_USER_ID} from the room...")
    # The bot uses its co-admin powers to evict your user account
    kick_response = await client.room_kick(
        room_id=ROOM_ID_TO_DELETE,
        user_id=MY_USER_ID,
        reason="Purging and deleting this room."
    )

    if isinstance(kick_response, RoomKickResponse):
        print("✅ User kicked successfully.")
    else:
        print(f"⚠️ Could not kick user (you might have already left): {kick_response.message}")

    print("🚶 Step 2: Bot is leaving the room...")
    # The bot leaves, dropping the room membership to 0
    leave_response = await client.room_leave(room_id=ROOM_ID_TO_DELETE)

    if isinstance(leave_response, RoomLeaveResponse):
        print("\n🎉 SUCCESS! The room has been completely abandoned and is now marked for deletion.")
        print("It will instantly disappear from your Element sidebar.")
    else:
        print(f"❌ Failed to leave room: {leave_response.message}")

    await client.close()

if __name__ == "__main__":
    asyncio.run(main())
