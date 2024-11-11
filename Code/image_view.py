from PIL import Image, ImageDraw
import os
import cv2
import numpy as np

class ImageView:
    def __init__(self, image_path : str) -> None:
        self.__image_path = image_path
        temp_image = Image.open(self.__image_path)
        self.__image = temp_image.copy()
        temp_image.close()
        self.__drawn_image = self.__image.copy()
        self.img_size = self.__image.size

    def get_image(self):
        return self.__image.copy()
    
    def get_drawn_image(self):
        return self.__drawn_image.copy()
    
    def get_image_path(self):
        return self.__image_path

    def get_image_name(self):
        return os.path.basename(self.__image_path)
    
    def get_frame_num(self):
        return os.path.basename(self.__image_path).split(".")[0]

    def reset_drawn_image(self):
        self.__drawn_image = self.__image.copy()

    def draw_points(self, points_dict:dict, radius=5):
        base_img = self.__drawn_image
        overlay = Image.new("RGBA", self.img_size, (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)

        pos_points = points_dict.get("1")
        neg_points = points_dict.get("0")

        for point in pos_points:
            x, y = point
            overlay_draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=self.__get_color("green_full"))
        
        for point in neg_points:
            x, y = point
            overlay_draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=self.__get_color("red_full"))

        base_img = Image.alpha_composite(base_img.convert("RGBA"), overlay)
        self.__drawn_image = base_img

    def draw_border(self, side="all", color="red", thickness=5):
        base_img = self.__drawn_image
        color = self.__get_color(color)
        img_width, img_height = self.img_size

        # Ensure thickness is not larger than image size
        thickness = min(thickness, img_width, img_height)

        # Create overlay only once
        overlay = Image.new("RGBA", self.img_size, (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)

        # Define the borders based on side
        borders = {
            "all": [
                [(0, 0), (img_width, thickness)],  # top
                [(0, 0), (thickness, img_height)],  # left
                [(img_width - thickness, 0), (img_width, img_height)],  # right
                [(0, img_height - thickness), (img_width, img_height)]  # bottom
            ],
            "top": [
                [(0, 0), (img_width, thickness)]  # top
            ],
            "bottom": [
                [(0, img_height - thickness), (img_width, img_height)]  # bottom
            ],
            "left": [
                [(0, 0), (thickness, img_height)]  # left
            ],
            "right": [
                [(img_width - thickness, 0), (img_width, img_height)]  # right
            ]
        }

        # Draw the selected borders
        for rect in borders.get(side):
            overlay_draw.rectangle(rect, fill=color)

        # Composite the overlay onto the base image
        base_img = Image.alpha_composite(base_img.convert("RGBA"), overlay)
        self.__drawn_image = base_img


    def draw_polygon(self, polygons, color="red"):
        color = self.__get_color(color)
        base_img = self.__drawn_image

        overlay = Image.new("RGBA", self.img_size, (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay, "RGBA")
        if polygons:
            for polygon in polygons:
                polygon_tuples = [tuple(point) for point in polygon]
                if len(polygon_tuples) > 3:
                    overlay_draw.polygon(polygon_tuples, outline=color[:3], fill=color)

        base_img = Image.alpha_composite(base_img.convert("RGBA"), overlay)
        self.__drawn_image = base_img

    def draw_and_convert_masks(self, mask, color="red") -> list:
        polygons = []

        mask = np.squeeze(mask)  # Squeeze to remove dimensions of size 1
        
        # Extract contours using OpenCV
        contours, _ = cv2.findContours(mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            # Simplify the contour using approxPolyDP
            epsilon = 0.0005 * cv2.arcLength(contour, True)  # Adjust epsilon for simplification level
            simplified_contour = cv2.approxPolyDP(contour, epsilon, True)

            # Convert contour points to a list of tuples
            simplified_contour = [(int(point[0][0]), int(point[0][1])) for point in simplified_contour]
            
            polygons.append(simplified_contour)

        self.draw_poylgon(polygons, color)

        return polygons



    def __get_color(self, color="red"):
        color_map = {
            "red": (255, 0, 0, 100),         # Red with transparency
            "blue": (0, 0, 255, 100),        # Blue with transparency
            "green": (0, 255, 0, 100),       # Green with transparency
            "yellow": (255, 255, 0, 100),    # Yellow with transparency
            "magenta": (255, 0, 255, 100),   # Magenta with transparency
            "red_full": (255, 0, 0, 255),        # Red without transparency
            "blue_full": (0, 0, 255, 255),       # Blue without transparency
            "green_full": (0, 255, 0, 255),      # Green without transparency
            "yellow_full": (255, 255, 0, 255),   # Yellow without transparency
            "magenta_full": (255, 0, 255, 255)   # Magenta without transparency
        }

        return color_map.get(color)  # Default to red if the color is not found