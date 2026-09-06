# Bits UI: dates and calendars

Applies to `Calendar`, `RangeCalendar`, `DateField`, `DateRangeField`,
`DatePicker`, `DateRangePicker`, `TimeField`, and `TimeRangeField`.
Distilled from `https://bits-ui.com/docs/dates/llms.txt`.

Bits UI represents dates and times with `@internationalized/date`, not
JavaScript's native `Date`. Install it alongside `bits-ui`:

```bash
bun add @internationalized/date
```

## Why not native `Date`

Native `Date` conflates "a date," "a date and time," and "a moment in a
specific timezone" into one type, and it's notoriously bad at timezone
math. `@internationalized/date` splits these into three explicit,
immutable value types:

| Type               | Represents                   | Example                                       |
| ------------------ | ---------------------------- | --------------------------------------------- |
| `CalendarDate`     | A date, no time or timezone  | `2026-07-10`                                  |
| `CalendarDateTime` | A date and time, no timezone | `2026-07-10T12:30:00`                         |
| `ZonedDateTime`    | A date, time, and timezone   | `2026-07-10T21:00:00-04:00[America/New_York]` |

Which one a component uses is inferred from whatever value or `placeholder`
you give it — pass a `CalendarDate` to `Calendar.Root` and you get a
date-only picker; pass a `CalendarDateTime` and time selection appears too.

```ts
import {
	CalendarDate,
	CalendarDateTime,
	parseDate,
	today,
	getLocalTimeZone
} from '@internationalized/date';

const specific = new CalendarDate(2026, 7, 10); // year, month, day
const fromIso = parseDate('2026-07-10'); // same value
const currentInTz = today(getLocalTimeZone()); // "today" in the user's zone
```

Use `ZonedDateTime` specifically for anything where the exact moment
matters regardless of who's viewing it — a scheduled meeting or livestream
start time — not for things like birthdays or due dates that should stay
the same calendar date everywhere.

## Two mistakes everyone makes once

**Months are 1-indexed.** Unlike native `Date`, January is `1`, not `0`.
`new CalendarDate(2026, 1, 15)` is January 15, 2026.

**Values are immutable.** Every "update" produces a new instance; there's
no setter on the object itself.

```ts
// Wrong — CalendarDate has no mutable `month` setter, this throws or no-ops
placeholder.month = 8;

// Right — reassign the result of set/add/subtract/cycle
placeholder = placeholder.set({ month: 8 });
placeholder = placeholder.add({ months: 1 });
placeholder = placeholder.subtract({ days: 5 });
placeholder = placeholder.cycle('month', 'forward', [1, 3, 5, 7, 9, 11]);
```

## The `placeholder` prop

Every date/time component has a bindable `placeholder` that does three
jobs at once: the value shown before anything is selected, the type
signal for whether time/timezone fields should appear (inferred from
whether you hand it a `CalendarDate`, `CalendarDateTime`, or
`ZonedDateTime`), and the calendar's currently-visible month/year for
components with a grid view. Drive calendar navigation by reassigning it:

```svelte
<script lang="ts">
	import { Calendar } from 'bits-ui';
	import { today, getLocalTimeZone, type DateValue } from '@internationalized/date';

	let placeholder: DateValue = $state(today(getLocalTimeZone()));
</script>

<button onclick={() => (placeholder = placeholder.add({ months: 1 }))}> Next month </button>
<Calendar.Root bind:placeholder>
	<!-- ... -->
</Calendar.Root>
```

Match the `placeholder` type to what you actually need — if the field
should let someone pick a time, initialize it with a `CalendarDateTime` (or
`ZonedDateTime`), not a `CalendarDate`; the component can't add a
time-selection UI it wasn't told to expect.

## Ranges

`DateRangeField`, `DateRangePicker`, and `RangeCalendar` take a
`DateRange`:

```ts
type DateRange = { start: DateValue; end: DateValue };
```

Both `start` and `end` should be the same `DateValue` subtype as each
other (both `CalendarDate`, or both `ZonedDateTime`, etc.).

## Formatting and parsing

Use `DateFormatter` for locale-aware display — it wraps `Intl.DateTimeFormat`
while smoothing over browser inconsistencies. Create one instance and reuse
it rather than constructing a new formatter per render:

```ts
import { DateFormatter } from '@internationalized/date';

const formatter = new DateFormatter('en-US', { dateStyle: 'full' });
formatter.format(myDateValue.toDate(getLocalTimeZone()));
// "Friday, July 10, 2026"
```

Parsing from strings (API responses, form values, database rows) — pick
the function matching the shape of the string, don't hand-parse with
`new Date(str)`:

```ts
import {
	parseDate, // "2026-07-10" -> CalendarDate
	parseDateTime, // "2026-07-10T12:30:00" -> CalendarDateTime
	parseZonedDateTime, // "2026-07-10T12:30[America/New_York]" -> ZonedDateTime
	parseAbsolute, // UTC ISO string + IANA zone name -> ZonedDateTime
	parseAbsoluteToLocal // UTC ISO string -> ZonedDateTime in the user's local zone
} from '@internationalized/date';
```

## Quick checklist

- Reach for `CalendarDate` unless you specifically need time-of-day or a
  timezone-anchored moment.
- Never mutate a `DateValue` in place — always reassign the result of
  `set`/`add`/`subtract`/`cycle`.
- Months are 1-indexed everywhere in this package.
- Create `DateFormatter` instances once, outside render-triggered code.
- For a range component, keep `start`/`end` the same `DateValue` subtype.
