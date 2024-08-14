from __future__ import annotations


class BaseGCPError(Exception):
    """Base Google Cloud Provider Error."""


class AttributeGCPError(BaseGCPError):
    """Incorrect attribute provided."""


class NotSupportedGCPError(BaseGCPError):
    """Not supported by Google Cloud Provider."""
