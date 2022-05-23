import json
import yaml
from t9s.modules.utils.sh import SubProcessHelpers
from t9s.modules.kubernetes.k8s import K8s
from t9s.modules.kubernetes.objects import Resource, CustomResourceDefinition

sh = SubProcessHelpers()


# noinspection PyBroadException
class Commons:
    def __init__(self, logger):
        self.log = logger
        self.k8s = K8s(logger=self.log)

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

    def list_all_crds(self, ctx):
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
                            printer_cols=printer_cols
                        )
                    )
        return crd_list

    def list_all_custom_objects_by_type(self, ctx, ns, crd: CustomResourceDefinition):
        objs = list[Resource]()
        success, response = self.k8s.list_custom_objects_in_namespace(self.k8s.custom_clients[ctx], ns, crd.group, crd.version, crd.plural)
        if success:
            for item in response["items"]:
                resource = self.item_to_resource(ctx=ctx, ns=ns, item=item)
                objs.append(resource) if resource else None
        return objs

    def list_all_core_objects(self, ctx, ns):
        # TODO: Add daemonset, statefulset, job, cronjobs etc that is supported in the apps api
        # TODO: Sort items by group
        objs = list[Resource]()
        success, response = self.k8s.list_pods_in_namespace(self.k8s.core_clients[ctx], ns)
        if success:
            for item in response["items"]:
                resource = self.item_to_resource(ctx=ctx, ns=ns, item=item, kind="Pod")
                objs.append(resource) if resource else None
        success, response = self.k8s.list_deployments_in_namespace(self.k8s.apps_clients[ctx], ns)
        if success:
            for item in response["items"]:
                resource = self.item_to_resource(ctx=ctx, ns=ns, item=item, kind="Deployment")
                objs.append(resource) if resource else None
        success, response = self.k8s.list_replicasets_in_namespace(self.k8s.apps_clients[ctx], ns)
        if success:
            for item in response["items"]:
                resource = self.item_to_resource(ctx=ctx, ns=ns, item=item, kind="ReplicaSet")
                objs.append(resource) if resource else None
        success, response = self.k8s.list_configmaps_in_namespace(self.k8s.core_clients[ctx], ns)
        if success:
            for item in response["items"]:
                resource = self.item_to_resource(ctx=ctx, ns=ns, item=item, kind="ConfigMap")
                objs.append(resource) if resource else None
        success, response = self.k8s.list_secrets_in_namespace(self.k8s.core_clients[ctx], ns)
        if success:
            for item in response["items"]:
                resource = self.item_to_resource(ctx=ctx, ns=ns, item=item, kind="Secret")
                objs.append(resource) if resource else None
        success, response = self.k8s.list_service_accounts_in_namespace(self.k8s.core_clients[ctx], ns)
        if success:
            for item in response["items"]:
                resource = self.item_to_resource(ctx=ctx, ns=ns, item=item, kind="ServiceAccount")
                objs.append(resource) if resource else None
        success, response = self.k8s.list_pv_claims_in_namespace(self.k8s.core_clients[ctx], ns)
        if success:
            for item in response["items"]:
                resource = self.item_to_resource(ctx=ctx, ns=ns, item=item, kind="PersistentVolumeClaim")
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
            yaml_value=yaml.safe_load(json.dumps(item)),
        )
