from rich.text import Text
from textual.widgets import Footer


class T9s_Footer(Footer):
    def __init__(self):
        super().__init__()

    def make_key_text(self) -> Text:
        """Create text containing all the keys."""
        text = Text(
            style="bold black on #69b4ff",
            no_wrap=True,
            overflow="ellipsis",
            justify="left",
            end="",
        )
        for binding in self.app.bindings.shown_keys:
            key_display = binding.key.upper() if binding.key_display is None else binding.key_display
            hovered = self.highlight_key == binding.key
            key_text = Text.assemble(
                (f" {key_display} ", "reverse" if hovered else "default on default"),
                f" {binding.description} ",
                meta={"@click": f"app.press('{binding.key}')", "key": binding.key},
            )
            text.append_text(key_text)
        return text
