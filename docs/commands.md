todo: clean
# Introduction
This page lists some commands often used during development. Some of these will be added as VSCode tasks.

# Docker
## Compose up
- Spin up on dev server: `docker-compose -f infrastructure/development.yml --env-file ./.docker-env -p athlon up --build`

## Build
- Build: `docker build -t auckebos/athlon-flex-notifier -f docker/Dockerfile .`
- Build with BuildX: 
    - Create builder: `docker buildx create --name athlon-flex-notifier-builder`
    - Build: `docker buildx use athlon-flex-notifier-builder`
    - Build & push for both required architectures: `docker buildx build --platform linux/amd64,linux/arm64 -t auckebos/athlon-flex-notifier --push -f infrastructure/Dockerfile .`
    - Build for one architecture: `docker buildx build --platform linux/arm64 -f infrastructure/Dockerfile .`


