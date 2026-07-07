import os
import json
from datetime import datetime, timedelta
import re

from app.ai.llm import llm


def extract_task(text):
    if llm is None or llm.provider is None:
        return {}

    extraction_prompt = f"""
    Extract task and date from text.

    Return ONLY JSON.

    Example:
       {{"task": "meeting", "date": "2026-04-25"}}
    "{text}"

    Return JSON:
    {{
      "task": "...",
      "date": "YYYY-MM-DD" or null
    }}
    """

    try:
        res = llm.invoke(extraction_prompt)
        cleaned = res.strip()
        if "```json" in cleaned:
            cleaned = cleaned.split("```json")[1].split("```")[0].strip()
        elif "```" in cleaned:
            cleaned = cleaned.split("```")[1].split("```")[0].strip()
        
        return json.loads(cleaned)
    except Exception as e:
        print(f"Error in extraction parsing: {e}", flush=True)
        return {}


def parse_datetime(text):
    now = datetime.now()
    lower_text = text.lower()

    if "yarin" in lower_text or "yarın" in lower_text or "tomorrow" in lower_text:
        date = now + timedelta(days=1)
    elif "bugun" in lower_text or "bugün" in lower_text or "today" in lower_text:
        date = now
    elif "haftaya" in lower_text or "next week" in lower_text:
        date = now + timedelta(days=7)
    else:
        date = None

    hour_match = re.search(r"(\d{1,2})(?::(\d{2}))?", text)

    if date and hour_match:
        hour = int(hour_match.group(1))
        minute = int(hour_match.group(2)) if hour_match.group(2) else 0
        return date.replace(hour=hour, minute=minute, second=0, microsecond=0)

    return None
