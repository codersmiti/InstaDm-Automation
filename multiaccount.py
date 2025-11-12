"""
Multi-Account Instagram DM Automation (GPT-Powered)
---------------------------------------------------
Simplified and modular Python version inspired by the Riona AI Agent.
Now includes:
  • GPT-generated personalized messages based on user profiles.
  • Automatic image sending after DM.
  • Multiple account support with session saving.
  • Logs all DM results per account.
  • Randomized cooldowns + human-like actions.

Dependencies:
  pip install instagrapi openai python-dotenv
"""

import os
import csv
import time
import random
from datetime import datetime, timezone
from pathlib import Path
from instagrapi import Client
from openai import OpenAI
from dotenv import load_dotenv
import asyncio
from concurrent.futures import ThreadPoolExecutor

print("✅ Script started — imports loaded successfully.")

# ---------- CONFIG ----------
BASE_DIR = Path(__file__).resolve().parent
ACCOUNTS_FILE = BASE_DIR / "accounts.csv"          # username,password
LISTS_DIR = BASE_DIR / "lists"                     # per-account target lists
MEDIA_DIR = BASE_DIR / "media"                     # optional images
LOGS_DIR = BASE_DIR / "logs_multi"
SESSIONS_DIR = BASE_DIR / "sessions"

DMS_PER_HOUR = 7
TOTAL_HOURS = 5
DAILY_LIMIT = DMS_PER_HOUR * TOTAL_HOURS
COOLDOWN_MIN = 20   # seconds
COOLDOWN_MAX = 75   # seconds

# Load .env for OpenAI key
load_dotenv(BASE_DIR / ".env")
client_ai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ---------- UTILITIES ----------
def delay(seconds: int):
    """Pause execution for a given number of seconds."""
    time.sleep(seconds)

def ensure_dir(path: Path):
    """Create directory if it doesn't exist."""
    path.mkdir(parents=True, exist_ok=True)

