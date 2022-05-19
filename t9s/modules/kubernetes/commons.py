import json
from modules.utils.sh import SubProcessHelpers

sh = SubProcessHelpers()


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
    def get_all(context, namespace):
        obj_list = list()
        _, out, err = sh.run_proc(f"kubectl get all -n {namespace} -o json --context {context}")
        response = json.loads(out.decode())

        if not err and hasattr(response, "items"):
            for item in response["items"]:
                obj_list.append(
                    {
                        "kind": f'{item["kind"]}',
                        "name": f'{item["metadata"]["name"]}',
                        "owner_kind": f'{item["metadata"].get("ownerReferences", [{}])[0].get("kind", None)}',
                        "owner_name": f'{item["metadata"].get("ownerReferences", [{}])[0].get("name", None)}',
                    }
                )
        return obj_list
