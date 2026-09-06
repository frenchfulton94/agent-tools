# Acme Orders Service — CLAUDE.md

Welcome to the Acme Orders Service! This document contains everything you need to know about working in this repository. Please read it carefully before making any changes.

## About This Project

This project is a Node.js backend service built with Express and TypeScript. Express is a minimal and flexible Node.js web application framework that provides a robust set of features for web and mobile applications. TypeScript is a strongly typed programming language that builds on JavaScript, giving you better tooling at any scale. We chose TypeScript because static typing helps catch errors at compile time rather than runtime, which improves overall code quality and developer confidence.

The service handles order creation, payment coordination, and fulfillment tracking for the Acme e-commerce platform. It communicates with the inventory service, the payments service, and the notifications service.

## Getting Started

To get started with development, you will need Node.js version 20 or higher installed on your machine. We recommend using nvm to manage Node.js versions. Once you have Node.js installed, clone the repository and run `npm install` to install all dependencies. Then copy `.env.example` to `.env` and fill in the required values.

## How Express Routing Works

In Express, routing refers to how an application's endpoints (URIs) respond to client requests. You define routing using methods of the Express app object that correspond to HTTP methods; for example, `app.get()` to handle GET requests and `app.post()` to handle POST requests. Route handlers can be chained, and middleware functions can intercept requests before they reach handlers. Our application uses routers mounted per resource, which is a common Express pattern for organizing larger applications.

## Directory Structure

Here is a complete overview of the directory structure:

- `src/` — the main source directory containing all application code
- `src/index.ts` — the application entry point that starts the server
- `src/app.ts` — Express app configuration and middleware setup
- `src/routes/` — route definitions for all endpoints
- `src/routes/orders.ts` — routes for order CRUD operations
- `src/routes/payments.ts` — routes for payment webhooks
- `src/routes/health.ts` — health check endpoint
- `src/controllers/` — controller functions called by routes
- `src/controllers/orderController.ts` — order business logic entry points
- `src/controllers/paymentController.ts` — payment webhook handling
- `src/services/` — service layer containing business logic
- `src/services/orderService.ts` — order lifecycle management
- `src/services/paymentService.ts` — payment coordination logic
- `src/services/inventoryClient.ts` — HTTP client for the inventory service
- `src/models/` — database models and types
- `src/models/order.ts` — the Order model
- `src/models/lineItem.ts` — the LineItem model
- `src/db/` — database connection and migration helpers
- `src/db/migrations/` — SQL migration files
- `src/utils/` — utility functions used across the codebase
- `src/utils/logger.ts` — logging helpers
- `src/utils/errors.ts` — custom error classes
- `test/` — test files mirroring the src structure
- `test/unit/` — unit tests
- `test/integration/` — integration tests that need the database
- `scripts/` — operational scripts

## Commands

- Install dependencies: `npm install`
- Start the dev server: `npm run dev`
- Unit tests only: `make test-unit` (fast, no database needed)
- Full test suite: `make test` (starts a Postgres container; takes several minutes)
- Lint: `npm run lint`
- Build: `npm run build`

## Code Quality

We believe in writing clean, maintainable code. Always write meaningful commit messages that explain the intent of your changes. Follow best practices for TypeScript development. Handle errors appropriately and never swallow exceptions silently. Write tests for new functionality. Keep functions small and focused on a single responsibility. Use descriptive variable names. Avoid premature optimization. Remember that code is read far more often than it is written, so optimize for readability.

## TypeScript Best Practices

Always prefer `interface` over `type` for object shapes unless you need union types. Use `readonly` where mutation is not intended. Avoid `any`; if the type is genuinely unknown, use `unknown` and narrow it. Enable strict mode in tsconfig (already enabled here). Prefer async/await over raw promises for readability. These are general TypeScript guidelines that any experienced developer should already follow.

## Database Notes

We use PostgreSQL 15 with the `pg` driver. Connection pooling is handled by PgBouncer.

