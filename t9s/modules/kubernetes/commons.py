class Commons:
    @staticmethod
    def get_ns_list(k8s_helper, client):
        ns_list = list()
        success, response = k8s_helper.list_namespaces(client=client)
        if success and hasattr(response, "items"):
            for item in response.items:
                ns_list.append(item.metadata.name)
        return ns_list
