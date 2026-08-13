"""Session store implementations.

The canonical production implementation is Redis-backed. Batch 1 also includes
an explicit in-memory implementation that is only intended for tests and local
usage where durability is not required.
"""

from .memory import InMemorySessionStore

__all__ = ["InMemorySessionStore"]
