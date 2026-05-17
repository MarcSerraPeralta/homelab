import io
import json
import pathlib
import asyncio
import mimetypes
from nio import AsyncClient, AsyncClientConfig, UploadResponse

STORE_DIR = pathlib.Path("./store_gemini_bot-expenses")
CREDS_FILE = STORE_DIR / "credentials.json"

# Configurations
ROOM_ID = "!BniPKwqTilbnXsRoyO:servidoret.com"  # Put your E2EE room ID here
IMAGE_PATH = "./montly-expenses_icon.jpg"  # Path to your local image file


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

    local_file = pathlib.Path(IMAGE_PATH)
    if not local_file.exists():
        print(f"❌ Error: Local image file not found at {IMAGE_PATH}")
        await client.close()
        return

    mime_type, _ = mimetypes.guess_type(IMAGE_PATH)
    if not mime_type:
        mime_type = "image/jpeg"

    file_size = local_file.stat().st_size

    print(f"📤 Step 1: Uploading {local_file.name} ({file_size} bytes) to Synapse...")

    with open(local_file, "rb") as image_file:
        raw_bytes = image_file.read()
        buffer_stream = io.BytesIO(raw_bytes)

        upload_response = await client.upload(
            buffer_stream,
            content_type=mime_type,
            filename=local_file.name,
            filesize=file_size,
        )

    # --- FIX: Direct parsing of the nio response object or tuple ---
    mxc_uri = None

    # If it's a tuple, unwrap the first element
    if isinstance(upload_response, tuple):
        upload_response = upload_response[0]

    # Now parse the underlying object safely
    if isinstance(upload_response, UploadResponse):
        mxc_uri = upload_response.content_uri
    elif isinstance(upload_response, UploadError):
        print(f"❌ Upload failed with error: {upload_response.message}")
        await client.close()
        return
    elif isinstance(upload_response, dict):
        mxc_uri = upload_response.get("content_uri")

    if not mxc_uri:
        print(f"❌ Upload failed. Unexpected response format: {upload_response}")
        await client.close()
        return

    print(f"✅ Upload successful! Media URI extracted: {mxc_uri}")

    print("🖼️ Step 2: Assigning the media URI to the room profile avatar...")

    avatar_content = {"url": mxc_uri, "info": {"mimetype": mime_type}}

    state_response = await client.room_put_state(
        room_id=ROOM_ID,
        event_type="m.room.avatar",
        content=avatar_content,
        state_key="",
    )

    if hasattr(state_response, "event_id"):
        print("\n🎉 SUCCESS! The room profile picture has been updated.")
        print("Check Element right now—your room avatar is cleanly applied!")
    else:
        print(f"❌ Failed to set room avatar: {state_response.message}")

    await client.close()


if __name__ == "__main__":
    asyncio.run(main())
