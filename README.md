# URL Shortener API

A small URL-shortening backend built with FastAPI and PostgreSQL. Users can register, sign in, create short links, and manage their own links. Anyone with a short link can use it to redirect to the original URL.

The project is built as a practical backend engineering exercise: the focus is on API behavior, database correctness, authentication, migrations, testing, and a repeatable Docker-based setup.

## Features

- User registration and JWT bearer-token authentication.
- Argon2 password hashing and case-insensitive usernames.
- Seven-character Base62 short codes.
- Create, list, update, and delete a user's links.
- Public redirects with a `307` response.
- Per-user URL uniqueness, with short-code collisions handled by bounded retries.
- SQLAlchemy models and Alembic database migrations.
- Docker Compose for the API, PostgreSQL, and migration step.
- Locked production and development dependencies, pytest, Ruff, and GitHub Actions.

## Stack

- **API:** Python 3.14, FastAPI, Pydantic
- **Database:** PostgreSQL 17, SQLAlchemy, psycopg 3
- **Migrations:** Alembic
- **Authentication:** JWT (HS256), `pwdlib` with Argon2
- **Testing and quality:** pytest, `httpx2`, Ruff
- **Runtime and CI:** Docker, Docker Compose, GitHub Actions

## Run locally with Docker

### Requirements

Install Docker Desktop with Docker Compose, then clone the repository:

```bash
git clone https://github.com/Mehrshad-77/url-shortner.git
cd url-shortner
cp .env.example .env
```

Open `.env` and replace `JWT_SECRET_KEY=replace-with-a-random-secret` with a private secret at least 32 characters long. Generate one with:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

Copy the generated value into `.env`. The database values in `.env.example` are for local development; use different credentials and a proper secret for any deployed environment. If you change the PostgreSQL username or password, update both `COMPOSE_DATABASE_URL` and `COMPOSE_TEST_DATABASE_URL` to match. Percent-encode URL-special characters in passwords used inside a database URL.

Start the services:

```bash
docker compose up --build -d
docker compose ps
```

The API is available at:

- API root: <http://localhost:8000/>
- Health check: <http://localhost:8000/health>
- Interactive API docs: <http://localhost:8000/docs>

Compose starts PostgreSQL, runs the `migrate` service (`alembic upgrade head`), and starts the API after the migration succeeds. To inspect logs:

```bash
docker compose logs -f api
```

Stop the services with:

```bash
docker compose down
```

The PostgreSQL data volume is retained by default. **Do not use `docker compose down -v` unless you intentionally want to delete the stored database data.**

## Configuration

The real `.env` file is local and should not be committed. `.env.example` lists the expected Compose settings:

| Variable | Purpose |
|---|---|
| `POSTGRES_DB` | Initial application database name |
| `POSTGRES_USER` | PostgreSQL user |
| `POSTGRES_PASSWORD` | PostgreSQL password |
| `COMPOSE_DATABASE_URL` | Application database URL used by containers; hostname is `db` |
| `COMPOSE_TEST_DATABASE_URL` | Test database URL for the Compose network |
| `JWT_SECRET_KEY` | Private signing key; must be at least 32 characters |
| `JWT_ALGORITHM` | JWT signing algorithm (defaults to `HS256`) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token lifetime (defaults to `30`) |

The application requires `DATABASE_URL` and `JWT_SECRET_KEY`. Docker Compose supplies `DATABASE_URL` to the API and migration containers using `COMPOSE_DATABASE_URL`. A local process can set `DATABASE_URL` directly in its environment.

## API

Authenticated endpoints expect `Authorization: Bearer <token>` unless noted otherwise.

| Method | Path | Description | Authentication |
|---|---|---|---|
| `GET` | `/` | API welcome message | No |
| `GET` | `/health` | Health check | No |
| `POST` | `/users` | Register a user (`201` on success) | No |
| `POST` | `/token` | Exchange username and password for a JWT | No |
| `GET` | `/users/me` | Get the current user's profile | Yes |
| `GET` | `/users/me/urls` | List the current user's links | Yes |
| `POST` | `/urls` | Create a short link (`201` on success) | Yes |
| `PATCH` | `/users/me/urls/{short_code}` | Update a link owned by the current user | Yes |
| `DELETE` | `/users/me/urls/{short_code}` | Delete a link owned by the current user (`204`) | Yes |
| `GET` | `/{short_code}` | Redirect to the original URL (`307`) | No |

URLs must use HTTP or HTTPS. The user's link list supports `skip` and `limit` pagination (`limit` defaults to 20 and is restricted to 1–100). A user cannot manage another user's links; an unknown or unowned link returns `404`. Duplicate usernames and duplicate URLs for the same user return `409`.

### Quick example

Register a user:

