# SnapLive Backend

FastAPI backend application for SnapLive with MongoDB integration.

## Features

- FastAPI framework with async/await support
- MongoDB integration using Motor (async driver)
- CORS enabled for frontend communication
- Automatic API documentation (Swagger UI)
- Environment-based configuration
- Health check endpoints

## Prerequisites

- Python 3.11 or higher
- MongoDB Atlas account (or local MongoDB instance)
- pip (Python package installer)

## Project Structure

```
snaplive-backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Settings and configuration
│   ├── database.py          # MongoDB connection
│   └── api/
│       └── v1/
│           ├── api.py       # Router aggregation
│           └── endpoints/
│               └── health.py # Health check endpoints
├── .env                     # Environment variables (not in git)
├── .env.example             # Example environment file
├── .gitignore
├── requirements.txt         # Python dependencies
└── README.md
```

## Setup Instructions

### 1. Create Virtual Environment

```bash
cd snaplive-backend
python3.11 -m venv venv
```

### 2. Activate Virtual Environment

**macOS/Linux:**
```bash
source venv/bin/activate
```

**Windows:**
```bash
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

The `.env` file is already configured with your MongoDB Atlas connection. To modify settings, edit the `.env` file:

```bash
# MongoDB URL is already set
# Modify other settings as needed
```

### 5. Run the Application

```bash
uvicorn app.main:app --reload
```

The server will start on `http://localhost:8000`

## API Endpoints

### Root Endpoint
- **GET** `/` - Welcome message and API info

### Health Check
- **GET** `/health` - Basic health check
- **GET** `/api/v1/health` - Detailed health check with MongoDB status

### API Documentation
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## Testing the API

### Using curl

```bash
# Root endpoint
curl http://localhost:8000/

# Health check
curl http://localhost:8000/health

# API health check with MongoDB status
curl http://localhost:8000/api/v1/health
```

### Using Browser

Navigate to:
- `http://localhost:8000` - Welcome page
- `http://localhost:8000/docs` - Interactive API documentation
- `http://localhost:8000/health` - Health check

## Development

### Running in Development Mode

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The `--reload` flag enables auto-reload on code changes.

### Adding New Endpoints

1. Create a new file in `app/api/v1/endpoints/`
2. Define your router and endpoints
3. Import and include the router in `app/api/v1/api.py`

Example:

```python
# app/api/v1/endpoints/users.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/users")
async def get_users():
    return {"users": []}
```

```python
# app/api/v1/api.py
from app.api.v1.endpoints import health, users

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(users.router, tags=["users"])
```

## MongoDB Connection

The application uses Motor, an async MongoDB driver. The connection is established on startup and closed on shutdown.

Connection details:
- URL: Configured in `.env` file
- Database: `snaplive`
- Connection pooling: 10-50 connections

## CORS Configuration

CORS is configured to allow requests from:
- `http://localhost:3000` (Next.js frontend)

To add more origins, modify the `CORS_ORIGINS` in `.env`.

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `APP_NAME` | Application name | SnapLive Backend |
| `APP_VERSION` | Application version | 0.1.0 |
| `DEBUG` | Debug mode | True |
| `MONGODB_URL` | MongoDB connection URL | (required) |
| `MONGODB_DB_NAME` | Database name | snaplive |
| `PORT` | Server port | 8000 |
| `CORS_ORIGINS` | Allowed CORS origins | ["http://localhost:3000"] |

## Production Deployment

For production deployment:

1. Set `DEBUG=False` in `.env`
2. Use a production-grade ASGI server configuration
3. Enable HTTPS
4. Set proper CORS origins
5. Use environment-specific MongoDB credentials
6. Consider using Docker for containerization

## License

Proprietary
