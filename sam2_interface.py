"""
This Programm loads images from a directory and lets you iteractively use SAM2 to track an object through the video
"""

import tkinter as tk
from tkinter import ttk, filedialog
from PIL import Image, ImageTk
import torch
import os
import numpy as np
from sam2.build_sam import build_sam2_video_predictor # type: ignore
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Initialize the predictor as needed
sam2_checkpoint = r"C:\Users\K3000\segment-anything-2\checkpoints\sam2_hiera_large.pt"
model_cfg = "sam2_hiera_l.yaml"

# use bfloat16 for the entire notebook
torch.autocast(device_type="cuda", dtype=torch.bfloat16).__enter__()

if torch.cuda.get_device_properties(0).major >= 8:
    torch.backends.cuda.matmul.allow_tf32 = True
    torch.backends.cudnn.allow_tf32 = True

predictor = build_sam2_video_predictor(model_cfg, sam2_checkpoint)

class ImageDisplayApp(tk.Tk):
    def __init__(self, video_dir = ""):
        super().__init__()
        self.title("Image Grid Display with Input Field")
        self.geometry("1000x1000")
        self.images = []
        self.image_paths = []
        self.initialized = False

        # Initialize object ID
        self.ann_obj_id = 1

        # Initialize canvas
        self.canvas = tk.Canvas(self, width=800, height=600, bg='white')
        self.canvas.pack(fill='both', expand=True)

        # Frame to hold the input field, button, and directory selection
        input_frame = tk.Frame(self)
        input_frame.pack(side='top', fill='x', padx=10, pady=5)

        # Label
        tk.Label(input_frame, text="Grid Size:").pack(side='left', padx=(0, 5))

        # Entry field with specified width
        self.grid_entry = tk.Entry(input_frame, width=10)  # Set the width here
        self.grid_entry.insert(0, '3')
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
        self.frame_dir = None
        self.mask_dir = None
        self.output_dir = None
        self.predictor_initialized = False
        self.select_directory(video_dir)

        




    def select_directory(self, video_dir):
        """Open a directory dialog and load images from the selected directory."""
        if video_dir == "":
            directory = filedialog.askdirectory()
        else:
            directory = video_dir

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
            self.frame_dir = directory  # Save directory path
            self.mask_dir = os.path.join(self.frame_dir, "masks")
            os.makedirs(self.mask_dir, exist_ok=True)     

            # Initialize predictor state
            if not self.predictor_initialized:
                self.inference_state = predictor.init_state(video_path=self.frame_dir)
                self.predictor_initialized = True
            
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
            
            img = self.images[img_index]
            img_width = int(cell_width)
            img_height = int(cell_height)
            

            mask_file = os.path.join(self.mask_dir, f"mask_{img_index:05d}.png")
            

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

    def on_canvas_click(self, event):
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
        


    def save_points_to_file(self, frame_number):
        """Save points and labels to a .txt file."""
        filename = os.path.join(self.mask_dir, f'{frame_number:05d}.txt')
        with open(filename, 'w') as file:
            for point, label in zip(self.points, self.labels):
                file.write(f"{point[0]}, {point[1]}, {label}\n")
        print(f"Points saved to {filename}")


    def add_points(self, image, frame_number):
        """Function to handle adding points to an image and updating the mask."""
        self.points = []
        self.labels = []

        # Create a new top-level window for annotation
        annotation_window = tk.Toplevel(self)
        annotation_window.title("Add Points to Image")

        # Define event handlers
        def on_click(event):
            ix, iy = int(event.xdata), int(event.ydata)
            if event.button == 1:  # Left click
                print(f"Left click at ({ix}, {iy}) - 1")
                self.points.append([ix, iy])
                self.labels.append(1)
            elif event.button == 3:  # Right click
                print(f"Right click at ({ix}, {iy}) - 0")
                self.points.append([ix, iy])
                self.labels.append(0)
            update_mask(frame_number)

        def on_key_press(event):
            if event.key == "Backspace":
                if self.points:
                    self.points.pop()
                    self.labels.pop()
                    update_mask(frame_number)

        def update_mask(frame_number):
            if self.points and self.labels:
                points_np = np.array(self.points, dtype=np.float32)
                labels_np = np.array(self.labels, dtype=np.float32)

                _, out_obj_ids, out_mask_logits = predictor.add_new_points_or_box(
                    inference_state=self.inference_state,
                    frame_idx=frame_number,
                    obj_id=int(self.ann_obj_id),
                    points=points_np,
                    labels=labels_np,
                )
                
                mask = (out_mask_logits[0] > 0.0).squeeze().cpu().numpy().astype(np.uint8) * 255
            
                # Speichere die Maske als Bilddatei
                mask_image = Image.fromarray(mask)
                mask_image.save(os.path.join(self.mask_dir, f'mask_{frame_number:05d}.png'))

                

                # Clear previous plot and update the mask
                ax.clear()
                ax.imshow(image, aspect='auto')
                ax.axis('off')  # Ensure axes are completely off
                show_points(points_np, labels_np, ax)
                show_mask((out_mask_logits[0] > 0.0).cpu().numpy(), ax, obj_id=out_obj_ids[0])
                canvas.draw()
        
        def show_mask(mask, ax, obj_id=None, random_color=False):
            if random_color:
                color = np.concatenate([np.random.random(3), np.array([0.6])], axis=0)
            else:
                cmap = plt.get_cmap("tab10")
                cmap_idx = 0 if obj_id is None else obj_id
                color = np.array([*cmap(cmap_idx)[:3], 0.6])
            h, w = mask.shape[-2:]
            mask_image = mask.reshape(h, w, 1) * color.reshape(1, 1, -1)
            ax.imshow(mask_image, alpha=0.5)

        def show_points(coords, labels, ax, marker_size=200):
            pos_points = coords[labels==1]
            neg_points = coords[labels==0]
            ax.scatter(pos_points[:, 0], pos_points[:, 1], color='green', marker='*', s=marker_size, edgecolor='white', linewidth=1.25)
            ax.scatter(neg_points[:, 0], neg_points[:, 1], color='red', marker='*', s=marker_size, edgecolor='white', linewidth=1.25)

        def on_close():
            print("closed")
            self.save_points_to_file(frame_number)
            annotation_window.destroy()
            self.show_propagated_images()

        # Create a Matplotlib figure and axis for the image
        fig = plt.Figure(figsize=(6, 6), dpi=100)
        ax = fig.add_subplot(111)
        ax.imshow(image, aspect='auto')
        ax.axis('off')

        # Create a canvas for the Matplotlib figure in the new window
        canvas = FigureCanvasTkAgg(fig, master=annotation_window)
        canvas.draw()
        canvas.get_tk_widget().pack(side=tk.LEFT, fill=tk.BOTH, expand=1)

        # Bind mouse click and key press events
        fig.canvas.mpl_connect('button_press_event', on_click)
        fig.canvas.mpl_connect('key_press_event', on_key_press)



        annotation_window.protocol("WM_DELETE_WINDOW", on_close)

    def show_propagated_images(self):
        # Run propagation throughout the video and collect the results in a dict
        video_segments = {}  # video_segments contains the per-frame segmentation results
        
        for out_frame_idx, out_obj_ids, out_mask_logits in predictor.propagate_in_video(self.inference_state):
            video_segments[out_frame_idx] = {
                out_obj_id: (out_mask_logits[i] > 0.0).cpu().numpy()
                for i, out_obj_id in enumerate(out_obj_ids)
            }


        for out_frame_idx, masks in video_segments.items():
            for out_obj_id, out_mask in masks.items():
                # Remove singleton dimensions
                out_mask = np.squeeze(out_mask)  # Squeeze to remove dimensions of size 1

                # Convert the mask to a PIL image
                if out_mask.ndim == 2:  # If the mask is 2D, proceed
                    out_mask_img = Image.fromarray((out_mask * 255).astype('uint8'))
                    # Save the mask image with an increasing index
                    out_mask_img.save(os.path.join(self.mask_dir, f'mask_{out_frame_idx:05d}.png'))
                else:
                    print(f"Unexpected mask shape: {out_mask.shape}")
        
        self.update_grid()
            
        
            

    def run(self):
        """Start the Tkinter event loop."""
        self.initialized = True
        self.canvas.bind("<Button-1>", self.on_canvas_click)  # Bind left click to canvas
        self.canvas.bind("<Button-3>", self.on_canvas_click)  # Bind right click to canvas

        self.update_idletasks()
        self.update()
        self.update_grid()
        self.mainloop()

if __name__ == "__main__":
    app = ImageDisplayApp(video_dir = r"C:\Users\K3000\Videos\SAM2 Tests\KI_1")
    app.run()
