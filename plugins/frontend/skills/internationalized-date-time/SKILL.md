---
name: internationalized-date-time
description: >
  Work with dates, times, time zones, and calendars using the @internationalized/date
  package (the framework-agnostic library behind React Aria / React Spectrum, also used
  standalone in Svelte, Vue, and vanilla JS). Use this whenever building UI components
  that handle dates or times — date pickers, calendars, date/time fields, booking and
  scheduling flows, reminders, availability, deadlines — or whenever code deals with
  time zones, daylight saving time, locale-aware week/weekend/first-day-of-week logic,
  non-Gregorian calendars (Hebrew, Islamic, Buddhist, Japanese, Persian, etc.), or
  parsing/formatting ISO 8601 date strings. Reach for this even when the user just says
  "let users pick a date," "store an appointment time," "add a duration to a date,"
  "compare two dates," or "increment/cycle a field in a date or time spinner" without
  naming the library — plain JS Date is almost always the wrong tool for these and this
  skill explains why and what to use instead.
license: Apache-2.0
metadata:
  library: '@internationalized/date'
  version: '1.x'
---

# Internationalized date & time (`@internationalized/date`)

This skill covers `@internationalized/date`, an immutable, locale-aware date/time
library. It is framework-agnostic — the same objects work in Svelte, Vue, vanilla JS,
and (via React Aria/Spectrum) React. Prefer it over the native JavaScript `Date`
whenever correctness across time zones, calendars, or locales matters.

**Why not `Date`?** `Date` has no concept of "a date without a time," conflates wall-clock
time with exact instants, silently uses the host time zone, mutates in place, and has no
locale-aware week/weekend logic. Most date bugs in UI code come from reaching for `Date`
when one of the four types below is what's actually needed.

## Keeping this skill current

The library's exact method signatures and the full function list can change between
versions. This skill teaches the **durable model** — which type to pick, and the traps to
avoid. Before writing code that depends on a specific signature, argument order, or a
function you're not certain exists, **`web_fetch` the relevant doc below and confirm
against it.** These `.md` URLs are the canonical, machine-readable docs and are the source
of truth over anything memorized here:

| Topic                                     | Doc URL                                                                 |
| ----------------------------------------- | ----------------------------------------------------------------------- |
| Overview, package structure, install      | https://react-aria.adobe.com/internationalized/date/index.md            |
| `CalendarDate` (date, no time)            | https://react-aria.adobe.com/internationalized/date/CalendarDate.md     |
| `CalendarDateTime` (date+time, no zone)   | https://react-aria.adobe.com/internationalized/date/CalendarDateTime.md |
| `ZonedDateTime` (exact instant in a zone) | https://react-aria.adobe.com/internationalized/date/ZonedDateTime.md    |
| `Time` (clock time, no date)              | https://react-aria.adobe.com/internationalized/date/Time.md             |
| `Calendar` (systems, eras, conversion)    | https://react-aria.adobe.com/internationalized/date/Calendar.md         |

Fetch the doc when: you need the precise parameters of a function; you're unsure whether a
helper exists; the user is on a specific version; or a compile/type error suggests the API
differs from what's written here. When you fetch and find a discrepancy, trust the doc.

> Note: those pages are hosted under the React Aria docs and their "Related Types" tables
> may show React `Calendar` **component** props. Ignore that component — it's React-only and
> not part of the core package. Everything else (the object types and the standalone
> functions like `parseDate`, `toZoned`, `startOfWeek`) is framework-agnostic and applies
> to Svelte.

## Install

```bash
npm install @internationalized/date
```

The whole library is ~8 kB Brotli; it's tree-shakeable, so import only what you use. See
`references/calendars-and-eras.md` for the bundle-size trap with `createCalendar`.

## The one decision that matters: which type?

Picking the right type is 80% of using this library correctly. Choose by asking **"what does
this value really represent?"** — not by what's convenient.

| You're representing…                                   | Use                | Example                                          |
| ------------------------------------------------------ | ------------------ | ------------------------------------------------ |
| A date with **no time**                                | `CalendarDate`     | Birthday, all-day event, invoice due date        |
| A **clock time** with no date                          | `Time`             | Store opening time, alarm "07:30"                |
| A date+time that is the **same wall-clock everywhere** | `CalendarDateTime` | "Midnight on NYE" — fires at 00:00 in every zone |
| An **exact moment on Earth**                           | `ZonedDateTime`    | A meeting, a reminder, a past log entry          |

Rules of thumb that prevent real bugs:

- If you'd be wrong to shift the value when the user changes time zone, it's a `CalendarDate`
  or `CalendarDateTime` (a birthday doesn't move). If it _should_ track a real instant, it's a
  `ZonedDateTime`.
- **Most scheduling values are `ZonedDateTime`.** A calendar event happens at a real instant
  in a real place. Store the zone with it (see serialization below) so it survives DST-rule
  changes.
- Reach for `CalendarDateTime` only for genuinely zone-independent wall-clock times, which are
  rarer than they seem.

Detailed per-type API and examples live in `references/`:

- `references/calendar-date.md` — dates without time
- `references/calendar-date-time.md` — dates+time without a zone
- `references/zoned-date-time.md` — exact instants, time zones, DST, parsing/serialization
- `references/time.md` — clock times
- `references/calendars-and-eras.md` — non-Gregorian calendars, eras, conversion, bundle size

Read the reference for a type when you're about to write non-trivial logic with it —
they carry the method details and the per-type gotchas.

## Gotchas that bite everyone

These are the mistakes the model (and most developers) make without being warned. They are
the highest-value part of this skill.

### 1. Everything is immutable — reassign, don't mutate

`add`, `subtract`, `set`, and `cycle` **return new objects**. The original is untouched.

```ts
let d = new CalendarDate(2022, 2, 3);
d.add({ days: 1 }); // ❌ result thrown away; d is still Feb 3
d = d.add({ days: 1 }); // ✅ d is now Feb 4
```

In **Svelte 5**, this pairs naturally with runes — reassign the `$state` variable instead of
mutating, and reactivity just works:

```svelte
<script lang="ts">
	import { today, getLocalTimeZone } from '@internationalized/date';
	let date = $state(today(getLocalTimeZone()));
	function nextDay() {
		date = date.add({ days: 1 });
	} // reassign → reactive
</script>
```

### 2. `set` constrains, `cycle` wraps, `add`/`subtract` balance

Same-looking operations, different overflow behavior. Pick intentionally:

- **`set`** — out-of-range values are _constrained_ to the valid range. `set({day: 100})` on a
  February date → Feb 28, not March. Setting `month: 5` then would keep the constrained day.
- **`cycle`** — increments/decrements **one field** and _wraps_ it without touching neighbors.
  `cycle('month', 1)` on Dec → Jan of the **same** year (not next year). This is what date-field
  spinner UIs want. With `{round: true}`, the value rounds to a multiple of the amount **in the
  direction of the sign** — a positive amount rounds _up_ to the next multiple, a negative amount
  rounds _down_. There is no single "nearest" mode, so pick the direction the UI needs (e.g.
  `cycle('minute', 5, {round: true})` on :22 → :25; use `-5` to get :20).
- **`add`/`subtract`** — _balance_ across fields. Adding a day to Aug 31 → Sep 1. Use these for
  real date math ("due in 30 days").

If adding to one field makes another invalid, the date is _constrained_ (add 1 month to Aug 31
→ Sep 30, since Sep 31 doesn't exist).

### 3. Locale-dependent queries REQUIRE a locale — don't hardcode

`startOfWeek`, `endOfWeek`, `getDayOfWeek`, `isWeekday`, `isWeekend`, and `getWeeksInMonth`
take a locale string, because the answer changes by locale: the US week starts Sunday, France
Monday; the weekend is Sat/Sun in the US but Fri/Sat in Israel (`he-IL`). Pass the user's real
locale; don't hardcode `'en-US'`. An optional `firstDayOfWeek` (e.g. `'mon'`) overrides the
locale default when your product needs a fixed start day.

```ts
startOfWeek(date, 'en-US'); // Sunday-based
startOfWeek(date, 'fr-FR'); // Monday-based
```

### 4. DST makes some conversions ambiguous — resolve it deliberately

When converting a `CalendarDateTime` to a zone (`toZoned`, `toDate`) or `set`-ing fields on a
`ZonedDateTime` across a DST boundary, a wall-clock time can be skipped ("spring forward") or
occur twice ("fall back"). These accept a `disambiguation` option:
`'compatible'` (default), `'earlier'`, `'later'`, or `'reject'` (throws). Default to
`'compatible'` unless the product has a reason to pick a side; use `'reject'` if a wrong guess
would be worse than an error. Details and examples: `references/zoned-date-time.md`.

### 5. Serialize by intent — the string format encodes a decision

How you turn a `ZonedDateTime` into a string is a data-integrity choice, not cosmetic:

- **Future events tied to a place** (meetings, reminders, calendar entries) → keep the zone:
  `toString()` produces `2022-02-03T09:45-08:00[America/Los_Angeles]`; parse back with
  `parseZonedDateTime`. Storing the zone (not pre-converted UTC) keeps the local time correct
  even if that region later changes its DST rules.
- **Exact past instants / cross-zone equality** → use UTC: `toAbsoluteString()` →
  `...Z`; parse with `parseAbsolute(str, zone)` or `parseAbsoluteToLocal(str)`.

Full parsing/serialization guidance is in `references/zoned-date-time.md`.

### 6. `getLocalTimeZone()` is cached

First call caches the host zone. In tests, control it with `setLocalTimeZone` /
`resetLocalTimeZone` instead of expecting it to re-read the environment.

### 7. `today` / `now` need a time zone

`today(timeZone)` and `now(timeZone)` require an explicit zone so "today" is unambiguous. Use
`getLocalTimeZone()` for the user's own, or a fixed IANA id (`'America/New_York'`) when the
domain fixes it (e.g. a US-market trading calendar).

### 8. Non-Gregorian calendars & the `createCalendar` bundle trap

Pass a `Calendar` instance to any constructor for Hebrew, Islamic, Buddhist, Japanese, Persian,
etc.; convert with `toCalendar`. Importing `createCalendar` pulls **every** calendar into the
bundle — if size matters and you only need a few, write your own small `switch`. See
`references/calendars-and-eras.md`.

## Suggested workflow

1. **Classify the value** using the type table. State which type and why before coding — this
   is where most bugs are prevented.
2. **Read the matching `references/*.md`** for the methods you'll use.
3. **When unsure of an exact signature or whether a helper exists, `web_fetch` the doc URL**
   for that type and confirm.
4. **Write the code**, honoring immutability (reassign results) and passing locale/zone
   explicitly where required.
5. **Sanity-check the traps**: Did you keep the return value? Is the overflow behavior
   (`set` vs `cycle` vs `add`) the one you want? Did you pass a locale to week/weekend queries?
   Did you handle DST disambiguation on zone conversions? Is the serialization format right for
   the intent?