def append_log(username: str, target: str, status: str, message: str, image_sent: bool):
    """Append one log entry per DM sent."""
    ensure_dir(LOGS_DIR)
    log_file = LOGS_DIR / f"dm_log_{username}.csv"
    new_file = not log_file.exists()

    with open(log_file, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if new_file:
            writer.writerow(["username", "status", "timestamp", "message", "image_sent"])
        writer.writerow([
            target, status, datetime.now(timezone.utc).isoformat(),
            message, str(image_sent)
        ])

def random_image() -> Path | None:
    """Select a random image from MEDIA_DIR."""
    if not MEDIA_DIR.exists():
        return None
    images = [f for f in MEDIA_DIR.iterdir() if f.suffix.lower() in [".jpg", ".png", ".jpeg"]]
    return random.choice(images) if images else None

def human_like_action(client: Client):
    """Perform a small random 'human-like' action (like a recent post)."""
    try:
        feed = client.feed_timeline()
        if not feed:
            return
        item = random.choice(feed)
        if random.random() < 0.6:
            client.media_like(item.pk)
            print("   ❤️ Liked a random post")
        else:
            client.media_comment(item.pk, "Nice post! ✨")
            print("   💬 Commented on a random post")
    except Exception:
        print("   ⚠️ Skipped human-like behavior")

# ---------- GPT MESSAGE GENERATION ----------
def generate_gpt_dm(to_user: str, bio: str = "", competitor: str = "Dreamland Journals"):
    """
    Generate a short, natural Instagram DM as a friendly journaling enthusiast
    introducing Sentari AI, customized to the target's bio/interests.
    """
    # Extract interests from bio
    interests = None
    bio_lower = bio.lower()
    if "journal" in bio_lower or "mindful" in bio_lower:
        interests = "mindful journaling"
    elif "travel" in bio_lower:
        interests = "travel and exploration"
    elif "fitness" in bio_lower:
        interests = "wellness and personal growth"
    elif "art" in bio_lower or "design" in bio_lower:
        interests = "art and creativity"

    personalization = (
        f"They seem genuinely into {interests}."
        if interests
        else f"They follow {competitor}, which shares reflective and mindful journaling content."
    )

    prompt = f"""
You are writing a short, natural Instagram DM (1–2 sentences) as a friendly journaling enthusiast reaching out to @{to_user}.
You’re introducing *Sentari AI*, a journaling companion that helps people reflect on moods and personal growth.

💬 Guidelines:
- Make it sound like a genuine person, not a brand.
- Mention “Sentari AI” exactly once, woven naturally into the sentence.
- Be warm, curious, and human — like someone who also loves journaling.
- {personalization}
- Vary the message style each time: some reflective, some curious, some lightly funny.
- Use emojis *only when they fit* (✨, 🌿, 💭, 📖).
- Avoid “Hey, check this out!” or hashtags.
- Make it sound personal and spontaneous.
"""

    try:
        response = client_ai.chat.completions.create(
            model="gpt-4o-mini",
            temperature=1.15,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100,
        )
        msg = response.choices[0].message.content.strip()
        return msg or "Hey! I’ve been journaling with Sentari AI lately—it’s been surprisingly grounding ✨"
    except Exception as e:
        print(f"⚠️ GPT generation failed: {e}")
        return "Hey! I’ve been journaling with Sentari AI lately—it’s been surprisingly grounding ✨"

# ---------- PER-ACCOUNT WORKER ----------
def run_account(username: str, password: str):
    """Login to one account and send personalized DMs."""
    print(f"\n=== Starting worker for account: {username} ===")

    targets_file = LISTS_DIR / f"{username}.txt"
    if not targets_file.exists():
        print(f"⚠️ No target list found for {username}")
        return

    targets = [t.strip() for t in targets_file.read_text().splitlines() if t.strip()]
    if not targets:
        print(f"⚠️ No targets to message for {username}")
        return

    ensure_dir(SESSIONS_DIR)
    session_path = SESSIONS_DIR / f"{username}.json"
    client = Client()

    # Try to restore session if exists
    if session_path.exists():
        try:
            client.load_settings(session_path)
            client.login(username, password)
            print(f"   🗂 Restored session for {username}")
        except Exception:
            print(f"   ⚠️ Failed to restore session; logging in fresh")
            client.login(username, password)
    else:
        client.login(username, password)

    client.dump_settings(session_path)
    print(f"   ✅ Logged in {username}")

    sent_total = 0
    for hour in range(1, TOTAL_HOURS + 1):
        print(f"⏰ Hour {hour}/{TOTAL_HOURS} for {username}")
        batch = targets[(hour - 1) * DMS_PER_HOUR : hour * DMS_PER_HOUR]
        if not batch:
            break

        for target in batch:
            if sent_total >= DAILY_LIMIT:
                print(f"🌙 Daily limit reached for {username}")
                break

            print(f"→ Sending DM to @{target}")
            image_sent = False
            message = ""

            try:
                # Use fallback to avoid extract_user_gql() bug
                try:
                    user_info = client.user_info_by_username_v1(target)
                except Exception:
                    user_info = client.user_info_by_username(target)

                user_id = user_info.pk
                bio = getattr(user_info, "biography", "")
                message = generate_gpt_dm(target, bio=bio)

                # Send text message
                client.direct_send(message, [user_id])
                print(f"   ✅ Text sent to @{target}")

                # Send image (80% chance)
                img = random_image()
                if img and random.random() < 0.8:
                    client.direct_send([str(img)], [user_id])
                    print(f"   📸 Image sent: {img.name}")
                    image_sent = True

                append_log(username, target, "success", message, image_sent)
                sent_total += 1

                # Occasionally act human
                if random.random() < 0.35:
                    human_like_action(client)

                cooldown = random.randint(COOLDOWN_MIN, COOLDOWN_MAX)
                print(f"   ⏳ Cooling for {cooldown}s")
                delay(cooldown)

            except Exception as e:
                print(f"   ❌ Failed to send to @{target}: {e}")
                append_log(username, target, "failed", message or 'N/A', image_sent)

        # Save session each hour
        client.dump_settings(session_path)
        if hour < TOTAL_HOURS:
            print("🕐 Waiting 1 hour for next batch...")
            delay(60 * 60)

    print(f"=== Finished {username}: sent {sent_total} DMs ===")

# ---------- ORCHESTRATOR ----------


async def run_concurrent(accounts):
    """Run multiple accounts simultaneously with limited concurrency and staggered starts."""
    max_concurrent = 3  # how many accounts run in parallel
    loop = asyncio.get_event_loop()

    with ThreadPoolExecutor(max_workers=max_concurrent) as executor:
        tasks = []
        for i, (username, password, *_) in enumerate(accounts):
            # small stagger between account starts (3–8 s apart)
            await asyncio.sleep(random.randint(3, 8))
            task = loop.run_in_executor(executor, run_account, username.strip(), password.strip())
            tasks.append(task)
        await asyncio.gather(*tasks)

def main():
    """Run automation concurrently across all accounts."""
    ensure_dir(LOGS_DIR)
    ensure_dir(SESSIONS_DIR)

    if not ACCOUNTS_FILE.exists():
        raise FileNotFoundError(f"Missing {ACCOUNTS_FILE}")

    with open(ACCOUNTS_FILE, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        accounts = [row for row in reader if row and len(row) >= 2]

    # Run all accounts concurrently
    asyncio.run(run_concurrent(accounts))

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Fatal error: {e}")
