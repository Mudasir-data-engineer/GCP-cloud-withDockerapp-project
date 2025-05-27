up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f

build:
	docker compose build

ps:
	docker compose ps

restart:
	docker compose down && docker compose up -d

# Special for fake-api service
fake-api-logs:
	docker compose logs -f fake-api

restart-fake-api:
	docker compose restart fake-api
