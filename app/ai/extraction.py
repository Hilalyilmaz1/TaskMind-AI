from langchain_core.prompts import PromptTemplate
import os
from langchain_ollama import OllamaLLM
from datetime import datetime, timedelta
import re

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://host.docker.internal:11434")

llm = OllamaLLM(
    model="llama3",
    base_url=OLLAMA_URL
)

prompt=PromptTemplate(
    input_variables=["text"],
    template="""
Extract structured task info from this text:
{text}

Return JSON with:
-task
-datetime
"""
)



def extract_task(text):
    prompt = f"""
    Extract task and date from text.

    Return ONLY JSON.

    Example:
       {{"task": "meeting", "date": "2026-04-25"}}
    "{text}"

    JSON olarak döndür:
    {{
      "task": "...",
      "date": "YYYY-MM-DD" veya null
    }}
    """

    response = llm.invoke(prompt)

    return response

def parse_datetime(text):
    now = datetime.now()

    # tarih
    if "yarın" in text:
        date = now + timedelta(days=1)
    elif "bugün" in text:
        date = now
    elif "haftaya" in text:
        date = now + timedelta(days=7)
    else:
        date = None

    # saat (regex)
    hour_match = re.search(r'(\d{1,2})(:(\d{2}))?', text)

    if date and hour_match:
        hour=int(hour_match.group(1))
        minute=int(hour_match.group(3)) if hour_match.group(3) else 0

        return date.replace(hour=hour, minute=minute, second=0)

    return None