# SkyCommons backend - API guide for the frontend

This backend is the editable source for the content the SvelteKit app
currently reads from local JSON files. It exposes three URL surfaces; you
will most likely only need the first one.

Base URL: `http://localhost:8000` in development. Production URL TBD.

## 1. Compatibility layer (drop-in replacement for the static files)

Same paths, same JSON shapes as the files in the static build. The goal is
that the frontend build can switch from reading local files to fetching
these URLs with no other change. A contract test suite in this repo
guarantees the responses match the current files exactly (values, nulls,
optional keys, key order).

| URL | Replaces | Content |
|---|---|---|
| `/content/index.json` | `content/index.json` | Homepage editorial copy: header, introduction, countries, satellite and information sections, each with title/text and CTA(s) |
| `/content/countries.json` | `content/countries.json` | The "What we observed" section of the countries page |
| `/data/country-<id>.json` | `data/country-<id>.json` | Full research dossier for one country (`brazil`, `fiji`, `indonesia`, `malaysia`, `nigeria`, `ukraine`): identity/stats, texts, the five scored research dimensions with their indicators, and the timeline. Unknown ids return 404 |
| `/data/countries-id-name.json` | `data/countries-id-name.json` | ISO code to display name map (176 entries) used by the world map |

Notes:

- Prose fields may contain inline HTML (links, `<br/>`), exactly as today.
  Nothing new to handle on your side.
- `data/satellites.json` is NOT served by this backend. It stays a
  generated pipeline artifact published as a static file; same for
  `data/countries-110m.json` (TopoJSON geometry).
- The read APIs are open by design: everything they return is public on
  the site anyway, and they are read-only (writes return 405). The only
  protected surface is the admin. No tokens to manage on your side.

## 2. Content API (plain REST, read-only)

Conventional REST endpoints over the same data, useful for anything the
compat shapes do not cover (listing, pagination, browsing). Read-only:
all editing happens in the CMS admin.

| URL | Content |
|---|---|
| `/api/countries/` | Paginated list of countries (summary fields: slug, name, iso_code, region, report_date, risk_level) |
| `/api/countries/<slug>/` | One country with everything nested: research dimensions (with indicators) and timeline |
| `/api/sections/` | All editorial content sections |
| `/api/sections/<slug>/` | One section (`header`, `introduction`, `countries`, `satellite`, `information`, `observations`) |
| `/api/map-country-names/` | ISO code/name pairs (unpaginated) |

All endpoints support `?format=json` and render a browsable HTML view when
opened in a browser. List endpoints paginate with `?page=N` (50 per page).

## 3. Wagtail API v2 (CMS-level)

Standard Wagtail headless API, exposed for completeness. The editorial
content above does not live in Wagtail pages, so you probably will not
need these - but images and documents uploaded by editors are served here.

| URL | Content |
|---|---|
| `/api/v2/pages/` | Wagtail page tree (currently just the placeholder home page) |
| `/api/v2/images/` | Images uploaded through the CMS |
| `/api/v2/documents/` | Documents uploaded through the CMS |

See the Wagtail API v2 docs for filtering and field selection parameters.

## Other URLs

| URL | Content |
|---|---|
| `/` | Backend landing page (links to the public site) |
| `/admin/` | Wagtail admin - where editors manage all content |
| `/django-admin/` | Raw Django admin (internal/debug use) |

## The editing model, in one paragraph

Editors work in the Wagtail admin on structured records: six country
dossiers (with ordered inline lists for the research dimensions, their
indicators, and the timeline), the editorial sections, and the map name
lookup. Whatever
they publish is what the URLs above return. Since the frontend is a static
build that fetches at build time, published changes appear on the site
after the next frontend build - the rebuild trigger (webhook on publish)
is on our roadmap and we will coordinate it with you.
