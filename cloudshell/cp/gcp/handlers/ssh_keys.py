from __future__ import annotations

import logging
from functools import cached_property

from google.cloud import storage

from cloudshell.cp.gcp.handlers.base import BaseGCPHandler

logger = logging.getLogger(__name__)


class SSHKeysHandler(BaseGCPHandler):
    @cached_property
    def storage_client(self):
        return storage.Client(credentials=self.credentials)

    def upload_ssh_keys(self, bucket_name: str, folder_path: str, file_path: str):
        """
        Uploads a file to a GCP bucket in a specified folder.

        :param bucket_name: Name of the bucket
        :param folder_path: Path of the folder in the bucket
        :param file_path: Path of the file to upload
        """
        bucket = self.storage_client.bucket(bucket_name)
        blob = bucket.blob(f"{folder_path}/{file_path.split('/')[-1]}")
        blob.upload_from_filename(file_path)
        print(
            f"File {file_path} uploaded to {folder_path} in bucket {bucket_name}.")

    def download_ssh_key(self, bucket_name: str, file_path: str,
                      destination_path: str):
        """
        Downloads a file from a GCP bucket.

        :param bucket_name: Name of the bucket
        :param file_path: Path of the file in the bucket
        :param destination_path: Path to save the downloaded file
        """
        bucket = self.storage_client.bucket(bucket_name)
        blob = bucket.blob(file_path)
        blob.download_to_filename(destination_path)
        print(
            f"File {file_path} downloaded from bucket {bucket_name} to {destination_path}.")

    def delete_ssh_keys(self, bucket_name: str, folder_path: str,
                               file_name: str):
        """
        Deletes a file and its parent folder from a GCP bucket.

        :param bucket_name: Name of the bucket
        :param folder_path: Path of the folder in the bucket
        :param file_name: Name of the file to delete
        """
        bucket = self.storage_client.bucket(bucket_name)
        file_blob = bucket.blob(f"{folder_path}/{file_name}")
        file_blob.delete()
        print(
            f"File {file_name} deleted from folder {folder_path} in bucket {bucket_name}.")

        # Delete all blobs in the parent folder
        blobs = bucket.list_blobs(prefix=folder_path)
        for blob in blobs:
            blob.delete()
        print(
            f"Folder {folder_path} and all its contents deleted from bucket {bucket_name}.")