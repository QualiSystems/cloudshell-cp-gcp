from __future__ import annotations

import logging

from google.cloud import compute_v1
from functools import cached_property
from typing import TYPE_CHECKING

from cloudshell.cp.gcp.handlers.base import BaseGCPHandler


# if TYPE_CHECKING:

logger = logging.getLogger(__name__)


class SubnetHandler(BaseGCPHandler):
    def create(self, network_name):
        pass

    def get(self):
        pass

    def delete(self):
        pass
