import rich
from rich.text import Text, TextType
from textual.reactive import Reactive
from textual.widget import RenderableType
from textual.widgets import TreeClick, TreeControl, TreeNode, NodeID

# noinspection PyProtectedMember
from textual.widgets._tree_control import NodeDataType

from modules.kubernetes.k8s import K8s
from modules.kubernetes.commons import Commons
from modules.kubernetes.objects import Resource
from functools import lru_cache

k8s_helper = K8s()
commons = Commons()


# noinspection PyProtectedMember
class ExplorerTree(TreeControl[Resource]):
    def __init__(self, console: rich.console.Console) -> None:
        data = Resource(name="/")
        super().__init__(label=Text("K8s Contexts"), name="Explorer", data=data)
        self.rich_console = console

    has_focus: Reactive[bool] = Reactive(False)

    async def add(
        self,
        node_id: NodeID,
        label: TextType,
        data: NodeDataType,
    ):
        parent = self.nodes[node_id]
        self.id = NodeID(self.id + 1)
        child_tree = parent._tree.add(label)
        child_node: TreeNode[NodeDataType] = TreeNode(parent, self.id, self, child_tree, label, data)
        parent.children.append(child_node)
        child_tree.label = child_node
        self.nodes[self.id] = child_node
        self.refresh(layout=True)
        return child_node

    def on_focus(self) -> None:
        self.has_focus = Reactive(True)

    def on_blur(self) -> None:
        self.has_focus = Reactive(False)

    async def on_mount(self) -> None:
        await self.load_contexts(self.root)

    async def load_contexts(self, node: TreeNode[Resource]):
        for ctx in k8s_helper.contexts:
            await node.add(label=f"ctx/{ctx}", data=Resource(name=ctx, kind="Context", context=ctx))
        node.loaded = True
        await node.expand()
        self.refresh(layout=True)

    async def load_ns(self, node: TreeNode[Resource]):
        ns_list = commons.get_ns_list(context=node.data.context)
        self.log(ns_list)
        if ns_list and isinstance(ns_list, list) and len(ns_list) > 0:
            for ns in ns_list:
                await node.add(label=f"ns/{ns}", data=Resource(name=ns, kind="Namespace", context=node.data.context, namespace=ns))
        node.loaded = True
        await node.expand()
        self.refresh(layout=True)

    @staticmethod
    async def get_objs_for_ctx_ns(ctx, ns):
        objs = list()
        crds = commons.list_all_namespaced_crds(ctx=ctx)
        for crd in crds:
            co_list = commons.list_all_custom_objects_by_type(ctx=ctx, ns=ns, crd=crd)
            for co in co_list:
                objs.append(co)
        return objs + commons.list_all_core_objects(ctx=ctx, ns=ns)

    @staticmethod
    def get_resource_by_uid(uid, objs: list[Resource]):
        for o in objs:
            if o.uid == uid:
                return o
        return None

    # noinspection PyTypeChecker
    async def load_objects(self, node: TreeNode[Resource], objs: list[Resource] = None, hierarchy: dict = None):
        """
        :param node: node is the current node on the tree, for this level it will be namespace for first run of recursion
        :param objs: is a list of all objects in namespace, pass this bad boy along in recursion
        :param hierarchy: hierarchy dict that specifies the UID hierarchy
        :return:
        """
        if not objs or not hierarchy:
            objs = await self.get_objs_for_ctx_ns(ctx=node.data.context, ns=node.data.namespace)
            hierarchy = commons.get_hierarchy(objs=objs)

        uid_list = hierarchy.keys()
        for uid in uid_list:
            resource = self.get_resource_by_uid(uid=uid, objs=objs)
            if hierarchy[uid]:
                resource.has_children = True
            label = f"{resource.kind}/{resource.name}"
            child = await self.add(node_id=node.id, label=label, data=resource)
            if hierarchy[uid]:
                await self.load_objects(node=child, objs=objs, hierarchy=hierarchy[uid])
        node.loaded = True
        # await node.expand()
        self.refresh(layout=True)

    async def handle_tree_click(self, message: TreeClick[Resource]) -> None:
        if message.node.data.context:
            if not message.node.loaded and message.node.data.kind == "Context":
                await self.load_ns(message.node)
                await message.node.expand()
            elif not message.node.loaded and message.node.data.kind == "Namespace":
                await self.load_objects(message.node)
                await message.node.expand()
            elif not message.node.loaded and message.node.data.has_children:
                await self.load_objects(message.node, None, None)
                await message.node.expand()
            else:
                await message.node.toggle()

        """
        if not dir_entry.is_dir:
            await self.emit(FileClick(self, dir_entry.path))
        """

    def render_node(self, node: TreeNode[Resource]) -> RenderableType:
        return self.render_tree_label(
            node,
            node.data.kind,
            node.data.has_children,
            node.expanded,
            node.is_cursor,
            node.id == self.hover_node,
            self.has_focus,
        )

    @lru_cache(maxsize=1024 * 32)
    def render_tree_label(
        self,
        node: TreeNode[Resource],
        kind: str,
        has_children: bool,
        expanded: bool,
        is_cursor: bool,
        is_hover: bool,
        has_focus: bool,
    ) -> RenderableType:
        meta = {
            "@click": f"click_label({node.id})",
            "tree_node": node.id,
            "cursor": node.is_cursor,
        }
        label = Text(node.label) if isinstance(node.label, str) else node.label
        if is_hover:
            label.stylize("bold underline")

        label.stylize("bold white")
        # Catch-all
        icon = "🌴"
        # General
        if kind and has_children:
            label.stylize("bold #ffffff")
            icon = "➕"
        if kind and not has_children:
            label.stylize("bold #ffffff")
            icon = "📦"
        # More specific
        if kind == "Context":
            label.stylize("#ebae3d") if not expanded else label.stylize("bold #f5ca7a")
            icon = "💻"
        if kind == "Pod":
            icon = "🐳"
        if kind == "Namespace":
            label.stylize("#39cbf7") if not expanded else label.stylize("bold #83dcf7")
            icon = "📂" if expanded else "📁"

        if is_cursor and has_focus:
            label.stylize("reverse")

        icon_label = Text(f"{icon} ", no_wrap=True, overflow="ellipsis") + label
        icon_label.apply_meta(meta)
        return icon_label
