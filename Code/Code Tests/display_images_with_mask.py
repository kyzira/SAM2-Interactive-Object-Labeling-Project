"""
This program loads images from a directory and shows the masks on the images.
"""

import tkinter as tk
from tkinter import ttk, filedialog
from PIL import Image, ImageTk
import os


class ImageDisplayApp(tk.Tk):
    def __init__(self, frame_dir=None, video_path=None, frame_rate=None, window_title="Image Grid Display with Input Field"):
        super().__init__()
        self.title(window_title)
        self.geometry("1200x1000")
        self.images = []
        self.image_paths = []
        self.initialized = False

        # Initialize object ID
        self.ann_obj_id = 1

        # Initialize canvas
        self.canvas = tk.Canvas(self, width=1000, height=800, bg='white')
        self.canvas.pack(fill='both', expand=True)

        # Frame to hold the input field, button, and directory selection
        input_frame = tk.Frame(self)
        input_frame.pack(side='top', fill='x', padx=10, pady=5)

        # Add Previous and Next buttons to navigate images
        self.prev_button = ttk.Button(input_frame, text="Previous", command=self.prev_images)
        self.prev_button.pack(side='left', padx=(5, 0))

        self.next_button = ttk.Button(input_frame, text="Next", command=self.next_images)
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

        # Button to select directory
        self.select_dir_button = ttk.Button(input_frame, text="Select Directory", command=self.select_directory)
        self.select_dir_button.pack(side='left', padx=(5, 0))



        self.points = []
        self.labels = []
        self.inference_state = None
        self.frame_dir = frame_dir
        self.mask_dir = None
        self.output_dir = None
        self.predictor_initialized = False
        self.current_index = 0  # Track the current image index
        self.select_directory()
        self.video_path = video_path
        self.frame_rate = frame_rate

    def find_video_path(self):
        """Find the video file that corresponds to the frame directory."""
        video_name = os.path.basename(self.frame_dir)
        parent_dir = os.path.dirname(self.frame_dir)
        video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.mpg']
        
        for ext in video_extensions:
            for case_ext in [ext, ext.upper()]:
                potential_video_path = os.path.join(parent_dir, video_name + case_ext)
                if os.path.isfile(potential_video_path):
                    return potential_video_path
        return None

    def select_directory(self, init=False):
        # Open a directory dialog and load images from the selected directory.
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
            self.mask_dir = os.path.join(self.frame_dir, "masks")
            os.makedirs(self.mask_dir, exist_ok=True)
            self.update_grid()

    def display_images(self):
        """Displays images in a grid format on the canvas."""
        if not self.initialized:
            return

        self.canvas.delete("all")

        # Get canvas size
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        if canvas_width <= 0 or canvas_height <= 0:
            return

        try:
            grid_size = int(self.grid_entry.get())
        except ValueError:
            print("Invalid input. Please enter a valid integer.")
            return

        if grid_size <= 0:
            return

        cell_width = canvas_width / grid_size
        cell_height = canvas_height / grid_size

        start_index = self.current_index

        self.image_ids = []
        self.tk_images = []

        for i in range(grid_size * grid_size):
            img_index = start_index + i
            if img_index >= len(self.images):
                break

            img_path = self.image_paths[img_index]
            img = self.images[img_index]
            img_width = int(cell_width)
            img_height = int(cell_height)

            base_filename = os.path.splitext(os.path.basename(img_path))[0]
            mask_file = os.path.join(self.mask_dir, f"{base_filename}.png")

            if os.path.isfile(mask_file):
                mask = Image.open(mask_file).convert("1")
                red_overlay = Image.new("RGBA", img.size, (255, 0, 0, 100))
                mask_binary = mask.point(lambda p: p > 128 and 255)
                red_overlay = Image.composite(red_overlay, Image.new("RGBA", img.size, (0, 0, 0, 0)), mask_binary)

                if img.mode != 'RGBA':
                    img = img.convert('RGBA')

                img = Image.alpha_composite(img, red_overlay)
                img = img.convert("RGB")

            img = img.resize((img_width, img_height), Image.Resampling.LANCZOS)
            tk_img = ImageTk.PhotoImage(img)
            self.tk_images.append(tk_img)

            row = i // grid_size
            col = i % grid_size
            x_position = col * cell_width
            y_position = row * cell_height
            image_id = self.canvas.create_image(x_position + cell_width // 2, y_position + cell_height // 2, image=tk_img)
            self.image_ids.append(image_id)

    def update_grid(self):
        """Update the grid size and refresh the displayed images."""
        try:
            if not self.initialized:
                return

            grid_size = int(self.grid_entry.get())

            if grid_size < 1:
                raise ValueError("Grid size must be greater than 0.")

            print(f"Grid updated: Size = {grid_size}")

            # Update the slider range based on the number of images and grid size
            images_per_grid = grid_size * grid_size
            slider_max = max(0, len(self.images) - images_per_grid)
            self.image_slider.config(from_=0, to=slider_max)

            self.display_images()

        except ValueError as e:
            print(f"Error updating grid: {e}")

    def slider_update(self, value):
        """Update image display when the slider is moved."""
        self.current_index = int(float(value))
        self.display_images()

    def prev_images(self):
        """Go to the previous set of images."""
        grid_size = int(self.grid_entry.get())
        self.current_index = max(0, self.current_index - grid_size)
        self.display_images()
        self.image_slider.set(self.current_index)  # Update slider

    def next_images(self):
        """Go to the next set of images."""
        grid_size = int(self.grid_entry.get())
        images_per_grid = grid_size * grid_size
        self.current_index = min(len(self.images) - images_per_grid, self.current_index + grid_size)
        self.display_images()
        self.image_slider.set(self.current_index)  # Update slider

    def run(self):
        """Start the Tkinter event loop."""
        self.initialized = True
        self.update_grid()
        self.update_idletasks()
        self.update()
        self.update_grid()
        self.mainloop()


if __name__ == "__main__":
    app = ImageDisplayApp()
    app.run()
