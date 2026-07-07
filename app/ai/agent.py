import os
from app.ai.llm import llm


def prioritize_task(text: str):
    if llm is None or llm.provider is None:
        return 3

    prompt = f"""
    What is the priority of this task? Return only a number between 1 and 5.
    1 means very important, 5 means low importance.

    Task:
    {text}
    """

    try:
        response = llm.invoke(prompt)
        # Clean response to retrieve just the digits
        import re
        digits = re.findall(r"\d", response)
        if digits:
            val = int(digits[0])
            if 1 <= val <= 5:
                return val
        return 3
    except Exception:
        return 3
