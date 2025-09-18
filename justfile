# FastAPI + React E-commerce Demo Automation
# Install 'just' via: brew install just (macOS) or cargo install just

# ─── variables ──────────────────────────────────────────────
CM := "podman-compose"

# Default recipe to display available commands
default:
    @just --list

# Install backend dependencies
install:
    cd backend && uv sync

# Install frontend dependencies
install-frontend:
    cd frontend && npm ci

# Install E2E test dependencies
install-e2e:
    cd frontend && npm install --save-dev @playwright/test
    cd frontend && npx playwright install --with-deps

# ─── containers (hot-reload, canonical ports) ─────────────
# Start both services with hot-reload
up:
    @echo "🐳 Starting dev containers on 3001/8001..."
    {{CM}} up --build -d

# Stop all containers
down:
    @echo "🛑 Stopping and cleaning up containers..."
    -{{CM}} down --remove-orphans 2>/dev/null || true
    @echo "🧹 Force removing any remaining containers and networks..."
    -podman container stop $(podman ps -aq) 2>/dev/null || true
    -podman container rm -f $(podman ps -aq) 2>/dev/null || true  
    -podman pod rm -f $(podman pod ls -q) 2>/dev/null || true
    -podman network rm $(podman network ls --filter "name=amp-demo" -q) 2>/dev/null || true
    @echo "✅ Cleanup complete"

# Run backend only
backend:
    {{CM}} up backend --build -d

# Run frontend only
frontend:
    {{CM}} up frontend --build -d

# Seed the database with products and images
seed:
    cd backend && uv run python -m app.seed

# Run backend tests
test:
    {{CM}} run --rm backend pytest

# Run backend tests with coverage
test-cov:
    {{CM}} run --rm backend pytest --cov=app --cov-report=html

# ─── local testing (faster development) ──────────────────────
# Run backend tests locally (requires: uv sync)
test-local:
    cd backend && uv run pytest

# Run backend tests with coverage locally
test-cov-local:
    cd backend && uv run pytest --cov=app --cov-report=html --cov-report=term

# Run single test locally
test-local-single TEST:
    cd backend && uv run pytest {{TEST}}

# Run E2E tests in containers (headless - default)
test-e2e:
    @echo "🎭 Running E2E tests in containers (headless)..."
    {{CM}} --profile test up -d backend frontend
    @sleep 5
    {{CM}} --profile test run --rm -e HEADED=0 e2e
    {{CM}} --profile test down

# Run E2E tests in containers (headed mode for debugging)
test-e2e-headed:
    @echo "🎭 Running E2E tests in containers (headed)..."
    {{CM}} --profile test up -d backend frontend
    @sleep 5
    {{CM}} --profile test run --rm -e HEADED=1 e2e
    {{CM}} --profile test down

# Run E2E tests locally (headless - default)
test-e2e-local:
    cd frontend && HEADED=0 npx playwright test

# Run E2E tests locally (headed mode for debugging)
test-e2e-local-headed:
    cd frontend && HEADED=1 npx playwright test

# Setup E2E testing locally
setup-e2e-local:
    cd frontend && npx playwright install --with-deps

# Run all tests (backend + E2E) - containers
test-all:
    @just test
    @just test-e2e

# Run all tests locally (backend + E2E) - faster development
test-all-local:
    @just test-local
    @just test-e2e-local

# View recent logs for a specific service (default: backend)
logs SERVICE="backend":
    {{CM}} logs --tail=50 {{SERVICE}}

# Follow logs for a specific service (default: backend) 
logs-follow SERVICE="backend":
    {{CM}} logs -f {{SERVICE}}

# Check backend code quality
check:
    cd backend && uv run ruff check .
    cd backend && uv run mypy .

# Format backend code
format:
    cd backend && uv run ruff format .

# Build frontend for production
build:
    cd frontend && npm run build

# Reset database (removes store.db files)
reset-db:
    cd backend && rm -f store.db store.db-*

# Health check for running services
health:
    @echo "🔍 Checking service health..."
    @curl -f http://localhost:8001/health || echo "❌ Backend not responding"
    @curl -f http://localhost:3001 || echo "❌ Frontend not responding"

# Run database shell (SQLite CLI)
db-shell:
    {{CM}} exec backend sqlite3 store.db

# Database migration commands
migrate-create MESSAGE:
    {{CM}} exec backend alembic revision --autogenerate -m "{{MESSAGE}}"

migrate-up:
    {{CM}} exec backend alembic upgrade head

migrate-down:
    {{CM}} exec backend alembic downgrade -1

migrate-history:
    {{CM}} exec backend alembic history
