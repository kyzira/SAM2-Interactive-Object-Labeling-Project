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
import json
from skimage import measure


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
    def __init__(self, frame_dir = None, video_path = None, frame_rate = None, window_title = "Image Grid Display with Input Field", schadens_kurzel = None):
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


        self.points = []
        self.labels = []
        self.inference_state = None
        self.frame_dir = frame_dir
        self.working_dir = os.path.dirname(frame_dir)
        self.mask_dir = None
        self.output_dir = None
        self.predictor_initialized = False
        self.current_index = 0
        self.select_directory()
        self.video_path = video_path
        self.frame_rate = frame_rate
        self.all_points_data = {}
        self.update_radiobuttons()

        self.frame_index = []
        for file in os.listdir(self.frame_dir):
            if file.endswith(".jpg"):
                self.frame_index.append(file)
        

        


    def update_radiobuttons(self):
        for widget in self.radio_container.winfo_children():
            widget.destroy()

        # Create the Radiobuttons in a horizontal layout
        for option in self.options:
            rb = tk.Radiobutton(self.radio_container, text=option, variable=self.radio_var, value=option)
            rb.pack(side='left', padx=5)  # Use side='left' to arrange them horizontally

            current_damage_dir = os.path.join(self.working_dir, str(option))
            os.makedirs(current_damage_dir, exist_ok=True)


        # Set the default selection to the first option
        if self.options:
            self.radio_var.set(self.options[0])


    def add_option(self):
        """Add a new option to the radiobutton list."""
        new_option = self.new_option_entry.get().strip()
        if new_option:
            if new_option not in self.options:
                self.options.append(new_option)
                self.update_radiobuttons()
                self.new_option_entry.delete(0, tk.END)


    def get_selected_option_index(self):
        selected_option = self.radio_var.get()

        if selected_option in self.options:
            self.ann_obj_id = self.options.index(selected_option)
        else:
            self.ann_obj_id = 0
    

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
        """Save points and labels to a single JSON file sorted by frame and then by label."""
        # Check if the frame number is within the valid range
        if frame_number < 0 or frame_number >= len(self.image_paths):
            print("Frame number out of range")
            return

        # Ensure that the dictionary has an entry for the current frame using the frame number as the key
        if frame_number not in self.all_points_data:
            self.all_points_data[frame_number] = {0: [], 1: []}  # Initialized with empty lists for labels

        # Collect points and labels for the current frame
        for point, label in zip(self.points, self.labels):
            if label in self.all_points_data[frame_number]:  # Using frame_number as the key directly
                self.all_points_data[frame_number][label].append({"x": int(point[0]), "y": int(point[1])})

        # Construct the filename for saving all points data
        points_json_file = os.path.join(self.working_dir, self.options[self.ann_obj_id], 'set_points.json')

        # Save the all_points_data dictionary to a JSON file
        with open(points_json_file, 'w') as file:
            json.dump(self.all_points_data, file, indent=4)  # Save with pretty printing





    def add_points(self, image, frame_number):
        """Function to handle adding points to an image and updating the mask."""
        self.points = []
        self.labels = []
        self.get_selected_option_index()

        # Convert the PIL image to a NumPy array
        image_np = np.array(image)

        # Create a new top-level window for annotation
        annotation_window = tk.Toplevel(self)
        annotation_window.title(f"Punkte für {self.options[self.ann_obj_id]} hinzufügen")

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


        def is_collinear(p1, p2, p3):
            """ Check if three points are collinear """
            return (p2[1] - p1[1]) * (p3[0] - p2[0]) == (p2[0] - p1[0]) * (p3[1] - p2[1])
        
        frame_number = self.frame_index

        # Dictionary to hold all frame data
        all_frame_data = {}

        for out_frame_idx, masks in video_segments.items():
            # Create a list to hold all mask data for the current frame
            mask_data = []
            for out_obj_id, out_mask in masks.items():
                # Remove singleton dimensions
                out_mask = np.squeeze(out_mask)  # Squeeze to remove dimensions of size 1

                # Extract the contours of the mask
                contours = measure.find_contours(out_mask, 0.5)  # Adjust the level as necessary

                # If contours were found, process them
                if contours:
                    for contour in contours:
                        contour = np.flip(contour, axis=1)

                        # Convert coordinates to integers
                        contour = [(int(x), int(y)) for x, y in contour]

                        # Filter to keep only start and end points of straight lines
                        filtered_contour = []
                        if len(contour) > 1:
                            filtered_contour.append(contour[0])  # Always add the first point
                            for i in range(1, len(contour) - 1):
                                if not is_collinear(contour[i-1], contour[i], contour[i+1]):
                                    filtered_contour.append(contour[i])  # Add the point if not collinear
                            filtered_contour.append(contour[-1])  # Always add the last point
                        
                        # Append filtered coordinates to mask_data
                        mask_data.append(filtered_contour)

            # Add mask data to all_frame_data with the frame number as the key
            all_frame_data[frame_number[out_frame_idx]] = mask_data

        # Sort the all_frame_data dictionary according to the order in frame_number
        sorted_frame_data = {frame_number[i]: all_frame_data[frame_number[i]] for i in range(len(frame_number)) if frame_number[i] in all_frame_data}

        # Construct the filename for saving the mask data as a single JSON file
        json_file = os.path.join(self.working_dir, self.options[self.ann_obj_id], "masks.json")

        # Save the sorted all_frame_data dictionary to a JSON file
        with open(json_file, 'w') as f:
            json.dump(sorted_frame_data, f, indent=4)  # Save with pretty printing
            

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

