# SignalDesk

Advertising performance reporting for one agency: approved Google accounts, role-based client access, manually entered daily campaign metrics, date-filtered reports, channel comparisons and English/Russian dark UI. Inspired by the product category of Cometly; this MVP does not perform event attribution.

## Current status

Specification approved on 2026-10-19 with the user message “да давай сделать и не забудь зайти в мой гит”. Documentation and local issue staging are being prepared. No test results, deployment, GitHub repository or issue publication is implied by this document. See `_docs/process.md` for stage evidence and `_docs/backlog.json` for unpublished planned issues.

## Planned architecture

React + TypeScript + Vite frontend; FastAPI REST backend; SQLAlchemy ORM, Alembic migrations and SQLite persistence. Frontend starts against mockService, followed by OpenAPI, in-memory backend, SQLite, then full integration. See `_docs/architecture.md`.

## Setup

Exact runnable setup commands will be added when implementation is present and verified. Planned prerequisites: Node.js 22+, Python 3.11+, and Google OAuth web application credentials configured outside git. Google login requires an authorized redirect URL and an administrator allowlisted through configuration. No credentials are bundled.

## Documentation

- `_docs/plan.md`: approved MVP and deferred proposals.
- `chat-brainstorm.md` and `_docs/chat-brainstorm.md`: actual conversation.
- `_docs/process.md`: iteration gates and issue workflow.
- `_docs/architecture.md`, `_docs/design-system.md`, `_docs/testing-guidelines.md`: implementation guidance.
- `_docs/team/`: PM, engineering, QA and design roles.

No license or production hosting commitment has been selected.
