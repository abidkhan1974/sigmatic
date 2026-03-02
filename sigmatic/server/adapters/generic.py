"""Generic JSON passthrough adapter - to be implemented in Phase 1."""

from typing import Any

from sigmatic.server.adapters.base import BaseAdapter


class GenericAdapter(BaseAdapter):
    """Passthrough adapter for sources that send normalized JSON."""

    def normalize(self, raw_payload: dict[str, Any], source_config: dict[str, Any]) -> dict[str, Any]:
        """Pass through a pre-normalized signal payload."""
        raise NotImplementedError("Generic adapter not yet implemented")
