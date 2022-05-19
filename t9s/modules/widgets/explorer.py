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
    context: str = None
    namespace: str = None
    obj: str = None
    workload: str = None
    deliverable: str = None


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
            await node.add(label=f"{ctx}", data=ExplorerEntry(name=f"ctx-{ctx}", context=ctx))
        node.loaded = True
        await node.expand()
        self.refresh(layout=True)

    async def load_ns(self, node: TreeNode[ExplorerEntry]):
        ns_list = commons.get_ns_list(context=node.data.context)
        self.log(ns_list)
        if ns_list and isinstance(ns_list, list) and len(ns_list) > 0:
            for ns in ns_list:
                await node.add(label=f"{ns}", data=ExplorerEntry(name=f"ns-{ns}", namespace=ns, context=node.data.context))
        node.loaded = True
        await node.expand()
        self.refresh(layout=True)

    async def load_objects(self, node: TreeNode[ExplorerEntry]):
        objs = commons.get_all(context=node.data.context, namespace=node.data.namespace)
        if objs and isinstance(objs, list) and len(objs) > 0:
            for obj in objs:
                obj_name = f"{obj['kind']}/{obj['name']}"
                await node.add(
                    label=obj_name,
                    data=ExplorerEntry(name=f"obj-{obj_name}", namespace=node.data.namespace, context=node.data.context, obj=obj_name),
                )
        node.loaded = True
        await node.expand()
        self.refresh(layout=True)

    async def handle_tree_click(self, message: TreeClick[ExplorerEntry]) -> None:
        if message.node.data.context:
            if not message.node.loaded and not message.node.data.namespace:
                await self.load_ns(message.node)
                await message.node.expand()
            elif not message.node.loaded and not message.node.data.obj:
                await self.load_objects(message.node)
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
            node.data.context,
            node.data.namespace,
            node.data.workload,
            node.data.deliverable,
            node.data.obj,
            node.expanded,
            node.is_cursor,
            node.id == self.hover_node,
            self.has_focus,
        )

    @lru_cache(maxsize=1024 * 32)
    def render_tree_label(
        self,
        node: TreeNode[ExplorerEntry],
        context: str,
        namespace: str,
        workload: str,
        deliverable: str,
        obj: str,
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
        icon = "🌴"
        if context:
            label.stylize("#ebae3d") if not expanded else label.stylize("bold #f5ca7a")
            icon = "💻"
        if namespace:
            label.stylize("#39cbf7") if not expanded else label.stylize("bold #83dcf7")
            icon = "📂" if expanded else "📁"
        if obj:
            label.stylize("bold #ffffff")
            icon = "📦"
        if label.plain.startswith("."):
            label.stylize("dim")

        if is_cursor and has_focus:
            label.stylize("reverse")

        icon_label = Text(f"{icon} ", no_wrap=True, overflow="ellipsis") + label
        icon_label.apply_meta(meta)
        return icon_label
