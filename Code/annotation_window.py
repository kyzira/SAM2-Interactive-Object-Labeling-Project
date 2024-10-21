import numpy as np
import matplotlib.pyplot as plt
import tkinter as tk
from PIL import Image, ImageTk, ImageDraw
import cv2

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

    def __init__(self, annotation_window: tk.Toplevel, annotation_window_geomertry, img: Image, img_index: int, polygon_list, object_class_id: int, sam2):
        """
            annotation_window:
                This is a tkinter window class. it is used to add a canvas to it and display the image and register where on it it was clicked.
            img:
                This is the image to be displayed, opened as a PIL.Image
            img_index:
                This is the Index of the Image in relation to SAMs Images. For example, if this is the 2. Image which is displayed in sam, then the Index will be 2
            Object_class_id:
                This is the ID belonging to the to be tracked object
        """
        if not annotation_window:
            print("Error: annotation window is not set")
            return
        if not img:
            print("Error: Image not set")
            return
        if img_index == None:
            print("Error: Image Index not set")
            return
        if object_class_id == None:
            print("Error: Object Class ID not set")
            return    
        if not sam2:
            print("Error: SAM not set")   
        
        self.annotation_window = annotation_window

        self.points = []
        self.labels = []

        if len(polygon_list)>0:
            print("Existing Polygons found!")
            self.polygons = polygon_list
        else:
            self.polygons = []

        self.geometry_data = None
        self.window_maximized = False

        self.sam2 = sam2
        self.object_class_id = object_class_id
        self.img_index = img_index
        self.original_image = img  # Store the original image
        
        # Store the shown image
        self.image = img.copy()
        
        self.resized_width = None
        self.resized_height = None

        # Create a canvas
        self.canvas = tk.Canvas(self.annotation_window)
        
        if annotation_window_geomertry["Maximized"] == True:
            self.annotation_window.state("zoomed")

        elif annotation_window_geomertry["Geometry"]:
            annotation_window.geometry(annotation_window_geomertry["Geometry"])

        else:
            annotation_window.geometry(f"{img.width}x{img.height}")  # Set initial window size to image size

        self.canvas.pack()

        # Display the image on the canvas
        self.image_id = None # ToDo: change to image_exists = False

        if len(self.polygons)>0:
            self.__draw_initial_polygons()
        else:
            self.__display_image(self.image)

        # Change image width when resizing
        self.annotation_window.bind('<Configure>', self.__on_resize)

        # Bind mouse click and key press events 
        self.canvas.bind('<Button-1>', self.__on_click)  
        self.canvas.bind('<Button-3>', self.__on_click)
        self.canvas.bind('<Key>', self.__on_key_press)

        self.canvas.focus_set()

        # Add a protocol to handle window close
        self.annotation_window.protocol("WM_DELETE_WINDOW", self.__on_close)

    def get_points_and_labels(self):
        return self.points, self.labels, self.polygons
    
    def get_geometry(self):
        # This returns the size and position of the annotation window
        return self.window_maximized, self.geometry_data


    def __on_resize(self, event):
        # Update canvas size to match window size
        new_width = event.width
        new_height = event.height
        
        self.canvas.config(width=new_width, height=new_height)

        resized_image = self.original_image.resize((new_width, new_height), Image.LANCZOS)
        self.tk_image = ImageTk.PhotoImage(resized_image)

        # Update the image on the canvas
        if self.image_id is not None:
            self.canvas.delete(self.image_id)
        self.image_id = self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)

        self.resized_width = new_width
        self.resized_height = new_height
        # Redraw points on the resized image
        self.__display_image(self.image)


    def __display_image(self, image):
        # Create a new image to draw points on
        if self.resized_width and self.resized_height:
            img_with_points = image.resize((self.resized_width, self.resized_height), Image.LANCZOS)
        else:
            img_with_points = image.copy()

        draw = ImageDraw.Draw(img_with_points)

        # Loop through points and draw them based on the new size
        original_width, original_height = self.original_image.size
        for point, label in zip(self.points, self.labels):
            color = (0, 255, 0) if label == 1 else (255, 0, 0)  # Green for 1, Red for 0
            x, y = point
            
            # Scale points to the resized image dimensions
            scaled_x = int(self.resized_width * (x / original_width))
            scaled_y = int(self.resized_height * (y / original_height))
            
            # Draw a circle at the scaled point
            radius = 5  # Size of the circle
            draw.ellipse([(scaled_x - radius, scaled_y - radius), (scaled_x + radius, scaled_y + radius)], fill=color)

        # Create a new PhotoImage to display
        self.tk_image = ImageTk.PhotoImage(img_with_points)
        
        # If there's an existing image, delete it before displaying the new one
        if self.image_id is not None:
            self.canvas.delete(self.image_id)

        # Create a new image on the canvas
        self.image_id = self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)

    def __on_close(self):
        # This function is called when the annotation window is closed
        if self.annotation_window.state() == "zoomed":
            self.window_maximized = True
        self.geometry_data = self.annotation_window.geometry()
        self.annotation_window.destroy()

    def __on_click(self, event):
        if event.num == 1: # left click
            self.labels.append(1)
        elif event.num == 3: # right click
            self.labels.append(0)
        
        # Get the coordinates of the click
        x, y = event.x, event.y
        # Canvas size
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        # actual image size
        image_width, image_height = self.original_image.size

        # Clicked Coordinates in relation to actual image pixels
        image_x = int(image_width * (x / canvas_width))
        image_y = int(image_height * (y / canvas_height))

        self.points.append([image_x, image_y])

        self.image = self.__create_propagated_image()
        self.__display_image(self.image)

    def __on_key_press(self, event):
        # Remove last added Point
        if event.keysym == "BackSpace":
            if self.points:
                print(f"Removed last point: {self.points[-1]} with label {self.labels[-1]}")
                self.points.pop()
                self.labels.pop()

                self.image = self.__create_propagated_image()
                self.__display_image(self.image)

            else:
                # Clear the mask and show the original image if no points are left
                self.__display_image(self.original_image)

    def __create_propagated_image(self):
        # Give the list of clicked points to Sam, get a mask back, convert the mask into polygons and then draw them
        if not self.points or not len(self.points):
            return self.original_image
        
        mask = self.__propagate_image()  # Get the mask from your existing propagate method
        self.polygons = self.__convert_mask_to_polygons(mask)  # Convert the mask to polygons
        propagated_image = self.__draw_polygons_on_image(self.original_image.copy(), self.polygons)  # Draw the polygons on the original image
        return propagated_image

    def __propagate_image(self):
        # Prepare the structure and then send to sam
        points_labels_and_frame_index = {
            "Points" : self.points,
            "Labels" : self.labels,
            "Image Index" : self.img_index
        }

        mask = self.sam2.add_point(points_labels_and_frame_index, self.object_class_id)

        if len(mask) == 0:
            print("Error: Mask length == 0")

        return mask


    def __convert_mask_to_polygons(self, mask):
        # Initialize a list to hold all mask data
        polygons = []

        # Remove singleton dimensions
        mask = np.squeeze(mask)  # Squeeze to remove dimensions of size 1

        # Extract contours using OpenCV
        contours, _ = cv2.findContours(mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            # Simplify the contour using approxPolyDP
            epsilon = 0.0001 * cv2.arcLength(contour, True)  # Adjust epsilon for simplification level
            simplified_contour = cv2.approxPolyDP(contour, epsilon, True)

            # Convert contour points to a list of tuples
            simplified_contour = [(int(point[0][0]), int(point[0][1])) for point in simplified_contour]
            if len(simplified_contour) > 2:
                polygons.append(simplified_contour)

        return polygons

    def __draw_initial_polygons(self):

        self.image = self.__draw_polygons_on_image(self.original_image.copy(), self.polygons)
        self.__display_image(self.image)

    def __draw_polygons_on_image(self, image, polygons, color=(255, 0, 0, 100)):  # Default color is semi-transparent red
        overlay = Image.new('RGBA', image.size, (0, 0, 0, 0))  # Create an empty overlay
        overlay_draw = ImageDraw.Draw(overlay)

        for polygon in polygons:
            polygon_tuples = [tuple(point) for point in polygon]

            if len(polygon_tuples) > 3:  # Ensure there are enough points to form a polygon
                if polygon_tuples[0] != polygon_tuples[-1]:
                    polygon_tuples.append(polygon_tuples[0])
                
                overlay_draw.polygon(polygon_tuples, outline=color[:3], fill=color)
            else:
                print(f"Invalid polygon with only {len(polygon_tuples)} points")

        # Composite the overlay with the original image
        if image.mode != 'RGBA':
            image = image.convert('RGBA')
        image = Image.alpha_composite(image, overlay)
        return image.convert("RGB")  # Return a standard RGB image