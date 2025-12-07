# Multi-user Delta Exchange Algorithmic Trading Platform

A self-hosted web application that enables up to 4 users (expandable to 100) to run crypto-derivative trading algorithms on Delta Exchange with separate profiles, API keys, and algorithm configurations.

## Features

- **Multi-user Support**: Up to 100 users with JWT-based authentication
- **Profile Management**: Multiple profiles per user with separate API keys and configurations
- **Algorithm Editor**: In-browser code editor (Monaco) for Python trading algorithms
- **Parameter Management**: Dynamic parameter forms with validation
- **Version Control**: Algorithm versioning with rollback capability
- **Real-time Execution**: Background workers execute algorithms per profile
- **Sandbox & Live Modes**: Toggle between sandbox and live trading environments
- **Observability**: Real-time logs, trade history, P&L metrics, and dashboards
- **Safety Features**: Kill-switch, max drawdown limits, risk controls
- **24/7 Operation**: Containerized deployment with automatic restart and log rotation

## Tech Stack

- **Backend**: Python 3.11+ with FastAPI
- **Frontend**: React 18+ with Vite, Monaco Editor
- **Database**: PostgreSQL 15+
- **Cache/Broker**: Redis 7+
- **Containerization**: Docker + Docker Compose
- **Process Management**: systemd (Linux) or NSSM (Windows)

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)
- Node.js 18+ (for local development)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd Crypto_Trading
```

2. Copy environment template:
```bash
cp .env.example .env
```

3. Edit `.env` and set:
   - `TRADE_MASTER_KEY`: A 32-byte hex string for API key encryption (generate with `openssl rand -hex 32`)
   - Database credentials
   - Other configuration values

4. Start services:
```bash
docker-compose up -d
```

5. Access the application:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

### Initial Setup

1. Register the first user via the UI or API
2. Create a profile with your Delta Exchange API keys
3. Upload or write your trading algorithm
4. Configure parameters and risk settings
5. Enable the profile to start trading

## Project Structure

```
Crypto_Trading/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API routes
│   │   ├── core/           # Core configuration, security
│   │   ├── models/         # Database models
│   │   ├── services/       # Business logic
│   │   ├── workers/        # Background workers
│   │   └── exchange/       # Delta Exchange client
│   ├── alembic/            # Database migrations
│   ├── tests/              # Backend tests
│   └── requirements.txt
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── pages/         # Page components
│   │   ├── services/      # API clients
│   │   └── utils/         # Utilities
│   └── package.json
├── docker-compose.yml      # Docker Compose configuration
├── .env.example           # Environment variables template
└── README.md              # This file
```

## Configuration

### Environment Variables

See `.env.example` for all available configuration options. Key variables:

- `TRADE_MASTER_KEY`: Master encryption key (32-byte hex)
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `JWT_SECRET`: Secret for JWT token signing
- `DELTA_SANDBOX_URL`: Delta Exchange sandbox API URL
- `DELTA_LIVE_URL`: Delta Exchange live API URL

### Delta Exchange Setup

1. Create an account at [Delta Exchange](https://www.delta.exchange/)
2. Generate API keys in the dashboard
3. For sandbox testing, use sandbox API keys
4. Add keys to your profile in the platform

## Deployment

### Linux (systemd)

1. Copy `deployment/systemd/trading-platform.service` to `/etc/systemd/system/`
2. Edit the service file with your paths
3. Enable and start:
```bash
sudo systemctl enable trading-platform
sudo systemctl start trading-platform
```

### Windows (NSSM)

1. Install NSSM
2. Create service:
```bash
nssm install TradingPlatform "docker-compose" "-f docker-compose.yml up"
nssm set TradingPlatform AppDirectory "D:\CryptoTrading\Crypto_Trading"
nssm start TradingPlatform
```

### Log Rotation

Logs are automatically rotated via Docker logging driver or logrotate. See `deployment/logrotate/` for configuration.

## Development

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Running Tests

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

## API Documentation

Interactive API documentation is available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Security

- API keys are encrypted at rest using AES-256
- JWT tokens with short expiration
- CORS restrictions
- Rate limiting on API endpoints
- Input validation and sanitization
- SQL injection protection (SQLAlchemy ORM)

## Monitoring

- Prometheus metrics endpoint: `/metrics`
- Health check: `/health`
- Structured JSON logging
- Real-time log streaming in UI

## Troubleshooting

### Common Issues

1. **Database connection errors**: Check PostgreSQL is running and credentials in `.env`
2. **Redis connection errors**: Verify Redis is accessible
3. **API key encryption errors**: Ensure `TRADE_MASTER_KEY` is set correctly
4. **Worker not executing**: Check profile is enabled and worker logs

### Logs

View logs:
```bash
docker-compose logs -f backend
docker-compose logs -f worker
docker-compose logs -f frontend
```

## License

[Specify your license]

## Support

[Add support contact information]

