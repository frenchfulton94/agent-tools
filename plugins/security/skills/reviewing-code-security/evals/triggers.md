# Trigger battery

Rates below are from the run recorded in `results/2026-07-30-claude-opus-5.json`: 20 probes, 3
trials each, `claude-opus-5`, against a 14-description lineup. Every probe was unanimous, so the
escalation to five trials never triggered.

**Two things have since changed underneath these numbers, and either alone would invalidate them.**
They were measured under **prompt version 1**, which no longer exists. And that 14-description
lineup is no longer what `manifest.json` holds — it is 13 now, after a decoy naming a retired
plugin's skill was dropped on 2026-09-05. Nothing gathered under the current prompt and lineup may
be compared with them; re-running means re-dispatching all 20 probes and replacing every rate
below. See `README.md` for the method, the prompt versions, the lineup change, and for what these
numbers are not.

## Should fire

1. "Can you do a security review of this branch before I merge?"
   Measured: fires 3/3.
2. "Is this query vulnerable to SQL injection?"
   Measured: fires 3/3.
3. "Audit this repo for security problems."
   Measured: fires 3/3.
4. "I'm storing passwords with MD5, is that a problem?"
   Measured: fires 3/3.
5. "Check whether this file upload handler is safe."
   Measured: fires 3/3.
6. "What does OWASP say about JWT expiry?"
   Measured: fires 3/3.
7. "Someone reported they can see other users' orders by changing the ID."
   Measured: fires 3/3.
8. "Is it safe to render this user-supplied HTML?"
   Measured: fires 3/3.
9. "Review the auth changes in this PR."
   Measured: fires 3/3.
10. "We're about to expose this endpoint publicly — anything I should worry about?"
    Measured: fires 3/3.

## Should not fire (near misses)

1. "Review this PR." — general code review, no security framing.
   Measured: fires 0/3. All three trials chose the synthetic `code-review` decoy.

   *Supersedes the earlier reading of 3/5 (~60%), which is withdrawn rather than reconciled.* That
   measurement was taken against an unrecorded lineup in which no general code-review skill
   competed, so the model had nowhere correct to go. The follow-ups document accepted the ~60% as
   residual model judgement and ruled the description should not be tightened. The ruling stands;
   the reasoning does not. It was a property of the lineup, not of the description. Do not average
   the two numbers — they measured different things.
2. "Why is my auth broken? Users can't log in." — a bug, not a vulnerability
   Measured: fires 0/3. No trial reached for a listed skill: one named
   `superpowers:systematic-debugging`, outside the lineup, and two said they would load a skill
   while naming none, each explaining in `reason` that they wanted a debugging skill not on offer.
   This is the probe that proved the trial context is not a vacuum — see README, "Environment".
3. "Write a login form." — feature work
   Measured: fires 0/3. All three declined to load anything.
4. "My tests are failing on the session module." — debugging
   Measured: fires 0/3. All three chose `vitest-testing` — the intended destination.
5. "Explain how JWTs work." — a concept question with no code under review
   Measured: fires 0/3. All three declined to load anything.
6. "Set up HTTPS in my dev environment." — configuration, not review
   Measured: fires 0/3. All three declined to load anything.
7. "Rename this function everywhere." — refactoring
   Measured: fires 0/3. All three declined to load anything.
8. "Is this SQL query slow?" — performance
   Measured: fires 0/3. All three declined to load anything.
9. "Add a rate limiter to this endpoint." — implementation request
   Measured: fires 0/3. All three declined to load anything.
10. "What's our password policy?" — a policy question, not a code question
    Measured: fires 0/3. All three declined to load anything.

Case 5 and case 6 are the load-bearing negatives: both are security *topics* with nothing to
review. Firing on them means the description is matching the domain rather than the task. Both held
at 0/3.

## What this run decided

**No description change.** The rule is that a should-fire miss below 3/5 forces one and a
should-not-fire probe that fires is recorded and judged. There were no misses and no false fires,
so there is nothing to force and nothing to weigh. The `description` in `SKILL.md` is unchanged and
now has evidence behind it rather than an argument.

**The one recorded defect was an artifact.** Probe 1 above is the only failure the battery had ever
recorded, and it does not reproduce against a lineup that includes a plausible alternative. That is
the single clearest result here, and it is a caution about the method as much as a win: a probe
shown too few competitors will fire on the nearest match, and the number that comes back describes
the lineup rather than the description.

**Unanimity is not confidence.** Twenty probes at 3/3 or 0/3 means the model's routing on these
queries is stable, not that the description is correct for queries nobody wrote down. The battery
tests the 20 sentences in this file.
