FROM python:3.12-slim

WORKDIR /app

# Step 1: Install dependencies only (cached unless pyproject.toml changes)
COPY backend/pyproject.toml /tmp/pyproject.toml
RUN python -c "\
import tomllib, subprocess, sys; \
deps = tomllib.load(open('/tmp/pyproject.toml','rb'))['project']['dependencies']; \
subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--no-cache-dir'] + deps)"

# Step 2: Copy backend source
COPY backend/ backend/

# Step 3: Install the package itself without re-downloading deps (fast)
RUN pip install --no-cache-dir --no-deps "./backend"
