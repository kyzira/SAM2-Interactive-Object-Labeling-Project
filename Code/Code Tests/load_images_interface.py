import tkinter as tk
from tkinter import ttk, filedialog
from PIL import Image, ImageTk
import os

class ImageDisplayApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Image Grid Display with Input Field")
        self.geometry("1000x1000")

        self.images = []
        self.image_paths = []
        self.initialized = False

        # Initialize canvas
        self.canvas = tk.Canvas(self, width=800, height=600, bg='white')
        self.canvas.pack(fill='both', expand=True)

        self.grid_size = 3  # Default size for both rows and columns

        # Frame to hold the input field, button, and directory selection
        input_frame = tk.Frame(self)
        input_frame.pack(side='top', fill='x', padx=10, pady=5)

        # Label
        tk.Label(input_frame, text="Grid Size:").pack(side='left', padx=(0, 5))

        # Entry field with specified width
        self.grid_entry = tk.Entry(input_frame, width=10)  # Set the width here
        self.grid_entry.insert(0, str(self.grid_size))
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
        self.image_slider = ttk.Scale(self.slider_frame, from_=0, to=0, orient='horizontal', command=self.update_displayed_images)
        self.image_slider.pack(fill='x')

        # Bind mouse click event to canvas
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.initialized = True
        

    def select_directory(self):
        """Open a directory dialog and load images from the selected directory."""
        directory = filedialog.askdirectory()
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

    def display_images(self):
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

        # Create placeholder images
        self.tk_images = []
        self.image_ids = []  # Store image IDs for click detection
        for i in range(grid_size * grid_size):
            if i >= len(self.images):
                break

            img = self.images[i]
            h, w = img.size

            img_width = int(w * cell_width / w)
            img_height = int(h * cell_height / h)
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
            self.update_displayed_images()

        except ValueError as e:
            print(f"Error updating grid: {e}")

    def update_displayed_images(self, event=None):
        """Update the images displayed on the canvas based on the slider value."""
        if not self.initialized:
            return

        # Get the grid size from the entry field
        try:
            grid_size = int(self.grid_entry.get())
        except ValueError:
            print("Invalid input. Please enter a valid integer.")
            return

        # Get the slider value
        slider_value = int(self.image_slider.get())
        images_per_grid = grid_size * grid_size

        # Determine the start index for the images
        start_index = slider_value

        # Ensure the start index is within bounds
        if start_index + images_per_grid > len(self.images):
            start_index = len(self.images) - images_per_grid
        
        # Display the images within the bounds
        self.canvas.delete("all")
        self.tk_images = []
        self.image_ids = []
        for i in range(images_per_grid):
            img_index = start_index + i
            if img_index >= len(self.images):
                break

            img = self.images[img_index]
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            cell_width = canvas_width / grid_size
            cell_height = canvas_height / grid_size
            h, w = img.size

            img_width = int(w * cell_width / w)
            img_height = int(h * cell_height / h)
            img = img.resize((img_width, img_height), Image.Resampling.LANCZOS)
            tk_img = ImageTk.PhotoImage(img)
            self.tk_images.append(tk_img)

            row = i // grid_size
            col = i % grid_size
            x_position = col * cell_width
            y_position = row * cell_height
            image_id = self.canvas.create_image(x_position + cell_width // 2, y_position + cell_height // 2, image=tk_img)
            self.image_ids.append(image_id)  # Save the image ID

    def on_canvas_click(self, event):
        """Handle mouse click events on the canvas."""
        # Get the click coordinates
        x, y = event.x, event.y

        # Find the closest item to the click coordinates
        item = self.canvas.find_closest(x, y)
        if item:
            # Print the path of the clicked image
            if item[0] in self.image_ids:
                index = self.image_ids.index(item[0])
                if 0 <= index < len(self.image_paths):
                    index += int(self.image_slider.get())
                    print(f"Clicked image path: {self.image_paths[index]}")




if __name__ == "__main__":
    app = ImageDisplayApp()  # Creates an instance of the application
    app.mainloop()  # Starts the Tkinter event loop
