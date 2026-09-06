# Trigger Battery

Run each query in a clean context with only the skill's `name` and `description`
loaded. Record fire / no-fire. Target: all of group A fires, none of group B.

The negatives matter more than the positives. Group B is built from adjacent
container work that this skill should stay out of — a description that fires on
"write me a production Dockerfile" is over-broad and will inject 200 lines of dev
container guidance into unrelated Docker tasks.

## A. Should fire

1. "Set up a dev container for this repo."
2. "Add a .devcontainer folder with Node 22 and Postgres."
3. "My devcontainer.json isn't installing the extensions I listed."
4. "The container builds but exits immediately when I reopen in container."
5. "How do I add the AWS CLI to my dev container?"
6. "Why are files created in my container owned by root on my Mac?"
7. "Reopen in Container just hangs at postCreateCommand forever."
8. "New hires lose two days getting their environment working — can we fix that?"
9. "I want everyone on the team pinned to the same Go and Node versions."
10. "Make this repo work in GitHub Codespaces."
11. "Port 3000 is running in the container but I can't hit it from my browser."
12. "Can you review our .devcontainer config before we roll it out?"

Items 8 and 9 are the symptom triggers — the user never says "container." If those
fail to fire, the "Also use when" clause needs the phrasing they actually used.

## B. Should not fire

1. "Write a production Dockerfile for this Node app." — deployment image, not an
   inner-loop environment.
2. "Optimize my Docker image size with multi-stage builds." — production concern.
3. "Explain the difference between Docker volumes and bind mounts." — general Docker
   knowledge.
4. "Write a docker-compose.yml to run my app and Redis in production." — Compose, but
   no dev container involved.
5. "Deploy this container to ECS." — orchestration.
6. "My GitHub Actions workflow is failing on the build step." — CI generally.
7. "Set up a Python virtualenv for this project." — local env, no container.
8. "What's the difference between a container and a VM?" — conceptual.
9. "Configure ESLint for this repo." — tooling config, no container.
10. "Kubernetes pod keeps crash-looping." — orchestration.

Item 4 is the sharpest near-miss: it shares vocabulary (`docker-compose.yml`,
services, Postgres) with the Compose section of this skill but has no dev container
in it. If it fires, the description leans too hard on Compose vocabulary.

## Description-only comprehension check

Read the description alone and answer:

- Would you know when to reach for this? (Should be yes.)
- Would you believe you already know the workflow without opening the body?
  (Should be **no** — if the description reads as a procedure, the agent will follow
  the summary and skip the lifecycle table and the verify step, which is where the
  actual value is.)
