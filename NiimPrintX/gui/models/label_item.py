from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from enum import Enum


class ItemType(Enum):
    TEXT = "text"
    IMAGE = "image"


@dataclass
class LabelItem:
    x: float = 0
    y: float = 0
    width: float = 0
    height: float = 0
    rotation: float = 0
    data: Dict[str, Any] = field(default_factory=dict)
    item_type: Optional[ItemType] = None

    def to_dict(self) -> dict:
        return {
            'item_type': self.item_type.value if self.item_type else None,
            'x': self.x,
            'y': self.y,
            'width': self.width,
            'height': self.height,
            'rotation': self.rotation,
            'data': self.data
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'LabelItem':
        return cls(
            item_type=ItemType(data['item_type']),
            x=data.get('x', 0),
            y=data.get('y', 0),
            width=data.get('width', 0),
            height=data.get('height', 0),
            rotation=data.get('rotation', 0),
            data=data.get('data', {})
        )


@dataclass
class TextItem(LabelItem):
    content: str = ""
    font_family: str = "Arial"
    font_size: int = 16
    font_weight: str = "normal"
    font_slant: str = "roman"
    underline: bool = False
    kerning: float = 0.0

    def __post_init__(self):
        self.item_type = ItemType.TEXT

    def to_dict(self) -> dict:
        d = super().to_dict()
        d.update({
            'content': self.content,
            'font_family': self.font_family,
            'font_size': self.font_size,
            'font_weight': self.font_weight,
            'font_slant': self.font_slant,
            'underline': self.underline,
            'kerning': self.kerning,
        })
        return d

    @classmethod
    def from_dict(cls, data: dict) -> 'TextItem':
        return cls(
            item_type=ItemType.TEXT,
            x=data.get('x', 0),
            y=data.get('y', 0),
            width=data.get('width', 0),
            height=data.get('height', 0),
            rotation=data.get('rotation', 0),
            data=data.get('data', {}),
            content=data.get('content', ''),
            font_family=data.get('font_family', 'Arial'),
            font_size=data.get('font_size', 16),
            font_weight=data.get('font_weight', 'normal'),
            font_slant=data.get('font_slant', 'roman'),
            underline=data.get('underline', False),
            kerning=data.get('kerning', 0.0),
        )

    def get_font_props(self) -> dict:
        return {
            'family': self.font_family,
            'size': self.font_size,
            'weight': self.font_weight,
            'slant': self.font_slant,
            'underline': self.underline,
            'kerning': self.kerning,
        }


@dataclass
class ImageItem(LabelItem):
    image_path: str = ""
    image_data: Optional[bytes] = None

    def __post_init__(self):
        self.item_type = ItemType.IMAGE

    def to_dict(self) -> dict:
        d = super().to_dict()
        d.update({
            'image_path': self.image_path,
        })
        return d

    @classmethod
    def from_dict(cls, data: dict) -> 'ImageItem':
        return cls(
            item_type=ItemType.IMAGE,
            x=data.get('x', 0),
            y=data.get('y', 0),
            width=data.get('width', 0),
            height=data.get('height', 0),
            rotation=data.get('rotation', 0),
            data=data.get('data', {}),
            image_path=data.get('image_path', ''),
        )
