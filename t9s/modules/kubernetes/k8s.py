import kubernetes as k8s


# noinspection PyBroadException,PyTypeChecker
class K8s:
    def __init__(self):
        self.config = k8s.config
        self.client = k8s.client
        self.contexts: list[str] = list()
        self.core_clients: dict[str, k8s.client.CoreV1Api] = dict()
        self.custom_clients: dict[str, k8s.client.CustomObjectsApi] = dict()
        self.plural_of = dict()
        self.load_contexts_and_clients()

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
                        self.contexts.append(ctx["name"])
                    except Exception:
                        pass
            except Exception:
                pass
