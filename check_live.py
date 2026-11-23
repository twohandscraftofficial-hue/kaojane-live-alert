
"""KaoJane Telegram LIVE notifier. Private-chat opt-in and per-artist preferences."""

import asyncio
import json
import os
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from cryptography.fernet import Fernet, InvalidToken
from TikTokLive import TikTokLiveClient

PEOPLE = {
    "janeeyeh": "เจนเย่",
    "supassra_sp": "พี่เก้า",
}
ALL_ARTISTS = list(PEOPLE)
LIVE_STATE = Path("live_state.json")
MEMBERS_FILE = Path("subscribers.enc")

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
OWNER_ID = os.environ.get("TELEGRAM_CHAT_ID", "").strip()


def api(method, params):
    if not TOKEN:
        raise RuntimeError("Missing TELEGRAM_BOT_TOKEN secret")

    data = urlencode({
        k: (
            json.dumps(v, ensure_ascii=False)
            if isinstance(v, (dict, list))
            else v
        )
        for k, v in params.items()
    }).encode()

    req = Request(
        f"https://api.telegram.org/bot{TOKEN}/{method}",
        data=data,
        method="POST",
    )

    try:
        with urlopen(req, timeout=25) as response:
            payload = json.load(response)
    except HTTPError as exc:
        detail = exc.read().decode(errors="replace")[:250]
        raise RuntimeError(
            f"Telegram {method} returned HTTP {exc.code}: {detail}"
        ) from None
    except URLError as exc:
        raise RuntimeError(
            f"Telegram {method} network failure: {exc.reason}"
        ) from None

    if not payload.get("ok"):
        raise RuntimeError(
            f"Telegram {method}: "
            f"{payload.get('description', 'unknown error')}"
        )

    return payload["result"]


def menu():
    return {
        "inline_keyboard": [
            [
                {
                    "text": "💗 ทั้งสองคน",
                    "callback_data": "follow:both",
                }
            ],
            [
                {
                    "text": "🌷 เจนเย่",
                    "callback_data": "follow:janeeyeh",
                },
                {
                    "text": "✨ พี่เก้า",
                    "callback_data": "follow:supassra_sp",
                },
            ],
            [
                {
                    "text": "🔕 ปิดแจ้งเตือน",
                    "callback_data": "follow:stop",
                }
            ],
        ]
    }


def send(chat_id, text, with_menu=False):
    params = {
        "chat_id": str(chat_id),
        "text": text,
        "disable_web_page_preview": "true",
    }

    if with_menu:
        params["reply_markup"] = menu()

    api("sendMessage", params)


def selection_label(selected):
    if not selected:
        return "ปิดแจ้งเตือน"

    if len(selected) == 2:
        return "เจนเย่ + พี่เก้า"

    return PEOPLE[selected[0]]


def load_members():
    key = os.environ.get("SUBSCRIBERS_KEY", "")

    if not key:
        raise RuntimeError(
            "Missing SUBSCRIBERS_KEY secret; "
            "generate with generate_key.py"
        )

    cipher = Fernet(key.encode())

    if MEMBERS_FILE.exists():
        try:
            db = json.loads(
                cipher.decrypt(
                    MEMBERS_FILE.read_bytes()
                ).decode()
            )
        except (InvalidToken, ValueError, KeyError) as exc:
            raise RuntimeError(
                "Cannot decrypt subscribers.enc: "
                "check SUBSCRIBERS_KEY. "
                "Do not overwrite the file."
            ) from exc
    else:
        db = {
            "next_update_id": 0,
            "members": {},
            "notified": {},
        }

        if OWNER_ID:
            db["members"][OWNER_ID] = ALL_ARTISTS.copy()

    db.setdefault("notified", {})

    return db, cipher


def save_members(db, cipher):
    plaintext = json.dumps(
        db,
        ensure_ascii=False,
        sort_keys=True,
    ).encode()

    if MEMBERS_FILE.exists():
        existing = cipher.decrypt(
            MEMBERS_FILE.read_bytes()
        )
        if existing == plaintext:
            return

    MEMBERS_FILE.write_bytes(
        cipher.encrypt(plaintext)
    )


def configure(db, chat_id, artists, note=""):
    members = db["members"]

    if artists:
        members[chat_id] = artists
    else:
        members.pop(chat_id, None)

    prefix = (note + "\n") if note else ""

    send(
        chat_id,
        f"{prefix}💗 ตั้งค่าการแจ้งเตือน: "
        f"{selection_label(artists)}\n"
        "เปลี่ยนได้ทุกเมื่อด้วย /start",
        with_menu=True,
    )


