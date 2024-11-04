import tkinter as tk
from tkinter import ttk, filedialog
import observation_management
from sam2_class import Sam
from json_read_write import JsonReadWrite 
from frame_info_struct import FrameInfoStruct 
from further_extract_frames import LoadMoreFrames
from extract_frames_from_video import extract_frames_by_frame
import os
from extraction_video_interface import VideoPlayer
from annotation_window import AnnotationWindow
import cv2
import numpy as np
from image_grid_manager import ImageGridManager
import math


class ImageDisplayWindow(tk.Tk):
    def __init__(self, frame_dir=None, video_path=None, frame_rate=None, window_title="View Mode", schadens_kurzel=None, stop_callback=None, sam_paths=dict(), add_object_buttons=[], settings={}):
        super().__init__()

        self.title(window_title)
        self.geometry("1200x1000")
        self.sam_paths = sam_paths
        self.initialized = False
        self.video_path = video_path
        checkbox_vars = {}
        self.stop_callback = stop_callback
        self.marked_frames = []
        self.annotation_window_geomertry = {
            "Maximized": None,
            "Geometry": None
        }

        # Loading Settings
        default_grid_size = settings.get("default_grid_size", 0)
        self.scroll_speed = settings.get("scroll_speed", 1)
        
        # Stores the observations
        self.observations = observation_management.RadioButtonManagement()

        if not frame_dir:
            print("Frame Dir not given, switching to View Mode")
            frame_dir = filedialog.askdirectory(title="Select the Labeled Info Directory",initialdir=os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

            if not frame_dir:
                # If File Dialog had an error
                print("Error: No File Path!")
                return 
            
            # If the Video folder was given:
            if os.path.isdir(os.path.join(frame_dir, "source images")):
                frame_dir = os.path.join(frame_dir, "source images")

            # If neither the Video folder was given, nor the source images folder then quit
            elif os.path.basename(frame_dir) != "source images":
                return 


        

        # Saves Frame information, like the names, filepaths and so on
        self.frame_info = FrameInfoStruct(frame_dir)
        # Manages extraction of further frames on basis of Frame info

        # Loads and interacts with the SAM2 segmentation model
        self.sam_model = Sam(frame_dir, sam_paths)
        self.object_class_id = 0

        # Initializes the json storage file and reads it, if it exists
        json_path = os.path.join(self.frame_info.working_dir, f"{str(os.path.basename(self.frame_info.working_dir))}.json")
        self.json = JsonReadWrite(json_path)
        if self.json.get_load_successful() == 0:
            skip = self.json.json_read_failed()
            if skip:
                self.destroy()
        
        self.marked_frames = self.json.get_marked_frames_from_first_index()

        if schadens_kurzel:
            self.observations.add_observation(schadens_kurzel)

        if not self.json.get_json():
            self.json.prepare_json_with_frames(self.frame_info.get_frame_name_list(), self.observations.get_observation_list())
        else:
            self.check_json_for_observations()

        # Radiobutton variable to store the selected option
        self.radio_var = tk.StringVar()

        # Frame for Radiobuttons and input field
        radio_frame = tk.Frame(self)
        radio_frame.pack(side="top", fill="x", padx=10, pady=5)

        # Radiobuttons container
        self.radio_container = tk.Frame(radio_frame)
        self.radio_container.pack(side="left", padx=10, pady=5)

        self.wait_label = tk.Label(radio_frame, text="", font=("Helvetica", 16), fg="red")
        self.wait_label.pack(side="left", padx=10, pady=5)

        # Button to skip to next label
        self.next_button = ttk.Button(radio_frame, text="Next", command=self.close_window, padding=(10, 10))
        self.next_button.pack(side="right", padx=(5, 5))

        # Button to stop labeling
        self.finish_button = ttk.Button(radio_frame, text="Finish", command=lambda n=True: self.close_window(stop=n), padding=(10, 10))
        self.finish_button.pack(side="right", padx=(5, 5))

        self.skip_button = ttk.Button(radio_frame, text="Skip", command=lambda n=True: self.close_window(skip=n), padding=(10, 10))
        self.skip_button.pack(side="right", padx=(5, 5))

        # Separate Frame for the Buttons
        button_frame = tk.Frame(self)
        button_frame.pack(side="top", fill="x", padx=10, pady=5)

        # Create a style for the button with custom font color
        style = ttk.Style()
        style.configure("Custom.TButton", background="red")

        # Add button
        add_button = ttk.Button(button_frame, text="Add new <Text>", command=self.open_new_obj_window)
        add_button.pack(side="left", padx=(5, 0))

        # Add the predefined Buttons
        if len(add_object_buttons) > 0:
            for obj in add_object_buttons:
                button = ttk.Button(button_frame, text=f"Add new {obj}", command=lambda n=obj: self.read_option_or_display_entry_field(n))
                button.pack(side="left", padx=(5, 0))

        # Button to delete labeling
        self.delete_button = ttk.Button(button_frame, text="Delete unselected label objects", command=self.delete_damage, style="Custom.TButton")
        self.delete_button.pack(side="left", padx=(80))

        # Initialize canvas
        self.canvas = tk.Canvas(self, width=1000, height=800, bg="white")
        self.canvas.pack(fill="both", expand=True)

        # Frame to hold the input field, button, and directory selection
        input_frame = tk.Frame(self)
        input_frame.pack(side="top", fill="x", padx=10, pady=5)

        # Initialize ImageGridManager before creating buttons that call its methods
        self.grid = ImageGridManager(
            canvas=self.canvas,
            image_slider=None,  # Placeholder; will be set after creating the slider
            grid_entry=None,    # Placeholder; will be set after creating the entry
            frame_info=self.frame_info,
            json=self.json,
            observations=self.observations,
            checkbox_vars=checkbox_vars,
            radio_var=self.radio_var
        )

        # Add Previous and Next buttons to navigate images
        self.prev_button = ttk.Button(input_frame, text="<", command=self.grid.prev_images)
        self.prev_button.pack(side="left", padx=(5, 0))

        self.next_button = ttk.Button(input_frame, text=">", command=self.grid.next_images)
        self.next_button.pack(side="left", padx=(5, 0))

        # Short slider (10% of the window width)
        self.image_slider = ttk.Scale(input_frame, from_=0, to=0, orient="horizontal", command=self.grid.slider_update)
        self.image_slider.pack(side="left", fill="x", expand=False, padx=(10, 5), ipadx=24)

        self.more_images_forward = ttk.Button(input_frame, text="Extract next images", command=lambda: self.extract_images(self.video_path, forwards=True))
        self.more_images_forward.pack(side="right", padx=(5, 0))

        self.more_images_back = ttk.Button(input_frame, text="Extract previous images", command=lambda: self.extract_images(self.video_path, forwards=False))
        self.more_images_back.pack(side="right", padx=(5, 0))

        self.more_images_back = ttk.Button(input_frame, text="Extract from Video", command=self.extract_from_video)
        self.more_images_back.pack(side="right", padx=(5, 0))

        # Button for reloading Model
        self.button = ttk.Button(input_frame, text="Reload SAM2", command=self.reload_model)
        self.button.pack(side="right", padx=(5, 0))

        # Button for updating grid
        self.button = ttk.Button(input_frame, text="Update Grid", command=self.grid.reload_grid_and_images)
        self.button.pack(side="right", padx=(5, 0))

        # Entry field for grid size
        self.grid_entry = tk.Entry(input_frame, width=10)

        grid_size = None
        if default_grid_size == 0:
            frame_names = self.frame_info.get_frame_name_list()
            grid_size = str(int(math.sqrt(len(frame_names))))
        else:
            grid_size = default_grid_size

        self.grid_entry.insert(0, int(grid_size))
        self.grid_entry.pack(side="right", fill="x", expand=False, padx=(0, 5))

        # Label for grid size
        tk.Label(input_frame, text="Grid Size:").pack(side="right", padx=(0, 5))

        # After the grid instance is created, link the slider and grid entry
        self.grid.image_slider = self.image_slider  # Set the slider
        self.grid.grid_entry = self.grid_entry  # Set the grid entry



    def reload_model(self):
        # Saves Frame information, like the names, filepaths and so on
        frame_dir = self.frame_info.frame_dir
        self.frame_info = FrameInfoStruct(frame_dir)

        # Loads and interacts with the SAM2 segmentation model
        self.sam_model = Sam(frame_dir, self.sam_paths)
        self.object_class_id = 0

        self.grid.reload_grid_and_images()

    def extract_from_video(self):
        if self.initialized:
            frame_dir = self.frame_info.frame_dir

            start_frame = int(self.frame_info.get_frame_name_list()[0].split(".")[0])
            video_window = tk.Toplevel(self)
            video_window.title("Video Player")
            player = VideoPlayer(video_window, self.video_path, start_frame)
            self.wait_window(video_window)
            start_frame, end_frame = player.get_start_and_end_frame()

            if start_frame == None or end_frame == None:
                return

            for file in os.listdir(frame_dir):
                file_path = os.path.join(frame_dir, file)
                try:
                    if os.path.isfile(file_path):  # Check if it's a file
                        os.remove(file_path)
                except Exception as e:
                    print(f"Error deleting file {file_path}: {e}")
                    
            extract_frames_by_frame(self.video_path, self.frame_info.frame_dir, start_frame, end_frame, frame_rate=25)

            print("Resetting Sam now!")
            self.reload_model()
            self.image_slider.set(0)

            frame_dir = self.frame_info.frame_dir
            self.frame_info = FrameInfoStruct(frame_dir)
            self.grid.frame_info = self.frame_info
            self.grid.reload_grid_and_images()

    

    def extract_images(self, video_path, forwards):
        if self.initialized:
            frame_extraction = LoadMoreFrames(self.frame_info)

            popup = tk.Toplevel()
            popup.title("Processing")

            label = tk.Label(popup, text="Frames are being extracted...")
            label.pack(padx=20, pady=10)

            # Create a progress bar
            progress = ttk.Progressbar(popup, orient="horizontal", length=300, mode="indeterminate")
            progress.pack(pady=10)
            progress.start()  # Start the progress bar animation

            popup.update()

            # Perform the extraction directly without threading
            if forwards:
                frame_extraction.extract_forwards(video_path, 10)
            else:
                frame_extraction.extract_backwards(video_path, 10)

            print("frames have been extracted! Continue resetting Sam")

            # Continue with resetting Sam
            print("Resetting Sam now!")
            self.reload_model()
            self.image_slider.set(0)

            frame_dir = self.frame_info.frame_dir
            self.frame_info = FrameInfoStruct(frame_dir)
            self.grid.frame_info = self.frame_info
            self.grid.reload_grid_and_images()

            # Stop the progress bar and close the popup
            progress.stop()
            popup.destroy()


    def open_new_obj_window(self):
        # Create new Toplevel window
        self.new_window = tk.Toplevel(self)
        self.new_window.title("Add Option")
        
        # Create frame for label and entry
        option_frame = tk.Frame(self.new_window)
        option_frame.pack(padx=10, pady=10)

        # Add label
        tk.Label(option_frame, text="Add option:").pack(side="top", padx=(0, 5))
        
        # Entry field
        self.new_option_entry = tk.Entry(option_frame, width=15)
        self.new_option_entry.pack(side="top", padx=(0, 5))
        self.new_option_entry.focus()

        # Enter Key Press
        self.new_window.bind("<Return>", lambda event: self.add_entry_field_text())

        # Add button
        add_button = ttk.Button(self.new_window, text="Add", command=self.add_entry_field_text,  padding=(10, 0))
        add_button.pack(side="top", pady=(5, 10))

    def add_entry_field_text(self):
        if self.new_option_entry:
            obj = self.new_option_entry.get()
            if self.new_window:
                self.new_window.destroy()
            self.read_option_or_display_entry_field(obj)
        


    def read_option_or_display_entry_field(self, obj):
        # Check if obj is provided or use entry field value
        if not obj: 
            print("Error: No Object given to add!")
        # Add the new option to observations
        self.observations.add_observation(obj)
        self.update_observation_radiobuttons(reset_selection=False)

    
    def update_obj_id_to_selected_observation(self):
        selected_option = self.radio_var.get()
        observation_list = self.observations.get_observation_list()
        if selected_option in observation_list:
            self.object_class_id = observation_list.index(selected_option)
        else:
            self.object_class_id = 0

    def check_json_for_observations(self):
        json_data = self.json.get_json()
        observation_list = self.observations.get_observation_list()
        for frame in json_data.keys():
            if "Observations" not in json_data[frame]:
                continue

            observation = json_data[frame]["Observations"]
            for key in observation.keys():
                if key not in observation_list:
                    observation_list.append(key)
                    self.observations.add_observation(key)

    def update_observation_radiobuttons(self, reset_selection=True):
        # Define the colors for the radio buttons (matching overlay colors)
        colors = [
            (255, 100, 100),   # Red
            (100, 100, 255),   # Blue
            (100, 255, 100),   # Green
            (255, 255, 100),   # Yellow
            (255, 100, 255)    # Magenta
        ]

        # Clear existing radio buttons
        for widget in self.radio_container.winfo_children():
            widget.destroy()

        # Reset Checkbox_vars
        self.grid.checkbox_vars = {}

        observation_list = self.observations.get_observation_list()
        # Create the Radiobuttons in a horizontal layout
        for index, option in enumerate(observation_list):
            # Get the color based on the index and rotate it if there are more options than colors
            color = colors[index % len(colors)]
            color_hex = "#{:02x}{:02x}{:02x}".format(*color)  # Convert RGB to hex

            # Create a frame for each radio button and checkbox
            frame = tk.Frame(self.radio_container)
            frame.pack(side="left", padx=5)

            # Create the radio button
            rb = tk.Radiobutton(frame, text=option, variable=self.radio_var, value=option, bg="white", command=self.radio_button_value_changed)
            rb.pack()

            # Create a Checkbutton below each Radiobutton
            check_var = tk.BooleanVar(value=True)  # Set to True initially (checked)
            checkbox = tk.Checkbutton(frame, variable=check_var, bg=color_hex, command=self.grid.show_selected_images)
            checkbox.pack()

            # Store the check_var in a dictionary with the option as the key
            self.grid.checkbox_vars[option] = check_var

        # Set the default selection to the first option
        if not observation_list:
            return
        
        if reset_selection:
            if not self.radio_var.get() or len(self.radio_var.get())>1:
                self.radio_var.set(observation_list[0])
        else:
            self.radio_var.set(observation_list[-1])


    def delete_damage(self):
        to_delete_list = []
        observation_list = self.observations.get_observation_list()
        for observation in observation_list:
            if not self.grid.checkbox_vars[observation].get():
                to_delete_list.append(observation)

        self.observations.remove_observations(to_delete_list)
        self.json.remove_damages_from_json(to_delete_list)

        json_path = self.json.json_path
        self.json = JsonReadWrite(json_path)

        self.update_observation_radiobuttons(reset_selection=True)
        self.grid.reload_grid_and_images()

    def close_window(self, stop=False, skip=False):
        """Function to stop the program and signal the loop to exit."""
        if not skip:
            self.json.save_json_to_file()
        else:
            self.json.add_to_info(key="Skipped", value="True")

        if self.stop_callback and stop:
            self.stop_callback()  # Call the stop callback to stop the loop
        self.destroy()

    def radio_button_value_changed(self):
        self.update_obj_id_to_selected_observation()
        self.init_sam_with_selected_observation()
        self.grid.reload_grid_and_images()

    def init_sam_with_selected_observation(self):
        points_dict = self.get_points_for_selected_observations()   # load points for selected observation from json
        self.sam_model.reset_predictor_state()   # reset sam state and add new points

        if points_dict:
            self.add_new_points_to_sam(points_dict)

    def add_new_points_to_sam(self, points_dict):
        valid_points = []
        invalid_points = []

        for frame_dict in points_dict.values(): 
            order = frame_dict["Selection Order"]
            if order >= 0:
                valid_points.append((order, frame_dict))
            else:
                invalid_points.append(frame_dict)

           # Sort valid points by "Selection Order"
            valid_points.sort(key=lambda x: x[0])

            # Process points in order: valid first, then invalid (-1)
            for _, frame_dict in valid_points:
                self.sam_model.add_point(frame_dict, self.object_class_id)
            for frame_dict in invalid_points:
                self.sam_model.add_point(frame_dict, self.object_class_id)

    def get_points_for_selected_observations(self):
        points_dict = dict()
        json_data = self.json.get_json()
        sel_observation = self.radio_var.get()

        if len(json_data) == 0:
            return None
        
        for frame_number, frame_data in json_data.items():
            if "Observations" not in frame_data:
                continue

            observations = frame_data["Observations"]
            if sel_observation not in observations:
                continue

            kuerzel_data = observations[sel_observation]
            
            points_list = []
            labels_list = []
            frame_name = frame_data["File Name"]

            if "Points" not in kuerzel_data:
                continue

            if "Selection Order" in kuerzel_data:
                sel_order = kuerzel_data["Selection Order"]
            else:
                sel_order = -1

            pos_points = kuerzel_data["Points"].get("1", [])
            neg_points = kuerzel_data["Points"].get("0", [])
            
            for punkt in pos_points:
                points_list.append(punkt)
                labels_list.append(1)

            for punkt in neg_points:
                points_list.append(punkt)
                labels_list.append(0)

            frame_list = self.frame_info.get_frame_name_list()
            img_index = frame_list.index(frame_name)

            points_dict[frame_number] = {"Image Index" : img_index,
                                        "Points" : points_list,
                                        "Labels" : labels_list,
                                        "Selection Order" : sel_order
                                        }
            
        if len(points_dict) < 0:
            return None
                
        return points_dict

 
    def on_canvas_click(self, event):
        """Handle left click events on the canvas."""
        x, y = event.x, event.y
        cell_width , cell_height, grid_size = self.grid.get_canvas_info()

        row = int(y // cell_height)
        col = int(x // cell_width)

        start_index = int(self.image_slider.get())

        # Calculate the index of the clicked image
        index = row * grid_size + col + start_index

        print(f"Clicked Image index: {index}")
        # Open the selected image in a new window and add points
        
        observations = self.observations.get_observation_list()
        if not len(observations):
            print("No value selected or observation list empty!")
            return
        
        self.open_annotation_window_save_Coordinates(index)
        self.grid.reload_grid_and_images()

    def get_polygon_list(self, img_index):
        json_data = self.json.get_json()
        frame_names = self.frame_info.get_frame_name_list()

        if str(int(frame_names[img_index].split(".")[0])) not in json_data:
            return []
        if self.radio_var.get() not in json_data[str(int(frame_names[img_index].split(".")[0]))]["Observations"]:
            return []
        if "Mask Polygon" not in json_data[str(int(frame_names[img_index].split(".")[0]))]["Observations"][self.radio_var.get()]:
            return []
            
        return json_data[str(int(frame_names[img_index].split(".")[0]))]["Observations"][self.radio_var.get()]["Mask Polygon"]

    def open_annotation_window_save_Coordinates(self, img_index):
        annotation_window = tk.Toplevel(self)
        annotation_window.title(f"Punkte für {self.radio_var.get()} hinzufügen")
        shown_frames = self.frame_info.get_frames()
        annotation_window.grab_set()

        observation_list = self.observations.get_observation_list()
        color_index = observation_list.index(self.radio_var.get())
        polygon_list = self.get_polygon_list(img_index)        
        window = AnnotationWindow(annotation_window, self.annotation_window_geomertry, shown_frames[img_index], img_index, polygon_list, self.object_class_id, self.sam_model, color_index)

        self.wait_window(annotation_window)
        print("Annotation window closed")

        # Save Coordinates
        points, labels, polygons = window.get_points_and_labels()

        self.annotation_window_geomertry["Maximized"], self.annotation_window_geomertry["Geometry"] = window.get_geometry()

        if len(points) > 0 and len(points) == len(labels):
            self.add_info_to_json(img_index, polygons, points, labels)
            
            popup = tk.Toplevel()
            popup.title("Processing")
            label = tk.Label(popup, text="Objects are being tracked...")
            label.pack(padx=20, pady=10)
            popup.grab_set()  
            popup.update()

            self.track_object()
            popup.destroy()



    def add_info_to_json(self, img_index, polygons, points = None, labels = None):
        if img_index == None:
            print("Error: No Image index given to add to json")
            return
        
        pos_points = []
        neg_points = []

        if points:
            for coordinates, label in zip(points, labels):
                if label == 1:
                    pos_points.append(coordinates)
                elif label == 0:
                    neg_points.append(coordinates)

        all_frames = self.frame_info.get_frame_name_list()
        frame_name = all_frames[img_index]
        observation = self.radio_var.get()


        if points and labels:

            self.json.add_frame_to_json(frame_name=frame_name,
                                        observation=observation,
                                        polygons=polygons,
                                        pos_points=pos_points,
                                        neg_points=neg_points,
                                        selection_order=0)
        else:
            self.json.add_frame_to_json(frame_name=frame_name,
                                        observation=observation,
                                        polygons=polygons)
        self.json.save_json_to_file()

    def track_object(self):
        video_segments = self.sam_model.propagate_in_video()

        for out_frame_idx, masks in video_segments.items():
            
            mask_data = []

            for out_mask in masks.values():
                # Remove singleton dimensions
                out_mask = np.squeeze(out_mask)  # Squeeze to remove dimensions of size 1
                
                # Extract contours using OpenCV
                contours, _ = cv2.findContours(out_mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

                for contour in contours:
                    # Simplify the contour using approxPolyDP
                    epsilon = 0.0005 * cv2.arcLength(contour, True)  # Adjust epsilon for simplification level
                    simplified_contour = cv2.approxPolyDP(contour, epsilon, True)

                    # Convert contour points to a list of tuples
                    simplified_contour = [(int(point[0][0]), int(point[0][1])) for point in simplified_contour]
                    
                    mask_data.append(simplified_contour)

            self.add_info_to_json(out_frame_idx, mask_data)
        
        self.json.save_json_to_file()

    def on_key_press(self, event):
        if event.keysym == "Right":
            self.next_images()
        elif event.keysym == "Left":
            self.prev_images()
    
    def on_mousewheel_scroll(self, event):
        amount_of_images = self.frame_info.get_amount_of_frames()
        if event.state & 0x0004:  # Mousewheel + Ctrl
            gridsize = int(self.grid.grid_entry.get())
            if event.delta < 0:
                gridsize = min(gridsize + 1, int(math.sqrt(amount_of_images)))
            else:
                gridsize = max(gridsize - 1, 1)

            self.grid.grid_entry.delete(0, tk.END)
            self.grid.grid_entry.insert(0, f"{gridsize}")

        else:
            index = int(self.grid.image_slider.get())
            if event.delta > 0:
                index = min(index + 1, amount_of_images)
            else:
                index = max(index - 1, 0)
            self.grid.image_slider.set(index)

        self.grid.reload_grid_and_images()


    def run(self):
        """Start the Tkinter event loop."""
        self.initialized = True
        self.update_observation_radiobuttons()
        self.init_sam_with_selected_observation()
        self.canvas.bind("<Button-1>", self.on_canvas_click)  # Bind left click to canvas
        self.canvas.bind("<Button-3>", self.grid.mark_up_image)  # Bind right click to canvas
        self.canvas.bind("<Button-2>", self.grid.delete_label)  # Bind mousewheel click to canvas
        self.bind('<Key>', self.on_key_press)
        self.canvas.bind("<MouseWheel>", self.on_mousewheel_scroll)

        

        self.state("zoomed")    
        self.update_idletasks()
        self.update()
        self.grid.reload_grid_and_images()
        self.mainloop()

if __name__ == "__main__":
    app = ImageDisplayWindow()
    app.run()