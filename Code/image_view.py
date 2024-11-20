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

        self.__borders = {"Marked": False}
        self.__data = {}

    def get_image(self):
        return self.__image.copy()
    
    def get_drawn_image(self):
        return self.__drawn_image.copy()
    
    def get_image_path(self):
        return self.__image_path

    def get_image_name(self):
        return os.path.basename(self.__image_path)
    
    def get_frame_num(self):
        return int(os.path.basename(self.__image_path).split(".")[0])
    
    def get_data(self):
        return self.__data.copy()
    
    def get_image_size(self):
        return self.__image.size

    def get_border_value(self, observation: str, border = None):
        if border:
            return self.__borders[observation].get(border)
        else:
            return self.__borders.get(observation)

    def set_border(self, observation: str, border: str, value: bool):
        if border == "Marked":
            self.__borders[border] = value

        if observation not in self.__borders.keys():
            self.__borders[observation] = {
                "Border Left": False,
                "Border Right": False,
                "First Frame": False
            }

        if observation not in self.__data.keys():
            self.__data[observation] = {}

        self.__borders[observation][border] = value

    def set_data(self, data):
        self.__data = data

    def add_to_data(self, observation, observation_data):
        self.__data[observation] = observation_data

    def add_to_observation(self, observation, type, data):
        # For Example add to BBA 0, "Mask Polygon" following Polygon
        if observation not in self.__data:
            self.__data[observation] = {} 
        self.__data[observation][type] = data

    def draw(self, button_states: dict, intervals: list):
        self.reset_drawn_image()

        shown_observation = []
        selected_observation = None

        num_of_intervall = 0
        frame_num = self.get_frame_num()
        for num, (start, end) in enumerate(intervals):
            if start <= frame_num <= end:
                num_of_intervall = num

        for observation, values in button_states.items():
            if values.get("Visible"):
                shown_observation.append(observation)
            if values.get("Selected"):
                selected_observation = observation

        for observation, observation_data in self.__data.items():
            if observation not in shown_observation:
                continue

            if observation_data.get("Mask Polygon"):
                if len(observation_data.get("Mask Polygon")) > 0:
                    self.draw_polygon(polygons=observation_data["Mask Polygon"], color=button_states[observation].get("Color"))
            
            if self.__borders.get("Marked"):
                self.draw_border(side="top", color="red_full")
            
            if observation != selected_observation:
                continue 

            if observation_data.get("Points"):
                self.draw_points(points_dict=observation_data["Points"])

            if observation not in self.__borders.keys():
                continue

            if self.__borders[observation].get("Border Left"):
                self.draw_border(side="left", num_of_intervall=num_of_intervall)
            if self.__borders[observation].get("Border Right"):
                self.draw_border(side="right", num_of_intervall=num_of_intervall)
            if self.__borders[observation].get("First Frame"):
                self.draw_border(side="all", color="yellow_full", thickness=15)

    def draw_points(self, points_dict:dict, radius=5):
        base_img = self.__drawn_image
        overlay = Image.new("RGBA", self.img_size, (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)

        pos_points = points_dict.get("1", [])
        neg_points = points_dict.get("0", [])

        for point in pos_points:
            x, y = point
            overlay_draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=self.__get_color("green_full"))
        
        for point in neg_points:
            x, y = point
            overlay_draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=self.__get_color("red_full"))

        base_img = Image.alpha_composite(base_img.convert("RGBA"), overlay)
        self.__drawn_image = base_img

    def draw_border(self, side="all", color=None, num_of_intervall=0, thickness=20):
        base_img = self.__drawn_image
        if color:
            color = self.__get_color(color)
        elif num_of_intervall >= 0:
            color = self.__get_split_color(num_of_intervall)
            
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
        
        # Ensure polygons is a list of lists of tuples
        if polygons:
            for polygon in polygons:
                # Here, we check if the polygon is already in tuple format
                if isinstance(polygon[0], tuple):
                    polygon_tuples = polygon
                else:
                    # Convert the polygon points into tuples if they are not already
                    polygon_tuples = [tuple(point) for point in polygon]

                if len(polygon_tuples) > 3:  # Draw the polygon only if it has more than 3 points
                    overlay_draw.polygon(polygon_tuples, outline=color[:3], fill=color)

        # Composite the overlay onto the base image
        base_img = Image.alpha_composite(base_img.convert("RGBA"), overlay)
        self.__drawn_image = base_img

    def draw_and_convert_masks(self, mask, color="red") -> list:
        polygons = []
        self.reset_drawn_image()

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

        self.draw_polygon(polygons, color)
        return polygons
    
    def pop_observation(self, observation):
        if observation in self.__data:
            return self.__data.pop(observation)


    def reset_drawn_image(self):
        self.__drawn_image = self.__image.copy()

    def close_image_view(self):
        self.__data = None
        self.__image = None
        self.__drawn_image = None
        self.img_size = None
        self.__borders = None

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
    
    def __get_split_color(self, num):
        color_map = [
            (0, 0, 64, 255),         # dark navy (darker version of navy)
            (65, 105, 225, 255),     # mediumblue (darker version of lightblue)
            (34, 139, 34, 255),      # forestgreen (darker version of lightgreen)
            (0, 139, 139, 255),      # darkcyan (darker version of cyan)
            (75, 0, 130, 255),       # indigo (darker version of blueviolet)
            (139, 0, 139, 255)       # darkviolet (darker version of mediumvioletred)
        ]
        return color_map[num%6]
