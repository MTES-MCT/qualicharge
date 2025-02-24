# -- Base image --
FROM python:3.12-slim

ARG DOCKER_UID 1000
ARG DOCKER_GID 1000

# Upgrade system packages to install security updates
RUN apt-get update && \
    apt-get -y upgrade && \
    apt-get install -y curl && \
    rm -rf /var/lib/apt/lists/*

# Upgrade pip to its latest release to speed up dependencies
# installation
RUN pip install --upgrade pip && \
    pip install pipenv==2024.4.1

# Pipenv configuration
ENV PIPENV_USER_UID=${DOCKER_UID}
ENV PIPENV_USER_GID=${DOCKER_GID}
ENV PIPENV_USER_NAME=pipenv
ENV PIPENV_GROUP_NAME=pipenv
ENV PIPENV_USER_HOME=/opt/pipenv/
ENV PIPENV_CUSTOM_VENV_NAME=qualicharge

# Create a pipenv user and group
RUN groupadd \
      -g ${PIPENV_USER_GID} \
      ${PIPENV_GROUP_NAME} && \
    useradd -rm \
      -d ${PIPENV_USER_HOME} \
      -s /bin/bash \
      -u ${PIPENV_USER_UID} \
      -g ${PIPENV_USER_GID} \
      ${PIPENV_USER_NAME}

# /app will be our working directory
RUN mkdir /app && \
    chown ${PIPENV_USER_NAME}:${PIPENV_GROUP_NAME} /app

# -- build (⚠️ development only) --
COPY --chown="${PIPENV_USER_NAME}:${PIPENV_GROUP_NAME}" . /app
WORKDIR /app
USER ${PIPENV_USER_NAME}:${PIPENV_GROUP_NAME}
RUN pipenv install -d

# -- Run --
CMD ["pipenv", "run", "honcho", "start", "web"]
