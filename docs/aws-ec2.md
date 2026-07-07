# AWS EC2 Production Deployment Guide

This guide describes how to deploy the TaskMind AI application on a single AWS EC2 instance using **Docker** and **Docker Compose**. This setup runs PostgreSQL (with pgvector), FastAPI (backend), and Streamlit (frontend) inside an isolated, secure virtual network.

---

## 1. Instance & Network Setup

### Launch EC2 Instance
- **AMI**: Ubuntu 24.04 LTS (x86_64)
- **Instance Type**: `t3.small` (2 vCPUs, 2 GB RAM) or `t3.medium` (4 GB RAM). *Note: `t2.micro` is not recommended as building Docker containers and running python services may run out of memory unless swap space is configured.*
- **Storage**: 20 GB gp3 SSD.

### Configure Security Group
Create a security group with the following rules:

| Protocol | Port | Source | Description |
|---|---|---|---|
| TCP | 22 | My IP | SSH Management |
| TCP | 8501 | Anywhere (`0.0.0.0/0`) | Streamlit Web Access |
| TCP | 80 | Anywhere (`0.0.0.0/0`) | HTTP Access (If using Nginx Reverse Proxy) |
| TCP | 443 | Anywhere (`0.0.0.0/0`) | HTTPS Access (If using SSL) |

> [!IMPORTANT]
> Do NOT expose port `5433` (PostgreSQL) or `8000/8001` (FastAPI) to the public internet. They will communicate securely inside the internal Docker network.

---

## 2. Server Installation

Connect to your EC2 instance via SSH:
```bash
ssh -i /path/to/key.pem ubuntu@<EC2_PUBLIC_IP>
```

Update packages and install Docker:
```bash
sudo apt-get update && sudo apt-get upgrade -y

# Install Docker dependencies
sudo apt-get install -y ca-certificates curl gnupg lsb-release

# Add Docker's official GPG key
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Set up repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine & Compose
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Add ubuntu user to docker group
sudo usermod -aG docker $USER
```
*Note: After adding the group, log out and log back in for group changes to take effect.*

---

## 3. Deploying TaskMind AI

### Transfer Files
Clone the repository or copy files to the instance (excluding virtual environments and local `.env` files):
```bash
git clone <your-repository-url> taskmind
cd taskmind
```

### Configure Environment Variables
Create a production `.env` file:
```bash
cp .env.example .env
nano .env
```

Ensure the following variables are configured:
```env
# Database configuration
DATABASE_URL=postgresql://user:password@pgvector_db:5432/tasks

# FastAPI Security (Change this to a strong random key!)
SECRET_KEY=generate-a-long-random-string-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_HOURS=24

# API URLs
TASKMIND_API_URL=http://api:8000

# Cloud LLM APIs (Ollama is set to false)
TASKMIND_ENABLE_OLLAMA=false
GROQ_API_KEY=gsk_your_groq_api_key
OPENAI_API_KEY=sk-proj-your_openai_api_key

# Telegram Notifications
TELEGRAM_TOKEN=your_telegram_bot_token
CHAT_ID=your_telegram_chat_id
```

### Start the Application Stack
Build and launch the containers in detached (background) mode:
```bash
docker compose up -d --build
```

Verify that all services are running and healthy:
```bash
docker compose ps
docker compose logs api
docker compose logs web
```

The application will now be running and accessible at: `http://<EC2_PUBLIC_IP>:8501`.

---

## 4. (Optional) Production Enhancements

### Nginx Reverse Proxy (SSL/Port 80)
If you want to map the application to standard HTTP/HTTPS ports (80/443) or use a domain name with Let's Encrypt:

1. Install Nginx:
   ```bash
   sudo apt install nginx -y
   ```
2. Configure Nginx virtual host (`/etc/nginx/sites-available/taskmind`):
   ```nginx
   server {
       listen 80;
       server_name yourdomain.com;

       location / {
           proxy_pass http://127.0.0.1:8501;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection "upgrade";
           proxy_set_header Host $host;
           proxy_cache_bypass $http_upgrade;
       }
   }
   ```
3. Enable configuration and restart Nginx:
   ```bash
   sudo ln -s /etc/nginx/sites-available/taskmind /etc/nginx/sites-enabled/
   sudo systemctl restart nginx
   ```
