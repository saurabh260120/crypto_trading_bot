# Setup Guide

This guide will help you set up the Delta Exchange Trading Platform from scratch.

## Prerequisites

- **Docker** 20.10+ and **Docker Compose** 2.0+
- **Git** for cloning the repository
- **OpenSSL** for generating encryption keys (usually pre-installed)

## Step 1: Clone Repository

```bash
git clone <repository-url>
cd Crypto_Trading
```

## Step 2: Configure Environment

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Generate a master encryption key:
```bash
openssl rand -hex 32
```

3. Edit `.env` and set the following required values:
   - `TRADE_MASTER_KEY`: Paste the generated key from step 2
   - `JWT_SECRET`: Generate another random string (e.g., `openssl rand -hex 32`)
   - `POSTGRES_PASSWORD`: Set a strong database password
   - `POSTGRES_USER`: Database username (default: `trading_user`)
   - `POSTGRES_DB`: Database name (default: `trading_db`)

4. Optionally configure:
   - Delta Exchange API URLs (if using custom endpoints)
   - CORS origins (for frontend access)
   - Log levels and paths
   - Worker concurrency settings

## Step 3: Start Services

Start all services with Docker Compose:

```bash
docker-compose up -d
```

This will start:
- PostgreSQL database
- Redis cache/broker
- Backend API server
- Worker process
- Frontend web app

## Step 4: Initialize Database

Run database migrations:

```bash
docker-compose exec backend alembic upgrade head
```

## Step 5: Verify Installation

1. **Check services are running:**
```bash
docker-compose ps
```

All services should show "Up" status.

2. **Test backend API:**
```bash
curl http://localhost:8000/health
```

Should return: `{"status": "healthy"}`

3. **Access the application:**
   - Frontend: http://localhost:3000
   - API Documentation: http://localhost:8000/docs
   - API Health: http://localhost:8000/health

## Step 6: Create First User

1. Open http://localhost:3000 in your browser
2. Click "Register" to create an account
3. Login with your credentials

## Step 7: Create a Profile

1. Navigate to "Profiles" in the UI
2. Click "Create Profile"
3. Fill in:
   - Profile name
   - Delta Exchange API key and secret
   - Environment (sandbox or live)
4. Save the profile

## Step 8: Add Trading Algorithm

1. Go to your profile details
2. Click the "Algorithm" tab
3. Write or paste your Python trading algorithm code
4. Click "Save Algorithm"

See `backend/example_algorithm.py` for a template.

## Step 9: Configure Parameters

1. In profile details, go to "Parameters" tab
2. Set runtime parameters for your algorithm
3. Save parameters

## Step 10: Start Trading

1. Ensure your profile has:
   - ✓ API keys configured
   - ✓ Algorithm uploaded
   - ✓ Parameters set (if needed)

2. Click "Start" on your profile
3. Monitor logs in the "Logs" tab
4. View orders in the "Orders" tab

## Troubleshooting

### Port Already in Use

If ports 3000, 8000, 5432, or 6379 are already in use:

1. Stop conflicting services, or
2. Change ports in `docker-compose.yml` and update `.env`

### Database Connection Errors

1. Check PostgreSQL is running: `docker-compose ps postgres`
2. Verify credentials in `.env` match `docker-compose.yml`
3. Check logs: `docker-compose logs postgres`

### Frontend Not Loading

1. Check frontend container: `docker-compose logs frontend`
2. Verify `VITE_API_URL` in frontend environment
3. Check browser console for errors

### Worker Not Executing

1. Check worker logs: `docker-compose logs worker`
2. Verify profile is enabled in database
3. Check Redis connection: `docker-compose exec redis redis-cli ping`

### API Key Encryption Errors

1. Verify `TRADE_MASTER_KEY` is set in `.env`
2. Ensure key is exactly 64 hex characters (32 bytes)
3. Restart backend: `docker-compose restart backend`

## Next Steps

- Read [README.md](README.md) for feature overview
- Read [DEPLOYMENT.md](DEPLOYMENT.md) for production deployment
- Review `example_users.json` for multi-user setup
- Check `backend/example_algorithm.py` for algorithm examples

## Development Setup

For local development without Docker:

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql://user:pass@localhost/trading_db"
export TRADE_MASTER_KEY="your-key-here"
# ... other env vars

# Run migrations
alembic upgrade head

# Start server
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install

# Set API URL
export VITE_API_URL="http://localhost:8000/api/v1"

# Start dev server
npm run dev
```

## Support

For issues or questions:
1. Check logs: `docker-compose logs`
2. Review documentation
3. Check GitHub issues (if applicable)

