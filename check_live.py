import asyncio
import json
import os
import sys
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from TikTokLive import TikTokLiveClient

PEOPLE = [("เจนเย่", "janeeyeh"), ("พี่เก้า", "supassra_sp")]
STATE_PATH = Path("live_state.json")


def send_telegram(message: str) -> None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        raise RuntimeError("Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in GitHub Actions secrets")
    payload = urlencode({"chat_id": chat_id, "text": message, "disable_web_page_preview": "true"}).encode()
    request = Request(f"https://api.telegram.org/bot{token}/sendMessage", data=payload, method="POST")
    with urlopen(request, timeout=20) as response:
        result = json.load(response)
    if not result.get("ok"):
        raise RuntimeError("Telegram API did not confirm success")


async def get_live(username: str):
    client = TikTokLiveClient(unique_id=f"@{username}")
    try:
        return bool(await asyncio.wait_for(client.is_live(), timeout=35))
    except Exception as exc:
        print(f"CHECK FAILED for @{username}: {type(exc).__name__}: {exc}", file=sys.stderr)
        return None  # never treat failed checks as offline
    finally:
        try:
            await client.disconnect()
        except (AttributeError, Exception):
            pass


async def main():
    if os.environ.get("TEST_MESSAGE") == "1":
        send_telegram("💗 KaoJane Alert Bot ส่งข้อความทดสอบสำเร็จ!\nจาก GitHub Actions")
        print("Telegram test delivered")
        return
    state = json.loads(STATE_PATH.read_text(encoding="utf-8")) if STATE_PATH.exists() else {}
    had_failure = False
    for name, username in PEOPLE:
        is_live = await get_live(username)
        if is_live is None:
            had_failure = True
            continue
        previous = state.get(username, {}).get("live", False)
        if is_live and not previous:
            msg = f"🔴 {name} IS LIVE! 💗\nTikTok: @{username}\nhttps://www.tiktok.com/@{username}/live"
            try:
                send_telegram(msg)
            except Exception as exc:
                print(f"SEND FAILED for @{username}: {exc}", file=sys.stderr)
                had_failure = True
                continue # don't mark notified if message wasn't delivered
        state[username] = {"live": is_live}
        print(f"@{username}: {'LIVE' if is_live else 'offline'}, previously={previous}")
    STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if had_failure:
        print("At least one profile check or Telegram delivery failed; review Actions logs", file=sys.stderr)


if __name__ == "__main__":
    asyncio.run(main())
