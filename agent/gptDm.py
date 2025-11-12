# agent/gpt_dm.py
import os
from openai import OpenAI
from dotenv import load_dotenv

# Load API key
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_dm(to_user: str, competitor: str = "Dreamland Journals", interests: str | None = None) -> str:
    """
    Generate a personalized, natural-sounding Instagram DM using OpenAI.
    Mimics human tone and lightly promotes Sentari AI as a journaling companion.
    """
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
- Use emojis *only when they truly fit* the vibe (e.g. ✨, 🌿, 💭, 📖).
- No “Hey, check this out!” or hashtags.
- It should feel personal, spontaneous, and unique.
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=1.15,  # higher temp = more variety
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100,
        )
        msg = response.choices[0].message.content.strip()
        return msg or "Hey! I’ve been journaling with Sentari AI lately—it’s been surprisingly grounding ✨"
    except Exception as e:
        print(f"⚠️ GPT generation failed: {e}")
        return "Hey! I’ve been journaling with Sentari AI lately—it’s been surprisingly grounding ✨"
