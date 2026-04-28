import os
from langchain_ollama import OllamaLLM
from app.ai.extraction import llm

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://host.docker.internal:11434")

llm = OllamaLLM(
    model="llama3",
    base_url=OLLAMA_URL
)

def prioritize_task(text:str):
    prompt=f"""
    Bu görevin önceliği nedir? 1-5 arasında bir sayı ver. 1 en yüksek öncelik, 5 en düşük önceliktir.
    {text}
    1=Çok önemli
    5=Önemsiz

    sadecce sayı döndür.
    """

    response=llm.invoke(prompt)

    try:
        return int(response.content.strip())       
    except:
        return 3               