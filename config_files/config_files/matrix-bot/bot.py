from datetime import datetime
import os
from pathlib import Path
from dotenv import load_dotenv
import json
import aiofiles
import asyncio
from nio import (
    AsyncClient,
    AsyncClientConfig,
    RoomCreateResponse,
    RoomPreset,
    EnableEncryptionBuilder,
    UploadError,
    RoomPutStateError,
    RoomKickError,
    RoomLeaveError,
    RoomSendError,
    RoomEncryptedFile,
    Event,
    MatrixRoom,
    DownloadError,
)
from nio.crypto.attachments import decrypt_attachment

_ = load_dotenv()

STORE_DIR: Path = Path(os.environ.get("STORE_DIR"))
CREDS_FILE: Path = STORE_DIR / os.environ.get("CREDENTIALS_NAME")
DOWNLOAD_DIR: Path = Path(os.environ.get("DOWNLOAD_DIR"))

HOMESERVER: str = os.environ.get("HOMESERVER")
BOT_USER_ID: str = os.environ.get("BOT_USER_ID")
MY_USER_ID: str = os.environ.get("MY_USER_ID")
ROOM_IMAGE_FILE: str = os.environ.get("ROOM_IMAGE_FILE")
SUMMARY_ROOM_ID: str = os.environ.get("SUMMARY_ROOM_ID")

TODAY = datetime.now()
DOWNLOAD_DIR.mkdir(exist_ok=True, parents=True)


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


async def create_encrypted_room(client: AsyncClient, room_name: str) -> str:
    # define room configuration:
    # - power level: bot and my user are admins, but bot can kick me out.
    # - encryption enabled.
    initial_state = [
        {
            "type": "m.room.power_levels",
            "content": {"users": {BOT_USER_ID: 100, MY_USER_ID: 99}},
        },
        {
            "type": "m.room.encryption",
            "content": EnableEncryptionBuilder().as_dict()["content"],
        },
    ]

    response = await client.room_create(
        name=room_name,
        invite=[MY_USER_ID],
        is_direct=True,
        preset=RoomPreset.private_chat,
        initial_state=initial_state,
    )

    if not isinstance(response, RoomCreateResponse):
        raise ValueError(f"Failed to create room: {response.message}")

    return response.room_id


async def set_room_avatar(client: AsyncClient, room_id: str) -> None:
    image_file = Path(ROOM_IMAGE_FILE)
    if not image_file.exists():
        raise ValueError(f"Image file not found: {image_file}.")

    # upload image to synapse
    async with aiofiles.open(image_file, "r+b") as file:
        upload_response, _ = await client.upload(
            file,
            content_type="image/jpeg",
            filename=image_file.name,
            filesize=image_file.stat().st_size,
        )

    if isinstance(upload_response, UploadError):
        raise ValueError("Upload failed with error: {upload_response.message}.")

    # assign uploaded image as room profile avatar
    mxc_uri = upload_response.content_uri
    avatar_content = {"url": mxc_uri, "info": {"mimetype": "image/jpeg"}}

    state_response = await client.room_put_state(
        room_id=room_id,
        event_type="m.room.avatar",
        content=avatar_content,
    )

    if isinstance(state_response, RoomPutStateError):
        raise ValueError(f"Failed to set room avatar: {state_response.message}")

    return


async def delete_room(client: AsyncClient, room_id: str) -> None:
    # kick myself from room
    kick_response = await client.room_kick(
        room_id=room_id,
        user_id=MY_USER_ID,
    )

    if isinstance(kick_response, RoomKickError):
        raise ValueError(f"Could not kick user: {kick_response.message}")

    # bot leaves room, dropping the room membership to 0
    leave_response = await client.room_leave(room_id=room_id)

    if isinstance(leave_response, RoomLeaveError):
        raise ValueError(f"Failed to leave room: {leave_response.message}")
    return


async def send_message(client: AsyncClient, message: str, room_id: str) -> None:
    response = await client.room_send(
        room_id=room_id,
        message_type="m.room.message",
        content={"msgtype": "m.text", "body": message},
        ignore_unverified_devices=True,  # bot is not a verified device
    )

    if isinstance(response, RoomSendError):
        raise ValueError(f"Failed to send message: {response.message}.")
    return


async def media_callback(
    client: AsyncClient,
    room: MatrixRoom,
    event: Event,
    room_id: str,
    bot_state: dict[str, int],
) -> None:
    # listen only to the specified room
    if room.room_id != room_id:
        return

    # extract file dictionary payload from the source JSON content block
    file_info = event.source.get("content", {}).get("file")
    if not file_info:
        raise ValueError("This event does not contain valid encrypted file metadata.")
    mxc_url: str = file_info.get("url")

    media_response = await client.download(mxc_url)
    if isinstance(media_response, DownloadError):
        raise ValueError(f"Failed to download file: {media_response.message}.")

    decrypted_bytes = decrypt_attachment(
        media_response.body,
        file_info["key"]["k"],
        file_info["hashes"]["sha256"],
        file_info["iv"],
    )

    output_path = DOWNLOAD_DIR / f"{TODAY.strftime('%Y-%m')}-{bot_state['downloads']}"
    with open(output_path, "wb") as f:
        f.write(decrypted_bytes)
    bot_state["downloads"] += 1

    return


async def get_bank_statements() -> str:

    client = await get_authenticated_client()

    room_id = await create_encrypted_room(client, f"Expenses {TODAY.strftime('%b %Y')}")
    await set_room_avatar(client, room_id)

    # sync local room cache with server
    _ = await client.sync(timeout=3000)
    await send_message(client, "Upload bank statements to continue", room_id)

    # set bot behaviour when it sees an attached file
    bot_state = {"downloads": 0}
    client.add_event_callback(
        lambda room, event: media_callback(
            client, room, event, room_id=room_id, bot_state=bot_state
        ),
        RoomEncryptedFile,
    )

    while bot_state["downloads"] < 2:
        _ = await client.sync(timeout=30_000, full_state=True)

    await client.close()
    return room_id


async def process_missing_categories(missing_categories) -> None:
    client = await get_authenticated_client()
    return


async def send_summary(room_id: str) -> None:
    client = await get_authenticated_client()
    await delete_room(client, room_id)
    # send summary to SUMMARY_ROOM_ID
    return


if __name__ == "__main__":
    room_id = asyncio.run(get_bank_statements())

    # process bank statements

    asyncio.run(process_missing_categories([]))
    asyncio.run(send_summary(room_id))
