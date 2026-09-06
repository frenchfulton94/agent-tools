# Trigger battery — managing-container-runtimes

Run each query in a clean session with only the description visible. Record fired / did not fire.

## Should trigger

1. "Cannot connect to the Docker daemon at unix:///var/run/docker.sock — is the docker daemon running?"
2. "How do I install Docker on my Mac?"
3. "Is OrbStack worth switching to from Docker Desktop?"
4. "Docker is eating 12 GB of RAM and my fans are on constantly."
5. "docker: permission denied while trying to connect to the Docker daemon socket."
6. "I have Colima and Docker Desktop both installed and things behave differently in different terminals."
7. "Docker is using 80 GB of disk. How do I get that back?"
8. "How do I give the Docker VM more CPUs?"
9. "toomanyrequests: You have reached your pull rate limit."
10. "I ran brew install docker but the docker command still doesn't work."

Item 10 is the specific failure the skill's first section exists for — an agent without it commonly suggests reinstalling the CLI.

## Should not trigger (near misses)

1. "Write me a Dockerfile for this Django app." → `containerizing-apps`
2. "My multi-stage build fails at the COPY --from step." → `containerizing-apps`
3. "How do I add a healthcheck to my compose file?" → `containerizing-apps`
4. "My container can't reach the Postgres service." → `containerizing-apps`
5. "Set up a Kubernetes cluster on AWS." → cloud infrastructure, not local runtime
6. "How do I install Node on my Mac?" → not a container runtime
7. "My VM in VirtualBox won't boot." → a VM, but not a container runtime
8. "Explain the difference between an image and a container." → conceptual
9. "Scan our images for vulnerabilities." → `securing-container-supply-chain`
10. "Set up image signing in CI." → `securing-container-supply-chain`

Items 1–4 are the important negatives: unmistakably Docker, but authoring work rather than runtime work.

## A/B assertions

Run "docker isn't working on my Mac, I get 'Cannot connect to the Docker daemon'" with and without the skill. With the skill, the response should:

- [ ] Run diagnostics before recommending any install
- [ ] Check `docker context ls` as part of that
- [ ] Check which runtimes are already present on the machine
- [ ] Offer the runtime-appropriate start command rather than assuming Docker Desktop
- [ ] Not suggest `brew install docker` as a fix

The last assertion is the one that separates a skilled response from the default. Grade against quoted evidence.
