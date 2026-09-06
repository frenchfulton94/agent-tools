# `CalendarDateTime` — date + time, no time zone

Read this when the value is a wall-clock date+time that is **the same everywhere regardless of
zone** — e.g. "New Year's Eve fireworks at midnight" happens at 00:00 local in every zone. This
is rarer than it seems: if the value marks a real instant at a real place, use `ZonedDateTime`.

Live doc (source of truth): https://react-aria.adobe.com/internationalized/date/CalendarDateTime.md

## Creating

```ts
import { CalendarDateTime, parseDateTime } from '@internationalized/date';

new CalendarDateTime(2022, 2, 3, 9, 15); // Feb 3 2022, 09:15
parseDateTime('2022-02-03T09:15'); // from ISO (no zone)
```

## Manipulation (immutable — reassign)

Same model as `CalendarDate` plus time fields:

```ts
let d = new CalendarDateTime(2022, 2, 3, 9, 45);
d = d.add({ hours: 1 }); // balances (09:45 → 10:45)
d = d.set({ hour: 18 }); // constrains (set({hour: 30}) → 23:45)
d = d.cycle('minute', 15, { round: true }); // wraps one field; rounds to a multiple in
// the sign's direction (+ up, - down)
d.cycle('hour', 1, { hourCycle: 12 }); // 12-hour cycling preserves AM/PM
```

## Converting

```ts
import { toCalendarDate, toTime, toZoned } from '@internationalized/date';

toCalendarDate(d); // drop the time
toTime(d); // just the time → Time
toZoned(d, 'America/Los_Angeles'); // attach a zone → ZonedDateTime
d.toString(); // '2022-02-03T09:45:00'
```

### Converting to a zone can be ambiguous (DST)

`toZoned` and `toDate` may hit a skipped/repeated wall-clock time. Pass a `disambiguation`
option — `'compatible'` (default), `'earlier'`, `'later'`, or `'reject'`:

```ts
// spring-forward: 2 AM doesn't exist that day
new CalendarDateTime(2020, 3, 8, 2).toZoned?.('America/Los_Angeles'); // see toZoned()
toZoned(new CalendarDateTime(2020, 3, 8, 2), 'America/Los_Angeles', 'earlier');
// → 01:00-08:00
```

(Confirm the exact `toZoned` signature/argument order in the live doc if unsure.)

## Queries

Identical surface to `CalendarDate` (comparison, same/equal helpers, start/end-of, and the
**locale-taking** week/weekend/day-of-week functions). Start/end-of functions only touch the
date part and leave the time unchanged.
