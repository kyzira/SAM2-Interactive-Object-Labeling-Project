import tkinter as tk
from tkinter import simpledialog, ttk
from PIL import Image, ImageTk
import os
from image_view import ImageView
from annotation_window import AnnotationWindow
from math import sqrt
from json_read_write import JsonReadWrite
from frame_extraction import FrameExtraction


class MainWindow:
    def __init__(self, root, sam_model, next_callback, start_observation = None):
        super().__init__()
        self.root = root
        self.root.title("Grid SAM Labeling Tool")

        self.next_callback = next_callback

        self.grid_size = 3  # Default grid size
        self.max_grid_size = None

        self.frames = []
        self.frame_dir = None

        self.frame_extraction = None

        self.json_read_write = None

        self.create_widgets()
        self.root.bind("<MouseWheel>", self.on_scroll)
        self.root.bind("<Escape>", self.reset_left_click_modes)

        self.sam_model = sam_model
        self.annotation_window = None

        self.observations = []
        if start_observation:
            self.observations.append(start_observation)

        self.button_states = {}
        self.selected_observation = None
        self.last_clicked_intervall = None

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

        self.is_init_completed = False

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
        
        self.root.after(100, self.create_image_grid)

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

        json_data = self.json_read_write.get_json()

        self.marked_frames = json_data["Info"].get("Marked Frames", [])
        self.split_intervals = json_data["Info"].get("Instance Intervals", {})

        for value in json_data.values():
            if "Observations" in value:
                for observation in value["Observations"].keys():
                    if observation in self.observations:
                        continue
                    self.observations.append(observation)

        # Load Info for all frames
        self.root.after(100, self.add_overlay_to_frames())

    def init_add_observations_menu(self, object_add_buttons:list, disable_next_buttons = False, enable_evaluation_buttons = False):
        for observation in object_add_buttons:
            self.add_menu.add_command(label=f"Add {observation}", command=lambda n=observation: self.add_observation(observation=n))

        self.disable_next_buttons = disable_next_buttons
        self.enable_evaluation_buttons = enable_evaluation_buttons

        self.create_first_row_widgets()
        self.create_second_row_widgets()

    def init_frame_extraction_buttons(self, frame_extraction: FrameExtraction, extract_seconds_buttons_enable: bool):
        self.frame_extraction = frame_extraction

        if extract_seconds_buttons_enable:
            self.extract_forwards = tk.Button(self.second_frame, text="> +10s", command=lambda: self.on_extract_frames(10, False), height=2, width=10).pack(side="right", padx=5, pady=5)
            self.extract_backwards = tk.Button(self.second_frame, text="+10s <", command=lambda: self.on_extract_frames(10, True), height=2, width=10).pack(side="right", padx=5, pady=5)

    def init_complete(self):
        self.is_init_completed = True


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
        grid_menu.add_command(label="Reload Grid", command=self.create_image_grid)
        grid_menu.add_command(label="Redraw Images", command=self.draw_overlays_on_image_views)
        grid_menu.add_command(label="Change Grid Size", command=self.prompt_grid_size)

        # Add options to change grid size
        sam_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="SAM2 Options", menu=sam_menu)
        sam_menu.add_command(label="Reset SAM2", command=lambda: self.sam_model.reset_predictor_state())
        sam_menu.add_command(label="Reinit SAM2", command=lambda: self.sam_model.init_predictor_state())

        left_click_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Frame Properties", menu=left_click_menu)
        left_click_menu.add_command(label="New Split", command=lambda n="Splitting": self.set_left_click_mode(n))
        left_click_menu.add_command(label="Mark up Frames", command=lambda n="Marking Up": self.set_left_click_mode(n))
        left_click_menu.add_command(label="Delete Split", command=lambda n="Delete Split": self.set_left_click_mode(n))
        left_click_menu.add_command(label="Delete Label", command=lambda n="Deleting": self.set_left_click_mode(n))

        # Top frame
        self.first_frame = tk.Frame(self.root, bg="lightgrey", height=50)
        self.first_frame.grid(row=0, column=0, sticky="nsew")
        self.root.grid_columnconfigure(0, weight=1)  # Configure column weight

        # second frame
        self.second_frame = tk.Frame(self.root, bg="lightgrey", height=50)
        self.second_frame.grid(row=1, column=0, columnspan=2, sticky="nsew")
        self.second_frame.grid_columnconfigure(0, weight=1)        

        # Middle frame for images with dynamic grid
        self.middle_frame = tk.Frame(self.root, bg="white")
        self.middle_frame.grid(row=2, column=0, columnspan=2, sticky="nsew")

        # Canvas and scrollbar setup
        self.canvas = tk.Canvas(self.middle_frame, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.middle_frame, orient="vertical", command=self.canvas.yview)

        # Place canvas to fill the width of the window
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Place scrollbar to the right of the canvas without overlapping
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Scrollable frame within canvas
        self.scrollable_frame = tk.Frame(self.canvas)
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # Bind mouse wheel scrolling
        self.canvas.bind_all("<MouseWheel>", self.on_mousewheel)

        # Handle window resizing
        self.middle_frame.bind("<Configure>", self.resize_images)
        

    def create_first_row_widgets(self):
        for widget in self.first_frame.winfo_children():
            widget.destroy()

        first_button_selected = False

        for observation in self.observations:
            if observation not in self.button_states:
                self.button_states[observation] = {}

            # Create the button
            button = tk.Button(
                self.first_frame,
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


        # Create the button
        if not self.disable_next_buttons:
            self.next_button = tk.Button(self.first_frame, text="Next", command=lambda: self.close_window(), height=2, width=10, bg="indianred")
            self.next_button.pack(side="right", padx=5, pady=5)
            self.skip_button = tk.Button(self.first_frame, text="Skip", command=lambda: self.close_window(skip=True), height=2, width=10, bg="indianred")
            self.skip_button.pack(side="right", padx=5, pady=5)

        if self.enable_evaluation_buttons:
            self.good_button = tk.Button(self.first_frame, text="Good", command=lambda: self.eval_video_tracking(state=True), height=2, width=10, bg="lightgray").pack(side="right", padx=5, pady=5)
            self.bad_button = tk.Button(self.first_frame, text="Bad", command=lambda: self.eval_video_tracking(state=False), height=2, width=10, bg="lightgray").pack(side="right", padx=5, pady=5)

        self.start_tracking_button = tk.Button(self.first_frame, text="Start Tracking", command=lambda: self.track_object_in_video(), height=2, width=10, bg="palegreen").pack(side="right", padx=5, pady=5)
        self.add_split_button = tk.Button(self.first_frame, text="Add new Split", command=lambda n="Splitting": self.set_left_click_mode(n), height=2, width=10, bg="lightblue").pack(side="right", padx=5, pady=5)

    def create_second_row_widgets(self):
        for widget in self.second_frame.winfo_children():
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
                self.second_frame,
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
        
        self.extract_from_video = tk.Button(self.second_frame, text="Extract from Video", command=lambda: self.open_extraction_window(), height=2, width=23).pack(side="right", padx=5, pady=5)


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
        
        self.sam_model.reset_predictor_state()
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
            
            if frame_num in self.marked_frames:
                image_view.set_border(self.selected_observation, "Marked", True)

            for observation, list in self.split_intervals.items():
                for start, end in list:
                    if start == frame_num:
                        image_view.set_border(observation, "Border Left", True)
                    elif end == frame_num:
                        image_view.set_border(observation, "Border Right", True)

        self.draw_overlays_on_image_views()


    def on_image_left_click(self, event):
        # Calculate the row and column from the event
        if not (self.root and self.root.winfo_exists()):  # Ensure root still exists
            return
        
        if self.selected_observation == None:
            print("Select Observation first")
            return

        row = event.widget.grid_info()["row"]
        col = event.widget.grid_info()["column"]

        # Rest of the function code
        img_index = (col) + (row * self.grid_size)
        print(f"Clicked Image Index: {img_index}")
        
        
        if self.left_click_modes.get("Marking Up"):
            if self.frames[img_index].get_border_value("Marked") == False:
                self.marked_frames.append(self.frames[img_index].get_frame_num())
                self.frames[img_index].draw_border(side="top", color="red_full")
                self.frames[img_index].set_border(self.selected_observation, "Marked", True)

            elif self.frames[img_index].get_border_value("Marked") == True:
                self.marked_frames.remove(self.frames[img_index].get_frame_num())
                print(self.marked_frames)
                self.frames[img_index].set_border(self.selected_observation, "Marked", False)
                self.frames[img_index].draw(self.button_states, self.split_intervals.get(self.selected_observation, []))


        elif self.left_click_modes.get("Splitting"):
            # Check that current split is not inside other split
            if self.selected_observation in self.split_intervals:
                for start, end in self.split_intervals[self.selected_observation]:
                    if start <= self.frames[img_index].get_frame_num() <= end:

                        if self.split_start:
                            self.frames[self.split_start].set_border(self.selected_observation, "Border Left", False)

                        self.reset_left_click_modes()
                        return

            if self.split_start is None:
                self.split_start = img_index
                self.frames[img_index].set_border(self.selected_observation, "Border Left", True)
                self.frames[img_index].draw(self.button_states, self.split_intervals.get(self.selected_observation, []))
                
                
            elif self.split_end is None:
                if img_index >= self.split_start:
                    self.split_end = img_index
                    self.frames[img_index].set_border(self.selected_observation, "Border Right", True)
                    
                    intervall_list = self.split_intervals.get(self.selected_observation, [])
                    intervall_list.append((self.frames[self.split_start].get_frame_num(), self.frames[self.split_end].get_frame_num()))
                    self.split_intervals[self.selected_observation] = intervall_list
                    
                
                else:
                    self.frames[self.split_start].set_border(self.selected_observation, "Border Left", False)

                self.reset_left_click_modes(event)

        elif self.left_click_modes.get("Delete Split"):
            frame_num = self.frames[img_index].get_frame_num()
            intervals_for_observation = self.split_intervals.get(self.selected_observation, [])
            for start, end in intervals_for_observation:
                if start <= frame_num <= end:

                    start_index = self.frames.index(next((f for f in self.frames if f.get_frame_num() == start), None))
                    end_index = self.frames.index(next((f for f in self.frames if f.get_frame_num() == end), None))
                    print(f"to delete start: {start}, end: {end}")
                    self.split_intervals[self.selected_observation].remove((start, end))

                    for i in range(start_index, end_index + 1):
                        img_view = self.frames[i]

                        img_view.set_border(self.selected_observation, "Border Left", False)
                        img_view.set_border(self.selected_observation, "Border Right", False)
                        img_view.pop_observation(self.selected_observation)

                    self.reset_left_click_modes(event)
                    break

        elif self.left_click_modes.get("Deleting"):
            img_view = self.frames[img_index]
            img_view.pop_observation(self.selected_observation)
            print(f"Popped {self.selected_observation} from frame {img_view.get_frame_num()}")
            img_view.draw(self.button_states, self.split_intervals.get(self.selected_observation, []))
        else:
            intervall_list = self.split_intervals.get(self.selected_observation, [])
            if len(intervall_list) == 0:
                intervall_list.append((self.frames[0].get_frame_num(), self.frames[-1].get_frame_num()))
                self.split_intervals[self.selected_observation] = intervall_list

                self.frames[0].set_border(self.selected_observation, "Border Left", True)
                self.frames[-1].set_border(self.selected_observation, "Border Right", True)
                self.draw_overlays_on_image_views()
                

            for start, end in self.split_intervals[self.selected_observation]:
                if start <= self.frames[img_index].get_frame_num() <= end:
                    clicked_intervall = (start, end)
            
            if clicked_intervall != self.last_clicked_intervall:   
                self.sam_model.reset_predictor_state()

            try:
                self.next_button.config(state=tk.DISABLED)
                self.skip_button.config(state=tk.DISABLED)
            except:
                pass

            self.open_annotation_window(img_index)

            self.last_clicked_intervall = clicked_intervall

        self.draw_overlays_on_image_views()
        
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
            self.create_image_grid()

    def on_mousewheel(self, event):
        # Enable mousewheel scrolling
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def on_slider_change(self, value):
        # self.draw_images_on_grid(value)
        print

    def on_annotation_window_close(self):
        # save settings
        points, polygons = self.annotation_window.get_points_and_labels()

        if len(points.get("1", [])) == 0 and len(points.get("0", [])) == 0:
            self.sam_model.reset_predictor_state()

        else:
            self.annotation_window_geometry_data["Maximized"], self.annotation_window_geometry_data["Geometry"] = self.annotation_window.get_geometry()
            index = self.annotation_window.get_index()

            observation_data = {
                "Mask Polygon": polygons,
                "Points": points
            }

            self.frames[index].add_to_data(self.selected_observation, observation_data)
            self.draw_overlays_on_image_views()
        
        # Clean up any resources or state related to the AnnotationWindow
        self.annotation_window.annotation_window.destroy()
        self.annotation_window = None
        print("Annotation Window closed")
        
    def on_observation_button_pressed(self, observation):
        if observation not in self.button_states:
            return

        for button in self.button_states.values():
            button["Button"].config(relief="raised")
            button["Selected"] = False

        self.button_states[observation]["Selected"] = True
        self.button_states[observation]["Button"].config(relief="sunken")

        self.selected_observation = observation
        self.sam_model.reset_predictor_state()
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

    def on_extract_frames(self, time, reverse=False):
        self.frame_extraction.extract_further(extra_seconds_to_extract=abs(time), reverse=reverse)

        self.reinit_frames()
        self.reinit_sam()
        self.draw_overlays_on_image_views()


    def open_extraction_window(self):
        start_frame, end_frame = self.frame_extraction.extract_from_video_player()
        if start_frame or end_frame:

            # Delete images
            for file in os.listdir(self.frame_dir):
                file_path = os.path.join(self.frame_dir, file)
                try:
                    if os.path.isfile(file_path):  # Check if it's a file
                        os.remove(file_path)
                except Exception as e:
                    print(f"Error deleting file {file_path}: {e}")

            self.frame_extraction.extract_frames(start_frame, end_frame, frame_rate=25)

            self.reinit_frames()
            self.reinit_sam()
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
        self.first_frame.config(background=self.left_click_mode_colors.get(mode, "goldenrod"))
        self.second_frame.config(background=self.left_click_mode_colors.get(mode, "goldenrod"))
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
        self.first_frame.config(background="lightgrey")
        self.second_frame.config(background="lightgrey")
    
    def draw_overlays_on_image_views(self):
        try:
            intervals = self.split_intervals.get(self.selected_observation, [])
            for image_view in self.frames:
                image_view.draw(self.button_states, intervals)
            
            self.root.after(200, self.create_image_grid)
        except: pass


    def create_image_grid(self):
        self.image_references = []

        orig_width, orig_height = self.frames[0].get_image_size()
        ratio = orig_height/orig_width

        canvas_width = self.canvas.winfo_width()
        cell_width = max((canvas_width - self.grid_size*9)//self.grid_size, 1)

        # Clear the scrollable_frame before adding new labels
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        for i, img_view in enumerate(self.frames):
            image = img_view.get_drawn_image()
            try:
                image = image.resize((cell_width, int(cell_width*ratio)), Image.Resampling.LANCZOS)
            except:
                return
            photo = ImageTk.PhotoImage(image)

            # Store the reference to the image
            self.image_references.append(photo)

            label = tk.Label(self.scrollable_frame, image=photo)
            label.grid(row=i // self.grid_size, column=i % self.grid_size, padx=2, pady=2, sticky="nsew")
            label.bind("<Button-1>", self.on_image_left_click)  # Bind click event
            label.bind("<Button-3>", lambda event: self.set_left_click_mode("Splitting"))

        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
            

    def prompt_grid_size(self):
        # Prompt the user to input new grid dimensions
        grid_size = simpledialog.askinteger("Grid Size", "Enter Grid Size:", minvalue=1, maxvalue=10)
        if grid_size:
            self.grid_size = grid_size
            self.create_image_grid()

    def set_scale_value(self, value=None, add_value=None):
        max_value = self.slider.cget("to")
        
        if add_value and not value:
            value = self.slider.get() + add_value
            value = min(value, max_value)
            value = max(value, 0)
        if value >= 0:
            self.slider.set(value)

        self.on_slider_change(value)

    def resize_images(self, event=None):
        self.create_image_grid()


    def reinit_sam(self):
        self.sam_model.init_predictor_state()

    def reinit_frames(self):
        # Get Current Frame list:
        frame_name_list = []
        new_frames = []
        for img_view in self.frames:
            frame_name = img_view.get_image_name()
            frame_name_list.append(frame_name)

        for file in sorted(os.listdir(self.frame_dir)):
            if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                image_view = None
                if file in frame_name_list:
                    image_view = self.frames[frame_name_list.index(file)]
                else:
                    file_path = os.path.join(self.frame_dir, file)
                    image_view = ImageView(file_path)

                new_frames.append(image_view)

        self.frames = new_frames



    def track_object_in_video(self):
        # Initialize a dictionary to store all tracked segments
        all_video_segments = dict()

        try:
            self.next_button.config(state=tk.NORMAL)
            self.skip_button.config(state=tk.NORMAL)
        except:
            pass

        if self.selected_observation in self.split_intervals.keys() and len(self.split_intervals[self.selected_observation]) > 0:
            # If the selected observation has intervals
            for start, end in self.split_intervals[self.selected_observation]:
                print(f"\nTracking Object {self.selected_observation} form frame {start} to frame {end}!\n")
                # Get Index first:
                start_index = next((self.frames.index(f) for f in self.frames if f.get_frame_num() == start), None)
                end_index = next((self.frames.index(f) for f in self.frames if f.get_frame_num() == end), None)

                # Check if start_index and end_index are valid
                if start_index is None or end_index is None:
                    print(f"Error: Frame indices for start ({start}) or end ({end}) could not be found.")
                    continue

                # Call propagate_through_interval for each interval and accumulate results
                video_segments = self.sam_model.propagate_through_interval(
                    self.frames, self.button_states, start_index, end_index
                )
                if video_segments:
                    all_video_segments.update(video_segments)  # Merge results

                self.sam_model.reset_predictor_state()

        
        # Process each frame in all_video_segments
        for out_frame_idx, masks in all_video_segments.items():
            img_view = self.frames[out_frame_idx]
            polygons = []
            for mask in masks.values():
                polygon = img_view.draw_and_convert_masks(mask, self.button_states[self.selected_observation]["Color"])
                polygons.append(polygon)
            
            if len(polygons) == 1:
                polygons = polygons[0]
            img_view.add_to_observation(self.selected_observation, "Mask Polygon", polygons)

        self.draw_overlays_on_image_views()


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


    def eval_video_tracking(self, state = True):
        '''
        state -> if the video tracking result is good (= True) or bad (= False)
        '''
        state_name = "Good" if state else "Bad"

        self.json_read_write.add_to_info(key="Segmentation Evaluation",
                                         value=state_name)

        self.close_window()


    def remove_image_view(self):
        for frame in self.frames:
            frame.close_image_view()
        self.frames = None

    def close_window(self, skip=False):
        if skip:
            self.json_read_write.add_to_info(key="Skipped", value="True")
        
        self.next_callback()

