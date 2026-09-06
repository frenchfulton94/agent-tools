# `ZonedDateTime` — exact instants, time zones, DST

Read this when you're storing or manipulating a value that represents **a real moment at a
real place**: meetings, reminders, deadlines with a location, log timestamps, anything that
should track an actual instant. This is the correct type for most scheduling data.

Live doc (source of truth): https://react-aria.adobe.com/internationalized/date/ZonedDateTime.md

## Creating one

Prefer parsing or `now` over the raw constructor (the constructor takes a UTC-offset in ms,
which is error-prone to write by hand).

```ts
import {
	now,
	getLocalTimeZone,
	parseZonedDateTime,
	parseAbsolute,
	parseAbsoluteToLocal,
	fromDate,
	fromAbsolute
} from '@internationalized/date';

now('America/New_York'); // current instant in a zone
now(getLocalTimeZone()); // current instant in the user's zone

parseZonedDateTime('2022-11-07T00:45[America/Los_Angeles]'); // zone-tagged
parseAbsolute('2021-11-07T07:45:00Z', 'America/Los_Angeles'); // UTC → given zone
parseAbsoluteToLocal('2021-11-07T07:45:00Z'); // UTC → user's zone
fromDate(new Date(), 'America/Los_Angeles'); // from a JS Date
fromAbsolute(1688023843144, 'America/Los_Angeles'); // from epoch ms
```

## Choosing a parse/serialize pair — this is a data decision

| Intent                                           | Parse with                               | Serialize with       | Stored string                          |
| ------------------------------------------------ | ---------------------------------------- | -------------------- | -------------------------------------- |
| Future event tied to a place (meeting, reminder) | `parseZonedDateTime`                     | `toString()`         | `...T09:45-08:00[America/Los_Angeles]` |
| Exact past instant / cross-zone equality         | `parseAbsolute` / `parseAbsoluteToLocal` | `toAbsoluteString()` | `2022-02-03T20:24:45.000Z`             |

**Why keep the zone for future events?** If you pre-convert to UTC and a region later changes
its DST rules, the local wall-clock time you show the user will drift. Storing
`zone + offset + local time` (what `toString()` does) preserves the user's intended local time
regardless of future rule changes. Use UTC (`toAbsoluteString`) only when the exact instant,
independent of any locale, is what matters.

## DST is the deep gotcha

Arithmetic, `set`, and `cycle` are all **time-zone aware**. Around DST transitions the UTC
offset shifts under the hood so the wall-clock result stays sensible:

```ts
// "spring forward": adding an hour skips the 2 AM hour
parseZonedDateTime('2020-03-08T01:00-08:00[America/Los_Angeles]').add({ hours: 1 }); // 2020-03-08T03:00-07:00[America/Los_Angeles]

// "fall back": the 1 AM hour repeats
parseZonedDateTime('2020-11-01T01:00-07:00[America/Los_Angeles]').add({ hours: 1 }); // 2020-11-01T01:00-08:00[America/Los_Angeles]
```

Changing the **date** onto a day where the wall-clock time doesn't exist shifts the hour
(spring-forward skips 2 AM), and `set` across a boundary keeps the wall time while moving the
offset.

### Ambiguity and the `disambiguation` option

When a `set` (or a `CalendarDateTime → ZonedDateTime` conversion) lands on a skipped or repeated
time, resolve it explicitly:

- `'compatible'` (default) — later time for spring-forward, earlier for fall-back. Matches how
  most platforms behave; good default.
- `'earlier'` / `'later'` — force a side.
- `'reject'` — throw. Use when silently guessing wrong is worse than surfacing an error.

```ts
parseZonedDateTime('2020-03-01T02:00-08:00[America/Los_Angeles]').set({ day: 8 }); // 2020-03-08T03:00-07:00 (compatible)
parseZonedDateTime('2020-03-01T02:00-08:00[America/Los_Angeles]').set({ day: 8 }, 'earlier'); // 2020-03-08T01:00-08:00
```

## Manipulation (all return new objects — reassign)

`add` / `subtract` (balance across fields), `set` (constrains out-of-range), `cycle` (wraps one
field; supports `{round: true}` and `{hourCycle: 12}`). Behavior mirrors `CalendarDateTime` plus
the DST awareness above. Confirm exact signatures in the live doc when needed.

## Converting

```ts
import {
	toTimeZone,
	toLocalTimeZone,
	toCalendarDate,
	toTime,
	toCalendarDateTime
} from '@internationalized/date';

toTimeZone(z, 'America/Chicago'); // same instant, different zone
toLocalTimeZone(z); // same instant, user's zone
toCalendarDate(z); // drop time + zone → CalendarDate
toTime(z); // just the clock time → Time
toCalendarDateTime(z); // drop the zone → CalendarDateTime
z.toDate(); // native Date (only when you must, e.g. Intl formatting)
```

## Queries

`compare`; `isSameYear/Month/Day`, `isToday` (calendar-aware, convert second arg);
`isEqualYear/Month/Day` (require same calendar); `startOf/endOf Year/Month/Week` and
`getDayOfWeek/isWeekday/isWeekend/getWeeksInMonth` — **the week/day/weekend ones take a locale**
(and optional `firstDayOfWeek`). Start/end-of functions leave the time fields unchanged.
