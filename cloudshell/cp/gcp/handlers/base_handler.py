from functools import cached_property

import googleapiclient
from googleapiclient.discovery import Resource


class BaseGCPHandler:
    class Decorators:
        @classmethod
        def get_data(
            cls,
            retries: int = 6,
            timeout: int = 5,
            raise_on_timeout: bool = True
        ):
            def wrapper(decorated):
                def inner(*args, **kwargs):
                    exception = None
                    attempt = 0
                    while attempt < retries:
                        try:
                            return decorated(*args, **kwargs).json()["data"]
                        except Exception as e:
                            exception = e
                            time.sleep(timeout)
                            attempt += 1

                    if raise_on_timeout:
                        if exception:
                            raise exception
                        else:
                            raise BaseProxmoxException(
                                f"Cannot get data for {retries*timeout} sec."
                            )

                return inner
            return wrapper

        @classmethod
        def zone_wait(client, project, zone, operation):
            """ input: client, project, zone, and operation
                output: request result - json
                sleep/waits for zone operation to complete
            """
            while True:
                result = client.zoneOperations().get(project=project, zone=zone,
                                                     operation=operation).execute()
                if result['status'] == 'DONE':
                    print("done")
                    if 'error' in result:
                        raise Exception(result['error'])
                    return result
                else:
                    print("waiting for " + operation)
                time.sleep(1)

        @classmethod
        def region_wait(client, project, region, operation):
            """ input: gce connection and operation
                output: request result - json
                sleep/waits for region operation to complete
            """
            while True:
                result = client.regionOperations().get(project=project, region=region,
                                                       operation=operation).execute()
                if result['status'] == 'DONE':
                    print("done")
                    if 'error' in result:
                        raise Exception(result['error'])
                    return result
                else:
                    print("waiting for " + operation)
                time.sleep(1)

        @classmethod
        def global_wait(client, project, operation):
            """ input: gce client and operation
                output: request result - json
                sleep/waits for global operation to complete
            """
            while True:
                result = client.globalOperations().get(project=project,
                                                       operation=operation).execute()
                if result['status'] == 'DONE':
                    print("done")
                    if 'error' in result:
                        raise Exception(result['error'])
                    return result
                else:
                    print("waiting for " + operation)
                time.sleep(1)

    @cached_property
    def gcp_session(self) -> Resource:
        return googleapiclient.discovery.build('compute', 'v1')
