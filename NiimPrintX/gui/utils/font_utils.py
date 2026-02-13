from typing import Dict, List
from PyQt6.QtGui import QFontDatabase, QFont


def get_system_fonts() -> Dict[str, Dict[str, List[str]]]:
    families = QFontDatabase.families()
    
    fonts = {}
    for family in families:
        styles = QFontDatabase.styles(family)
        fonts[family] = {
            "fonts": {
                "Regular": {
                    "name": family,
                    "variants": list(styles),
                    "main": "Regular" in styles or len(styles) == 1
                }
            }
        }
    
    return fonts


def get_font_list() -> List[str]:
    return sorted(QFontDatabase.families())


def get_styles_for_font(family: str) -> List[str]:
    return list(QFontDatabase.styles(family))
