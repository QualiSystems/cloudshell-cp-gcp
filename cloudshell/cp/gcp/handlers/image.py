from __future__ import annotations

import logging
import re

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
class ImageHandler(BaseGCPHandler):
    image: compute.Disk

    @classmethod
    def parse_image_name(cls, image_url: str) -> dict[str, str]:
        """Get image data from the disk url.

        :rtype: str
        """
        result = {}
        # image_url = projects/debian-cloud/global/images/debian-12-bookworm-v20240815
        match_image = re.match(
            r"^.*projects/(?P<image_project>\S+)/global/images/(?P<image_name>\S+)$",
            image_url, flags=re.IGNORECASE
        )
        if match_image:
            result = match_image.groupdict()
        return result

    @classmethod
    def get(
            cls,
            credentials: Credentials,
            image_url: str,
            image_project: str | None = None,
    ) -> Self:
        """Get disk object from GCP and create DiskHandler object."""
        image_data = cls._parse_image_name(image_url)
        image_name = image_data.get("image_name", "N/A")
        image_project = image_data.get("image_project", image_project)
        logger.info(f"Getting Image {image_name} from {image_project}.")
        client = compute_v1.ImagesClient(credentials=credentials)
        image = client.get(
            project=image_project,
            image=image_name
        )
        return cls(image=image, credentials=credentials)