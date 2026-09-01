"""Deprecated model generator retained only to prevent accidental data-model loss."""

raise SystemExit(
    "generate_models_v3.py is disabled because it overwrites production models with stale definitions. "
    "Change models in app/models and create an Alembic migration instead."
)
