import os
from langchain_ollama import OllamaLLM
from langchain_ollama import OllamaEmbeddings

OLLAMA_URL = os.getenv("OLLAMA_URL")
ENABLE_OLLAMA = os.getenv("TASKMIND_ENABLE_OLLAMA", "false").lower() == "true"
EMBEDDING_DIMENSIONS = 768

class LLMWrapper:
    def __init__(self):
        self.ollama_url = OLLAMA_URL
        self.enable_ollama = ENABLE_OLLAMA
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")

        # Select provider based on configuration availability
        if self.enable_ollama and self.ollama_url:
            self.provider = "ollama"
            self.llm = OllamaLLM(model="llama3", base_url=self.ollama_url)
            print("AI Provider: Ollama configured.")
        elif self.groq_api_key and not self.groq_api_key.startswith("your-") and not self.groq_api_key == "":
            self.provider = "groq"
            from groq import Groq
            self.client = Groq(api_key=self.groq_api_key)
            print("AI Provider: Groq configured.")
        elif self.openai_api_key and not self.openai_api_key.startswith("your-") and not self.openai_api_key == "":
            self.provider = "openai"
            from openai import OpenAI
            self.client = OpenAI(api_key=self.openai_api_key)
            print("AI Provider: OpenAI configured.")
        else:
            self.provider = None
            self.llm = None
            print("AI Provider: None configured. Fallback mode active.")

    def invoke(self, prompt: str) -> str:
        if self.provider == "ollama":
            return self.llm.invoke(prompt)
        elif self.provider == "groq":
            try:
                response = self.client.chat.completions.create(
                    model="llama3-8b-8192",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.5
                )
                return response.choices[0].message.content
            except Exception as e:
                print(f"Groq invocation error: {e}", flush=True)
                raise e
        elif self.provider == "openai":
            try:
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.5
                )
                return response.choices[0].message.content
            except Exception as e:
                print(f"OpenAI invocation error: {e}", flush=True)
                raise e
        else:
            raise RuntimeError("No LLM provider configured or keys are placeholders.")

llm = LLMWrapper()


def get_embedding(text: str) -> list[float]:
    ollama_url = OLLAMA_URL
    enable_ollama = ENABLE_OLLAMA
    openai_api_key = os.getenv("OPENAI_API_KEY")

    if enable_ollama and ollama_url:
        try:
            embeddings = OllamaEmbeddings(model="nomic-embed-text", base_url=ollama_url)
            return embeddings.embed_query(text)
        except Exception as exc:
            print(f"Ollama embedding error: {exc}", flush=True)
    elif openai_api_key and not openai_api_key.startswith("your-") and not openai_api_key == "":
        try:
            from openai import OpenAI
            client = OpenAI(api_key=openai_api_key)
            response = client.embeddings.create(
                input=[text],
                model="text-embedding-3-small",
                dimensions=EMBEDDING_DIMENSIONS
            )
            return response.data[0].embedding
        except Exception as exc:
            print(f"OpenAI embedding error: {exc}", flush=True)

    # Return standard zero-vector fallback if no embeddings can be computed
    return [0.0] * EMBEDDING_DIMENSIONS
