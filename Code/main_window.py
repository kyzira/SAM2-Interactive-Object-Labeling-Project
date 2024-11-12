import tkinter as tk
from tkinter import simpledialog
from PIL import Image, ImageTk
import os
from image_view import ImageView
from annotation_window import AnnotationWindow
from math import sqrt
from json_read_write import JsonReadWrite


class ImageGridApp:
    def __init__(self, root, sam_model, next_callback):
        self.root = root
        self.root.title("Grid SAM Labeling Tool")

        self.next_callback = next_callback

        self.grid_size = 3  # Default grid size
        self.max_grid_size = None

        self.frames = []
        self.frame_dir = None

        self.json_read_write = None

        self.create_widgets()
        self.root.bind("<MouseWheel>", self.on_scroll)
        self.root.bind("<Escape>", self.reset_left_click_modes)

        self.sam_model = sam_model
        self.annotation_window = None
        self.observations = ["BBA 0", "BCA 0"]
        self.button_states = {}
        self.selected_observation = None

        self.left_click_modes = {
            "Splitting" : False,
            "Delete Split" : False,
            "Deleting" : False,
            "Marking Up" : False
        }
        self.left_click_mode_colors = {
            "Splitting" : "lightblue",
            "Delete Split" : "indigo",
            "Deleting" : "darkred",
            "Marking Up" : "lightcoral"
        }

        self.split_intervals = {}
        self.marked_frames = []
        self.split_start = None
        self.split_end = None


        self.annotation_window_geometry_data = {
            "Maximized" : False,
            "Geometry" : None
        }

    def init_frames(self, frame_dir:str):
        self.frames = []
        self.frame_dir = frame_dir
        if not frame_dir:
            print("Error: can not init frames, frame dir empty")
        
        for file in sorted(os.listdir(frame_dir)):
            if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                file_path = os.path.join(frame_dir, file)
                image_view = ImageView(file_path)
                self.frames.append(image_view)
        
        self.root.after(100, self.draw_images_on_grid)
        self.create_bottom_row_widgets(slider_max=(len(self.frames) - (self.grid_size * self.grid_size)))

    def init_settings(self, settings:dict):
        window_width = settings.get("window_width", 800)
        window_height = settings.get("window_height", 600)

        if window_height == 0 and window_width == 0:
            self.root.state("zoomed")
        else:  
            self.root.geometry(f"{window_width}x{window_height}")


        grid_size = settings.get("default_grid_size", 0)
        if grid_size == 0:
            self.grid_size = int(sqrt(len(self.frames))) + 1
        else:
            self.grid_size = grid_size
        self.max_grid_size = int(sqrt(len(self.frames))) + 1

    def init_json(self, table_row={}):
        json_dir = os.path.dirname(self.frame_dir)
        json_path = os.path.join(json_dir, f"{os.path.basename(json_dir)}.json")

        self.json_read_write = JsonReadWrite(json_path, table_row)

        # Load Info for all frames
        self.add_overlay_to_frames()

    def init_add_observations_menu(self, object_add_buttons:list):
        for observation in object_add_buttons:
            self.add_menu.add_command(label=f"Add {observation}", command=lambda n=observation: self.add_observation(observation=n))

        self.create_first_row_widgets()
        self.create_second_row_widgets()



    def create_widgets(self):
        # Configure grid layout for the root window
        self.root.grid_rowconfigure(2, weight=1)  # Middle frame resizes
        self.root.grid_columnconfigure(0, weight=1)  # Frames span full width

        # Create a menu
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        self.add_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Add Options", menu=self.add_menu)
        self.add_menu.add_command(label="Add <Text>", command=self.add_observation)
        
        # Add options to change grid size
        grid_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Grid Options", menu=grid_menu)
        grid_menu.add_command(label="Reload Grid", command=self.draw_images_on_grid)
        grid_menu.add_command(label="Redraw Images", command=self.draw_overlays_on_image_views)
        grid_menu.add_command(label="Change Grid Size", command=self.prompt_grid_size)

        left_click_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Left Click Options", menu=left_click_menu)
        left_click_menu.add_command(label="Mark up Frames", command=lambda n="Marking Up": self.set_left_click_mode(n))
        left_click_menu.add_command(label="New Split", command=lambda n="Splitting": self.set_left_click_mode(n))
        left_click_menu.add_command(label="Delete Split", command=lambda n="Delete Split": self.set_left_click_mode(n))
        left_click_menu.add_command(label="Delete Label", command=lambda n="Deleting": self.set_left_click_mode(n))

        # Top frame
        self.first_row_frame = tk.Frame(self.root, bg="lightgrey", height=50)
        self.first_row_frame.grid(row=0, column=0, sticky="nsew")
        self.root.grid_columnconfigure(0, weight=1)  # Configure column weight

        # Additional frame next to the first row frame
        self.second_half_frame = tk.Frame(self.root, bg="lightgrey", height=50)
        self.second_half_frame.grid(row=0, column=1, sticky="nsew")
        self.root.grid_columnconfigure(1, weight=1)  # Configure column weight
        self.create_second_half_widgets()
        

        # second frame
        self.second_row_frame = tk.Frame(self.root, bg="lightgrey", height=50)
        self.second_row_frame.grid(row=1, column=0, columnspan=2, sticky="nsew")
        self.second_row_frame.grid_columnconfigure(0, weight=1)        

        # Middle frame for images with dynamic grid
        self.middle_frame = tk.Frame(self.root, bg="white")
        self.middle_frame.grid(row=2, column=0, columnspan=2, sticky="nsew")
        
        # Bottom frame
        self.bottom_frame = tk.Frame(self.root, bg="lightgrey", height=50)
        self.bottom_frame.grid(row=3, column=0, columnspan=2, sticky="nsew")


    def create_first_row_widgets(self):
        for widget in self.first_row_frame.winfo_children():
            widget.destroy()

        first_button_selected = False

        for observation in self.observations:
            if observation not in self.button_states:
                self.button_states[observation] = {}

            # Create the button
            button = tk.Button(
                self.first_row_frame,
                text=observation,
                command=lambda n=observation: self.on_observation_button_pressed(n),
                height=2,
                width=10
            )
            button.pack(side="left", padx=5, pady=5)

            self.button_states[observation]["Button"] = button

            # Ensure the button stays in the same state as it was before, only reset if the state is new
            if "Selected" not in self.button_states[observation]:
                self.button_states[observation]["Selected"] = False
                button.config(relief="raised")  # Default state for new button
            elif self.button_states[observation]["Selected"]:
                button.config(relief="sunken")  # Selected state
                first_button_selected = True

        # Autoselect first button if none are selected
        if not first_button_selected and self.observations:
            first_observation = self.observations[0]
            self.button_states[first_observation]["Selected"] = True
            self.button_states[first_observation]["Button"].config(relief="sunken")
            self.selected_observation = first_observation

    def create_second_half_widgets(self):
        # Create the button
        self.next_button = tk.Button(self.second_half_frame, text="Next", command=lambda: self.close_window(), height=2, width=10).pack(side="right", padx=5, pady=5)
        self.skip_button = tk.Button(self.second_half_frame, text="Skip", command=lambda: self.close_window(skip=True), height=2, width=10).pack(side="right", padx=5, pady=5)
        self.start_tracking_button = tk.Button(self.second_half_frame, text="Start Tracking", command=lambda: print, height=2, width=10, bg="palegreen").pack(side="right", padx=25, pady=5)



    def create_second_row_widgets(self):
        for widget in self.second_row_frame.winfo_children():
            widget.destroy()

        colors = [
            "red",  # Red
            "blue",  # Blue
            "green",  # Green
            "yellow",  # Yellow
            "magenta"   # Magenta
        ]

        # Add buttons with colors based on their index
        for idx, observation in enumerate(self.observations):
            color = colors[idx % len(colors)]  # Cycle colors if there are more observations
            
            button = tk.Button(
                self.second_row_frame,
                bg=color,
                command=lambda n=observation: self.on_visibility_button_pressed(n),
                height=2,
                width=10
            )
            button.pack(side="left", padx=5, pady=5)

            self.button_states[observation]["Visibility Button"] = button

            # Handle the button's visibility and state
            if self.button_states[observation].get("Visible") == True:
                self.button_states[observation]["Visibility Button"].config(relief="sunken", bg=color)
            elif self.button_states[observation].get("Visible") == False:
                self.button_states[observation]["Visibility Button"].config(relief="raised", bg="lightgrey")
            else:
                self.button_states[observation]["Visible"] = True
                self.button_states[observation]["Visibility Button"].config(relief="sunken", bg=color)

            self.button_states[observation]["Color"] = color



    def create_bottom_row_widgets(self, slider_max=0):
        for widget in self.bottom_frame.winfo_children():
            widget.destroy()
        # Slider for image navigation
        self.slider = tk.Scale(self.bottom_frame, from_=0, to=slider_max, orient="horizontal", command=self.on_slider_change, length=200)
        self.slider.pack(side="left", padx=10, pady=10)
        tk.Button(self.bottom_frame, text="<", command=lambda: self.set_scale_value(add_value=-int(self.grid_size)), width=5).pack(side="left", pady=10, padx=5)
        tk.Button(self.bottom_frame, text=">", command=lambda: self.set_scale_value(add_value=int(self.grid_size)), width=5).pack(side="left", pady=10, padx=5)
        
    def add_observation(self, observation=None):
        if observation == None:
            observation = simpledialog.askstring("Add Observation", "Add Observation:")

        counter = 0
        new_observation = f"{observation} {counter}"

        while new_observation in self.observations:
            counter += 1
            new_observation = f"{observation} {counter}" 

        if observation not in self.observations:
            self.observations.append(new_observation)   
        
        self.create_first_row_widgets()
        self.create_second_row_widgets()


    def add_overlay_to_frames(self):
        json_data = self.json_read_write.get_json()

        for image_view in self.frames:
            frame_num = image_view.get_frame_num()
            frame_data = json_data.get(str(int(frame_num)))

            if frame_data == None:
                continue
            
            image_view.set_data(frame_data["Observations"])
        
        self.draw_overlays_on_image_views()


    def on_image_left_click(self, event):
        # Calculate the row and column from the event
        if not (self.root and self.root.winfo_exists()):  # Ensure root still exists
            return

        row = event.widget.grid_info()["row"]
        col = event.widget.grid_info()["column"]

        # Rest of the function code
        img_index = (self.slider.get()) + (col) + (row * self.grid_size)
        print(f"Clicked Image Index: {img_index}")
        
        
        if self.left_click_modes.get("Marking Up"):
            if self.frames[img_index].get_border_value("Marked") == False:
                self.marked_frames.append(img_index)
                self.frames[img_index].draw_border(side="top", color="red_full")
                self.frames[img_index].set_border(self.selected_observation, "Marked", True)

            elif self.frames[img_index].get_border_value("Marked") == True:
                self.marked_frames.append(img_index)
                self.frames[img_index].set_border(self.selected_observation, "Marked", False)
                self.frames[img_index].draw(self.button_states)


        elif self.left_click_modes.get("Splitting"):
            # Check that current split is not inside other split
            if self.selected_observation in self.split_intervals:
                for start, end in self.split_intervals[self.selected_observation]:
                    if start <= img_index <= end:
                        self.reset_left_click_modes()
                        return

            # If not returned because selected point in other split:
            if self.split_start is None:
                self.split_start = img_index
                self.frames[img_index].draw_border(side="left", color="blue_full")
                self.frames[img_index].set_border(self.selected_observation, "Border Left", True)
                
            elif self.split_end is None:
                self.split_end = img_index
                self.frames[img_index].draw_border(side="right", color="blue_full")
                self.frames[img_index].set_border(self.selected_observation, "Border Right", True)
                
                intervall_list = self.split_intervals.get(self.selected_observation, [])
                intervall_list.append((self.split_start, self.split_end))
                self.split_intervals[self.selected_observation] = intervall_list

                self.split_start = None
                self.split_end = None
                self.reset_left_click_modes(event)

        elif self.left_click_modes.get("Delete Split"):
            for start, end in self.split_intervals[self.selected_observation]:
                if start <= img_index <= end:
                    self.split_intervals[self.selected_observation].remove((start, end))
                    self.frames[start].set_border(self.selected_observation, "Border Left", False)
                    self.frames[start].draw(self.button_states)
                    self.frames[end].set_border(self.selected_observation, "Border Right", False)
                    self.frames[end].draw(self.button_states)
                    self.reset_left_click_modes(event)
                    break

        elif self.left_click_modes.get("Deleting"):
            print            
        else:
            self.open_annotation_window(img_index)

        self.draw_images_on_grid()
        
    
    def on_scroll(self, event):
        # Check if the Ctrl key is held down during the scroll
        ctrl_pressed = event.state & 0x4  # Check if Ctrl is pressed (0x4 is the mask for Ctrl)


        if ctrl_pressed:
            if event.delta < 0:
                if self.grid_size < self.max_grid_size:
                    self.grid_size += 1
            else:
                if self.grid_size > 1:
                    self.grid_size -= 1
            self.draw_images_on_grid()
        else:
            if self.grid_size == self.max_grid_size:
                return
            
            if event.delta > 0:
                self.set_scale_value(add_value=1)
            else:
                self.set_scale_value(add_value=-1)

    def on_slider_change(self, value):
        self.draw_images_on_grid(value)

    def on_annotation_window_close(self):
        # save settings
        points, polygons = self.annotation_window.get_points_and_labels()
        self.annotation_window_geometry_data["Maximized"], self.annotation_window_geometry_data["Geometry"] = self.annotation_window.get_geometry()
        index = self.annotation_window.get_index()

        observation_data = {
            "Mask Polygon": polygons,
            "Points": points
        }

        self.frames[index].add_to_data(self.selected_observation, observation_data)
        
        
        # Clean up any resources or state related to the AnnotationWindow
        self.annotation_window.annotation_window.destroy()
        self.annotation_window = None
        print("Annotation Window closed")

        self.draw_overlays_on_image_views()

        
        

    def on_observation_button_pressed(self, observation):
        if observation not in self.button_states:
            return

        for button in self.button_states.values():
            button["Button"].config(relief="raised")
            button["Selected"] = False

        self.button_states[observation]["Selected"] = True
        self.button_states[observation]["Button"].config(relief="sunken")

        self.selected_observation = observation
        self.reset_left_click_modes()
        self.draw_overlays_on_image_views()



    def on_visibility_button_pressed(self, observation):
        visible = self.button_states[observation]["Visible"]

        if visible == False:
            self.button_states[observation]["Visible"] = True
            self.button_states[observation]["Visibility Button"].config(relief="sunken", bg=self.button_states[observation]["Color"])
        elif visible == True:
            self.button_states[observation]["Visible"] = False
            self.button_states[observation]["Visibility Button"].config(relief="raised", bg="lightgrey")
        
        self.draw_overlays_on_image_views()
            
    def open_annotation_window(self, index):
        img_view = self.frames[index]

        img_view.reset_drawn_image()
        data = img_view.get_data()
        
        if not data.get(self.selected_observation):
            data[self.selected_observation] = {}

        if data[self.selected_observation].get("Mask Polygon"):
            img_view.draw_polygon(polygons=data[self.selected_observation]["Mask Polygon"],
                                  color=self.button_states[self.selected_observation].get("Color"))

        # Create a new AnnotationWindow instance
        self.annotation_window = AnnotationWindow(img_view, color=self.button_states[self.selected_observation].get("Color"))
        self.annotation_window.init_window(self.annotation_window_geometry_data)
        self.annotation_window.init_sam(index, self.observations.index(self.selected_observation), self.sam_model)

        # Bind the window close event to a custom method
        self.annotation_window.annotation_window.protocol("WM_DELETE_WINDOW", self.on_annotation_window_close)
        self.annotation_window.annotation_window.mainloop()

    def set_left_click_mode(self, mode):
        self.middle_frame.config(background=self.left_click_mode_colors.get(mode, "goldenrod"))

        for key in self.left_click_modes.keys():
            if key == mode:
                self.left_click_modes[key] = True
            else:
                self.left_click_modes[key] = False

    def reset_left_click_modes(self, event=None):
        for keys in self.left_click_modes.keys():
            self.left_click_modes[keys] = False

        self.split_start = None
        self.split_end = None
        self.middle_frame.config(background="white")

        

    def update_grid(self, grid_size=None):
        if grid_size is None:
            grid_size = self.grid_size
        else:
            self.grid_size = grid_size

        # Clear existing widgets in the middle frame
        if self.middle_frame:
            for widget in self.middle_frame.winfo_children():
                widget.destroy()

        # Calculate cell dimensions based on middle_frame's current size
        cell_width = self.middle_frame.winfo_width() // grid_size
        cell_height = self.middle_frame.winfo_height() // grid_size

        if cell_width < 1 or cell_height < 1:
            print("Invalid cell dimensions, skipping grid update")
            return False

        # Configure grid rows and columns
        for r in range(self.grid_size):
            self.middle_frame.grid_rowconfigure(r, weight=1)
            for c in range(self.grid_size):
                self.middle_frame.grid_columnconfigure(c, weight=1)

        return cell_width, cell_height  # Return cell dimensions for use in draw_images_on_grid
    
    def draw_overlays_on_image_views(self):
        for image_view in self.frames:
            image_view.draw(self.button_states)
        
        self.root.after(200, self.draw_images_on_grid)


    def draw_images_on_grid(self, start_index=0):
        cell_dimensions = self.update_grid()
        if not cell_dimensions:
            return  # If grid update failed, exit early

        cell_width, cell_height = cell_dimensions
        image_count = len(self.frames)

        # Store references to images to prevent garbage collection
        self.image_references = []

        # Set start index from slider if not specified
        if start_index:
            start_index = int(start_index)
        else:
            start_index = self.slider.get()

        # Ensure we do not exceed the number of available images
        if start_index + self.grid_size * self.grid_size > image_count:
            if self.grid_size != self.max_grid_size:
                return

        # Populate grid with images or "No Image" placeholders
        image_index = 0
        for r in range(self.grid_size):
            for c in range(self.grid_size):
                if image_index < image_count:
                    # Load and resize the image
                    image = self.frames[image_index + start_index].get_drawn_image()
                    image = image.resize((cell_width, cell_height), Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(image)

                    # Store the reference to the image
                    self.image_references.append(photo)

                    # Create a label with the image
                    label = tk.Label(self.middle_frame, image=photo, borderwidth=1, relief="solid")
                    label.grid(row=r, column=c, sticky="nsew", padx=1, pady=1)

                    # Bind click event to each label
                    label.bind("<Button-1>", self.on_image_left_click)

                    image_index += 1
                else:
                    # Display "No Image" text if no image is available
                    label = tk.Label(self.middle_frame, text="No Image", borderwidth=1, relief="solid", anchor="center")
                    label.grid(row=r, column=c, sticky="nsew", padx=1, pady=1)


    def prompt_grid_size(self):
        # Prompt the user to input new grid dimensions
        grid_size = simpledialog.askinteger("Grid Size", "Enter Grid Size:", minvalue=1, maxvalue=10)
        if grid_size:
            self.grid_size = grid_size
            self.draw_images_on_grid()

    def set_scale_value(self, value=None, add_value=None):
        max_value = self.slider.cget("to")
        
        if add_value and not value:
            value = self.slider.get() + add_value
            value = min(value, max_value)
            value = max(value, 0)
        if value >= 0:
            self.slider.set(value)

        self.on_slider_change(value)


    def save_to_json(self):
        for img_view in self.frames:
            data = img_view.get_data()
            for observation, observation_data in data.items():
                self.json_read_write.add_to_frame(frame_name=img_view.get_image_name(),
                                                  observation=observation,
                                                  observation_data=observation_data)
        

        self.json_read_write.add_to_info("Marked Frames", self.marked_frames)
        self.json_read_write.add_to_info("Instance Intervals", self.split_intervals)

        self.json_read_write.save_json_to_file()


    def close_window(self, skip=False):
        if skip:
            self.json_read_write.add_to_info(key="Skipped", value="True")
        
        self.next_callback()