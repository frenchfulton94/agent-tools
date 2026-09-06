# `CalendarDate` — a date with no time

Read this when the value is a **date only** and time-of-day is meaningless: birthdays,
all-day events, due dates, date-range pickers. If time or zone matters, use
`CalendarDateTime` or `ZonedDateTime` instead.

Live doc (source of truth): https://react-aria.adobe.com/internationalized/date/CalendarDate.md

## Creating

```ts
import { CalendarDate, parseDate, today, getLocalTimeZone } from '@internationalized/date';

new CalendarDate(2022, 2, 3); // Feb 3, 2022 (Gregorian by default)
parseDate('2022-02-03'); // from ISO string
today(getLocalTimeZone()); // user's today
today('America/New_York'); // today in a fixed zone
```

`today` needs a zone because the calendar date differs across zones at any given instant.

## Manipulation (immutable — always reassign the result)

```ts
let d = new CalendarDate(2022, 2, 3);
d = d.add({ weeks: 1 }); // 2022-02-10  (balances across fields)
d = d.subtract({ months: 1 }); // back a month
d = d.set({ day: 10 }); // set a field; out-of-range is CONSTRAINED
d.set({ day: 100 }); // → 2022-02-28 (last valid day), not March
d = d.cycle('month', 1); // WRAPS within year: Dec → Jan, same year
d.cycle('year', 5, { round: true }); // rounds to a multiple of 5 in the sign's direction
// (+ rounds up, - rounds down; no "nearest" mode)
```

`parseDuration('P3Y6M6W4D')` → a duration object you can pass to `add`/`subtract`.

## Converting up to a time or zone

```ts
import { toCalendarDateTime, toZoned, Time } from '@internationalized/date';

toCalendarDateTime(d); // midnight, no zone
toCalendarDateTime(d, new Time(8, 30)); // attach a specific time
toZoned(d, 'America/Los_Angeles'); // midnight in a zone → ZonedDateTime
d.toDate('America/Los_Angeles'); // native Date (zone required)
d.toString(); // '2022-02-03'
```

## Calendar systems

Pass a `Calendar` instance for non-Gregorian systems; convert with `toCalendar`. See
`calendars-and-eras.md`.

## Queries

- Ordering: `a.compare(b)` (<0, 0, >0).
- Cross-calendar partial equality: `isSameYear/Month/Day`, `isToday` (converts the second date
  into the first's calendar).
- Same-calendar equality: `isEqualYear/Month/Day` (no conversion; calendars must match).
- Boundaries: `startOfYear/Month/Week`, `endOfYear/Month/Week`.
- **Locale-dependent (pass a locale, optional `firstDayOfWeek`):** `startOfWeek`, `endOfWeek`,
  `getDayOfWeek`, `isWeekday`, `isWeekend`, `getWeeksInMonth`.

```ts
startOfWeek(d, 'en-US'); // Sunday-based
startOfWeek(d, 'fr-FR', 'mon'); // Monday-based / explicit override
isWeekend(d, 'he-IL'); // Fri/Sat weekend
```