```bash
curl -X POST http://localhost:8000/users \
  -H 'Content-Type: application/json' \
  -d '{"username":"alice","password":"a-strong-password"}'
```

Sign in. `/token` accepts form data:

```bash
curl -X POST http://localhost:8000/token \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'username=alice&password=a-strong-password'
```

Use the returned `access_token` as a bearer token to create a short link:

```bash
curl -X POST http://localhost:8000/urls \
  -H 'Authorization: Bearer YOUR_ACCESS_TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{"url":"https://example.com"}'
```

The response includes a `short_code`. Open `http://localhost:8000/<short_code>` to redirect to the original URL. You can also try these requests through `/docs`.

## Database migrations

Alembic is responsible for changing the application database schema. Editing `app/models.py` alone does not update an existing database. When the models change, create and review a migration, then apply it:

```bash
alembic revision --autogenerate -m "describe the schema change"
alembic upgrade head
alembic check
```

Run these commands with `DATABASE_URL` pointing at the intended development database. `alembic upgrade head` applies the migration chain; `alembic check` compares the database schema with the SQLAlchemy models. Review autogenerated migrations before applying them.

GitHub Actions also verifies migrations on every push and pull request: it applies the migration chain to the fresh application database, runs `alembic check`, then runs the API tests against a separate test database. This catches both migrations that fail to execute and model changes that have no corresponding migration.

The Compose `migrate` service applies `alembic upgrade head` during startup. The application starts only after that service completes successfully.

## Run tests locally

Tests run from the development environment because the production image intentionally does not include test tools.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev-lock.txt
```

Set `DATABASE_URL` and `TEST_DATABASE_URL` to two PostgreSQL databases that your local test user can access, then run:

```bash
python -m pytest -q
```

For example, adapt the host, port, username, and password to your local PostgreSQL setup:

```bash
export DATABASE_URL='postgresql+psycopg://USER:PASSWORD@localhost:5432/url_shortener'
export TEST_DATABASE_URL='postgresql+psycopg://USER:PASSWORD@localhost:5432/url_shortener_test'
```

**Important:** the test fixture drops and recreates tables in `TEST_DATABASE_URL` before each test. Point it only at a dedicated, disposable test database, and never set it to the same database as `DATABASE_URL` or to a database containing data you need to keep.

Run lint and format checks with the same Ruff version used in CI:

```bash
python -m pip install ruff==0.17.0
ruff check .
ruff format --check .
```

## How the project evolved

The project started as an authenticated URL-shortening API and grew through focused fixes to its data model, failure handling, and runtime setup:

- Routes, services, schemas, and database models were separated so API handling and business logic are easier to follow.
- Username handling was made case-insensitive. Passwords use Argon2, and failed logins return a consistent message.
- Short-code creation was changed to rely on the database's unique constraint with a bounded retry when a collision occurs, instead of a race-prone check-then-insert sequence.
- URL uniqueness became per-user: one user cannot save the same destination twice, but another user can save that destination. Ownership is enforced in update and delete queries.
- Alembic migrations became the way to change the real schema. The production container was also moved to a non-root user, test packages were split out of the runtime lockfile, and GitHub Actions was added for repeatable checks.

The changes were driven by failure cases as well as the happy path: concurrent short-code creation, duplicate URLs across users, case-insensitive usernames, invalid authentication, schema changes, and container permissions.

## CI

The GitHub Actions workflow currently has three jobs:

- **Lint:** `ruff check .` and `ruff format --check .`
- **Test:** start PostgreSQL 17, create a separate test database, run `alembic upgrade head` and `alembic check` against the application database, then run pytest against the test database
- **Build image:** build the production Docker image without publishing it

The migration checks are deliberately separate: `alembic upgrade head` verifies that the migration chain runs successfully, while `alembic check` detects model/schema changes that need a migration. Workflow: [`.github/workflows/tests.yml`](.github/workflows/tests.yml).

## Project layout

```text
app/
  api/              API routes and authentication dependencies
  services/         User and URL business logic
  config.py         Application settings
  database.py       SQLAlchemy engine and session setup
  models.py         SQLAlchemy models and constraints
  schemas.py        Request and response schemas
  security.py       Password hashing and JWT creation
alembic/            Migration environment and migration versions
docker/postgres/    PostgreSQL initialization SQL
tests/              API and service tests
Dockerfile
docker-compose.yml
requirements.in                 Runtime dependency inputs
requirements-lock.txt           Pinned runtime dependencies
requirements-dev.in             Development/test dependency inputs
requirements-dev-lock.txt       Pinned development/test dependencies
.github/workflows/tests.yml     GitHub Actions workflow
```

## Current scope

This project is focused on the core URL-shortening and account-management flow. Rate limiting for registration and login is not currently implemented, and the API has not been presented as a fully production-hardened public service.
