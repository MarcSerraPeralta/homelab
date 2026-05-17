from datetime import datetime
import yaml
import os
from pathlib import Path
from dotenv import load_dotenv
import asyncio
from nio import RoomEncryptedFile, AsyncClient, MegolmEvent, Event

from matrix_helpers import (
    get_authenticated_client,
    create_encrypted_room,
    set_room_avatar,
    send_message,
    download_attachment_callback,
    send_image,
    delete_room,
    poll_event_callback,
    send_poll,
    end_poll,
    MY_USER_ID,
)

_ = load_dotenv()

PLOTS_DIR: Path = Path(os.environ.get("PLOTS_DIR"))
SUMMARY_ROOM_ID: str = os.environ.get("SUMMARY_ROOM_ID")
CATEGORIES_FILE: str = os.environ.get("CATEGORIES_FILE")

TODAY = datetime.now()

with open(CATEGORIES_FILE, "r") as file:
    CATEGORIES: list[str] = list(yaml.safe_load(file))


async def get_bank_statements(client: AsyncClient) -> str:
    room_id = await create_encrypted_room(client, f"Expenses {TODAY.strftime('%b %Y')}")
    await set_room_avatar(client, room_id)

    # sync local room cache with server
    _ = await client.sync(timeout=3000)
    await send_message(client, "Upload bank statements to continue", room_id)

    # set bot behaviour when it sees an attached file
    bot_state = {"downloads": 0}
    client.add_event_callback(
        lambda room, event: download_attachment_callback(
            client, room, event, room_id=room_id, bot_state=bot_state
        ),
        RoomEncryptedFile,
    )

    while bot_state["downloads"] < 2:
        _ = await client.sync(timeout=30_000, full_state=True)

    return room_id


async def request_missing_categories(
    client: AsyncClient, unclassified_elements: list[str], room_id: str
) -> list[str]:
    bot_context = {"active_poll_id": "", "user_selection": ""}
    poll_answered_signal = asyncio.Event()  # to track answers asyncronously

    # catch any Event (not just encrypted ones) because the poll response
    # may be a UnkownEvent which is not a MegolmEvent.
    client.add_event_callback(
        lambda room, event: poll_event_callback(
            room,
            event,
            bot_context,
            poll_answered_signal,
            room_id=room_id,
            user_id=MY_USER_ID,
        ),
        Event,
    )
    # enable decyption by setting a callback listening to MegolmEvent.
    client.add_event_callback(lambda r, e: None, MegolmEvent)

    answers: list[str] = []
    for element in unclassified_elements:
        poll_answered_signal.clear()

        poll_id = await send_poll(client, room_id, question=element, options=CATEGORIES)
        bot_context["active_poll_id"] = poll_id

        while not poll_answered_signal.is_set():
            _ = await client.sync(timeout=5000, full_state=False)
            await asyncio.sleep(0.5)

        selected_id = int(bot_context["user_selection"])
        answer = CATEGORIES[selected_id]
        answers.append(answer)

        await end_poll(client, room_id, poll_id)
        _ = await client.sync(timeout=1000)

    return answers


async def send_summary(client: AsyncClient, room_id: str) -> None:
    await delete_room(client, room_id)

    image_path = PLOTS_DIR / f"{TODAY.strftime('%Y-%m')}_summary.jpg"
    await send_image(client, image_path, SUMMARY_ROOM_ID)

    await client.close()
    return


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    client = loop.run_until_complete(get_authenticated_client())

    room_id = loop.run_until_complete(get_bank_statements(client))

    # process bank statements
    unclassified_elements = [
        "10€ 2026/... BIZUM",
        "some other statement",
        "another statement",
    ]

    answers = loop.run_until_complete(
        request_missing_categories(client, unclassified_elements, room_id)
    )
    print(answers)

    # add classification to processed bank statements

    loop.run_until_complete(send_summary(client, room_id))

    loop.run_until_complete(client.close())
