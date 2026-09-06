# Trigger battery — containerizing-apps

Run each query in a clean session with only the description visible. Record fired / did not fire.

## Should trigger

1. "Can you containerize this Flask app?"
2. "Write me a Dockerfile for a Go service."
3. "My Docker image is 1.8 GB, how do I get it down?"
4. "Add Redis and Postgres to my compose file."
5. "The build reinstalls all my npm packages every single time and it takes four minutes."
6. "My API container starts before Postgres is ready and crashes."
7. "It works on my machine but the container 404s on every route."
8. "Why can't my app connect to the database? The env var says localhost:5432."
9. "Should I be worried that my Dockerfile has an ARG for the npm token?"
10. "I restarted the stack and all my database rows are gone."

Note that 5–10 never say "Docker" or name a file — they describe a symptom. Those are the ones a weak description misses.

## Should not trigger (near misses)

1. "Docker isn't running — I get 'Cannot connect to the Docker daemon'." → `managing-container-runtimes`
2. "Should I use OrbStack or Docker Desktop?" → `managing-container-runtimes`
3. "My Mac is out of disk space, Docker is using 60 GB." → `managing-container-runtimes`
4. "Write me a Kubernetes deployment manifest for this image." → out of scope; k8s authoring is not this skill
5. "Explain what a container is versus a VM." → conceptual question, no authoring work
6. "Set up a GitHub Actions workflow to run my tests." → CI authoring, not containerization
7. "How do I install Postgres on my laptop?" → no container involved
8. "Review this Terraform module for my ECS service." → infrastructure, not image authoring
9. "Scan this image for CVEs." → `securing-container-supply-chain`
10. "Generate an SBOM for our container." → `securing-container-supply-chain`
11. "How do I sign our images?" → `securing-container-supply-chain`

Items 1–3 are the important negatives: they are unmistakably Docker, and routing them here instead of to the runtime skill is the most likely failure mode for this pair.

## A/B assertions

Run "containerize this Express app" with and without the skill. With the skill, the output should show all of:

- [ ] Multi-stage build with a distinct runtime stage
- [ ] `COPY package*.json` before `COPY . .`
- [ ] A pinned base tag, not `latest`
- [ ] `USER` set to non-root before `CMD`
- [ ] `CMD` in exec (JSON array) form
- [ ] A `.dockerignore` created, including `.env` and `node_modules`
- [ ] No `version:` key if a compose file is produced
- [ ] `docker compose`, never `docker-compose`

Hardening lives in `references/hardening.md`, so a plain "containerize this" run is not expected to emit `cap_drop` or `read_only`. Test those with "harden this container for production" instead, and assert that the reference is opened.

Grade against quoted evidence from the output. A file that "implies" a step does not count.
