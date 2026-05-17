import json
from pathlib import Path
import asyncio
import os
from dotenv import load_dotenv
from nio import (
    AsyncClient,
    AsyncClientConfig,
    Event,
    MatrixRoom,
    MegolmEvent,
    RoomSendError,
)

_ = load_dotenv()

STORE_DIR: Path = Path(os.environ.get("STORE_DIR"))
CREDS_FILE: Path = STORE_DIR / os.environ.get("CREDENTIALS_NAME")
HOMESERVER: str = os.environ.get("HOMESERVER")
BOT_USER_ID: str = os.environ.get("BOT_USER_ID")
MY_USER_ID: str = os.environ.get("MY_USER_ID")
TARGET_ROOM_ID: str = os.environ.get("SUMMARY_ROOM_ID")

# 1. Hard-coded survey questions and answer arrays
POLL_QUESTIONS = [
    {
        "id": "q1",
        "question": "Which account did you use for the weekly groceries?",
        "options": [
            {"id": "opt_cc", "text": "Credit Card (Joint)"},
            {"id": "opt_deb", "text": "Debit Card (Personal)"},
            {"id": "opt_cash", "text": "Cash Vault"},
        ],
    },
    {
        "id": "q2",
        "question": "Is this a recurring monthly subscription expense?",
        "options": [
            {"id": "opt_yes", "text": "Yes, log as recurring"},
            {"id": "opt_no", "text": "No, it's a one-off payment"},
        ],
    },
]

# Trackers for running dynamic steps
poll_answered_signal = asyncio.Event()
current_active_poll_id = None
user_selections = {}


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


async def send_poll(
    client: AsyncClient,
    room_id: str,
    question_block: dict[str, str | list[dict[str, str]]],
) -> str:
    """Dispatches an MSC3381 compliant poll event to the room timeline."""

    # Generate fallback text layout for older clients
    fallback_text = f"Poll: {question_block['question']}\n"
    for idx, opt in enumerate(question_block["options"], start=1):
        fallback_text += f"{idx}. {opt['text']}\n"

    poll_content = {
        "msgtype": "org.matrix.msc3381.poll.start",
        "body": fallback_text,
        "org.matrix.msc3381.poll.start": {
            "question": {
                "org.matrix.msc1767.text": question_block["question"],
                "body": question_block["question"],
            },
            "kind": "org.matrix.msc3381.poll.disclosed",
            "max_selections": 1,
            "answers": [
                {
                    "id": opt["id"],
                    "org.matrix.msc1767.text": opt["text"],
                    "body": opt["text"],
                }
                for opt in question_block["options"]
            ],
        },
    }

    response = await client.room_send(
        room_id=room_id,
        message_type="org.matrix.msc3381.poll.start",
        content=poll_content,
        ignore_unverified_devices=True,
    )
    if isinstance(response, RoomSendError):
        raise ValueError(f"Failed to send poll: {response.message}.")
    return response.event_id


async def end_poll(
    client: AsyncClient, room_id: str, poll_event_id: str, question_text: str
) -> None:
    """Closes the poll on the timeline so users cannot vote further."""
    end_content = {
        "m.relates_to": {"rel_type": "m.reference", "event_id": poll_event_id},
        "org.matrix.msc3381.poll.end": {},
        "body": f"The poll for '{question_text}' is now closed.",
        "msgtype": "m.notice",
    }

    response = await client.room_send(
        room_id=room_id,
        message_type="org.matrix.msc3381.poll.end",
        content=end_content,
        ignore_unverified_devices=True,
    )
    if isinstance(response, RoomSendError):
        raise ValueError(f"Failed to end poll: {response.message}.")
    return


async def custom_event_callback(room: MatrixRoom, event: Event):
    """Listens globally for incoming decrypted timeline events."""
    global current_active_poll_id

    if room.room_id != TARGET_ROOM_ID or event.sender != MY_USER_ID:
        return

    # Check if the incoming event is a response to our open poll
    event_content = event.source.get("content", {})
    relation = event_content.get("m.relates_to", {})

    if (
        relation.get("rel_type") == "m.reference"
        and relation.get("event_id") == current_active_poll_id
    ):
        poll_resp = event_content.get("org.matrix.msc3381.poll.response")
        if poll_resp:
            selections = poll_resp.get("answers", [])
            if selections:
                chosen_option_id = selections[0]
                user_selections[current_active_poll_id] = chosen_option_id

                # Unlock the execution loop for this question
                poll_answered_signal.set()


async def main():
    global current_active_poll_id
    client = await get_authenticated_client()

    # Track structural events natively
    client.add_event_callback(custom_event_callback, Event)
    client.add_event_callback(lambda r, e: None, MegolmEvent)

    print(f"📡 Survey bot online. Connected to room: {TARGET_ROOM_ID}")

    try:
        # Loop sequentially through each question entry
        for q_block in POLL_QUESTIONS:
            print(f"\n🚀 Firing Poll Question: {q_block['question']}")

            # 2.1 Send the poll and track its structural event ID
            poll_answered_signal.clear()
            current_active_poll_id = await send_poll(client, TARGET_ROOM_ID, q_block)

            # 2.2 Wait continuously for you to make a choice
            print("⏳ Waiting for user input via Element client...")
            while not poll_answered_signal.is_set():
                await client.sync(timeout=5000, full_state=False)
                await asyncio.sleep(0.5)

            # Extract human readable translation
            selected_id = user_selections[current_active_poll_id]
            readable_answer = next(
                o["text"] for o in q_block["options"] if o["id"] == selected_id
            )
            q_block["resolved_answer"] = readable_answer

            # 2.3 Close the poll on the active timeline
            print("🔒 Answer captured! Finalizing timeline footprint...")
            await end_poll(
                client, TARGET_ROOM_ID, current_active_poll_id, q_block["question"]
            )

            # Run a quick sync pulse to flush event streams
            await client.sync(timeout=1000)

        # 3. Print the final results to standard output
        print("\n" + "=" * 40)
        print("📊 SURVEY COMPLETE — REPORT SUMMARY:")
        print("=" * 40)
        for idx, q_block in enumerate(POLL_QUESTIONS, 1):
            print(f"Question {idx}: {q_block['question']}")
            print(f"👉 Answered : {q_block.get('resolved_answer', 'None')}\n")
        print("=" * 40)

    finally:
        await client.close()
        print("\n🔌 Session closed cleanly.")


if __name__ == "__main__":
    asyncio.run(main())
