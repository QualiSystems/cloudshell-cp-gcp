from attr import define
from google.cloud import compute_v1

from cloudshell.cp.gcp.handlers.base import BaseGCPHandler
from cloudshell.cp.gcp.helpers.errors import AttributeGCPError


@define
class ZoneHandler(BaseGCPHandler):
    zone: str = None

    def get_zone(self, region: str, machine_type: str):
        """Determine short zone.

        Zone value depends on provided zone, region and/or machine type.
        """
        if not self.zone:
            region_client = compute_v1.RegionsClient(
                credentials=self.credentials
            )
            region_info = region_client.get(
                project=self.credentials.project_id,
                region=region
            )

            zones = [zone.split('/')[-1] for zone in region_info.zones]
        else:
            zones = [self.zone]

        machine_type_client = compute_v1.MachineTypesClient(
            credentials=self.credentials
        )

        # List all machine types in the specified zone
        for zone in zones:
            machine_types = machine_type_client.list(
                project=self.credentials.project_id,
                zone=zone
            )
            for m_type in machine_types:
                if machine_type == m_type.name:
                    return zone

        raise AttributeGCPError("Incompatible zone and machine type values.")