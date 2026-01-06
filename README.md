# TrueShift - AI Behavior Intelligence Engine

An AI-first personal performance system that continuously understands movement, environment, recovery, and digital behavior, and adapts coaching in real time.

**Not a workout app. A behavior intelligence engine.**

## Architecture

```
Mobile Clients
 ├─ iOS / Android (Expo → Native)
 ├─ Background services
 ├─ Offline cache
 ↓
API Gateway
 ├─ Auth & Consent
 ├─ Rate limiting
 ├─ Feature flags
 ↓
Core Platform
 ├─ User State Engine
 ├─ Event Stream
 ├─ AI Orchestrator
 ├─ Recommendation Engine
 ↓
AI & Data Layer
 ├─ Gemini LLMs (Reasoning)
 ├─ Vision Models
 ├─ Multi-Agent Architecture (Google ADK)
 ↓
Analytics & Growth
 ├─ Cohort tracking
 ├─ A/B experiments
 ├─ Retention models
```

## Tech Stack

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL + Redis
- **Auth**: Firebase Authentication
- **AI**: Google Gemini APIs + Google ADK

### Mobile
- **Framework**: React Native (Expo Bare workflow)
- **Background**: Background Fetch + Task Manager
- **Offline**: AsyncStorage + SQLite

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- Google API Key (for Gemini)

### Backend Setup

```bash
# Start database services
docker-compose up -d postgres redis

# Setup Python environment
cd apps/backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -e .

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Run development server
uvicorn app.main:app --reload
```

### Mobile Setup

```bash
cd apps/mobile
npm install
npx expo start
```

## Project Structure

```
trueShift/
├── apps/
│   ├── backend/           # FastAPI Backend
│   │   ├── app/
│   │   │   ├── ai/        # AI Agents & Orchestrator
│   │   │   ├── api/       # API Routes
│   │   │   ├── core/      # Config, DB, Security
│   │   │   ├── models/    # Database Models
│   │   │   ├── services/  # Business Logic
│   │   │   └── middleware/# Rate Limiting, Feature Flags
│   │   └── tests/
│   └── mobile/            # React Native App
│       └── src/
│           ├── api/
│           ├── hooks/
│           ├── screens/
│           └── services/
├── docker-compose.yml
└── README.md
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/v1/auth/register` | POST | Register/login user |
| `/api/v1/auth/me` | GET | Get current user |
| `/api/v1/auth/consent` | PUT | Update consents |
| `/api/v1/events` | POST | Ingest single event |
| `/api/v1/events/batch` | POST | Ingest batch events |
| `/api/v1/state` | GET | Get user state |
| `/api/v1/state/recommendations` | GET | Get recommendations |
| `/api/v1/state/ai/coaching` | GET | Full AI coaching |
