from __future__ import annotations

import logging
from contextlib import suppress
from functools import cached_property
from io import BytesIO, StringIO

from google.api_core.exceptions import NotFound
from google.cloud import storage

from cloudshell.cp.gcp.handlers.base import BaseGCPHandler

logger = logging.getLogger(__name__)


class SSHKeysHandler(BaseGCPHandler):
    @cached_property
    def storage_client(self):
        return storage.Client(credentials=self.credentials)

    def upload_ssh_keys(
        self, bucket_name: str, folder_path: str, private_key: str, public_key: str
    ) -> None:
        """Uploads a file to a GCP bucket in a specified folder."""
        bucket = self.storage_client.bucket(bucket_name)
        blob = bucket.blob(f"{folder_path}/private_key")
        blob.upload_from_string(private_key)
        blob = bucket.blob(f"{folder_path}/public_key")
        blob.upload_from_string(public_key)
        logger.info(
            f"SSH keypair uploaded to {folder_path} in bucket" f" {bucket_name}."
        )

    def get_ssh_key_pair(self, bucket_name: str, folder_path: str) -> tuple[str, str]:
        """Downloads a file from a GCP bucket."""
        public_key = None
        private_key = None
        with suppress(NotFound):
            private_key = self.download_ssh_key(
                bucket_name=bucket_name,
                file_path=f"{folder_path}/private_key",
            )
        with suppress(NotFound):
            public_key = self.download_ssh_key(
                bucket_name=bucket_name,
                file_path=f"{folder_path}/public_key",
            )
        return private_key, public_key

    def download_ssh_key(
        self,
        bucket_name: str,
        file_path: str,
    ) -> str:
        """Downloads a file from a GCP bucket."""
        bucket = self.storage_client.bucket(bucket_name)
        blob = bucket.blob(file_path)
        _file = BytesIO()
        blob.download_to_file(_file)
        logger.info(f"File {file_path} downloaded from bucket {bucket_name}.")
        return _file.read().decode()

    def delete_ssh_keys(
        self,
        bucket_name: str,
        folder_path: str,
    ) -> None:
        """Deletes a file and its parent folder from a GCP bucket."""
        bucket = self.storage_client.bucket(bucket_name)
        # file_blob = bucket.blob(f"{folder_path}/{file_name}")
        # file_blob.delete()
        # logger.info(
        #     f"File {file_name} deleted from folder {folder_path} in bucket {bucket_name}."
        # )

        # Delete all blobs in the parent folder
        blobs = bucket.list_blobs(prefix=folder_path)
        for blob in blobs:
            blob.delete()
        logger.info(
            f"Folder {folder_path} and all its contents deleted from bucket {bucket_name}."
        )
