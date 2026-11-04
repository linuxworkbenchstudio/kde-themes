"""What parts return: {relative path: str | bytes | Link}."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Link:
    """A symbolic link to `target` (a name in the same folder), e.g. a cursor alias."""
    target: str
