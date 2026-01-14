# TrueShift Backend Setup Guide

## Prerequisites

- Python 3.10 or higher
- Docker and Docker Compose (for PostgreSQL and Redis)
- WSL (for Windows users)

## Quick Start

### 1. Start Infrastructure Services

Start PostgreSQL and Redis using Docker Compose from the project root:

```bash
cd /e/vishnu/trueShift
docker compose up -d postgres redis
```

Verify services are running:
```bash
docker compose ps
```

### 2. Create Virtual Environment

```bash
cd apps/backend
python -m venv venv
source venv/bin/activate  # On WSL/Linux
```

### 3. Install Dependencies

```bash
pip install -e .
```

Or using requirements.txt:
```bash
pip install -r requirement.txt
```

### 4. Configure Environment

Create a `.env` file in `apps/backend/`:

```env
# Application
APP_ENV=development
DEBUG=true
API_VERSION=v1

# Database (localhost works from WSL because Docker exposes ports)
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/trueshift

# Redis
REDIS_URL=redis://localhost:6379/0

# Firebase (for Authentication)
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_CREDENTIALS_PATH=/path/to/firebase-credentials.json

# Google Gemini AI
GOOGLE_API_KEY=your-google-api-key-here
GEMINI_MODEL=gemini-pro

# Security
SECRET_KEY=your-secret-key-here-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Server
HOST=0.0.0.0
PORT=8000
```

### 5. Run Database Migrations

```bash
alembic upgrade head
```

### 6. Start the Backend Server

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`

## Package Dependencies

### Core Dependencies
- **fastapi** - Modern web framework
- **uvicorn** - ASGI server
- **sqlalchemy** - ORM with async support
- **asyncpg** - PostgreSQL async driver
- **redis** - Redis client
- **pydantic** - Data validation
- **pydantic-settings** - Settings management
- **python-jose** - JWT authentication
- **firebase-admin** - Firebase integration
- **google-generativeai** - Google AI SDK
- **google-adk** - Google Agent Development Kit
- **httpx** - HTTP client
- **python-multipart** - File upload support
- **alembic** - Database migrations

### Development Dependencies
- **pytest** - Testing framework
- **pytest-asyncio** - Async test support
- **pytest-cov** - Code coverage
- **black** - Code formatter
- **ruff** - Linter
- **mypy** - Type checker

## Database Connection from WSL

Your Docker Compose is configured to expose PostgreSQL on port 5432 and Redis on port 6379. From WSL, you can connect to these services using:

- **PostgreSQL**: `localhost:5432`
- **Redis**: `localhost:6379`

Test PostgreSQL connection:
```bash
psql -h localhost -U postgres -d trueshift
# Password: postgres
```

Test Redis connection:
```bash
redis-cli -h localhost ping
# Should return: PONG
```

## Useful Commands

### Stop Services
```bash
docker compose down
```

### View Logs
```bash
docker compose logs -f postgres
docker compose logs -f redis
```

### Reset Database
```bash
docker compose down -v  # Remove volumes
docker compose up -d postgres redis
```

### Run Tests
```bash
pytest
```

### Format Code
```bash
black .
ruff check .
```
