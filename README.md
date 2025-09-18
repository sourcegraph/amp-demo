# Amp Demo

This is a demo repo that is carefully crafted to showcase the capabilities of Amp centered around an example e-commerce platform with a FastAPI backend and React frontend. Data is stored in SQLite so it is self contained and easy to run.

For more information about Amp visit the [Amp manual](https://ampcode.com/manual).

See the [DEMO.md](DEMO.md) for more information about how to effectively use this repo for an array of different demo purposes ranging from fixes an issue with a PR to advanced refactors.

<img width="1673" height="1010" alt="Screenshot 2025-09-17 at 3 48 15 PM" src="https://github.com/user-attachments/assets/2fd2b128-d937-4cc9-9437-5386c3ebc1f6" />


## Project Structure

```
.
├── backend/           # FastAPI backend
│   ├── app/          # Application source code
│   ├── tests/        # Backend tests
│   ├── alembic/      # Database migrations (only needed if changes to database are made)
│   ├── pyproject.toml # Python dependencies (managed by uv)
│   └── pytest.ini    # Test configuration
├── frontend/          # React frontend (TypeScript/Vite)
│   ├── src/          # React components and pages
│   ├── e2e/          # Playwright E2E tests
│   ├── public/       # Static assets
│   └── package.json  # Node.js dependencies
├── compose.yml        # Docker Compose configuration
├── justfile          # Development automation commands
├── AGENTS.md         # Agent documentation
└── README.md
```

## Prerequisites

### Mandatory

- [Just](https://github.com/casey/just) - Command runner (`brew install just`)
- [Docker/Podman](https://podman.io/) - Container runtime (recommend podman)

### Locally Outside Containers Only

- [Node.js](https://nodejs.org/) - For frontend development
- [uv](https://docs.astral.sh/uv/) - Python package manager (backend uses Python 3.13+)

## Environment Configuration

The application uses environment variables for configuration. Copy `.env.example` to `.env` and customize as needed.

### Currency Exchange Configuration

- `FX_API_KEY`: OpenExchangeRates API key (optional - uses mock rates if not provided)
  - Get your free API key at: https://openexchangerates.org/signup/free
- `ALLOWED_CURRENCIES`: Comma-separated list of supported currencies (default: USD,GBP,EUR,AUD,MXN,JPY)
- `FX_CACHE_TTL_HOURS`: Cache duration for exchange rates (default: 1 hour)

### Other Configuration

- `DATABASE_URL`: Database connection string (default: sqlite:///./store.db)
- `DEBUG`: Enable debug mode (default: true)
- `DISABLE_SCHEDULER`: Disable the FX rate update scheduler (default: false)
- `VITE_API_URL`: Frontend API endpoint (default: http://localhost:8001)
- `VITE_DEFAULT_CURRENCY`: Default currency for frontend (default: USD)

## Quick Start

Clone the project:

```bash
git clone https://github.com/sourcegraph/amp-demo.git
cd amp-demo
```

Set up environment variables (optional):

```bash
cp .env.example .env
# Edit .env to add your OpenExchangeRates API key or customize settings
```

Run with Docker/Podman (recommended):

```bash
just up          # Start both services with hot-reload
```

Access the application:

- Frontend: http://localhost:3001
- Backend API: http://localhost:8001

## Development Commands

### Lifecycle Commands

```bash
just up               # Start both services
just backend          # Start only backend
just frontend         # Start only frontend
just down             # Stop all containers
```

### Seed Database

```bash
just seed             # Populate database with sample data (only needed if database changes)
```

### Local Development (without containers)

Install dependencies:
```bash
just install          # Backend dependencies (uv)
just install-frontend # Frontend dependencies (npm)
```

Run services locally:
```bash
# Backend
cd backend && uv run uvicorn main:app --reload

# Frontend
cd frontend && npm run dev
```

### Testing & Quality

#### Container Testing (Recommended - Guaranteed Portability)
```bash
just test             # Backend tests in container
just test-cov         # Backend tests with coverage in container
just test-e2e         # E2E tests in container (headless)
just test-e2e-headed  # E2E tests in container (headed - for debugging)
just test-all         # All tests in containers (CI equivalent)
```

#### Local Testing (Optional - Faster Development)
```bash
# Setup local environment first
./backend/setup-dev.sh                 # Setup backend for local testing
just setup-e2e-local                   # Setup E2E testing locally

# Run tests locally
just test-local                        # Backend tests locally
just test-cov-local                    # Backend coverage locally  
just test-local-single TEST            # Run single test locally
just test-e2e-local                    # E2E tests locally (headless)
just test-e2e-local-headed             # E2E tests locally (headed - for debugging)
just test-all-local                    # All tests locally
```

#### Code Quality
```bash
just check            # Run linting (ruff) and type checking (mypy)
just format           # Format backend code
cd frontend && npm run lint            # Lint frontend TypeScript
```

### Build & Deployment

```bash
just build            # Build frontend for production
cd frontend && npm run build  # Alternative frontend build
```

### Database Management

```bash
just reset-db         # Reset SQLite database
just db-shell         # Open SQLite CLI
just migrate-create "message"  # Create new migration
just migrate-up       # Apply migrations
just migrate-down     # Rollback migration
```

### Monitoring & Debugging

```bash
just health           # Check service health

just logs [service]   # View recent logs (default: backend)
just logs-follow [service]  # Follow live logs
```

### Source

Based on the [ecommerce-demo repo](https://github.com/ViaxCo/ecommerce-demo).
