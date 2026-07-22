# sky-commons-backend

Wagtail (Django) content backend for the SkyCommons Observatory
(https://skycommons.okfn.org/). Editors manage country dossiers and
editorial copy here; the SvelteKit frontend consumes it via API at build
time. See `API.md` for all endpoints.

## Setup

Requires [uv](https://docs.astral.sh/uv/).

```bash
uv sync
uv run python manage.py migrate
uv run python manage.py createsuperuser
uv run python manage.py runserver   # admin at http://localhost:8000/admin/
```

## Initial data

Two ways to populate a fresh database, pick one:

**From the bundled fixture** (no other checkout needed - use this in prod):

```bash
uv run python manage.py loaddata observatory
```

**From a checkout of the static site** (okfn/skycommons as a sibling
directory; reads its `docs/` JSON files):

```bash
uv run python manage.py import_site_data
# or from an arbitrary copy of the docs folder:
uv run python manage.py import_site_data --source /path/to/docs
```

Both are idempotent but overwrite CMS edits - they reset content to the
snapshot they carry. To refresh the fixture after a re-import or content
changes:

```bash
uv run python manage.py dumpdata observatory --indent 2 -o observatory/fixtures/observatory.json
```

## Tests

```bash
uv run python manage.py test
```

The contract tests (compat API output == static site JSON files) need the
sky-commons checkout; they skip when it is missing. `SKY_COMMONS_DOCS` env
var overrides where they (and `import_site_data`) look for the `docs`
folder. CI runs the full suite on every push/PR
(`.github/workflows/tests.yml`).
