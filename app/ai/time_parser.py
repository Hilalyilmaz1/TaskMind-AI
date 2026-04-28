from datetime import datetime, timedelta
from app.ai.extraction import llm
import re

def parse_datetime(text: str):
    prompt = f"""
Aşağıdaki metinden tarih ve saat çıkar:
"{text}"

Format:
YYYY-MM-DD HH:MM

Eğer tarih veya saat yoksa NONE döndür.
"""
    try:
        response = llm.invoke(prompt)
        result = response.strip()
    except Exception:
        return _fallback_parse_datetime(text)

    if not result or result.upper() == "NONE":
        return _fallback_parse_datetime(text)

    try:
        return datetime.strptime(result, "%Y-%m-%d %H:%M")
    except ValueError:
        return _fallback_parse_datetime(text, result)


def _fallback_parse_datetime(text: str, parsed: str | None = None):
    now = datetime.now()
    lower_text = text.lower()

    if "yarın" in lower_text or "yarin" in lower_text or "tomorrow" in lower_text:
        date = now + timedelta(days=1)
    elif "bugün" in lower_text or "bugun" in lower_text or "today" in lower_text:
        date = now
    else:
        date = now

    time_match = re.search(r"(\d{1,2})(?::(\d{2}))?", text)
    if time_match:
        hour = int(time_match.group(1))
        minute = int(time_match.group(2)) if time_match.group(2) else 0
        candidate = date.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if candidate < now and "yarın" not in lower_text and "yarin" not in lower_text and "tomorrow" not in lower_text:
            candidate += timedelta(days=1)
        return candidate

    if parsed:
        parsed_match = re.search(r"(\d{4})-(\d{2})-(\d{2})\s+(\d{1,2}):(\d{2})", parsed)
        if parsed_match:
            return datetime(
                int(parsed_match.group(1)),
                int(parsed_match.group(2)),
                int(parsed_match.group(3)),
                int(parsed_match.group(4)),
                int(parsed_match.group(5)),
            )

    return None