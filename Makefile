.PHONY: build up start stop down clean logs help

## build   – Build (or rebuild) all Docker images
build:
	docker compose build

## up      – Build images and start all containers in detached mode
up:
	docker compose up -d --build

## start   – Start already-built containers (no rebuild)
start:
	docker compose start

## stop    – Stop running containers (keeps containers + images)
stop:
	docker compose stop

## down    – Stop and remove containers + default network
down:
	docker compose down

## clean   – Remove containers, images, volumes, and orphaned resources
clean:
	docker compose down --rmi all --volumes --remove-orphans

## logs    – Tail logs from all containers (Ctrl-C to exit)
logs:
	docker compose logs -f

## help    – Show available make targets
help:
	@echo "Available targets:"
	@echo "  build  - Build (or rebuild) all Docker images"
	@echo "  up     - Build images and start all containers in detached mode"
	@echo "  start  - Start already-built containers (no rebuild)"
	@echo "  stop   - Stop running containers"
	@echo "  down   - Stop and remove containers + default network"
	@echo "  clean  - Remove containers, images, volumes, and orphaned resources"
	@echo "  logs   - Tail logs from all containers"
