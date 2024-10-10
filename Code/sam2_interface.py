"""
This Programm loads images from a directory and lets you iteractively use SAM2 to track an object through the video
"""

import tkinter as tk
from tkinter import ttk, filedialog
from PIL import Image, ImageTk, ImageDraw
import os
import numpy as np
import cv2
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import convert_video_to_frames
from annotation_window import AnnotationWindow


class ImageDisplayApp(tk.Tk):
    def __init__(self, frame_dir = None, video_path = None, frame_rate = None, window_title = "Image Grid Display with Input Field", schadens_kurzel = None, stop_callback=None):
        super().__init__()
        self.title(window_title)
        self.geometry("1200x1000")
        self.images = []
        self.image_paths = []
        self.initialized = False

        # Initialize object ID
        self.ann_obj_id = 0

        self.options = [schadens_kurzel]

        # Radiobutton variable to store the selected option
        self.radio_var = tk.StringVar()
        
        # Frame for Radiobuttons and input field
        radio_frame = tk.Frame(self)
        radio_frame.pack(side='top', fill='x', padx=10, pady=5)

        # Add widgets in the radio_frame horizontally
        tk.Label(radio_frame, text="Add option:").pack(side='left', padx=(0, 5))
        self.new_option_entry = tk.Entry(radio_frame, width=15)
        self.new_option_entry.pack(side='left', padx=(0, 5))

        # Add button
        add_button = ttk.Button(radio_frame, text="Add", command=self.add_option)
        add_button.pack(side='left', padx=(5, 0))

        # Radiobuttons container
        self.radio_container = tk.Frame(radio_frame)
        self.radio_container.pack(side='left', padx=10, pady=5)

        self.wait_label = tk.Label(radio_frame, text="", font=("Helvetica", 16), fg="red")
        self.wait_label.pack(side="left", padx=10, pady=5)


        # Button to delete labeling
        self.more_images_forward = ttk.Button(radio_frame, text="delete unselected labels", command=self.delete_damage)
        self.more_images_forward.pack(side='left', padx=(5, 5))

        # Button to skip to next label
        self.more_images_forward = ttk.Button(radio_frame, text="Next", command=self.destroy)
        self.more_images_forward.pack(side='right', padx=(5, 5))

        # Button to stop labeling
        self.more_images_forward = ttk.Button(radio_frame, text="Cancel", command=self.stop_program)
        self.more_images_forward.pack(side='right', padx=(5, 5))


        # Initialize canvas
        self.canvas = tk.Canvas(self, width=1000, height=800, bg='white')
        self.canvas.pack(fill='both', expand=True)

        # Frame to hold the input field, button, and directory selection
        input_frame = tk.Frame(self)
        input_frame.pack(side='top', fill='x', padx=10, pady=5)


        # Add Previous and Next buttons to navigate images
        self.prev_button = ttk.Button(input_frame, text="<", command=self.prev_images)
        self.prev_button.pack(side='left', padx=(5, 0))

        self.next_button = ttk.Button(input_frame, text=">", command=self.next_images)
        self.next_button.pack(side='left', padx=(5, 0))

        # Short slider (10% of the window width)
        self.image_slider = ttk.Scale(input_frame, from_=0, to=0, orient='horizontal', command=self.slider_update)
        self.image_slider.pack(side='left', fill='x', expand=False, padx=(10, 5), ipadx=12)  # Adjust width with ipadx

        
        # Label
        tk.Label(input_frame, text="Grid Size:").pack(side='left', padx=(0, 5))

        # Entry field with specified width
        self.grid_entry = tk.Entry(input_frame, width=10)  # Set the width here
        self.grid_entry.insert(0, '5')
        self.grid_entry.pack(side='left', fill='x', expand=True, padx=(0, 5))

        # Button for updating grid
        self.button = ttk.Button(input_frame, text="Update Grid", command=self.update_grid)
        self.button.pack(side='left', padx=(5, 0))

        # Button to extract more images
        self.more_images_back = ttk.Button(input_frame, text="extract previous images", command=self.load_more_images_back)
        self.more_images_back.pack(side='left', padx=(5, 0))

        # Button to extract more images
        self.more_images_forward = ttk.Button(input_frame, text="extract next images", command=self.load_more_images_forward)
        self.more_images_forward.pack(side='left', padx=(5, 0))


        self.frame_dir = frame_dir
        self.working_dir = os.path.dirname(frame_dir)
        self.output_dir = None
        self.predictor_initialized = False
        self.current_index = 0
        self.select_directory()
        self.video_path = video_path
        self.update_radiobuttons()
        self.stop_callback = stop_callback
        self.last_option = None

        self.json_path = os.path.join(self.working_dir, f"{str(os.path.basename(self.working_dir))}.json")
        
        
    def delete_damage(self):
        self.json_content = self.load_json()

        for option in self.options:
            if not self.checkbox_vars[option].get():
                self.options.remove(option)
                self.update_radiobuttons()

                # delete all entries from json
                for image in self.json_content:
                    if option in self.json_content[image]["Observations"]:
                        del self.json_content[image]["Observations"][option]
        self.save_json(self.json_content)






    def select_directory(self):
        """Open a directory dialog and load images from the selected directory."""
        if not self.frame_dir:
            self.frame_dir = filedialog.askdirectory()
        
        directory = self.frame_dir

        if directory:
            self.images = []
            self.image_paths = []
            for file_name in os.listdir(directory):
                file_path = os.path.join(directory, file_name)
                if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                    self.image_paths.append(file_path)
                    img = Image.open(file_path)
                    self.images.append(img)
            print(f"Loaded {len(self.images)} images from {directory}")
            
            self.update_grid()  # Refresh the grid and slider based on new images




    def on_canvas_click(self, event):

        self.wait_label.config(text= "Bitte Warten! Bilder werden berechnet")

        """Handle mouse click events on the canvas."""
        x, y = event.x, event.y

        # Get the grid size from the entry field
        try:
            grid_size = int(self.grid_entry.get())
        except ValueError:
            print("Invalid input. Please enter a valid integer.")
            return

        # Determine the clicked cell based on grid size
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        cell_width = canvas_width / grid_size
        cell_height = canvas_height / grid_size

        row = int(y // cell_height)
        col = int(x // cell_width)

        if row >= grid_size or col >= grid_size:
            return

        start_index = int(self.image_slider.get())

        # Calculate the index of the clicked image
        index = row * grid_size + col + start_index

        if index >= len(self.images):
            return

        # Open the selected image in a new window and add points
        selected_image = self.images[index]
        self.add_points(selected_image, index)
        




    def add_points(self, image, frame_number):
        """Function to handle adding points to an image and updating the mask."""
        self.points = []
        self.labels = []
        self.get_selected_option_index()

        # Create a new top-level window for annotation
        annotationWindow = AnnotationWindow(f"Punkte für {self.options[self.ann_obj_id]} hinzufügen")
        annotationWindow.display_image(image)


    def show_propagated_images(self):
        """Run propagation throughout the video and save the results."""
        self.json_content = self.load_json()

        for out_frame_idx, masks in video_segments.items():
            # Create a list to hold all mask data for the current frame    
            mask_data = []

            for out_obj_id, out_mask in masks.items():
                # Remove singleton dimensions
                out_mask = np.squeeze(out_mask)  # Squeeze to remove dimensions of size 1
                
                # Extract contours using OpenCV
                contours, _ = cv2.findContours(out_mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

                for contour in contours:
                    # Simplify the contour using approxPolyDP
                    epsilon = 0.001 * cv2.arcLength(contour, True)  # Adjust epsilon for simplification level
                    simplified_contour = cv2.approxPolyDP(contour, epsilon, True)

                    # Convert contour points to a list of tuples
                    simplified_contour = [(int(point[0][0]), int(point[0][1])) for point in simplified_contour]
                    
                    mask_data.append(simplified_contour)

            self.save_to_json(out_frame_idx, mask_data)

        self.save_json(self.json_content)
        self.update_grid()
    

    def run(self):
        """Start the Tkinter event loop."""
        self.initialized = True
        self.canvas.bind("<Button-1>", self.on_canvas_click)  # Bind left click to canvas
        self.canvas.bind("<Button-3>", self.on_canvas_click)  # Bind right click to canvas
        
        self.state('zoomed')    
        self.update_idletasks()
        self.update()
        self.update_grid()
        self.mainloop()



if __name__ == "__main__":
    app = ImageDisplayApp(frame_dir = r"C:\Users\K3000\Videos\SAM2 Tests\KI_1", schadens_kurzel = "BBA")
    app.run()

