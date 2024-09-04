"""
This Programm loads images from a directory and lets you iteractively use SAM2 to track an object through the video
"""

import tkinter as tk
from tkinter import ttk, filedialog
from PIL import Image, ImageTk
import torch
import os
import numpy as np
import cv2
from sam2.build_sam import build_sam2_video_predictor # type: ignore
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import convert_video_to_frames


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
    def __init__(self, frame_dir = None, video_path = None, frame_rate = None):
        super().__init__()
        self.title("Image Grid Display with Input Field")
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

        # Button to select directory
        self.more_images_back = ttk.Button(input_frame, text="extract previous images", command=self.load_more_images_back)
        self.more_images_back.pack(side='left', padx=(5, 0))

        # Button to select directory
        self.more_images_forward = ttk.Button(input_frame, text="extract next images", command=self.load_more_images_forward)
        self.more_images_forward.pack(side='left', padx=(5, 0))

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



    def detect_framerate(self):
        num1 = None
        num2 = None
        frame_files = []

        # Iterate through the files in the directory
        for file_name in os.listdir(self.frame_dir):
            file_path = os.path.join(self.frame_dir, file_name)
            
            # Skip directories
            if os.path.isdir(file_path):
                continue
            
            try:
                # Extract frame number from the file name
                frame_number = int(file_name.split(".")[0].lstrip("0"))
                frame_files.append(frame_number)
            except ValueError:
                # Skip files that cannot be converted to an integer
                continue

        # Ensure there are enough frame files to determine framerate
        if len(frame_files) < 2:
            print("Not enough numeric frame files to determine framerate.")
            return None, None, None

        # Sort frame numbers to calculate framerate
        frame_files = sorted(frame_files)
        num1 = frame_files[0]
        num2 = frame_files[1]

        last_num = frame_files[-1]
        framerate = num2 - num1
        print(f"Frame numbers detected: {num1}, {num2}")
        print(f"Framerate: {framerate}")

        return framerate, num1, last_num
    



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
        
        # If the video file is not found in the parent directory, you can search deeper or in other known directories
        # For now, return None if not found
        return None



        
    def load_more_images_back(self):
        """Load previous images."""
        if not self.initialized:
            return  # Do nothing if not initialized
        
        frame_rate, end_frame, _ = self.detect_framerate()
        
        if end_frame is None:
            print("Error: Could not detect frame rate or end frame.")
            return
        
        if not self.video_path:
            self.video_path = self.find_video_path()

        video_path = self.video_path

        if not video_path:
            print("Error: Video path not found.")
            return

        if end_frame > 8 * frame_rate:
            start_frame = end_frame - 8 * frame_rate
            end_frame = end_frame - frame_rate
        elif end_frame > frame_rate:
            end_frame = end_frame - frame_rate
            start_frame = 0
        else: 
            return

        print(f"Loading frames from {start_frame} to {end_frame} from video {video_path}")
        
        convert_video_to_frames.convert_video(input_path=video_path, start_frame=start_frame, end_frame=end_frame, frame_rate=frame_rate, output_path=self.frame_dir)
        self.images = []
        self.image_paths = []
        
        # Load images from the directory
        for file_name in sorted(os.listdir(self.frame_dir)):
            file_path = os.path.join(self.frame_dir, file_name)
            if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                self.image_paths.append(file_path)
                img = Image.open(file_path)
                self.images.append(img)
        
        if not self.images:
            print("No images loaded. Please check the directory or image file formats.")
            return
        
        print(f"Loaded {len(self.images)} images from {self.frame_dir}")

        self.inference_state = predictor.init_state(video_path=self.frame_dir)
        predictor.reset_state(self.inference_state)
        self.update_grid()






    def load_more_images_forward(self):
        if not self.initialized:
            return  # Do nothing if not initialized
        
        frame_rate, _, last_num = self.detect_framerate()

        if not self.video_path:
            self.video_path = self.find_video_path()

        video_path = self.video_path

        video_capture = cv2.VideoCapture(video_path)
        total_frames = int(video_capture.get(cv2.CAP_PROP_FRAME_COUNT))
        video_capture.release()

        if total_frames > last_num + frame_rate * 8:
            end_frame = last_num + frame_rate * 8
            start_frame = last_num + frame_rate
        elif total_frames > last_num + frame_rate:
            end_frame = total_frames
            start_frame = last_num + frame_rate
        else:
            return

        print(f"Loading frames from {start_frame} to {end_frame} from video {video_path}")
        
        convert_video_to_frames.convert_video(input_path=video_path, start_frame=start_frame, end_frame=end_frame, frame_rate=frame_rate, output_path=self.frame_dir)

        # Clear existing images
        self.images = []
        self.image_paths = []
        
        # Load images from the directory
        for file_name in sorted(os.listdir(self.frame_dir)):
            file_path = os.path.join(self.frame_dir, file_name)
            if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                self.image_paths.append(file_path)
                img = Image.open(file_path)
                self.images.append(img)
        
        if not self.images:
            print("No images loaded. Please check the directory or image file formats.")
            return
        
        print(f"Loaded {len(self.images)} images from {self.frame_dir}")

        self.inference_state = predictor.init_state(video_path=self.frame_dir)
        predictor.reset_state(self.inference_state)
        self.update_grid()




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
        # Get the image path for the current frame
        if frame_number >= len(self.image_paths):
            print("Frame number out of range")
            return

        img_path = self.image_paths[frame_number]
        base_filename = os.path.splitext(os.path.basename(img_path))[0]

        # Construct the filename for saving points
        points_file = os.path.join(self.mask_dir, f'{base_filename}.txt')

        with open(points_file, 'w') as file:
            for point, label in zip(self.points, self.labels):
                file.write(f"{point[0]}, {point[1]}, {label}\n")

        print(f"Points saved to {points_file}")




    def add_points(self, image, frame_number):
        """Function to handle adding points to an image and updating the mask."""
        self.points = []
        self.labels = []

        # Convert the PIL image to a NumPy array
        image_np = np.array(image)

        # Create a new top-level window for annotation
        annotation_window = tk.Toplevel(self)
        annotation_window.title("Add Points to Image")

        # Define event handlers
        def on_click(event):
            if event.xdata is not None and event.ydata is not None:
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
            if event.key == "backspace":
                if self.points:
                    self.points.pop()
                    self.labels.pop()
                    update_mask(frame_number)
                else:
                    # Clear the mask and show the original image if no points are left
                    ax.clear()
                    ax.imshow(image_np, aspect='equal')
                    ax.axis('off')
                    canvas.draw()

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
                
                # Clear previous plot and update the mask
                ax.clear()
                ax.imshow(image_np, aspect='equal')  # Maintain aspect ratio
                ax.axis('off')  # Ensure axes are completely off
                show_points(points_np, labels_np, ax)
                show_mask((out_mask_logits[0] > 0.0).cpu().numpy(), ax, obj_id=out_obj_ids[0])
                canvas.draw()
            else:
                # If no points are left, clear the mask and show the original image
                ax.clear()
                ax.imshow(image_np, aspect='equal')
                ax.axis('off')
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
            pos_points = coords[labels == 1]
            neg_points = coords[labels == 0]
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

        # Display the image
        ax.imshow(image_np, aspect='equal')
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
        """Run propagation throughout the video and save the results."""
        video_segments = {}  # video_segments contains the per-frame segmentation results

        for out_frame_idx, out_obj_ids, out_mask_logits in predictor.propagate_in_video(self.inference_state):
            video_segments[out_frame_idx] = {
                out_obj_id: (out_mask_logits[i] > 0.0).cpu().numpy()
                for i, out_obj_id in enumerate(out_obj_ids)
            }


        for out_frame_idx, out_obj_ids, out_mask_logits in predictor.propagate_in_video(self.inference_state, reverse=True):
            if out_frame_idx not in video_segments:
                video_segments[out_frame_idx] = {}
            for i, out_obj_id in enumerate(out_obj_ids):
                if out_obj_id not in video_segments[out_frame_idx]:
                    video_segments[out_frame_idx][out_obj_id] = (out_mask_logits[i] > 0.0).cpu().numpy()
                else:
                    # Optionally merge or update masks if needed
                    video_segments[out_frame_idx][out_obj_id] = np.maximum(video_segments[out_frame_idx][out_obj_id], (out_mask_logits[i] > 0.0).cpu().numpy())


        for out_frame_idx, masks in video_segments.items():
            for out_obj_id, out_mask in masks.items():
                # Remove singleton dimensions
                out_mask = np.squeeze(out_mask)  # Squeeze to remove dimensions of size 1

                # Convert the mask to a PIL image
                if out_mask.ndim == 2:  # If the mask is 2D, proceed
                    out_mask_img = Image.fromarray((out_mask * 255).astype('uint8'))

                    # Construct the filename for saving the mask
                    # Use the base filename for the mask based on the frame number
                    img_path = self.image_paths[out_frame_idx]
                    base_filename = os.path.splitext(os.path.basename(img_path))[0]
                    mask_file = os.path.join(self.mask_dir, f"{base_filename}.png")

                    # Save the mask image with the constructed filename
                    out_mask_img.save(mask_file)
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
    app = ImageDisplayApp(frame_dir = r"C:\Users\K3000\Videos\SAM2 Tests\KI_1")
    app.run()

