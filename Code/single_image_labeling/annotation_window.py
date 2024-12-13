import tkinter as tk
from PIL import Image, ImageTk
from image_info import ImageInfo
from draw_image_info import DrawImageInfo
import cv2
import numpy as np

class AnnotationWindow:
    """
        This Class handles displaying and interacting with the Annotation Window.
        In this Window the given Image will be shown, and if masks are provided from SAM, these will be drawn on top of the image.
        When clicked on the image the Coordinates of the click and wether it was a right or left click are stored, and forwarded to sam. Sam will then provide a mask, which is drawn on top of the image.
        
        Workflow:
            - Left Click
                Adds a positive Point to the clicked coordinates. A positive Point dictates to SAM that the Object you want to track is in the clicked position
            - Right Click
                Adds a negative Point to the clicked coordinates. A negative Point dictates to SAM that the Object you want to track is definetly not in the clicked position
            - Backspace Key
                Removes last added Point
            - Close Window
                Finishes the annotation process.
            - get_points_and_labels:
                This method can be called from outside this module. It will return a list of the clicked coordinates, a list wether those clicks were positive or negative points and the polygons for the current image.
                These lists can then be used to track the object throughout the whole video.
    """

    def __init__(self):
        self.annotation_window = None
        self.canvas = None

        self.points = {
            "1" : [],
            "0" : []
        }

        self.polygons = []
        self.order_of_addition = []

        self.image_info = None
        self.color = None

        self.geometry_data = None
        self.is_maximized = False


        self.sam_model = None
        self.object_class_id = None
        self.frame_index = None

        self.image_id = None        # To Store the image for it not to be garbage collected
        self.tk_image = None        # To Store the image for it not to be garbage collected
        
        self.resized_width = None
        self.resized_height = None

        self.__left_click = '<Button-1>'
        self.__right_click = '<Button-3>'

        self.is_set = {
            "Settings" : False,
            "Image Info" : False,
            "Segmenter" : False
        }


    def set_settings(self, geometry_data = None, is_maximized = False):
        self.geometry_data = geometry_data
        self.is_maximized = is_maximized
        self.is_set["Settings"] = True

    def set_image_info(self, image_info: ImageInfo):
        if image_info is None:
            print("Error: Image Info is None!")
            return
        
        self.image_info = image_info

        for i, damage_info in enumerate(self.image_info.data_coordinates):
            if damage_info.is_selected == True:
                self.object_class_id = i
                self.color = self.__get_color(color_index=i)

                self.is_set["Image Info"] = True
                return
        
        print("Error: No Damage in Image Info is_selected!")
        print("Using arbitrary Value: 0")
        self.object_class_id = 0
        self.color = self.__get_color(color_index=0)

    def set_segmenter(self, sam_model):
        """
        Args:
            sam_model: Loaded SAM2 Model
            frame_index: Index in relation to loaded Images, !not frame number!
        """
        
        if sam_model is None:
            print("Error: SAM2 is None!")
            return
        
        self.sam_model = sam_model
        self.is_set["Segmenter"] = True

    
    def open(self):
        self.__create_window()
        self.__draw_image_on_canvas()
        self.annotation_window.protocol("WM_DELETE_WINDOW", self.__on_close)
        self.annotation_window.mainloop()

    def __create_window(self):
        self.annotation_window = tk.Toplevel()
        self.annotation_window.title(f"Punkte hinzufügen")
        self.annotation_window.grab_set()

        if self.is_maximized:
            self.annotation_window.state("zoomed")
        elif self.geometry_data:
            self.annotation_window.geometry(self.geometry_data)
        else:
            self.annotation_window.geometry(f"{self.image_info.drawn_image.width}x{self.image_info.drawn_image.height}")  # Set initial window size to image size

        # Create a canvas
        self.canvas = tk.Canvas(self.annotation_window)
        self.canvas.pack()

        # Change image width when resizing
        self.annotation_window.bind('<Configure>', self.__on_resize)
        # Bind mouse click and key press events 
        self.canvas.bind(self.__left_click, self.__on_click)  
        self.canvas.bind(self.__right_click, self.__on_click)
        self.canvas.bind('<Key>', self.__on_key_press)
        self.canvas.focus_set()

    def __on_resize(self, event):
        # Update canvas size to match window size
        self.resized_width = event.width
        self.resized_height = event.height
        self.canvas.config(width=self.resized_width, height=self.resized_height)
   
        self.__draw_image_on_canvas()

    def __on_close(self):
        # Prepare geometry data
        if self.annotation_window.state() == "zoomed":
            self.is_maximized = True
        self.geometry_data = self.annotation_window.geometry()

        if len(self.points.get("1", [])) == 0 and len(self.points.get("0", [])) == 0:
            self.sam_model.reset_predictor_state()
        
        if self.annotation_window:
            self.annotation_window.quit()  # Ends the mainloop
            self.annotation_window.destroy()  # Destroys the window

    def __on_click(self, event):
        # Get the coordinates of the click
        x, y = event.x, event.y
        # Canvas size
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        # actual image size
        image_width, image_height = self.image_info.img_size

        # Clicked Coordinates in relation to actual image pixels
        image_x = int(image_width * (x / canvas_width))
        image_y = int(image_height * (y / canvas_height))

        if event.num == 1:  # Left click
            self.points["1"].append([image_x, image_y])
            self.order_of_addition.append(1)
        elif event.num == 3:  # Right click
            self.points["0"].append([image_x, image_y])
            self.order_of_addition.append(0)
        self.__create_segmented_image()

        self.__draw_image_on_canvas()


    def __on_key_press(self, event):
        # Remove last added Point
        if event.keysym != "BackSpace":
            return
        
        if len(self.order_of_addition) == 0:
            return
        
        label = self.order_of_addition.pop()
        self.points[str(label)].pop()
        if len(self.order_of_addition) == 0:
            self.image_info.reset_drawn_image()
        else:
            self.__create_segmented_image()
        
        self.__draw_image_on_canvas()

    def __draw_image_on_canvas(self):
        image_to_display = self.image_info.drawn_image.copy()

        if self.resized_width and self.resized_height:
            image_to_display = image_to_display.resize((self.resized_width, self.resized_height), Image.Resampling.LANCZOS)

        # Create a new PhotoImage to display
        self.tk_image = ImageTk.PhotoImage(image_to_display)
        
        # If there's an existing image, delete it before displaying the new one
        if self.image_id is not None:
            self.canvas.delete(self.image_id)

        # Create a new image on the canvas
        self.image_id = self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)

    def __create_segmented_image(self):
        # Give the list of clicked points to Sam, get a mask back, convert the mask into polygons and then draw them
        if not self.points:
            return
        if not len(self.points["1"]) and not len(self.points["0"]):
            return
        
        self.polygons = self.__segment_image()  # Get the mask from your existing propagate method
        
        self.image_info.data_coordinates[self.object_class_id].positive_point_coordinates = self.points.get("1")
        self.image_info.data_coordinates[self.object_class_id].negative_point_coordinates = self.points.get("0")
        self.image_info.data_coordinates[self.object_class_id].mask_polygon = self.polygons
        DrawImageInfo(self.image_info)  
        self.__draw_image_on_canvas()

    def __segment_image(self):
        # Prepare the structure and then send to sam

        try:
            self.image_info.data_coordinates[self.object_class_id].mask_polygon = self.polygons
            self.image_info.data_coordinates[self.object_class_id].positive_point_coordinates = self.points["1"]
            self.image_info.data_coordinates[self.object_class_id].negative_point_coordinates = self.points["0"]
        except Exception as e:
            print(f"Image info: {self.image_info}, object class id: {self.object_class_id}\nError: {e}")
            return

        masks, scores = self.sam_model.add_points(self.image_info)

        if len(masks) == 0:
            print("Error: Mask length == 0")
            return

        polygons = []
        mask = np.squeeze(masks)  # Squeeze to remove dimensions of size 1
        
        # Extract contours using OpenCV
        contours, _ = cv2.findContours(mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            # Simplify the contour using approxPolyDP
            epsilon = 0.0005 * cv2.arcLength(contour, True)  # Adjust epsilon for simplification level
            simplified_contour = cv2.approxPolyDP(contour, epsilon, True)

            # Convert contour points to a list of tuples
            simplified_contour = [(int(point[0][0]), int(point[0][1])) for point in simplified_contour]
            polygons.append(simplified_contour)
        return polygons
    

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