from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class NoteType(Enum):
    TEXT = "text"
    LIST = "list"


class NoteColor(Enum):
    DEFAULT = "DEFAULT"
    RED = "RED"
    ORANGE = "ORANGE"
    YELLOW = "YELLOW"
    GREEN = "GREEN"
    TEAL = "TEAL"
    BLUE = "BLUE"
    CERULEAN = "CERULEAN"
    PURPLE = "PURPLE"
    PINK = "PINK"
    BROWN = "BROWN"
    GRAY = "GRAY"


COLOR_HEX = {
    NoteColor.DEFAULT: "#FFFFFF",
    NoteColor.RED: "#F28B82",
    NoteColor.ORANGE: "#FBBC04",
    NoteColor.YELLOW: "#FFF475",
    NoteColor.GREEN: "#CCFF90",
    NoteColor.TEAL: "#A8F0E4",
    NoteColor.BLUE: "#CBF0F8",
    NoteColor.CERULEAN: "#AECBFA",
    NoteColor.PURPLE: "#D7AEFB",
    NoteColor.PINK: "#FDCFE8",
    NoteColor.BROWN: "#E6C9A8",
    NoteColor.GRAY: "#E8EAED",
}


@dataclass
class ChecklistItem:
    text: str
    checked: bool


@dataclass
class NoteModel:
    id: str
    title: str
    text: str
    note_type: NoteType
    pinned: bool
    color: NoteColor
    checklist_items: list[ChecklistItem] = field(default_factory=list)
    image_url: str | None = None
    updated: datetime | None = None
    created: datetime | None = None

    @property
    def color_hex(self) -> str:
        return COLOR_HEX.get(self.color, "#FFFFFF")

    @property
    def preview(self) -> str:
        if self.note_type == NoteType.LIST:
            lines = [f"{'☑' if i.checked else '☐'} {i.text}" for i in self.checklist_items[:3]]
            return "\n".join(lines)
        lines = self.text.strip().splitlines()
        return "\n".join(lines[:2])

    @property
    def content(self) -> str:
        if self.note_type == NoteType.LIST:
            return "\n".join(
                f"{'☑' if i.checked else '☐'} {i.text}" for i in self.checklist_items
            )
        return self.text.strip()
