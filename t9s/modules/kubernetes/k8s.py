import json
import kubernetes as k8s
from kubernetes.client import ApiException


# noinspection PyBroadException
class K8s:
    def __init__(self, logger):
        self.config = k8s.config
        self.client = k8s.client
        self.contexts: list[str] = list()
        self.core_clients: dict[str, k8s.client.CoreV1Api] = dict()
        self.custom_clients: dict[str, k8s.client.CustomObjectsApi] = dict()
        self.api_ext_clients: dict[str, k8s.client.ApiextensionsV1Api] = dict()
        self.apps_clients: dict[str, k8s.client.AppsV1Api] = dict()
        self.plural_of = dict()
        self.load_contexts_and_clients()
        self.log = logger

    def load_contexts_and_clients(self):
        # Adding try/catch block so that tappr init does not blow up if the KUBECONFIG has no clusters/entries
        if len(self.contexts) == 0:
            try:
                contexts_obj, current_context = self.config.list_kube_config_contexts()
                for ctx in contexts_obj:
                    try:
                        self.core_clients[ctx["name"]] = self.client.CoreV1Api(api_client=self.config.new_client_from_config(context=ctx["name"]))
                        self.custom_clients[ctx["name"]] = self.client.CustomObjectsApi(
                            api_client=self.config.new_client_from_config(context=ctx["name"])
                        )
                        self.api_ext_clients[ctx["name"]] = self.client.ApiextensionsV1Api(
                            api_client=self.config.new_client_from_config(context=ctx["name"])
                        )
                        self.apps_clients[ctx["name"]] = self.client.AppsV1Api(api_client=self.config.new_client_from_config(context=ctx["name"]))
                        self.contexts.append(ctx["name"])
                    except Exception:
                        pass
            except Exception:
                pass

    @staticmethod
    def get_all_crds(client: k8s.client.ApiextensionsV1Api):
        try:
            response = client.list_custom_resource_definition(_preload_content=False)
            return True, json.loads(response.data)
        except ApiException as err:
            return False, err

    @staticmethod
    def list_custom_objects_in_ns(client: k8s.client.CustomObjectsApi, namespace, group, version, plural):
        try:
            response = client.list_namespaced_custom_object(
                group=group, version=version, namespace=namespace, plural=plural, _preload_content=False
            )
            return True, json.loads(response.data)
        except ApiException as err:
            return False, err

    @staticmethod
    def list_pods_in_ns(client: k8s.client.CoreV1Api, namespace):
        try:
            response = client.list_namespaced_pod(namespace=namespace, _preload_content=False)
            return True, json.loads(response.data)
        except ApiException as err:
            return False, err

    @staticmethod
    def list_deployments_in_ns(client: k8s.client.AppsV1Api, namespace):
        try:
            response = client.list_namespaced_deployment(namespace=namespace, _preload_content=False)
            return True, json.loads(response.data)
        except ApiException as err:
            return False, err

    @staticmethod
    def list_replicasets_in_ns(client: k8s.client.AppsV1Api, namespace):
        try:
            response = client.list_namespaced_replica_set(namespace=namespace, _preload_content=False)
            return True, json.loads(response.data)
        except ApiException as err:
            return False, err

    @staticmethod
    def list_configmaps_in_ns(client: k8s.client.CoreV1Api, namespace):
        try:
            response = client.list_namespaced_config_map(namespace=namespace, _preload_content=False)
            return True, json.loads(response.data)
        except ApiException as err:
            return False, err

    @staticmethod
    def list_secrets_in_ns(client: k8s.client.CoreV1Api, namespace):
        try:
            response = client.list_namespaced_secret(namespace=namespace, _preload_content=False)
            return True, json.loads(response.data)
        except ApiException as err:
            return False, err

    @staticmethod
    def list_service_accounts_in_ns(client: k8s.client.CoreV1Api, namespace):
        try:
            response = client.list_namespaced_service_account(namespace=namespace, _preload_content=False)
            return True, json.loads(response.data)
        except ApiException as err:
            return False, err

    @staticmethod
    def list_pv_claims_in_ns(client: k8s.client.CoreV1Api, namespace):
        try:
            response = client.list_namespaced_persistent_volume_claim(namespace=namespace, _preload_content=False)
            return True, json.loads(response.data)
        except ApiException as err:
            return False, err
