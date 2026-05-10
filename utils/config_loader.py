"""Loads and validates configuration files."""

import json
from functools import lru_cache
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent


@lru_cache(maxsize=1)
def load_config() -> dict:
    path = PROJECT_ROOT / "config" / "settings.json"
    if not path.exists():
        raise FileNotFoundError(f"settings.json not found at {path}")
    return json.loads(path.read_text())


@lru_cache(maxsize=1)
def load_marketplaces() -> dict:
    path = PROJECT_ROOT / "config" / "marketplaces.json"
    if not path.exists():
        raise FileNotFoundError(f"marketplaces.json not found at {path}")
    return json.loads(path.read_text())


@lru_cache(maxsize=1)
def load_webhooks() -> dict:
    path = PROJECT_ROOT / "config" / "webhooks.json"
    if not path.exists():
        raise FileNotFoundError(f"webhooks.json not found at {path}")
    return json.loads(path.read_text())


def reload_all() -> None:
    load_config.cache_clear()
    load_marketplaces.cache_clear()
    load_webhooks.cache_clear()
