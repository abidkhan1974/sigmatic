"""Generic JSON passthrough adapter.

Expects the incoming payload to already use the Sigmatic field names
(symbol, direction, entry_zone, …). A field_map in source.config can
remap incoming field names before validation, e.g.:

    config: { "field_map": { "ticker": "symbol", "side": "direction" } }
"""

from typing import Any

from sigmatic.server.adapters.base import BaseAdapter


class GenericAdapter(BaseAdapter):
    """Passthrough adapter with optional field remapping."""

    def normalize(
        self, raw_payload: dict[str, Any], source_config: dict[str, Any]
    ) -> dict[str, Any]:
        field_map: dict[str, str] = (source_config or {}).get("field_map", {})
        return {field_map.get(k, k): v for k, v in raw_payload.items()}
