"""Abstract base class for signal schema adapters."""

from abc import ABC, abstractmethod
from typing import Any


class BaseAdapter(ABC):
    """Abstract base class for all signal adapters."""

    @abstractmethod
    def normalize(self, raw_payload: dict[str, Any], source_config: dict[str, Any]) -> dict[str, Any]:
        """Normalize a raw payload into a standard signal dict.

        Args:
            raw_payload: The raw incoming payload from the source.
            source_config: The source's configuration dict.

        Returns:
            A normalized signal dict matching the signal schema.
        """
        ...
