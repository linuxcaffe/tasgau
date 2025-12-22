## Installing TaskWarrior

# Install build dependencies
FROM fedora:43 AS taskw
RUN dnf install -y libuuid libuuid-devel cmake make g++ rustup git && \
    rustup-init -y

# Fetch & build release
RUN curl -L -o task-3.4.2.tar.gz  https://github.com/GothenburgBitFactory/taskwarrior/releases/download/v3.4.2/task-3.4.2.tar.gz && \
    tar xzf task-3.4.2.tar.gz && cd task-3.4.2 && \
    cmake -S . -B build -DCMAKE_BUILD_TYPE=Release && \
    cmake --build build

## Installing tasgau
FROM python:3.14-slim

# Install taskwarrior from previous build stage
COPY --from=taskw /task-3.4.2/build/src/task /bin/task

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Change the working directory to the `app` directory
WORKDIR /app

# Install dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --group deploy

ADD . /app

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --group deploy

CMD ["uv", "run", "gunicorn", "--bind", "0.0.0.0:8000", "app:app"]