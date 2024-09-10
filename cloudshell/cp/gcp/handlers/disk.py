from __future__ import annotations

import logging

from attr import define
from google.cloud import compute_v1
from google.cloud.compute_v1.types import compute
from typing_extensions import TYPE_CHECKING


from cloudshell.cp.gcp.handlers.base import BaseGCPHandler

if TYPE_CHECKING:
    from google.auth.credentials import Credentials
    from typing_extensions import Self

logger = logging.getLogger(__name__)

@define
class DiskHandler(BaseGCPHandler):
    disk: compute.Disk

    @classmethod
    def get(cls, disk_name: str, zone: str, credentials: Credentials) -> Self:
        """Get disk object from GCP and create DiskHandler object."""
        logger.info(f"Getting Disk {disk_name}.")
        client = compute_v1.DisksClient(credentials=credentials)
        disk = client.get(
            project=credentials.project_id,
            zone=zone,
            disk=disk_name
        )
        return cls(disk=disk, credentials=credentials)

    @property
    def disk_size(self) -> str:
        """Get image name from disk."""
        return self.disk.size_gb

    @property
    def disk_type(self) -> str:
        """Get image project from disk."""
        return self.disk.type_.rsplit("/", 1)[-1]

    @property
    def architecture(self) -> str:
        """Get image project from disk."""
        return self.disk.architecture

    @property
    def source_image(self) -> str:
        """Get image project from disk."""
        return self.disk.source_image
