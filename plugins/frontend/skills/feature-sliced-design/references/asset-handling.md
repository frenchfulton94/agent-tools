# Asset Handling

How to place static assets (images, icons, fonts, PDFs, stylesheets) inside an
FSD project. Assets follow the same placement rules as code: group by use
case, not by type, and keep them next to the code that uses them.

> **Caution:** A custom top-level `assets` segment that aggregates all static
> files is **not recommended**. It violates the FSD principles of high
> cohesion and locality of changes. Place assets where they are used.

## Contents

1. [Decision Tree](#decision-tree)
2. [Slice-specific Assets](#slice-specific-assets)
3. [Shared Assets](#shared-assets)
4. [Global Assets](#global-assets)
5. [Static Folder](#static-folder)
6. [Summary Table](#summary-table)
7. [Anti-patterns](#anti-patterns)

---

## Decision Tree

1. **Used by exactly one slice?** Keep the asset inside that slice, usually
   in the `ui/` segment, or in `model/` if it is part of business logic.
2. **Reused across the app (icons, placeholder images)?** Move to
   `shared/ui/`.
3. **Global stylesheet, font, or app-level resource?** Place in the `app/`
   layer (`app/styles/`, `app/fonts/`).
4. **Served as-is (favicon, robots.txt)?** Use SvelteKit's `static/`
   folder at the project root. `static/` is not part of FSD and does not
   conflict with FSD layers.

---

## Slice-specific Assets

When an asset belongs to one page, widget, or feature, keep it inside that
slice. The asset lives next to the component that renders it:

```text
pages/
  home/
    ui/
      hero-image.jpg          ← Used only by HomePage
      HomePage.svelte
    index.ts
```

If a slice uses many static images, group them in a subfolder of `ui/`:

```text
pages/
  home/
    ui/
      previews/
        cake.jpg
        pizza.jpg
        sushi.jpg
      HomePage.svelte
    index.ts
```

### Non-UI Assets

Some assets are not part of the UI but are coupled to business logic. For
example, a PDF template used to generate invoices. Place these in the
`model/` segment alongside the logic that consumes them, not in `ui/`:

```text
features/
  billing/
    model/
      invoice-template.pdf    ← Coupled to create-invoice.ts
      create-invoice.ts
    index.ts
```

The principle is locality of changes: if you delete the slice, every file it
owns goes with it. An asset that lives in business logic should sit next to
that logic.

---

## Shared Assets

When the same asset appears across multiple slices, move it to `shared/ui/`.
Place reusable images in a topical subfolder, or place a single asset next to
the shared component that uses it:

```text
shared/
  ui/
    placeholders/             ← Reused placeholder images
      cake.jpg
      pizza.jpg
    Dropdown.svelte
    chevron.svg               ← Used only by Dropdown, kept next to it
```

A single icon used by exactly one component in the UI kit stays next to that
component. A library of icons or images reused across many components goes
in a topical subfolder.

---

## Global Assets

Global stylesheets and fonts belong in the `app/` layer because they are
imported by the root layout (`src/routes/+layout.svelte`), not by
individual slices:

```text
lib/app/
  styles/
    reset.css
    global.css
  fonts/
    inter.woff2
```

Theme variables, CSS resets, and font registrations are app-wide concerns.
They bootstrap the application's visual layer the same way providers
bootstrap the runtime layer.

---

## Static Folder

SvelteKit serves the `static/` folder at the project root as-is, without
bundling or hashing. Its location is fixed.

`static/` is not part of FSD. It does not collide with FSD layers and lives
outside `src/`. Use it for files that must be served at fixed URLs: favicon,
`robots.txt`, `sitemap.xml`, OG images, and similar.

```text
static/
  favicon.ico
  robots.txt
  og-image.png
src/
  routes/
  lib/
    app/
    pages/
    shared/
```

---

## Summary Table

| Asset                                  | Location                                 |
| -------------------------------------- | ---------------------------------------- |
| Image used by one page/widget/feature  | Inside the slice's `ui/` segment         |
| PDF or template tied to business logic | Inside the slice's `model/` segment      |
| Icon reused across the app             | `shared/ui/` (topical subfolder if many) |
| Icon used by exactly one shared kit UI | Next to that component in `shared/ui/`   |
| Global CSS reset, theme variables      | `app/styles/`                            |
| Web fonts                              | `app/fonts/` or `static/`                |
| Favicon, robots.txt, sitemap           | `static/`                                |

---

## Anti-patterns

- **Do not create a top-level `assets/` segment** that holds all images,
  fonts, and icons. It breaks cohesion and forces consumers to import from a
  folder unrelated to the code they are working on.
- **Do not extract a slice-local asset to `shared/` "in case" it gets
  reused.** Move it only when actual reuse appears.
- **Do not place CSS modules in an `assets/` folder.** A component's
  stylesheet belongs next to that component in `ui/`.
- **Do not name an FSD segment `static` or `public`.** SvelteKit's
  `static/` folder is reserved and lives outside `src/`.
- **Do not split assets and the components that use them.** A page that
  ships a hero image should keep that image in the page so removing the page
  removes the image.

---

## See Also

- `references/layer-structure.md`: segment rules and layer organization
- [Desegmentation](https://fsd.how/docs/guides/issues/desegmented/): why
  technical-role grouping (including a generic `assets/` segment) hurts
  cohesion