IMPORTANT: The local development database URL must point at the PgBouncer pooled port 6543, NOT the direct Postgres port 5432. Migrations run against 5432 directly, but the application must always use 6543. If the app connects to 5432 in development it will exhaust connections and requests will hang with no error message.

Orders are soft-deleted: every query against the `orders` table must include `deleted_at IS NULL` or you will return cancelled orders to customers.

## The Release Procedure

Follow these steps exactly when releasing a new version:

1. Make sure your local main branch is up to date: `git checkout main && git pull`
2. Run the full test suite: `make test` and confirm everything passes
3. Bump the version in package.json following semver
4. Update CHANGELOG.md with all changes since the last release, grouped by type
5. Commit the version bump with the message `release: vX.Y.Z`
6. Tag the release: `git tag -a vX.Y.Z -m "Release X.Y.Z"`
7. Push the tag: `git push origin vX.Y.Z`
8. The CI pipeline will build the Docker image and push it to the registry
9. Watch the pipeline at ci.acme.internal until the build goes green
10. Run the deploy script: `scripts/deploy_v1.sh staging` and verify on staging
11. Smoke-test staging: create a test order and confirm the webhook fires
12. Promote to production: `scripts/deploy_v1.sh production`
13. Watch error rates in Grafana for 30 minutes after the deploy
14. Announce the release in #eng-releases with the changelog summary
15. If anything goes wrong, roll back with `scripts/deploy_v1.sh production --rollback`

## API Endpoints

The service exposes the following endpoints:

- `POST /orders` — create a new order. Body: `{ items: LineItem[], customerId: string }`. Returns 201 with the order object.
- `GET /orders/:id` — fetch a single order by ID. Returns 404 if not found or soft-deleted.
- `GET /orders?customerId=` — list orders for a customer, paginated with `limit` and `cursor` query params.
- `PATCH /orders/:id` — update order status. Allowed transitions: pending→confirmed, confirmed→shipped, any→cancelled.
- `POST /payments/webhook` — payment provider webhook. Verifies the HMAC signature header before processing.
- `GET /health` — liveness probe used by Kubernetes.

## Working With the Inventory Service

The inventory service is the source of truth for stock levels. Before confirming an order, the order service must reserve stock via `POST /reservations` on the inventory service. Reservations expire after 15 minutes. Note that the inventory service calls the product identifier `sku` while we call it `productId` — they are the same value.

## Git Workflow

Create feature branches from main using the format `yourname/short-description`. Keep pull requests small and focused. Request review from at least one team member. Squash-merge pull requests. Delete branches after merging. Rebase rather than merge when updating your branch with main.

## Sprint Process

We work in two-week sprints. Sprint planning happens on the first Monday of the sprint, where we estimate stories using planning poker. Daily standups are at 9:45am. Retrospectives happen on the last Friday of the sprint. The sprint board lives in Linear. When you pick up a ticket, move it to In Progress and assign yourself. When your PR is up, move the ticket to In Review. Tickets should be linked in PR descriptions using the Linear magic words so they auto-transition.

## Environment Variables

The following environment variables are required: `DATABASE_URL` (the pooled connection string), `INVENTORY_SERVICE_URL`, `PAYMENTS_WEBHOOK_SECRET` (HMAC key for webhook verification), `LOG_LEVEL` (defaults to info). See `.env.example` for the full list with example values.

## Monitoring and Observability

Logs are shipped to Datadog. Use the logger in `src/utils/logger.ts` rather than console.log so logs are structured. Metrics are exposed on `/metrics` in Prometheus format. Traces use OpenTelemetry with the collector configured in `otel.config.ts`. Dashboards live in Grafana under the "Orders" folder. Alerts page the on-call engineer via PagerDuty.

## Remember

Always be careful when making changes to payment-related code. Test thoroughly before deploying. Ask questions in #eng-orders if anything is unclear. Keep this document up to date as the project evolves.
