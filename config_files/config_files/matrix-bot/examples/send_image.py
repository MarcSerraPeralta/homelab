import os
from dotenv import load_dotenv
import json
import mimetypes
from pathlib import Path
import aiofiles
import asyncio
from nio import (
    AsyncClientConfig,
    AsyncClient,
    UploadError,
    RoomSendError,
)

_ = load_dotenv()

STORE_DIR: Path = Path(os.environ.get("STORE_DIR"))
CREDS_FILE: Path = STORE_DIR / os.environ.get("CREDENTIALS_NAME")

HOMESERVER: str = os.environ.get("HOMESERVER")
BOT_USER_ID: str = os.environ.get("BOT_USER_ID")
ROOM_IMAGE_FILE: str = os.environ.get("ROOM_IMAGE_FILE")
SUMMARY_ROOM_ID: str = os.environ.get("SUMMARY_ROOM_ID")


async def get_authenticated_client() -> AsyncClient:
    with open(CREDS_FILE, "r") as f:
        creds: dict[str, str] = json.load(f)

    config = AsyncClientConfig(encryption_enabled=True)
    client = AsyncClient(
        HOMESERVER,
        BOT_USER_ID,
        device_id=creds["device_id"],
        store_path=str(STORE_DIR),
        config=config,
    )
    client.restore_login(
        user_id=BOT_USER_ID,
        device_id=creds["device_id"],
        access_token=creds["access_token"],
    )

    # connect bot to server
    _ = await client.sync(timeout=3000)
    return client


async def send_image_message(
    client: AsyncClient, image_path: str | Path, room_id: str
) -> None:
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"Target image file not found at: {path}")

    # 1. Determine file details required by the server
    mime_type, _ = mimetypes.guess_type(path)
    mime_type = mime_type or "image/jpeg"
    file_size = path.stat().st_size

    print(f"🔒 Opening stream and encrypting file payload: {path.name}...")

    # 2. Open the file in binary read/write mode ("r+b") as required by the docs.
    # Passing the file object directly allows matrix-nio to upload it lazily.
    async with aiofiles.open(path, "r+b") as file:
        upload_response, decryption_info = await client.upload(
            data_provider=file,
            content_type=mime_type,
            filename=path.name,
            filesize=file_size,
            encrypt=True,  # <-- Crucial: Tells the library to return decryption info keys
        )

    # 3. Guard clause against network or server upload issues
    if isinstance(upload_response, UploadError):
        raise ValueError(
            f"Server rejected media payload upload: {upload_response.message}"
        )

    print("📨 Mapping attachment cryptographic metadata keys to room event timeline...")

    # 4. Construct a spec-compliant metadata payload mapping
    # Note that custom content_type values are ignored by the server if encrypt=True,
    # so we explicitly provide the mimetype inside the 'info' block.
    image_content = {
        "msgtype": "m.image",
        "body": path.name,  # The fallback title string visible in message notifications
        "info": {
            "mimetype": mime_type,
            "size": file_size,
        },
        "file": {
            "url": upload_response.content_uri,
            "key": decryption_info["key"],
            "iv": decryption_info["iv"],
            "hashes": decryption_info["hashes"],
            "v": decryption_info["v"],
        },
    }

    # 5. Dispatch the structurally complete cryptographic event to the timeline
    response = await client.room_send(
        room_id=room_id,
        message_type="m.room.message",
        content=image_content,
        ignore_unverified_devices=True,
    )

    if isinstance(response, RoomSendError):
        raise ValueError(
            f"Failed to post image metadata to the timeline: {response.message}"
        )

    print(f"🎉 SUCCESS! Encrypted image '{path.name}' sent successfully.")
    return


async def main():
    client = await get_authenticated_client()
    await send_image_message(client, ROOM_IMAGE_FILE, SUMMARY_ROOM_ID)
    await client.close()
    return


if __name__ == "__main__":
    asyncio.run(main())
