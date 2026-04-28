# 🤖 TaskMind AI

AI-powered task management system with semantic search and intelligent daily planning.

> Plan your day with AI, not just a to-do list.

🚀 Live Demo: (link buraya)
📦 Backend API: (link)

## 🎬 Demo
![Demo](demo.gif)

## ✨ Features

- 🧠 AI-powered task planning (RAG-based)
- 🔍 Semantic search with vector embeddings (pgvector)
- 📅 Smart calendar with task completion tracking
- 🔐 JWT Authentication
- 🔔 Real-time Telegram notifications
- ⚡ Natural language task creation (e.g., “yarın 10’da meeting”)

## 🏗️ Architecture

- **Backend:** FastAPI
- **Database:** PostgreSQL + pgvector
- **AI Layer:** RAG pipeline (embeddings + LLM)
- **Frontend:** Streamlit
- **Notifications:** Telegram Bot API

## 🧠 How AI Works

1. User creates tasks using natural language
2. Tasks are converted into embeddings
3. Similar tasks are retrieved via vector search
4. LLM generates contextual daily plans using RAG

## ⚙️ Setup

```bash
git clone https://github.com/username/taskmind-ai
cd taskmind-ai

cp .env.example .env

docker-compose up --build

---

## 📌 Example Usage

```md
## 📌 Example

**Input:**
> yarın ne yapacağım?

**Output:**
- Öncelikli görevler
- Günlük plan
- Öneriler