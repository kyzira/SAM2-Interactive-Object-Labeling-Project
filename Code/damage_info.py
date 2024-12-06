
from dataclasses import dataclass, field

@dataclass
class DamageInfo:
    damage_name: str

    positive_point_coordinates: list[tuple] = field(init=False, default_factory=list)
    negative_point_coordinates: list[tuple] = field(init=False, default_factory=list)

    mask_polygon: list[int] = field(init=False, default_factory=list)

    is_start_of_intervall: bool = field(init=False, default=False)
    is_end_of_intervall: bool = field(init=False, default=False)

    is_shown: bool = field(init=False, default=True)
    is_selected: bool = field(init=False, default=False)

    def get_dict(self) -> dict:  

        damage_dict = {}

        if len(self.positive_point_coordinates) > 0 or len(self.negative_point_coordinates) > 0:
            damage_dict["Points"] = {
                            "1": self.positive_point_coordinates,
                            "0": self.negative_point_coordinates
                        }
        
        if len(self.mask_polygon) > 0:
            damage_dict["Mask Polygon"] = self.mask_polygon

        return damage_dict