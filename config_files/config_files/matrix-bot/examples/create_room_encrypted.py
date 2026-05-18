import json
import pathlib
import asyncio
from nio import (
    AsyncClient,
    AsyncClientConfig,
    RoomCreateResponse,
    RoomPreset,
    EnableEncryptionBuilder,  # <-- Native encryption module helper
)

STORE_DIR = pathlib.Path("./store_gemini_bot-expenses")
CREDS_FILE = STORE_DIR / "credentials.json"

MY_USER_ID = "@marc:servidoret.com"
DESIRED_ALIAS = "my-new-room"


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

    print(f"🏗️ Creating E2EE room, making you Admin, and inviting {MY_USER_ID}...")

    # 1. Use the built-in matrix-nio builder to create a compliant encryption payload
    encryption_event = EnableEncryptionBuilder().as_dict()

    # 2. Define the room structure, explicitly assigning you Admin powers (Power Level 100)
    power_level_content = {
        "users": {
            "@bot-expenses:servidoret.com": 100,  # The bot is creator/admin
            MY_USER_ID: 100,  # Force YOU to be a full co-Admin immediately
        }
    }

    # 3. Compile the structural state changes cleanly
    initial_state_events = [
        {"type": "m.room.power_levels", "content": power_level_content},
        {"type": "m.room.encryption", "content": encryption_event["content"]},
    ]

    # Execute the room creation sequence
    response = await client.room_create(
        name="Secure Expenses Alerts",
        topic="Automated homelab metrics via End-to-End Encryption",
        invite=[MY_USER_ID],
        is_direct=True,
        preset=RoomPreset.private_chat,
        initial_state=initial_state_events,
        alias=DESIRED_ALIAS,
    )

    if isinstance(response, RoomCreateResponse):
        print(f"\n🎉 SUCCESS! Room created with ID: {response.room_id}")
        print("👉 Open Element, accept the invite, and check your Room Settings.")
        print("You will see that you are an Administrator and E2EE is cleanly active!")
    else:
        print(f"❌ Failed to create room: {response.message}")

    await client.close()


if __name__ == "__main__":
    asyncio.run(main())
