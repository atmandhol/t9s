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
    name: str
    is_context: bool = False
    is_namespace: bool = False
    is_workload: bool = False
    is_deliverable: bool = False


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
            await node.add(label=f"{ctx}", data=ExplorerEntry(name=ctx, is_context=True))
        node.loaded = True
        await node.expand()
        self.refresh(layout=True)

    async def load_ns(self, node: TreeNode[ExplorerEntry]):
        ns_list = commons.get_ns_list(k8s_helper=k8s_helper, client=k8s_helper.core_clients[node.data.name])
        self.log(ns_list)
        if ns_list and isinstance(ns_list, list) and len(ns_list) > 0:
            for ns in ns_list:
                await node.add(label=f"{ns}", data=ExplorerEntry(name=ns, is_namespace=True))
        node.loaded = True
        await node.expand()
        self.refresh(layout=True)

    async def handle_tree_click(self, message: TreeClick[ExplorerEntry]) -> None:
        if message.node.data.is_context:
            if not message.node.loaded:
                await self.load_ns(message.node)
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
            node.data.is_context,
            node.data.is_namespace,
            node.data.is_workload,
            node.data.is_deliverable,
            node.expanded,
            node.is_cursor,
            node.id == self.hover_node,
            self.has_focus,
        )

    @lru_cache(maxsize=1024 * 32)
    def render_tree_label(
        self,
        node: TreeNode[ExplorerEntry],
        is_context: bool,
        is_namespace: bool,
        is_workload: bool,
        is_deliverable: bool,
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
        if is_context:
            label.stylize("#ebae3d")
            icon = "💻"
        elif is_namespace:
            label.stylize("#39cbf7")
            icon = "📂" if expanded else "📁"
        else:
            label.stylize("white")
            icon = ""
            # label.highlight_regex(r"\..*$", "green")

        if label.plain.startswith("."):
            label.stylize("dim")

        if is_cursor and has_focus:
            label.stylize("reverse")

        icon_label = Text(f"{icon} ", no_wrap=True, overflow="ellipsis") + label
        icon_label.apply_meta(meta)
        return icon_label
