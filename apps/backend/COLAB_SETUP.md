# TrueShift Backend - Colab Setup
# Run these cells in order to set up PostgreSQL and Redis

## Cell 1: Install Services
```python
# Install PostgreSQL and Redis
!apt-get update -qq
!apt-get install -y postgresql postgresql-contrib redis-server

print("✅ PostgreSQL and Redis installed")
```

## Cell 2: Start and Configure Services
```python
# Start PostgreSQL
!service postgresql start

# Configure PostgreSQL database
!sudo -u postgres psql -c "ALTER USER postgres PASSWORD 'postgres';"
!sudo -u postgres psql -c "CREATE DATABASE trueshift;"

# Start Redis
!service redis-server start

print("✅ Services configured and running")
print("   PostgreSQL: localhost:5432")
print("   Redis: localhost:6379")
```

## Cell 3: Clone Repository (if needed)
```python
import os

# Only clone if not already cloned
if not os.path.exists('/content/trueShift'):
    !git clone https://YOUR_TOKEN@github.com/YOUR_USERNAME/trueShift.git /content/trueShift
    
%cd /content/trueShift/apps/backend
print("✅ Repository ready")
```

## Cell 4: Install Python Dependencies
```python
%cd /content/trueShift/apps/backend

# Install requirements
!pip install -q -r requirement.txt

print("✅ Dependencies installed")
```

## Cell 5: Create Environment File
```python
env_content = """
APP_ENV=development
DEBUG=true
SECRET_KEY=dev-secret-key

DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/trueshift
REDIS_URL=redis://localhost:6379/0

GOOGLE_API_KEY=YOUR_API_KEY_HERE
GEMINI_MODEL=gemini-1.5-pro

FIREBASE_PROJECT_ID=your-project-id
FIREBASE_CREDENTIALS_PATH=./firebase-credentials.json
"""

with open('.env', 'w') as f:
    f.write(env_content)

print("✅ .env file created")
print("⚠️  Remember to update GOOGLE_API_KEY!")
```

## Cell 6: Run Database Migrations
```python
# Run migrations
!alembic upgrade head

print("✅ Database migrations complete")
```

## Cell 7: Test Connections
```python
import asyncio
import asyncpg
import redis

async def test_postgres():
    try:
        conn = await asyncpg.connect(
            'postgresql://postgres:postgres@localhost:5432/trueshift'
        )
        version = await conn.fetchval('SELECT version();')
        await conn.close()
        print("✅ PostgreSQL connected:", version.split(',')[0])
        return True
    except Exception as e:
        print("❌ PostgreSQL error:", str(e))
        return False

def test_redis():
    try:
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        print("✅ Redis connected")
        return True
    except Exception as e:
        print("❌ Redis error:", str(e))
        return False

# Run tests
await test_postgres()
test_redis()
```

## Cell 8: Start Backend Server
```python
# Start the backend in background
!uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &

import time
time.sleep(3)

# Test if server is running
!curl -s http://localhost:8000/health || echo "Server starting..."

print("✅ Backend server starting on http://localhost:8000")
print("📚 API Docs: http://localhost:8000/docs")
```

## Verify Everything is Running
```python
# Check services status
!service postgresql status | grep "online" && echo "✅ PostgreSQL running"
!service redis-server status | grep "running" && echo "✅ Redis running"

# Check API health
import requests
try:
    response = requests.get('http://localhost:8000/health')
    if response.status_code == 200:
        print("✅ Backend API running")
        print(f"   Response: {response.json()}")
except:
    print("⚠️  Backend API not ready yet, wait a few seconds")
```

## Important Notes

1. **Services in Colab**: PostgreSQL and Redis will run only during your Colab session. They reset when the runtime disconnects.

2. **API Keys**: Update the `.env` file with your actual Google API key:
   ```python
   # Update Google API key
   import os
   os.environ['GOOGLE_API_KEY'] = 'your-actual-key-here'
   ```

3. **Port Forwarding**: To access the API from outside Colab, use ngrok:
   ```python
   # Install ngrok
   !pip install pyngrok
   
   from pyngrok import ngrok
   public_url = ngrok.connect(8000)
   print(f"🌐 Public URL: {public_url}")
   ```

4. **Backend Configuration**: The config file `app/core/config.py` is already set up for local services - no changes needed!