def process_updates(db):
    """Poll private chats and save the update cursor."""

    for _ in range(5):
        updates = api(
            "getUpdates",
            {
                "offset": db["next_update_id"],
                "limit": 100,
                "timeout": 0,
                "allowed_updates": [
                    "message",
                    "callback_query",
                ],
            },
        )

        if not updates:
            break

        for update in updates:
            message = update.get("message")
            callback = update.get("callback_query")

            if message:
                chat = message.get("chat", {})

                if chat.get("type") != "private":
                    db["next_update_id"] = (
                        update["update_id"] + 1
                    )
                    continue

                chat_id = str(chat["id"])
                command = (
                    message.get("text", "")
                    .strip()
                    .split(" ", 1)[0]
                    .lower()
                    .split("@")[0]
                )

                if command in ("/start", "/both"):
                    configure(
                        db,
                        chat_id,
                        ALL_ARTISTS.copy(),
                        "สมัครรับแจ้งเตือนแล้ว!",
                    )

                elif command in ("/jane", "/janeyeh"):
                    configure(
                        db,
                        chat_id,
                        ["janeeyeh"],
                    )

                elif command in ("/kao", "/supassra"):
                    configure(
                        db,
                        chat_id,
                        ["supassra_sp"],
                    )

                elif command == "/stop":
                    configure(db, chat_id, [])

                elif command in (
                    "/status",
                    "/help",
                    "/settings",
                ):
                    selected = db["members"].get(
                        chat_id, []
                    )

                    send(
                        chat_id,
                        f"💗 สถานะ: "
                        f"{selection_label(selected)}\n"
                        "เลือกการแจ้งเตือนด้านล่างได้เลย",
                        with_menu=True,
                    )

            elif callback:
                callback_id = callback.get("id")
                msg = callback.get("message") or {}
                chat = msg.get("chat") or {}
                user = callback.get("from") or {}

                if (
                    chat.get("type") == "private"
                    and str(chat.get("id"))
                    == str(user.get("id"))
                ):
                    chat_id = str(chat["id"])
                    data = callback.get("data", "")

                    choices = {
                        "follow:both": ALL_ARTISTS.copy(),
                        "follow:janeeyeh": ["janeeyeh"],
                        "follow:supassra_sp": ["supassra_sp"],
                        "follow:stop": [],
                    }

                    if data in choices:
                        configure(
                            db,
                            chat_id,
                            choices[data],
                        )

                # FIX: Ignore expired Telegram callback queries.
                # GitHub Actions polls every 10 minutes,
                # so callback query IDs may expire.
                if callback_id:
                    try:
                        api(
                            "answerCallbackQuery",
                            {"callback_query_id": callback_id},
                        )
                    except RuntimeError as exc:
                        error_text = str(exc)

                        if (
                            "HTTP 400" in error_text
                            and (
                                "query is too old" in error_text
                                or "query ID is invalid" in error_text
                            )
                        ):
                            print(
                                "Expired Telegram callback skipped"
                            )
                        else:
                            raise

            db["next_update_id"] = (
                update["update_id"] + 1
            )

        if len(updates) < 100:
            break


async def get_live(username):
    client = TikTokLiveClient(
        unique_id=f"@{username}"
    )

    try:
        return bool(
            await asyncio.wait_for(
                client.is_live(),
                timeout=35,
            )
        )
    except Exception as exc:
        print(
            f"CHECK FAILED @{username}: "
            f"{type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        return None
    finally:
        try:
            await client.disconnect()
        except Exception:
            pass


async def main():
    db, cipher = load_members()

    if os.environ.get("TEST_MESSAGE") == "1":
        if not OWNER_ID:
            raise RuntimeError(
                "TELEGRAM_CHAT_ID required for test message"
            )

        send(
            OWNER_ID,
            "💗 KaoJane Alert Bot ทดสอบสำเร็จ!\n"
            "ระบบสมาชิกพร้อมทดสอบ",
        )

        print("Test Telegram message delivered")
        return

    # Handle Telegram subscription commands.
    try:
        process_updates(db)
    finally:
        save_members(db, cipher)

    state = (
        json.loads(
            LIVE_STATE.read_text(encoding="utf-8")
        )
        if LIVE_STATE.exists()
        else {}
    )

    for username, display_name in PEOPLE.items():
        live = await get_live(username)

        if live is None:
            continue

        old = state.get(username, {})
        was_live = bool(
            old.get("live", False)
        )

        notified = (
            set(
                str(item)
                for item in db["notified"].get(
                    username, []
                )
            )
            if was_live
            else set()
        )

        if live:
            for chat_id, selected in list(
                db["members"].items()
            ):
                if (
                    username not in selected
                    or chat_id in notified
                ):
                    continue

                text = (
                    f"🔴 {display_name} IS LIVE! 💗\n"
                    f"TikTok: @{username}\n"
                    f"https://www.tiktok.com/@{username}/live"
                )

                try:
                    send(chat_id, text)
                    notified.add(chat_id)
                except Exception as exc:
                    print(
                        f"SEND FAILED @{username}: "
                        f"{type(exc).__name__}",
                        file=sys.stderr,
                    )

            state[username] = {
                "live": True
            }

            db["notified"][username] = sorted(
                notified
            )

        else:
            state[username] = {
                "live": False
            }

            db["notified"][username] = []

        print(
            f"@{username}: "
            f"{'LIVE' if live else 'offline'}, "
            f"previously={was_live}; "
            f"subscribers={len(db['members'])}"
        )

    LIVE_STATE.write_text(
        json.dumps(
            state,
            ensure_ascii=False,
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )

    save_members(db, cipher)


if __name__ == "__main__":
    asyncio.run(main())
