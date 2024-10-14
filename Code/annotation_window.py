import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from PIL import Image, ImageTk, ImageDraw


class AnnotationWindow:
    def __init__(self, annotation_window, img, index):
        self.annotation_window = annotation_window

        self.points = []
        self.labels = []

        # Store the original image
        self.original_image = img
        # Store the shown image
        self.image = img
        
        # Create a canvas
        self.canvas = tk.Canvas(self.annotation_window)
        self.annotation_window.geometry(f"{img.width}x{img.height}")  # Set initial window size to image size
        self.canvas.pack()

        self.img_imdex = index

        # Display the image on the canvas
        self.image_id = None
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


    def __on_resize(self, event):
        # Update canvas size to match window size
        new_width = event.width
        new_height = event.height
        
        self.canvas.config(width=new_width, height=new_height)

        # Resize the image to fit the new window size
        resized_image = self.image.resize((new_width, new_height), Image.LANCZOS)
        self.tk_image = ImageTk.PhotoImage(resized_image)

        # Update the image on the canvas
        self.canvas.itemconfig(self.image_id, image=self.tk_image)


    def __on_close(self):
        # This function is called when the annotation window is closed
        self.annotation_window.destroy()


    def __on_click(self, event):
        # Determine which mouse button was clicked
        if event.num == 1:
            self.labels.append(1)
        elif event.num == 3:
            self.labels.append(0)
        
        # Get the coordinates of the click
        x, y = event.x, event.y
        # Canvas size
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        # actual image size
        image_width, image_height = self.image.size


        # Clicked Coordinates in relation to actual image pixels
        image_x = int(image_width * (x/canvas_width))
        image_y = int(image_height * (y/canvas_height))

        self.points.append([image_x, image_y])

        # Print or log the button and coordinates
        print(f"Label {self.labels[-1]} at ({image_x}, {image_y})")

        # self.__create_propagated_image()
        self.__display_image(self.image)

    def __on_key_press(self, event):
        if event.keysym == "BackSpace":
            if self.points:
                print(f"Removed last point: {self.points[-1]} with label {self.labels[-1]}")
                self.points.pop()
                self.labels.pop()
                # self.__create_propagated_image()
                self.__display_image(self.image)
            else:
                # Clear the mask and show the original image if no points are left
                self.__display_image(self.original_image)


    def __display_image(self, img):
        # Create a new image to draw points on
        img_with_points = img.copy()
        draw = ImageDraw.Draw(img_with_points)

        # Loop through points and draw them
        for point, label in zip(self.points, self.labels):
            color = (0, 255, 0) if label == 1 else (255, 0, 0)  # Green for 1, Red for 0
            x, y = point
            
            # Draw a circle at the point
            radius = 5  # Size of the circle
            draw.ellipse([(x - radius, y - radius), (x + radius, y + radius)], fill=color)

        # Create a new PhotoImage to display
        self.tk_image = ImageTk.PhotoImage(img_with_points)
        
        # If there's an existing image, delete it before displaying the new one
        if self.image_id is not None:
            self.canvas.delete(self.image_id)

        # Create a new image on the canvas
        self.image_id = self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)


    def __propagate_image(self):
        print("Propagating image...")  # Add your logic here


    # def update_mask(frame_number):
    #     if self.points and self.labels:
    #         # Clear previous plot and update the mask
    #         ax.clear()
    #         ax.imshow(image_np, aspect='equal')  # Maintain aspect ratio
    #         ax.axis('off')  # Ensure axes are completely off
    #         show_points(points_np, labels_np, ax)
    #         show_mask(, ax, )
    #         canvas.draw()
    #     else:
    #         # If no points are left, clear the mask and show the original image
    #         ax.clear()
    #         ax.imshow(image_np, aspect='equal')
    #         ax.axis('off')
    #         canvas.draw()


    # def show_mask(mask, ax, obj_id=None, random_color=False):
    #     if random_color:
    #         color = np.concatenate([np.random.random(3), np.array([0.6])], axis=0)
    #     else:
    #         cmap = plt.get_cmap("tab10")
    #         cmap_idx = 0 if obj_id is None else obj_id
    #         color = np.array([*cmap(cmap_idx)[:3], 0.6])
    #     h, w = mask.shape[-2:]
    #     mask_image = mask.reshape(h, w, 1) * color.reshape(1, 1, -1)
    #     ax.imshow(mask_image, alpha=0.5)


    # def show_points(coords, labels, ax, marker_size=200):
    #     pos_points = coords[labels == 1]
    #     neg_points = coords[labels == 0]
    #     ax.scatter(pos_points[:, 0], pos_points[:, 1], color='green', marker='*', s=marker_size, edgecolor='white', linewidth=1.25)
    #     ax.scatter(neg_points[:, 0], neg_points[:, 1], color='red', marker='*', s=marker_size, edgecolor='white', linewidth=1.25)


    # def on_close():
    #     self.wait_label.config(text="")
    #     self.frame_for_point = frame_number
    #     annotation_window.destroy()
    #     self.show_propagated_images()