from __future__ import annotations

import logging
from functools import cached_property
from typing import TYPE_CHECKING

from google.cloud import compute_v1

from cloudshell.cp.gcp.handlers.base import BaseGCPHandler

# if TYPE_CHECKING:

logger = logging.getLogger(__name__)


class NetIfaceHandler(BaseGCPHandler):
    def attach_public_ip(self):
        pass

    def detach_public_ip(self):
        pass
