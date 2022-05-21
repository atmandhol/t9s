import json
from modules.utils.sh import SubProcessHelpers
from modules.kubernetes.k8s import K8s
from modules.kubernetes.objects import Resource, CustomResourceDefinition

sh = SubProcessHelpers()
k8s = K8s()


# noinspection PyBroadException
class Commons:
    @staticmethod
    def get_ns_list(context):
        ns_list = list()
        _, out, err = sh.run_proc(f"kubectl get ns -o json --context {context}")
        response = json.loads(out.decode())
        if not err and hasattr(response, "items"):
            for item in response["items"]:
                ns_list.append(item["metadata"]["name"])
        return ns_list

    @staticmethod
    def get_explorer_objects_in_ns(ctx, ns):
        objs = list[Resource]()

        # Run a command and get all objects in a namespace
        _, out, err = sh.run_proc(f"kubectl get all -n {ns} -o json --context {ctx}")
        response = json.loads(out.decode())

        if not err and hasattr(response, "items"):
            for item in response["items"]:
                objs.append(
                    Resource(
                        name=item["metadata"]["name"],
                        kind=item["kind"],
                        context=ctx,
                        namespace=ns,
                        uid=item["metadata"]["uid"] if "uid" in item["metadata"] else None,
                        owner=item["metadata"].get("ownerReferences", [{}])[0].get("uid", None),
                    )
                )
        return objs

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

    @staticmethod
    def list_all_crds(ctx):
        crd_list = list[CustomResourceDefinition]()
        success, response = k8s.get_all_crds(k8s.api_ext_clients[ctx])
        if success:
            for crd in response.items:
                crd_list.append(
                    CustomResourceDefinition(
                        group=crd.spec.group,
                        kind=crd.spec.names.kind,
                        plural=crd.spec.names.plural,
                        scope=crd.spec.scope,
                        version=crd.status.stored_versions[0],
                    )
                )
        return crd_list

    @staticmethod
    def list_all_namespaced_crds(ctx):
        crd_list = list[CustomResourceDefinition]()
        success, response = k8s.get_all_crds(k8s.api_ext_clients[ctx])
        if success:
            for crd in response.items:
                if crd.spec.scope == "Namespaced":
                    crd_list.append(
                        CustomResourceDefinition(
                            group=crd.spec.group,
                            kind=crd.spec.names.kind,
                            plural=crd.spec.names.plural,
                            scope=crd.spec.scope,
                            version=crd.status.stored_versions[0],
                        )
                    )
        return crd_list

    def list_all_custom_objects_by_type(self, ctx, ns, crd: CustomResourceDefinition):
        objs = list[Resource]()
        success, response = k8s.list_custom_objects_in_namespace(k8s.custom_clients[ctx], ns, crd.group, crd.version, crd.plural)
        if success:
            for item in response["items"]:
                resource = self.item_to_resource(ctx=ctx, ns=ns, item=item)
                objs.append(resource) if resource else None
        return objs

    def list_all_core_objects(self, ctx, ns):
        # TODO: Add daemonset, statefulset, job, cronjobs etc that is supported in the apps api
        # TODO: Sort items by group
        objs = list[Resource]()
        success, response = k8s.list_pods_in_namespace(k8s.core_clients[ctx], ns)
        if success:
            for item in response.items:
                resource = self.item_to_resource(ctx=ctx, ns=ns, item=item, kind="Pod")
                objs.append(resource) if resource else None
        success, response = k8s.list_deployments_in_namespace(k8s.apps_clients[ctx], ns)
        if success:
            for item in response.items:
                resource = self.item_to_resource(ctx=ctx, ns=ns, item=item, kind="Deployment")
                objs.append(resource) if resource else None
        success, response = k8s.list_replicasets_in_namespace(k8s.apps_clients[ctx], ns)
        if success:
            for item in response.items:
                resource = self.item_to_resource(ctx=ctx, ns=ns, item=item, kind="ReplicaSet")
                objs.append(resource) if resource else None
        success, response = k8s.list_configmaps_in_namespace(k8s.core_clients[ctx], ns)
        if success:
            for item in response.items:
                resource = self.item_to_resource(ctx=ctx, ns=ns, item=item, kind="ConfigMap")
                objs.append(resource) if resource else None
        success, response = k8s.list_secrets_in_namespace(k8s.core_clients[ctx], ns)
        if success:
            for item in response.items:
                resource = self.item_to_resource(ctx=ctx, ns=ns, item=item, kind="Secret")
                objs.append(resource) if resource else None
        success, response = k8s.list_service_accounts_in_namespace(k8s.core_clients[ctx], ns)
        if success:
            for item in response.items:
                resource = self.item_to_resource(ctx=ctx, ns=ns, item=item, kind="ServiceAccount")
                objs.append(resource) if resource else None
        success, response = k8s.list_pv_claims_in_namespace(k8s.core_clients[ctx], ns)
        if success:
            for item in response.items:
                resource = self.item_to_resource(ctx=ctx, ns=ns, item=item, kind="PersistentVolumeClaim")
                objs.append(resource) if resource else None
        return objs

    @staticmethod
    def item_to_resource(ctx, ns, item, kind=None):
        try:
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
            )
        except Exception:
            return Resource(
                name=item.metadata.name,
                kind=item.kind if not kind else kind,
                context=ctx,
                namespace=ns,
                uid=item.metadata.uid,
                owner=item.metadata.owner_references[0].uid if item.metadata.owner_references and len(item.metadata.owner_references) > 0 else None,
                metadata=item.metadata if hasattr(item, "metadata") else {},
                spec=item.spec if hasattr(item, "spec") else {},
                status=item.status if hasattr(item, "status") else {},
            )
