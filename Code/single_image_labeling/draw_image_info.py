from PIL import Image, ImageDraw
from image_info import ImageInfo

class DrawImageInfo:
    """
    This class draws masks, points and borders.
    """
    def __init__(self, image_info: ImageInfo):
        try:
            image_info.reset_drawn_image()
            self.__drawn_image = image_info.drawn_image
            for color_index, damage_info in enumerate(image_info.data_coordinates):

                self.__draw_polygon(damage_info.mask_polygon, color_index)
                self.__draw_points(damage_info.positive_point_coordinates, damage_info.negative_point_coordinates)

            image_info.drawn_image = self.__drawn_image
            
        except Exception as e:
            print(f"Error in drawing: {e}")

    def __draw_points(self, pos_points, neg_points, radius=5):
        base_img = self.__drawn_image
        overlay = Image.new("RGBA", base_img.size, (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)

        for point in pos_points:
            x, y = point
            overlay_draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=self.__get_color("green_full"))

        for point in neg_points:
            x, y = point
            overlay_draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=self.__get_color("red_full"))

        base_img = base_img.convert("RGBA")
        base_img = Image.alpha_composite(base_img, overlay)
        self.__drawn_image = base_img

    def __draw_polygon(self, polygons, color_index=0):
        color = self.__get_color(color_index=color_index)

        base_img = self.__drawn_image

        overlay = Image.new("RGBA", base_img.size, (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay, "RGBA")

        if polygons:
            for polygon in polygons:
                polygon_tuples = [tuple(point) for point in polygon]
                if len(polygon_tuples) > 3:
                    overlay_draw.polygon(polygon_tuples, outline=color[:3], fill=color)

        base_img = base_img.convert("RGBA")
        base_img = Image.alpha_composite(base_img, overlay)
        self.__drawn_image = base_img



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
