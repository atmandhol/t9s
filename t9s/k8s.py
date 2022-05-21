from modules.kubernetes.commons import Commons
from rich import print

comm = Commons()
ctx = "kind-tap-iterate"
ns = "ns1"

objs = list()
crds = comm.list_all_namespaced_crds(ctx=ctx)
for crd in crds:
    co_list = comm.list_all_custom_objects_by_type(ctx=ctx, ns=ns, crd=crd)
    for co in co_list:
        objs.append(co)
objs = objs + comm.list_all_core_objects(ctx=ctx, ns=ns)

# print(objs)
h = comm.get_hierarchy(objs)
print(h.keys())