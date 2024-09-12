from __future__ import annotations

from contextlib import suppress
from typing import TYPE_CHECKING

from google.cloud.exceptions import NotFound

from cloudshell.cp.core.cancellation_manager import CancellationContextManager
from cloudshell.cp.core.rollback import RollbackCommand, RollbackCommandsManager
from cloudshell.shell.core.driver_utils import GlobalLock


from cloudshell.cp.gcp.handlers.instance import InstanceHandler

if TYPE_CHECKING:
    from google.auth.credentials import Credentials
    from google.cloud.compute_v1.types import compute


class DeployInstanceCommand(RollbackCommand, GlobalLock):
    instance: compute.Instance
    credentials: Credentials
    rollback_manager: RollbackCommandsManager
    cancellation_manager: CancellationContextManager

    def __attrs_post_init__(self):
        super().__init__(
            rollback_manager=self.rollback_manager,
            cancellation_manager=self.cancellation_manager
        )

    @GlobalLock.lock
    def _execute(self) -> str:
        try:
            self._instance_handler = InstanceHandler.deploy(
                instance=self.instance,
                credentials=self.credentials
            )
        except Exception as e:
            raise

        return self._instance_handler.instance

    def rollback(self):
        with suppress(NotFound):
            if self._instance_handler.instance.name and self._instance_handler.instance.zone:
                self._instance_handler.delete()
