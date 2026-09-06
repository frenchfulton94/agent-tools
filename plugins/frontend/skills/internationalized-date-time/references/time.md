# `Time` — a clock time, no date

Read this when the value is a **time of day with no date**: an alarm, a store's opening hour, a
recurring "every day at 07:30." To pin it to a specific day, combine with a `CalendarDate` via
`toCalendarDateTime`.

Live doc (source of truth): https://react-aria.adobe.com/internationalized/date/Time.md

## Creating

```ts
import { Time, parseTime } from '@internationalized/date';

new Time(9, 45); // 09:45  (hour, minute, second?, millisecond?)
parseTime('09:45'); // from ISO time string
```

## Manipulation (immutable — reassign)

```ts
let t = new Time(9, 45);
t = t.add({ minutes: 30 }); // balances: 09:59 + 1m → 10:00
t = t.set({ hour: 12 }); // constrains: set({minute: 75}) → 09:59
t = t.cycle('minute', 15, { round: true }); // wraps; round to a multiple, IN THE
// SIGN'S DIRECTION (+ rounds up, - down;
// no "nearest" mode)
t.cycle('hour', 1, { hourCycle: 12 }); // 12-hour cycling preserves AM/PM
t.toString(); // '09:45:00'
```

## Combining with a date

```ts
import { toCalendarDateTime, toZoned, CalendarDate } from '@internationalized/date';

let date = new CalendarDate(2022, 2, 3);
let dt = toCalendarDateTime(date, new Time(8, 30)); // 2022-02-03T08:30:00
toZoned(dt, 'America/Los_Angeles'); // → exact instant
```

## Queries

Only ordering: `a.compare(b)` returns <0 / 0 / >0. (No locale/zone concepts apply to a bare
time.)
