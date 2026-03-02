"""TradingView webhook schema adapter - to be implemented in Phase 1."""

from typing import Any

from sigmatic.server.adapters.base import BaseAdapter


class TradingViewAdapter(BaseAdapter):
    """Adapter for TradingView webhook payloads."""

    def normalize(self, raw_payload: dict[str, Any], source_config: dict[str, Any]) -> dict[str, Any]:
        """Normalize a TradingView webhook payload.

        TradingView alerts send fields like: ticker, action, price
        """
        raise NotImplementedError("TradingView adapter not yet implemented")
