# -- Base image --
FROM python:3.14-slim

ARG DOCKER_UID 1000
ARG DOCKER_GID 1000

# Upgrade system packages to install security updates
RUN apt-get update && \
    apt-get -y upgrade && \
    apt-get install -y curl && \
    rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:0.9.7 /uv /uvx /bin/

# UV user configuration
ENV UV_USER_UID=${DOCKER_UID}
ENV UV_USER_GID=${DOCKER_GID}
ENV UV_USER_NAME=uv
ENV UV_GROUP_NAME=uv
ENV UV_USER_HOME=/home/uv/
ENV UV_CUSTOM_VENV_NAME=qualicharge

# Create a uv user and group
RUN groupadd \
      -g ${UV_USER_GID} \
      ${UV_GROUP_NAME} && \
    useradd -rm \
      -d ${UV_USER_HOME} \
      -s /bin/bash \
      -u ${UV_USER_UID} \
      -g ${UV_USER_GID} \
      ${UV_USER_NAME}

# Create virtual environment that will be used by uv with appropriate
# permissions
RUN mkdir -p /app/.venv && \ 
    chown -R "${DOCKER_UID}:${DOCKER_GID}" /app

USER ${DOCKER_UID}:${DOCKER_GID}
# UV cache directory
RUN mkdir -p /home/uv/.cache/uv

WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy from the cache instead of linking since it's a mounted volume
ENV UV_LINK_MODE=copy

# Install dependencies
RUN --mount=type=cache,uid=${DOCKER_UID},gid=${DOCKER_GID},target=/home/uv/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project

# Copy the project into the image
ADD --chown=${DOCKER_UID}:${DOCKER_GID} . /app

# Sync the project
RUN --mount=type=cache,uid=${DOCKER_UID},gid=${DOCKER_GID},target=/home/uv/.cache/uv \
    uv sync --locked

# -- Run --
CMD uv run honcho start -f Procfile.dev
