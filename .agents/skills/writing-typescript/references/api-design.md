# Designing Function and Type Signatures

From `declaration-files/Do's and Don'ts.md`. Load when writing a public API, a `.d.ts`, or any
signature that callers outside the file will depend on.

Contents:

- [Overload resolution](#overload-resolution)
- [Callback signatures](#callback-signatures)
- [Type choices](#type-choices)

## Overload resolution

TypeScript resolves a call against the **first matching overload**, which makes ordering
semantic rather than cosmetic.

```ts
// Wrong — general first, so the specific signatures are unreachable
declare function fn(x: unknown): unknown;
declare function fn(x: HTMLElement): number;
declare function fn(x: HTMLDivElement): string;

declare const el: HTMLDivElement;
const a = fn(el); // unknown

// Right — specific first
declare function fn(x: HTMLDivElement): string;
declare function fn(x: HTMLElement): number;
declare function fn(x: unknown): unknown;

const b = fn(el); // string
```

### Collapse overloads that differ only in trailing parameters

```ts
// Wrong
interface Example {
	diff(one: string): number;
	diff(one: string, two: string): number;
	diff(one: string, two: string, three: boolean): number;
}

// Right — only valid because every return type is identical
interface Example {
	diff(one: string, two?: string, three?: boolean): number;
}
```

Two concrete failures the overload form causes. First, signature compatibility checks pass if
_any_ target signature accepts the arguments, and extra arguments are permitted — so passing
`x.diff` where `(a: string, b: number, c: number) => void` is expected is wrongly accepted
under overloads and correctly rejected under optionals. Second, under `strictNullChecks`,
`x.diff("s", cond ? undefined : "hour")` is wrongly an error under overloads, because
`undefined` isn't assignable to the `string` parameter of the two-argument signature.

### Collapse overloads that differ by type in one position

```ts
// Wrong
interface Moment {
	utcOffset(): number;
	utcOffset(b: number): Moment;
	utcOffset(b: string): Moment;
}

// Right
interface Moment {
	utcOffset(): number;
	utcOffset(b: number | string): Moment;
}
```

`b` stays required here because the return types differ across signatures. The failure this
prevents is pass-through: a caller holding a `number | string` cannot satisfy either separate
overload, but satisfies the union fine.

## Callback signatures

### Ignored return values are `void`, not `any`

```ts
function fn(x: () => void) {
	const k = x();
	k.doSomething(); // error — correct. Would compile if the return type were `any`.
}
```

### Callback parameters are not optional

```ts
// Wrong — this says the callback may be invoked with 1 or 2 arguments
interface Fetcher {
	getObject(done: (data: unknown, elapsedTime?: number) => void): void;
}

// Right — callers may always ignore trailing parameters
interface Fetcher {
	getObject(done: (data: unknown, elapsedTime: number) => void): void;
}
```

Marking the parameter optional expresses something about the _caller's_ invocation, not about
whether the callback author cares. It is always legal to supply a function that accepts fewer
arguments.

### Don't overload on callback arity

```ts
// Wrong
declare function beforeAll(action: () => void, timeout?: number): void;
declare function beforeAll(action: (done: DoneFn) => void, timeout?: number): void;

// Right — single signature at maximum arity
declare function beforeAll(action: (done: DoneFn) => void, timeout?: number): void;
```

Listing the shorter callback first lets incorrectly-typed functions match the first overload.

## Type choices

- Never use `Number`, `String`, `Boolean`, `Symbol`, or `Object`. These are boxed object
  types, almost never what is meant. Use `number`, `string`, `boolean`, `symbol`, and — for
  "any non-primitive" — the lowercase `object`.
- Never write a generic type that doesn't use its type parameter. It doesn't constrain
  anything, and inference silently ignores it.
- Use `any` only while migrating a JavaScript codebase, where it marks not-yet-typed regions.
  The docs describe it as equivalent to wrapping every usage in `@ts-ignore`. For values you
  accept but don't interact with, `unknown` gives the same freedom without disabling checks
  downstream.
