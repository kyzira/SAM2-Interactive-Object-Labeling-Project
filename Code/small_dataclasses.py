from dataclasses import dataclass, field
import tkinter as tk
from sam2_class import Sam2Class
from frame_extraction import FrameExtraction

@dataclass
class Setup:
    config: dict
    frame_dir: str
    sam_model: Sam2Class
    frame_extraction : FrameExtraction
    damage_table_row: dict = field(default_factory=dict)

@dataclass
class ButtonState:
    button_name: str
    is_selected: bool
    is_visible: bool
    overlay_color: str
    selection_button: tk.Button = field(default=None)
    visibility_button: tk.Button = field(default=None)
