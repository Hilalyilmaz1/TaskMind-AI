# AWS ECS Deployment

This guide deploys TaskMind AI to AWS ECS Fargate with one public Streamlit frontend and one private FastAPI backend running in the same ECS task.

## Target Architecture

```text
Internet
  |
Application Load Balancer
  |
ECS Fargate service: taskmind-ai
  |-- web container: Streamlit on port 8501
  |-- api container: FastAPI on port 8000
  |
RDS PostgreSQL
```

The `web` container calls the `api` container through localhost:

```env
TASKMIND_API_URL=http://127.0.0.1:8000
```

## 1. Create ECR Repositories

Create two private ECR repositories:

```text
taskmind-api
taskmind-web
```

Then authenticate Docker to ECR:

```bash
aws ecr get-login-password --region <REGION> | docker login --username AWS --password-stdin <ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com
```

Build and push the API image:

```bash
docker build -f Dockerfile.api -t taskmind-api .
docker tag taskmind-api:latest <ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com/taskmind-api:latest
docker push <ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com/taskmind-api:latest
```

Build and push the web image:

```bash
docker build -f Dockerfile.web -t taskmind-web .
docker tag taskmind-web:latest <ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com/taskmind-web:latest
docker push <ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com/taskmind-web:latest
```

## 2. Create PostgreSQL

Create an RDS PostgreSQL database.

Recommended settings for a small first deployment:

```text
Engine: PostgreSQL
Public access: No
Database name: taskmind
```

Security group rule:

```text
RDS inbound PostgreSQL 5432 from ECS task security group
```

The app creates the `vector` extension on startup:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

Use an RDS PostgreSQL version that supports the pgvector extension.

## 3. Store Secrets

Create these values in AWS Secrets Manager or SSM Parameter Store:

```text
taskmind/DATABASE_URL
taskmind/SECRET_KEY
taskmind/GROQ_API_KEY
taskmind/OPENAI_API_KEY
taskmind/TELEGRAM_TOKEN
taskmind/CHAT_ID
```

`DATABASE_URL` format:

```env
postgresql://<USER>:<PASSWORD>@<RDS_ENDPOINT>:5432/<DB_NAME>
```

Required minimum values:

```text
taskmind/DATABASE_URL
taskmind/SECRET_KEY
taskmind/GROQ_API_KEY
```

Optional values can be left empty or removed from the task definition:

```text
taskmind/OPENAI_API_KEY
taskmind/TELEGRAM_TOKEN
taskmind/CHAT_ID
```

## 4. Create ECS Task Definition

Use [deploy/aws-ecs-task-definition.example.json](../deploy/aws-ecs-task-definition.example.json) as the starting point.

Replace:

```text
<ACCOUNT_ID>
<REGION>
```

Important container values:

```text
api PORT=8000
api TASKMIND_ENABLE_OLLAMA=false
web PORT=8501
web TASKMIND_API_URL=http://127.0.0.1:8000
```

## 5. Create ECS Service

Create an ECS cluster and a Fargate service.

Recommended service settings:

```text
Launch type: Fargate
Desired tasks: 1
Platform version: Latest
Task definition: taskmind-ai
Public IP: Disabled if using private subnets, enabled only for simple test deployments
```

Attach an Application Load Balancer to the `web` container:

```text
Container: web
Container port: 8501
Target group protocol: HTTP
Health check path: /_stcore/health
```

Security groups:

```text
ALB inbound: 80 and/or 443 from internet
ECS task inbound: 8501 from ALB security group
ECS task outbound: allow outbound
RDS inbound: 5432 from ECS task security group
```

Do not expose API port `8000` publicly. The web container reaches it through localhost inside the ECS task.

## 6. Test

Open the ALB DNS name in the browser.

Useful checks:

```text
Streamlit health: http://<ALB_DNS>/_stcore/health
FastAPI health is internal: http://127.0.0.1:8000/
```

If task creation fails:

1. Check CloudWatch logs for the `api` container.
2. Confirm `DATABASE_URL` is correct.
3. Confirm RDS security group allows traffic from the ECS task security group.
4. Confirm `TASKMIND_ENABLE_OLLAMA=false`.

## References

- [Amazon ECR image push docs](https://docs.aws.amazon.com/AmazonECR/latest/userguide/docker-push-ecr-image.html)
- [Amazon ECS environment variables](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/ecs-environment-variables.html)
- [Amazon ECS Fargate task definition parameters](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task_definition_parameters.html)
- [Amazon ECS service load balancing](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/service-load-balancing.html)
- [Amazon ECS Secrets Manager environment variables](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/secrets-envvar-secrets-manager.html)
