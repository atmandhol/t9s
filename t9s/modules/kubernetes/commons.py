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
