"""Compatibility entrypoint forwarding to the canonical backend app."""

from backend.main import app

__all__ = ["app"]
