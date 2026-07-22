# Operational Documentation Refresh Design

## Goal

I-align ang maintainer at admin-facing documentation sa current program-logo
implementation nang hindi binabago ang historical planning records.

## Source Of Truth

Ang current FastAPI routes, settings, SQLAlchemy models, MySQL schema, frontend
behavior, at passing tests ang source of truth. Historical specs, plans, at
handoff files ay implementation history lamang at hindi rerewrite-in.

## Scope

Iu-update ang mga operational document na ito:

- `backend/README.md`: program-logo API behavior, storage, public media URL,
  at PDF/public-page output.
- `backend/.env.example`: program-logo storage, size limit, at URL-prefix
  settings.
- `frontend/README.md`: optional program-logo support sa current views at
  machine-specific API configuration guidance.
- `frontend/manual-test-guide.md`: upload, replace/remove, public header, at
  PDF logo verification steps.
- `others/database/README.md`: chronological migration instructions para sa
  existing databases.
- `others/database/data-dictionary.md`: `programs.logo_path` definition.
- `others/README.md`: current-decision note para sa optional program logos.

## Explicit Non-Goals

- Hindi babaguhin ang `docs/superpowers/specs/` at `docs/superpowers/plans/`
  na historical feature records, maliban sa design na ito.
- Hindi babaguhin ang `others/dict-attendance-system-handoff.md`, dahil
  historical context ito ayon sa `others/README.md`.
- Hindi magpapalit ng actual LAN host address sa `frontend/js/config.js`.
  Environment-specific ito; ang docs ay magtuturo kung saan ito iko-configure.
- Hindi sakop ng documentation refresh ang code changes para sa program-logo
  image-content validation o additional automated tests.

## Acceptance Criteria

- Nakadokumento ang optional PNG/JPEG program-logo workflow at 2 MiB limit.
- Nakadokumento ang default program-logo directory at public media URL prefix.
- Nakadokumento na ang logo ay lumalabas sa public attendance page at PDF.
- Kumpleto ang existing-database migration order.
- Walang operational document na nagsasabing mali ang current `.131` API host.
- Walang historical document na binabago para lang gawing current reference.
