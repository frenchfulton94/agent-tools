test-unit:
	npx vitest run test/unit

test:
	docker compose up -d db && npx vitest run && docker compose down
