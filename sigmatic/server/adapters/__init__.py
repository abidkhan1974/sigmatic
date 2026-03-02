"""Schema adapters for normalizing signals from various sources."""

from sigmatic.server.adapters.base import BaseAdapter
from sigmatic.server.adapters.generic import GenericAdapter
from sigmatic.server.adapters.tradingview import TradingViewAdapter

_registry: dict[str, BaseAdapter] = {
    "generic": GenericAdapter(),
    "tradingview": TradingViewAdapter(),
}


def get_adapter(name: str) -> BaseAdapter:
    """Return the adapter for *name*, falling back to generic if unknown."""
    return _registry.get(name, _registry["generic"])


__all__ = ["BaseAdapter", "GenericAdapter", "TradingViewAdapter", "get_adapter"]
