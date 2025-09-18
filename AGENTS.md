# ecommerce-demo Agent Guide

## Running the App
**With containers (recommended for development):**

**Containers (hot-reload, ports 3001/8001):**
- `just up` - Both services with hot-reload (recommended)
- `just down` - Stop all containers
- `just backend` - Backend only (auto-reload)
- `just frontend` - Frontend only (Vite hot-reload)

**Locally without containers:**
- `cd backend && uv run uvicorn main:app --reload` - Backend only
- `cd frontend && npm run dev` - Frontend only

**URLs:** Frontend http://localhost:3001, Backend http://localhost:8001, Docs http://localhost:8001/docs

## Tests & Quality

### Container Testing (Default - Guaranteed Portability)
- `just test` - Backend tests in container
- `just test-cov` - Backend tests with coverage in container  
- `just test-e2e` - E2E tests in container
- `just test-all` - All tests in containers (CI equivalent)

### Local Testing (Optional - Faster Development)
- `just test-local` - Backend tests locally (requires: uv sync)
- `just test-cov-local` - Backend coverage locally
- `just test-local-single TEST` - Run single test locally
- `just test-e2e-local` - E2E tests locally (requires: npm ci, playwright install)
- `just test-all-local` - All tests locally

### Code Quality
- `just check` - Lint (ruff) and type check (mypy) backend
- `just format` - Format backend code with ruff
- `cd frontend && npm run lint` - Lint frontend TypeScript
- `just build` - Build frontend production bundle
- `just seed` - Seed a fresh SQLite database

## Architecture
FastAPI (Python 3.13+) backend with React TypeScript frontend. SQLite database with Alembic migrations. Docker containerized with development hot-reload. Backend serves API at :8001, frontend at :3001. Uses uv for Python deps, npm for Node deps.

## Code Style
**Backend**: Python type hints everywhere, SQLModel for DB models, Pydantic schemas for validation, HTTPException for errors, async/await patterns, dependency injection with Depends()
**Frontend**: Functional React components with TypeScript interfaces, Chakra UI styling, Context API state management, Formik forms with Yup validation, Framer Motion animations, arrow functions
