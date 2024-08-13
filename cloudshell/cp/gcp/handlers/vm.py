from __future__ import annotations

import logging

from google.cloud import compute_v1
from functools import cached_property
from typing import TYPE_CHECKING

from cloudshell.cp.gcp.handlers.base import BaseGCPHandler


# if TYPE_CHECKING:

logger = logging.getLogger(__name__)


class VMHandler(BaseGCPHandler):
    def create(self):
        pass

    def get_vm_details(self):
        pass

    def attach_net_iface(self):
        pass

    def detach_net_iface(self):
        pass

    def get_net_ifaces(self):
        pass

    def delete(self):
        pass
