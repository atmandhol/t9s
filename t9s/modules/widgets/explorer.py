import rich
from rich.text import Text
from textual.reactive import Reactive
from textual.widget import RenderableType
from textual.widgets import TreeClick, TreeControl, TreeNode
from modules.kubernetes.k8s import K8s
from modules.kubernetes.commons import Commons
from dataclasses import dataclass
from functools import lru_cache

k8s_helper = K8s()
commons = Commons()


@dataclass
class ExplorerEntry:
    name: str = None
    kind: str = None
    context: str = None
    namespace: str = None
    has_children: bool = False


class ExplorerTree(TreeControl[ExplorerEntry]):
    def __init__(self, console: rich.console.Console) -> None:
        data = ExplorerEntry(name="/")
        super().__init__(label=Text("K8s Contexts"), name="Explorer", data=data)
        self.rich_console = console

    has_focus: Reactive[bool] = Reactive(False)

    def on_focus(self) -> None:
        self.has_focus = Reactive(True)

    def on_blur(self) -> None:
        self.has_focus = Reactive(False)

    async def on_mount(self) -> None:
        await self.load_contexts(self.root)

    async def load_contexts(self, node: TreeNode[ExplorerEntry]):
        for ctx in k8s_helper.contexts:
            await node.add(label=f"ctx/{ctx}", data=ExplorerEntry(name=ctx, context=ctx, has_children=True, kind="ctx"))
        node.loaded = True
        await node.expand()
        self.refresh(layout=True)

    async def load_ns(self, node: TreeNode[ExplorerEntry]):
        ns_list = commons.get_ns_list(context=node.data.context)
        self.log(ns_list)
        if ns_list and isinstance(ns_list, list) and len(ns_list) > 0:
            for ns in ns_list:
                await node.add(label=f"ns/{ns}", data=ExplorerEntry(name=ns, namespace=ns, context=node.data.context, has_children=True, kind="ns"))
        node.loaded = True
        await node.expand()
        self.refresh(layout=True)

    def check_if_has_children(self, objs, kind, name):
        for obj in objs:
            self.log(obj["owner_name"])
            if obj["owner_kind"] == kind and obj["owner_name"] == name:
                return True
        return False

    async def load_objects(self, node: TreeNode[ExplorerEntry], owner_kind=None, owner_name=None):
        objs = commons.get_all(context=node.data.context, namespace=node.data.namespace)
        self.log(objs)
        if objs and isinstance(objs, list) and len(objs) > 0:
            for obj in objs:
                label = f"{obj['kind']}/{obj['name']}"
                self.log(f'{obj["owner_kind"]}/{owner_kind}/{obj["owner_name"]}/{owner_name}')
                if obj["owner_kind"] == owner_kind and obj["owner_name"] == owner_name:
                    await node.add(
                        label=label,
                        data=ExplorerEntry(
                            name=obj["name"],
                            kind=obj["kind"],
                            namespace=node.data.namespace,
                            context=node.data.context,
                            has_children=self.check_if_has_children(objs=objs, kind=obj["kind"], name=obj["name"]),
                        ),
                    )
        node.loaded = True
        await node.expand()
        self.refresh(layout=True)

    async def handle_tree_click(self, message: TreeClick[ExplorerEntry]) -> None:
        if message.node.data.context:
            if not message.node.loaded and not message.node.data.namespace:
                await self.load_ns(message.node)
                await message.node.expand()
            elif not message.node.loaded and message.node.data.kind == "ns":
                await self.load_objects(message.node, None, None)
                await message.node.expand()
            elif not message.node.loaded and message.node.data.has_children:
                await self.load_objects(message.node, message.node.data.kind, message.node.data.name)
                await message.node.expand()
            else:
                await message.node.toggle()

        """
        if not dir_entry.is_dir:
            await self.emit(FileClick(self, dir_entry.path))
        """

    def render_node(self, node: TreeNode[ExplorerEntry]) -> RenderableType:
        return self.render_tree_label(
            node,
            node.data.name,
            node.data.kind,
            node.data.context,
            node.data.namespace,
            node.data.has_children,
            node.expanded,
            node.is_cursor,
            node.id == self.hover_node,
            self.has_focus,
        )

    @lru_cache(maxsize=1024 * 32)
    def render_tree_label(
        self,
        node: TreeNode[ExplorerEntry],
        name: str,
        kind: str,
        context: str,
        namespace: str,
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
        if kind == "ctx":
            label.stylize("#ebae3d") if not expanded else label.stylize("bold #f5ca7a")
            icon = "💻"
        if kind == "ns":
            label.stylize("#39cbf7") if not expanded else label.stylize("bold #83dcf7")
            icon = "📂" if expanded else "📁"

        if is_cursor and has_focus:
            label.stylize("reverse")

        icon_label = Text(f"{icon} ", no_wrap=True, overflow="ellipsis") + label
        icon_label.apply_meta(meta)
        return icon_label
