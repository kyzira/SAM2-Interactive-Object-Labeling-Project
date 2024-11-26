from PIL import Image, ImageDraw
from image_info import ImageInfo

class DrawImageInfo:
    """
    This class draws the overlays and masks saved in image info onto its saved image.
    """
    def draw(self, image_info: ImageInfo):
        try:
            image_info.reset_drawn_image()
            for damage_info in image_info.data_coordinates:
                if not damage_info.is_shown or not damage_info.is_in_intervall:
                    continue

                color_index = image_info.data_coordinates.index(damage_info)
                self.__draw_polygon(damage_info.mask_polygon, image_info.drawn_image, color_index)

                if not damage_info.is_selected:
                    continue

                self.__draw_points(damage_info.positive_point_coordinates, damage_info.negative_point_coordinates, image_info.drawn_image)
                if damage_info.is_start_of_intervall:
                    self.__draw_border(image_info.drawn_image, "left", num_of_intervall=color_index)
                if damage_info.is_end_of_intervall:
                    self.__draw_border(image_info.drawn_image, "right", num_of_intervall=color_index)

            if image_info.is_marked:
                self.__draw_border(image_info.drawn_image, "top", "red_full")

        except Exception as e:
            print(f"Error in drawing: {e}")

    def __draw_points(self, pos_points, neg_points, drawn_image, radius=5):
        overlay = Image.new("RGBA", drawn_image.size, (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)

        for point in pos_points:
            x, y = point
            overlay_draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=self.__get_color("green_full"))

        for point in neg_points:
            x, y = point
            overlay_draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=self.__get_color("red_full"))

        drawn_image.paste(Image.alpha_composite(drawn_image.convert("RGBA"), overlay))

    def __draw_polygon(self, polygons, drawn_image, color_index=0):
        color = self.__get_color(color_index=color_index)
        overlay = Image.new("RGBA", drawn_image.size, (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay, "RGBA")

        if polygons:
            for polygon in polygons:
                polygon_tuples = [tuple(point) for point in polygon]
                if len(polygon_tuples) > 3:
                    overlay_draw.polygon(polygon_tuples, outline=color[:3], fill=color)

        drawn_image.paste(Image.alpha_composite(drawn_image.convert("RGBA"), overlay))

    def __draw_border(self, base_img, side="all", color=None, num_of_intervall=0, thickness=20):
        if color is None:
            color = self.__get_split_color(num_of_intervall)
        img_width, img_height = base_img.size
        thickness = min(thickness, img_width, img_height)

        overlay = Image.new("RGBA", base_img.size, (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)

        borders = {
            "all": [
                [(0, 0), (img_width, thickness)],  
                [(0, 0), (thickness, img_height)],  
                [(img_width - thickness, 0), (img_width, img_height)],  
                [(0, img_height - thickness), (img_width, img_height)]  
            ],
            "top": [[(0, 0), (img_width, thickness)]],
            "bottom": [[(0, img_height - thickness), (img_width, img_height)]],
            "left": [[(0, 0), (thickness, img_height)]],
            "right": [[(img_width - thickness, 0), (img_width, img_height)]],
        }

        for rect in borders.get(side, []):
            overlay_draw.rectangle(rect, fill=color)

        base_img.paste(Image.alpha_composite(base_img.convert("RGBA"), overlay))

    def __get_color(self, color=None, color_index=None) -> tuple:
        color_map = {
            "red": (255, 0, 0, 100),
            "blue": (0, 0, 255, 100),
            "green": (0, 255, 0, 100),
            "yellow": (255, 255, 0, 100),
            "magenta": (255, 0, 255, 100),
            "red_full": (255, 0, 0, 255),
            "blue_full": (0, 0, 255, 255),
            "green_full": (0, 255, 0, 255),
            "yellow_full": (255, 255, 0, 255),
            "magenta_full": (255, 0, 255, 255),
        }
        if color:
            return color_map.get(color)
        if color_index is not None:
            color_keys = list(color_map.keys())
            return color_map[color_keys[color_index % len(color_keys)]]
        raise ValueError("Either 'color' or 'color_index' must be provided.")

    def __get_split_color(self, num):
        color_map = [
            (0, 0, 64, 255),         
            (65, 105, 225, 255),     
            (34, 139, 34, 255),      
            (0, 139, 139, 255),      
            (75, 0, 130, 255),       
            (139, 0, 139, 255),      
        ]
        return color_map[num % len(color_map)]