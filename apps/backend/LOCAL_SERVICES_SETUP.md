# TrueShift Backend - Local Services Configuration

## Quick Setup for Colab/Local Environment

### Step 1: Install PostgreSQL and Redis

Run the installation script:
```bash
cd /e/vishnu/trueShift/apps/backend
chmod +x install-services.sh
./install-services.sh
```

Or manually in your notebook:
```python
# Install PostgreSQL and Redis
!apt-get update
!apt-get install -y postgresql postgresql-contrib redis-server

# Start services
!service postgresql start
!service redis-server start

# Configure PostgreSQL
!sudo -u postgres psql -c "ALTER USER postgres PASSWORD 'postgres';"
!sudo -u postgres psql -c "CREATE DATABASE trueshift;"

print("✅ Services installed and running!")
```

### Step 2: Create .env File

Create `.env` in `apps/backend/` with these contents:

```env
# Application
APP_ENV=development
DEBUG=true
SECRET_KEY=dev-secret-key-change-in-production

# Database - Local PostgreSQL Service
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/trueshift

# Redis - Local Redis Service  
REDIS_URL=redis://localhost:6379/0

# Firebase (replace with your values)
FIREBASE_PROJECT_ID=your-firebase-project-id
FIREBASE_CREDENTIALS_PATH=./firebase-credentials.json

# Google Gemini AI (replace with your API key)
GOOGLE_API_KEY=your-google-api-key-here
GEMINI_MODEL=gemini-1.5-pro
```

### Step 3: Install Python Dependencies

```bash
cd apps/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirement.txt
```

### Step 4: Run Database Migrations

```bash
alembic upgrade head
```

### Step 5: Start the Backend

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Connection Details

| Service | URL |
|---------|-----|
| PostgreSQL | `postgresql+asyncpg://postgres:postgres@localhost:5432/trueshift` |
| Redis | `redis://localhost:6379/0` |
| API Server | `http://localhost:8000` |
| API Docs | `http://localhost:8000/docs` |

## Verify Services

### Check PostgreSQL:
```bash
sudo -u postgres psql -c "SELECT version();"
```

### Check Redis:
```bash
redis-cli ping
# Should return: PONG
```

### Check Backend Connection:
```python
import asyncpg
import redis

# Test PostgreSQL
conn = await asyncpg.connect('postgresql://postgres:postgres@localhost:5432/trueshift')
await conn.close()
print("✅ PostgreSQL connected")

# Test Redis
r = redis.Redis(host='localhost', port=6379, db=0)
r.ping()
print("✅ Redis connected")
```

## Configuration Notes

The backend configuration is in `app/core/config.py`:
- Automatically loads from `.env` file
- Default database URL: `postgresql+asyncpg://postgres:postgres@localhost:5432/trueshift`
- Default Redis URL: `redis://localhost:6379/0`

These match the local service setup, so no code changes needed!
