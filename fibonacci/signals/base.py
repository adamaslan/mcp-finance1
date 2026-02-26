"""Base signal generator abstract class."""

from abc import ABC, abstractmethod
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from ..analysis.context import FibonacciContext
    from ..core.models import FibonacciSignal


class SignalGenerator(ABC):
    """Abstract base class for signal generators."""

    @abstractmethod
    def generate(self, context: 'FibonacciContext') -> List['FibonacciSignal']:
        """Generate signals from context."""
        pass
