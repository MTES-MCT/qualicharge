# The builder image, used to build the virtual environment
FROM python:3.12-slim AS base

ARG DOCKER_UID 1000
ARG DOCKER_GID 1000

# Upgrade system packages to install security updates
RUN apt-get update && \
    apt-get -y upgrade && \
    rm -rf /var/lib/apt/lists/*

# Upgrade pip to its latest release to speed up dependencies
# installation
RUN pip install --upgrade pip && \
    pip install poetry==1.8.3

# User and group
ENV POETRY_USER_UID=${DOCKER_UID} \
    POETRY_USER_GID=${DOCKER_GID} \
    POETRY_USER_NAME=poetry \
    POETRY_GROUP_NAME=poetry \
    POETRY_USER_HOME=/opt/poetry

# Create a pipenv user and group
RUN groupadd \
      -g ${POETRY_USER_GID} \
      ${POETRY_GROUP_NAME} && \
    useradd -rm \
      -d ${POETRY_USER_HOME} \
      -s /bin/bash \
      -u ${POETRY_USER_UID} \
      -g ${POETRY_USER_GID} \
      ${POETRY_USER_NAME}

# /app will be our working directory
RUN mkdir /app /tmp/cache && \
    chown ${POETRY_USER_NAME}:${POETRY_GROUP_NAME} /app /tmp/cache

# Poetry configuration
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=0 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/cache \
    POETRY_VIRTUALENVS_PATH=${POETRY_USER_HOME}/virtualenvs

WORKDIR /app

USER ${POETRY_USER_NAME}:${POETRY_GROUP_NAME}

# -- builder --
FROM base AS builder

COPY pyproject.toml poetry.lock README.md ./

RUN --mount=type=cache,uid=${POETRY_USER_UID},gid=${POETRY_USER_GID},target=${POETRY_CACHE_DIR} \
      poetry install --with=dev --no-root

# -- development --
FROM base AS development

COPY --from=builder ${POETRY_VIRTUALENVS_PATH} ${POETRY_VIRTUALENVS_PATH}
COPY . /app/

# Install current package
RUN --mount=type=cache,uid=${POETRY_USER_UID},gid=${POETRY_USER_GID},target=${POETRY_CACHE_DIR} \
      poetry install

ENTRYPOINT ["poetry", "run"]
