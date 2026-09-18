# Agent Handoff Guide

## Current state

The app is complete, locally tested, and committed on `main`. Run it from this folder with `python app.py`. The generated `database.db` is ignored by Git and must not be committed.

## Architecture

- `app.py` contains routes, database initialization, validation, calculations, and deterministic recommendation functions.
- `users` stores submitted profiles; `plans` stores a JSON snapshot created on registration.
- Dashboard, workout, and diet routes read the saved profile, then recompute metrics and regenerate recommendations live. This deliberately keeps rendered guidance current after rule changes.
- Templates are server-rendered through Jinja. JavaScript is optional only.

## Reliable continuation checklist

1. Keep Flask, SQLite, and Jinja; do not add a larger framework.
2. Preserve foreign-key setup and parameterized SQL in `get_db_connection()`.
3. When adding profile fields, update schema, validation, INSERT, form, and templates together.
4. Test all goal/level combinations plus knee, shoulder/wrist, and back injury terms after recommendation changes.
5. Run the README test steps after every change. GET routes must never create a user.
6. GitHub pushing requires an account or SSH key with write access to the repository.

## Invariants

- Only `POST /register` creates a user.
- `cursor.lastrowid` is the user ID passed to the dashboard redirect.
- Unknown profile pages redirect safely to registration.
- Guidance is informational and never medical advice.
