from concurrent.futures import wait

import concurrent.futures
from t9s.modules.kubernetes.k8s import K8s
from t9s.modules.kubernetes.objects import Resource, CustomResourceDefinition


# noinspection PyBroadException
class Commons:
    def __init__(self, logger):
        self.log = logger
        self.k8s = K8s(logger=self.log)

    def get_ns_list(self, ctx):
        ns_list = list()
        success, response = self.k8s.list_ns(client=self.k8s.core_clients[ctx])
        if success:
            for item in response["items"]:
                ns_list.append(item["metadata"]["name"])
        return ns_list

    def traverse(self, hierarchy, graph, names):
        for name in names:
            hierarchy[name] = self.traverse({}, graph, graph[name])
        return hierarchy

    def get_hierarchy(self, objs: list[Resource]):
        lst = list()
        for o in objs:
            lst.append((o.owner if o.owner is not None else "root", o.uid))
        graph = {name: set() for tup in lst for name in tup}
        has_parent = {name: False for tup in lst for name in tup}
        for parent, child in lst:
            graph[parent].add(child)
            has_parent[child] = True
        roots = [name for name, parents in has_parent.items() if not parents]
        h = self.traverse({}, graph, roots)
        return h["root"] if "root" in h else {}

    def _query_convert_item_to_resource(self, ctx, ns, query_func, client, crd: CustomResourceDefinition = None, kind=None) -> list[Resource]:
        objs = list[Resource]()
        if crd:
            success, response = query_func(client, ns, crd.group, crd.version, crd.plural)
        else:
            success, response = query_func(client, ns)
        if success:
            for item in response["items"]:
                resource = self.item_to_resource(ctx=ctx, ns=ns, item=item, kind=kind)
                objs.append(resource) if resource else None
        return objs

    @staticmethod
    def item_to_resource(ctx, ns, item, kind=None):
        return Resource(
            name=item.get("metadata", {}).get("name", "Undefined"),
            kind=item.get("kind", "Undefined") if not kind else kind,
            context=ctx,
            namespace=ns,
            uid=item.get("metadata", {}).get("uid", None),
            owner=item.get("metadata", {}).get("ownerReferences", [{}])[0].get("uid", None),
            metadata=item.get("metadata", {}),
            spec=item.get("spec", {}),
            status=item.get("status", {}),
            json_value=item,
        )

    def list_all_namespaced_crds(self, ctx):
        crd_list = list[CustomResourceDefinition]()
        success, response = self.k8s.get_all_crds(self.k8s.api_ext_clients[ctx])
        if success:
            for crd in response["items"]:
                # TODO: this will fail if multiple version of a crd are installed in a cluster
                version = crd.get("status", {}).get("storedVersions")[0]
                printer_cols = list()
                for ver in crd.get("spec", {}).get("versions", [{}]):
                    if ver.get("name") == version:
                        printer_cols = ver.get("additionalPrinterColumns")
                if crd.get("spec", {}).get("scope") == "Namespaced":
                    crd_list.append(
                        CustomResourceDefinition(
                            group=crd.get("spec", {}).get("group", ""),
                            kind=crd.get("spec", {}).get("names", {}).get("kind", ""),
                            plural=crd.get("spec", {}).get("names", {}).get("plural", ""),
                            scope=crd.get("spec", {}).get("scope", "Namespaced"),
                            version=version,
                            printer_cols=printer_cols,
                        )
                    )
        return crd_list

    def list_all_ns_objects(self, ctx, ns):
        objs = list[Resource]()
        crds = self.list_all_namespaced_crds(ctx=ctx)

        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = list()

            for crd in crds:
                futures.append(
                    executor.submit(
                        self._query_convert_item_to_resource,
                        ctx=ctx,
                        ns=ns,
                        query_func=self.k8s.list_custom_objects_in_ns,
                        client=self.k8s.custom_clients[ctx],
                        crd=crd,
                        kind=None,
                    )
                )

            futures.append(
                executor.submit(
                    self._query_convert_item_to_resource,
                    ctx=ctx,
                    ns=ns,
                    query_func=self.k8s.list_pods_in_ns,
                    client=self.k8s.core_clients[ctx],
                    crd=None,
                    kind="Pod",
                )
            )

            futures.append(
                executor.submit(
                    self._query_convert_item_to_resource,
                    ctx=ctx,
                    ns=ns,
                    query_func=self.k8s.list_deployments_in_ns,
                    client=self.k8s.apps_clients[ctx],
                    kind="Deployment",
                )
            )

            futures.append(
                executor.submit(
                    self._query_convert_item_to_resource,
                    ctx=ctx,
                    ns=ns,
                    query_func=self.k8s.list_replicasets_in_ns,
                    client=self.k8s.apps_clients[ctx],
                    kind="ReplicaSet",
                )
            )

            futures.append(
                executor.submit(
                    self._query_convert_item_to_resource,
                    ctx=ctx,
                    ns=ns,
                    query_func=self.k8s.list_configmaps_in_ns,
                    client=self.k8s.core_clients[ctx],
                    kind="ConfigMap",
                )
            )

            futures.append(
                executor.submit(
                    self._query_convert_item_to_resource,
                    ctx=ctx,
                    ns=ns,
                    query_func=self.k8s.list_secrets_in_ns,
                    client=self.k8s.core_clients[ctx],
                    kind="Secret",
                )
            )

            futures.append(
                executor.submit(
                    self._query_convert_item_to_resource,
                    ctx=ctx,
                    ns=ns,
                    query_func=self.k8s.list_service_accounts_in_ns,
                    client=self.k8s.core_clients[ctx],
                    kind="ServiceAccount",
                )
            )

            futures.append(
                executor.submit(
                    self._query_convert_item_to_resource,
                    ctx=ctx,
                    ns=ns,
                    query_func=self.k8s.list_pv_claims_in_ns,
                    client=self.k8s.core_clients[ctx],
                    kind="PersistentVolumeClaim",
                )
            )
            wait(futures)
            for future in concurrent.futures.as_completed(futures):
                objs += future.result()

        # TODO: Add daemonset, statefulset, job, cronjobs etc that is supported in the apps api
        # TODO: Sort items by group

        return objs
