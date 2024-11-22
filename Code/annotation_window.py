import tkinter as tk
from PIL import Image, ImageTk
from image_view import ImageView

class AnnotationWindow:
    """
        This class handles displaying and interacting with the Annotation Window.
        In this window the given image will be shown, and if masks are provided from SAM, these will be drawn on top of the image.
        When clicked on the image the coordinates of the click and wether it was a right or left click are stored and forwarded to SAM. SAM will then provide a mask, which is drawn on top of the image.
        
        Workflow:
            - Left Click
                Adds a positive point to the clicked coordinates. A positive point dictates to SAM that the object you want to track is in the clicked position
            - Right Click
                Adds a negative point to the clicked coordinates. A negative point dictates to SAM that the object you want to track is definetly not in the clicked position
            - Backspace Key
                Removes last added point
            - Close Window
                Finishes the annotation process.
            - get_points_and_labels:
                This method can be called from outside this module. It will return a list of the clicked coordinates, a list wether those clicks were positive or negative points and the polygons for the current image.
                These lists can then be used to track the object throughout the whole video.
    """

    def __init__(self, img_view:ImageView, color:str):
        self.annotation_window = None
        self.canvas = None

        self.points = {
            "1" : [],
            "0" : []
        }

        self.polygons = []
        self.order_of_addition = []

        self.img_view = img_view
        self.color = color

        self.geometry_data = None
        self.window_maximized = False

        self.sam_model = None
        self.object_class_id = None
        self.frame_index = None

        self.image_id = None        # To store the image for it not to be garbage collected
        self.tk_image = None        # To store the image for it not to be garbage collected
        
        self.resized_width = None
        self.resized_height = None

    def init_window(self, window_geometry:dict):
        annotation_window = tk.Toplevel()
        annotation_window.title(f"Punkte hinzufügen")
        annotation_window.grab_set()

        if window_geometry.get("Maximized", False) == True:
            annotation_window.state("zoomed")
        elif window_geometry.get("Geometry"):
            annotation_window.geometry(window_geometry["Geometry"])
        else:
            annotation_window.geometry(f"{self.img_view.get_image().width}x{self.img_view.get_image().height}")  # Set initial window size to image size

        # Create a canvas
        self.canvas = tk.Canvas(annotation_window)
        self.canvas.pack()

        # Change image width when resizing
        annotation_window.bind('<Configure>', self.__on_resize)
        # Bind mouse click and key press events 
        self.canvas.bind('<Button-1>', self.__on_click)  
        self.canvas.bind('<Button-3>', self.__on_click)
        self.canvas.bind('<Key>', self.__on_key_press)
        self.canvas.focus_set()
        # Add a protocol to handle window close
        annotation_window.protocol("WM_DELETE_WINDOW", self.__on_close)

        # Better directly use self.annotation_window above instead of storing everything in a copy and setting it afterwards
        self.annotation_window = annotation_window
        self.__draw_image_on_canvas()

    def init_sam(self, frame_index, object_class_id, sam_model):
        self.frame_index = frame_index
        self.object_class_id = object_class_id
        self.sam_model = sam_model

    def get_points_and_labels(self):
        return self.points, self.polygons
    
    def get_geometry(self):
        # This returns the size and position of the annotation window
        return self.window_maximized, self.geometry_data
    
    # better "get_frame_index" to make clear it's about the frame
    def get_index(self):
        return self.frame_index

    def __on_resize(self, event):
        # Update canvas size to match window size
        self.resized_width = event.width
        self.resized_height = event.height
        self.canvas.config(width=self.resized_width, height=self.resized_height)
   
        self.__draw_image_on_canvas()

    def __on_close(self):
        # This function is called when the annotation window is closed
        if self.annotation_window.state() == "zoomed":
            self.window_maximized = True
        self.geometry_data = self.annotation_window.geometry()

    def __on_click(self, event):
        # The following comments are not needed, because the code is self explaining, they unnecessarily bloat the code.
        # If you think something is not clear, try to find variable names that are more self explaining. If you do not find
        # a good way, then you can use a comment.
        # Get the coordinates of the click
        x, y = event.x, event.y
        # Canvas size
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        # actual image size
        image_width, image_height = self.img_view.get_drawn_image().size

        # Clicked Coordinates in relation to actual image pixels
        image_x = int(image_width * (x / canvas_width))
        image_y = int(image_height * (y / canvas_height))

        # Use constant variables instead of comment for the two click events that are initialized in __init__ function:
        # self.LEFT_CLICK = 1
        # self.RIGHT_CLICK = 3
        if event.num == 1: # left click
            self.points["1"].append([image_x, image_y])
            self.order_of_addition.append(1)
        elif event.num == 3: # right click
            self.points["0"].append([image_x, image_y])
            self.order_of_addition.append(0)

        self.__create_propagated_image()

    def __on_key_press(self, event):
        # Remove last added point
        # Since identations make the code structure more unclear, you should always try to avoid larger code blocks with indents:
        # if event.keysym != "BackSpace":
        #    return
        # if len(self.order_of_addition) == 0:
        #    return
        # label = self.order_of_addition.pop()
        # ...
        if event.keysym == "BackSpace":
            if len(self.order_of_addition) == 0:
                return
            
            label = self.order_of_addition.pop()
            self.points[str(label)].pop()
            if len(self.order_of_addition) == 0:
                self.img_view.reset_drawn_image()
            else:
                self.__create_propagated_image()
            
            self.__draw_image_on_canvas()

    def __draw_image_on_canvas(self):
        image_to_display = self.img_view.get_drawn_image()

        if self.resized_width and self.resized_height:
            image_to_display = image_to_display.resize((self.resized_width, self.resized_height), Image.Resampling.LANCZOS)

        # Create a new PhotoImage to display
        self.tk_image = ImageTk.PhotoImage(image_to_display)
        
        # Use self explaining variable instead of comment (it explains by itself, that deleting it is necessary in this case):
        # is_canvas_empty = self.image_id is None
        # if not is_canvas_empty:
        #    self.canvas.delete(self.image_id)
        # If there's an existing image, delete it before displaying the new one
        if self.image_id is not None:
            self.canvas.delete(self.image_id)

        # Create a new image on the canvas
        self.image_id = self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)

    def __create_propagated_image(self):
        # Give the list of clicked points to Sam, get a mask back, convert the mask into polygons and then draw them
        if not self.points:
            return
        if not len(self.points["1"]) and not len(self.points["0"]):
            return
        
        masks = self.__propagate_image()  # Get the mask from your existing propagate method
        self.polygons = self.img_view.draw_and_convert_masks(masks, self.color)
        self.img_view.draw_points(self.points)
        
        self.__draw_image_on_canvas()

    def __propagate_image(self):
        # Prepare the structure and then send to sam

        points = []
        labels = []

        for key, value in self.points.items():
            for point in value:
                points.append(point)
                labels.append(key)


        points_labels_and_frame_index = {
            "Points" : points,
            "Labels" : labels,
            "Image Index" : self.frame_index
        }

        mask = self.sam_model.add_point(points_labels_and_frame_index, self.object_class_id)

        if len(mask) == 0:
            print("Error: Mask length == 0")

        return mask