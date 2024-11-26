from dataclasses import dataclass, field
from PIL import Image
from typing import Optional
import os
import re
from damage_info import DamageInfo


@dataclass
class ImageInfo:
    """
    Dataclass to store information about a frame, including the original image,
    its overlays, and associated data for saving as JSON.
    """
    image_path: str
    image_index: int = field(init=False, default=None)
    image: Optional[Image.Image] = field(init=False, default=None)
    drawn_image: Optional[Image.Image] = field(init=False, default=None)
    is_marked: bool = field(init=False, default=None)
    data_coordinates: list[DamageInfo] = field(default_factory=list)
    

    @property
    def image_name(self) -> str:
        return os.path.basename(self.image_path) if self.image_path else ""

    @property
    def frame_num(self) -> int:
        if self.image_path:
            match = re.search(r'\d+', os.path.basename(self.image_path))
            return int(match.group()) if match else -1
        return -1

    @property
    def img_size(self) -> tuple:
        return self.image.size if self.image else (-1, -1)

    def load_image(self):
        try:
            if self.image_path:
                temp_image = Image.open(self.image_path)
                self.image = temp_image.copy()
                self.drawn_image = temp_image.copy()
                temp_image.close()
            else:
                raise ValueError("Image path must be set before loading an image.")
        except FileNotFoundError:
            raise FileNotFoundError(f"Image file not found: {self.image_path}")

    def reset_drawn_image(self):
        if self.image:
            self.drawn_image = self.image.copy()
        else:
            raise ValueError("Original image is not loaded.")

    def set_damage_info_attribute(self, observation: str, attribute: str, value) -> bool:
        """
        Sets a boolean attribute (e.g., 'start_intervall', 'end_intervall', 'is_shown', 'is_selected')
        on the DamageInfo object corresponding to the given observation name.
        """
        for damage_info in self.data_coordinates:
            if damage_info.damage_name == observation:
                if hasattr(damage_info, attribute):
                    setattr(damage_info, attribute, value)
                    return True
                else:
                    print(f"Error: Attribute '{attribute}' not found in DamageInfo.")
                    return False

        print("Error: Observation not found.")
        return False

    def add_new_observation(self, observation: str) -> bool:
        for damage_info in self.data_coordinates:
            if observation == damage_info.damage_name:
                print("Error: Observation already exists!")
                return False

        self.data_coordinates.append(DamageInfo(observation))
        return True

    def remove_observation(self, observation: str) -> bool:
        """Removes Observation from data_coordinates and returns True if successful"""
        for damage_info in self.data_coordinates:
            if observation == damage_info.damage_name:
                self.data_coordinates.remove(damage_info)
                return True

        print("Error: Observation not added yet!")
        return False

    def get_dict(self) -> dict:
        frame_info_dict = {}

        for damage_info in self.data_coordinates:
            frame_info_dict.update(damage_info.get_dict())

        return frame_info_dict