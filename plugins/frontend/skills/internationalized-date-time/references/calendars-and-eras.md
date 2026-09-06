# Calendars, eras, and conversion

Read this when working with **non-Gregorian calendars** (Hebrew, Islamic, Buddhist, Japanese,
Persian, Indian, Ethiopic, etc.), converting dates between calendar systems, handling **eras**,
or when **bundle size** matters.

Live doc (source of truth): https://react-aria.adobe.com/internationalized/date/Calendar.md

## Using a non-Gregorian calendar

Every date type defaults to Gregorian. Pass a `Calendar` instance as the first constructor
argument to use another system:

```ts
import {
	CalendarDate,
	BuddhistCalendar,
	HebrewCalendar,
	toCalendar,
	GregorianCalendar
} from '@internationalized/date';

new CalendarDate(new BuddhistCalendar(), 2563, 4, 30); // Buddhist calendar date

// Convert between systems (second arg is converted into the first's system elsewhere):
let greg = new CalendarDate(2020, 9, 19);
let hebrew = toCalendar(greg, new HebrewCalendar()); // 5781-01-01 (Hebrew)
toCalendar(hebrew, new GregorianCalendar()); // back to Gregorian
```

Supported identifiers (for `createCalendar`) include: `gregory`, `buddhist`, `ethiopic`,
`ethioaa`, `coptic`, `hebrew`, `indian`, `islamic-civil`, `islamic-tbla`, `islamic-umalqura`,
`japanese`, `persian`, `roc`. See the live doc's table for the meaning of each.

## Eras

Calendars with multiple eras (e.g. Japanese, one era per emperor) take an era identifier before
the year; years count from 1 within the era:

```ts
import { CalendarDate, JapaneseCalendar } from '@internationalized/date';
new CalendarDate(new JapaneseCalendar(), 'heisei', 31, 4, 30); // = 2019-04-30 Gregorian
```

Get valid era ids from a calendar instance's `getEras()`. If omitted, the current era is
assumed. Gregorian uses `BC`/`AD`; several calendars have a single era.

## Getting a calendar from a locale

```ts
import { createCalendar } from '@internationalized/date';

let id = new Intl.DateTimeFormat('th-TH').resolvedOptions().calendar; // 'buddhist'
createCalendar(id); // → BuddhistCalendar
```

## Bundle-size trap with `createCalendar`

Importing `createCalendar` pulls **every** calendar implementation into your bundle. If size
matters and you only need a couple, write your own resolver so the bundler can tree-shake the
rest:

```ts
import { GregorianCalendar, JapaneseCalendar } from '@internationalized/date';

function createCalendar(id) {
	switch (id) {
		case 'gregory':
			return new GregorianCalendar();
		case 'japanese':
			return new JapaneseCalendar();
		default:
			throw new Error(`Unsupported calendar ${id}`);
	}
}
```

## Custom calendars

You can implement the `Calendar` interface for custom business calendars (e.g. a 4-5-4 fiscal
calendar) by extending an existing calendar and overriding `toJulianDay`/`fromJulianDay` plus
`getDaysInMonth`/`getMonthsInYear`. See the live doc for a worked example — fetch it if the user
needs this.
