import pathlib
import json
import asyncio
from nio import (
    AsyncClient,
    AsyncClientConfig,
    MegolmEvent,
    RoomEncryptedFile,
    RoomEncryptedImage,
)
from nio.crypto.attachments import decrypt_attachment

STORE_DIR = pathlib.Path("./store_gemini_bot-expenses")
CREDS_FILE = STORE_DIR / "credentials.json"
DOWNLOAD_DIR = pathlib.Path("./downloads")

DOWNLOAD_DIR.mkdir(exist_ok=True)

# 🎯 TARGET CONFIGURATION
TARGET_ROOM_ID = "!BniPKwqTilbnXsRoyO:servidoret.com"


async def media_callback(client, room, event):
    # 🛑 FILTER: Lock onto the specified room
    if room.room_id != TARGET_ROOM_ID:
        return

    # Extract the file dictionary payload directly from the source JSON content block
    file_info = event.source.get("content", {}).get("file")
    if not file_info:
        print("❌ This event does not contain valid encrypted file metadata.")
        return

    filename = event.body
    mxc_url = file_info.get("url")

    print(f"\n⚡ Verified media event detected: {filename}")
    print(f"   Source URL: {mxc_url}")
    print("   ⬇️ Downloading media payload...")

    media_response = await client.download(mxc_url)

    if isinstance(media_response, tuple):
        media_response = media_response[0]

    if hasattr(media_response, "body"):
        raw_bytes = media_response.body

        print("   🔒 File is End-to-End Encrypted. Decrypting data layout...")

        try:
            # FIXED: Correct argument order according to the matrix-nio definition:
            # decrypt_attachment(ciphertext, key, hashes, iv)
            decrypted_bytes = decrypt_attachment(
                raw_bytes,
                file_info["key"]["k"],
                file_info["hashes"]["sha256"],
                file_info["iv"],
            )
        except Exception as crypto_err:
            print(f"   ❌ Cryptographic Error: {crypto_err}")
            return

        # Save the completely validated and unpacked document to local storage
        output_path = DOWNLOAD_DIR / filename
        with open(output_path, "wb") as f:
            f.write(decrypted_bytes)

        print(f"   🎉 SUCCESS! File saved locally to: {output_path.resolve()}\n")
    else:
        msg = getattr(media_response, "message", "Download network timeout")
        print(f"   ❌ Failed to download file data stream: {msg}\n")


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

    # Listen directly to specialized media classes
    client.add_event_callback(
        lambda room, event: media_callback(client, room, event), RoomEncryptedFile
    )
    client.add_event_callback(
        lambda room, event: media_callback(client, room, event), RoomEncryptedImage
    )

    # Maintain crypto session handshakes in background
    client.add_event_callback(lambda r, e: None, MegolmEvent)

    print(f"🔄 Bot online and locked onto target room: {TARGET_ROOM_ID}")
    print("Listening for file uploads...")

    await client.sync_forever(timeout=30000, full_state=True)


if __name__ == "__main__":
    asyncio.run(main())
