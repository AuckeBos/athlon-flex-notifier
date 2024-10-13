FROM python:3.12-bookworm
LABEL maintainer="Aucke Bos"

# Set user
ARG USERNAME=athlon
ARG UID=1000
ARG GID=$UID
RUN apt update && \
    apt install -y sudo && \
    addgroup --gid $GID athlon && \
    adduser --uid $UID --gid $GID --disabled-password --gecos "" athlon && \
    echo 'athlon ALL=(ALL) NOPASSWD: ALL' >> /etc/sudoers

ENV USERNAME=athlon
USER $USERNAME
# Copy files
COPY --chown=athlon:athlon ./pyproject.toml ./requirements.lock ./README.md /home/athlon/

# Install deps
WORKDIR /home/athlon
RUN PYTHONDONTWRITEBYTECODE=1 pip install --no-cache-dir -r requirements.lock

# Install self
COPY --chown=athlon:athlon ./src /home/athlon/src
RUN PYTHONDONTWRITEBYTECODE=1 pip install --no-cache-dir -e .

# Start Prefect worker
WORKDIR /home/athlon/src/athlon_flex_notifier
CMD ["python", "worker.py"]
