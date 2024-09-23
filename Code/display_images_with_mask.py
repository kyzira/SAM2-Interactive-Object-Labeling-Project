"""
This Programm loads images from a directory and shows the masks on the images
"""

import tkinter as tk
from tkinter import ttk, filedialog
from PIL import Image, ImageTk
import os




class ImageDisplayApp(tk.Tk):
    def __init__(self, frame_dir = None, video_path = None, frame_rate = None, window_title = "Image Grid Display with Input Field"):
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

        # Slider Frame
        self.slider_frame = tk.Frame(self)
        self.slider_frame.pack(side='bottom', fill='x', padx=10, pady=5)

        # Initialize slider
        self.image_slider = ttk.Scale(self.slider_frame, from_=0, to=0, orient='horizontal', command=self.display_images)
        self.image_slider.pack(fill='x')

        self.points = []
        self.labels = []
        self.inference_state = None
        self.frame_dir = frame_dir
        self.mask_dir = None
        self.output_dir = None
        self.predictor_initialized = False
        self.select_directory()
        self.video_path = video_path
        self.frame_rate = frame_rate
    



    def find_video_path(self):
        """Find the video file that corresponds to the frame directory."""
        # Get the directory name, which is expected to be the same as the video name
        video_name = os.path.basename(self.frame_dir)
        
        # Look for video files in the parent directory of the frame directory
        parent_dir = os.path.dirname(self.frame_dir)
        
        # Possible video extensions, including common variations
        video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.mpg']
        
        # Search for the video file
        for ext in video_extensions:
            # Check for both lowercase and uppercase versions of the extension
            for case_ext in [ext, ext.upper()]:
                potential_video_path = os.path.join(parent_dir, video_name + case_ext)
                if os.path.isfile(potential_video_path):
                    return potential_video_path
        
        return None




    def select_directory(self, init = False):
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
            
            self.update_grid()  # Refresh the grid and slider based on new images



    def display_images(self, *args):
        """Displays images in a grid format on the canvas."""
        if not self.initialized:
            return  # Do nothing if not initialized

        self.canvas.delete("all")

        # Get canvas size
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        # Ensure the canvas dimensions are valid
        if canvas_width <= 0 or canvas_height <= 0:
            return

        # Get the grid size from the entry field
        try:
            grid_size = int(self.grid_entry.get())
        except ValueError:
            print("Invalid input. Please enter a valid integer.")
            return

        # Prevent invalid sizes
        if grid_size <= 0:
            return

        # Calculate cell size based on canvas size and grid size
        cell_width = canvas_width / grid_size
        cell_height = canvas_height / grid_size

        start_index = int(self.image_slider.get())

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

            # Extract the base filename without extension
            base_filename = os.path.splitext(os.path.basename(img_path))[0]

            # Construct the path for the mask file using the base filename
            mask_file = os.path.join(self.mask_dir, f"{base_filename}.png")

            if os.path.isfile(mask_file):
                mask = Image.open(mask_file).convert("1")  # Load mask as grayscale

                # Create a red overlay with the same dimensions as the image
                red_overlay = Image.new("RGBA", img.size, (255, 0, 0, 100))  # Red color with 40% transparency

                # Convert the mask to binary and apply it
                mask_binary = mask.point(lambda p: p > 128 and 255)  # Binarize mask (white areas are 255)
                red_overlay = Image.composite(red_overlay, Image.new("RGBA", img.size, (0, 0, 0, 0)), mask_binary)

                if img.mode != 'RGBA':
                    img = img.convert('RGBA')

                # Apply the overlay to the image
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
            self.image_ids.append(image_id)  # Save the image ID



    def update_grid(self):
        """Update the grid size and slider based on the input field value."""
        try:
            if not self.initialized:
                return  # Do nothing if not initialized

            # Get the grid size from the entry field
            grid_size = int(self.grid_entry.get())

            if grid_size < 1:
                raise ValueError("Grid size must be greater than 0.")


            print("Grid updated: Size = {}".format(grid_size))

            # Re-display images with the updated grid
            self.display_images()

            # Update the slider's maximum value
            num_images = len(self.images)
            images_per_grid = grid_size * grid_size
            if images_per_grid > 0:
                self.image_slider.config(to=num_images - images_per_grid)
            else:
                self.image_slider.config(to=0)

            # Reset the slider value to 0
            self.image_slider.set(0)

            # Update the displayed images based on the slider value
            self.display_images()

        except ValueError as e:
            print(f"Error updating grid: {e}")




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

