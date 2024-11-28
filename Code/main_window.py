import tkinter as tk
from tkinter import simpledialog, ttk
from PIL import Image, ImageTk
import os
from image_info import ImageInfo
from draw_image_info import DrawImageInfo
from damage_info import DamageInfo
from annotation_window import AnnotationWindow
from math import sqrt
from json_annotation_manager import JsonAnnotationManager
from frame_extraction import FrameExtraction
from dataclasses import dataclass, field

@dataclass
class ButtonState:
    button_name: int
    is_selected: bool
    is_visible: bool
    overlay_color: str
    selection_button: tk.Button = field(default=None)
    visibility_button: tk.Button = field(default=None)


class MainWindow:
    """
    This Window shows an Grid of Images.
    """
    def __init__(self):
        super().__init__()

        self.root = tk.Tk()
        self.root.title("Grid SAM Labeling Tool")

        self.next_callback = None
        self.grid_size = 3  # Default grid size
        self.max_grid_size = None

        self.image_infos = []
        self.frame_dir = None
        self.frame_extractor = None
        self.json_annotation_manager = None

        self.root.bind("<Escape>", self.__reset_left_click_modes)

        self.sam_model = None
        self.annotation_window = None

        self.observations = []
        self.start_observation = None

        self.advance_buttons = None
        self.evaluation_buttons = None
        self.quick_extraction_buttons = None

        self.button_states = []
        self.selected_observation = None
        self.last_clicked_intervall = None

        self.split_intervals = {}
        self.marked_frames = []
        self.split_start = None
        

        self.left_click_mode = None

        self.left_click_mode_colors = {
            "Splitting" : "blue",
            "Delete Split" : "indigo",
            "Deleting" : "darkred",
            "Marking Up" : "red"
        }

        self.annotation_window_geometry = None
        self.annotation_window_maximized = False

        self.is_set = False

    def setup(self, setup, mode: str):
 
        self.__set_frames(setup.frame_dir)
        self.__set_settings(setup.config["settings"])
        self.__set_segmenter(setup.sam_model)
        self.__set_predefined_object_classes(setup.config["object_add_buttons"])
        self.__set_start_observation(setup.damage_table_row.get("Label"))
        self.__set_json(setup.damage_table_row)
        self.__set_extra_buttons(mode)

        self.is_set = True

    def open(self):
        if self.is_set == False:
            print("Error: Setup not run!")
            return
 
        self.__draw_overlays()
        self.__create_window()
        self.root.title(self.frame_dir)

        self.root.protocol("WM_DELETE_WINDOW", lambda: self.close_window())
        self.root.mainloop()

    def __set_frames(self, frame_dir:str):
        """
        Reads the Folder for frames and creates a list of the frames as image_view instances
        """
        try:
            self.image_infos = []
            self.frame_dir = frame_dir
            if not frame_dir:
                print("Error: can not init frames, frame dir empty")
            
            for file in sorted(os.listdir(frame_dir)):
                if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                    file_path = os.path.join(frame_dir, file)
                    image_info = ImageInfo(file_path)
                    image_info.image_index = len(self.image_infos)
                    image_info.load_image()
                    self.image_infos.append(image_info)
        
        except Exception as e:
            print(f"failed setting frames! \nError: {e}")

    def __set_settings(self, settings:dict):
        """
        Reads the settings dict and sets Window and Grid Size
        """

        try:
            window_width = settings.get("window_width", 800)
            window_height = settings.get("window_height", 600)

            if window_height == 0 and window_width == 0:
                self.root.state("zoomed")
            else:  
                self.root.geometry(f"{window_width}x{window_height}")


            grid_size = settings.get("default_grid_size", 0)
            if grid_size == 0:
                self.grid_size = int(sqrt(len(self.image_infos))) + 1
            else:
                self.grid_size = grid_size
            self.max_grid_size = int(sqrt(len(self.image_infos))) + 1
        
        except Exception as e:
            print(f"failed setting settings! \nError: {e}")

    def __set_json(self, info_dict={}):
        """
        Takes the information given from info_dict and saves it into the Info Key in the Json
        """
        try:
            json_dir = os.path.dirname(self.frame_dir)
            json_path = os.path.join(json_dir, f"{os.path.basename(json_dir)}.json")

            self.json_annotation_manager = JsonAnnotationManager()
            self.json_annotation_manager.load(json_path)
            self.json_annotation_manager.set_info(info_dict)
            self.__load_data_from_json()
        except Exception as e:
            print(f"failed setting json! \nError: {e}")
    

    def __set_segmenter(self, sam_model):
        try:
            self.sam_model = sam_model
            self.sam_model.load(self.frame_dir)
        except Exception as e:
            print(f"failed setting segmenter! \nError: {e}")

    def __set_predefined_object_classes(self, predefined_object_classes:list):
        """
        Takes the object_add_buttons list and adds the entries to the "Add" Drop down menu.
        """
        self.__create_menubar()

        for observation in predefined_object_classes:
            self.add_menu.add_command(label=f"Add {observation}", command=lambda n=observation: self.__add_observation(observation=n))

    def __set_start_observation(self, start_observation: str):
        self.start_observation = start_observation

    def __set_extra_buttons(self, mode):
        if mode == "list_mode":
            advance_buttons = True
            evaluation_buttons = False
            quick_extraction_buttons = True
        elif mode == "test_mode":
            advance_buttons = False
            evaluation_buttons = False
            quick_extraction_buttons = False
        elif mode == "folder_mode":
            advance_buttons = True
            evaluation_buttons = True
            quick_extraction_buttons = True
        else:
            advance_buttons = False
            evaluation_buttons = False
            quick_extraction_buttons = False

        self.advance_buttons = advance_buttons
        self.evaluation_buttons = evaluation_buttons
        self.quick_extraction_buttons = quick_extraction_buttons


    def __load_data_from_json(self):
        json_data = self.json_annotation_manager.get_json()

        self.marked_frames = json_data["Info"].get("Marked Frames", [])
        self.split_intervals = json_data["Info"].get("Instance Intervals", {})

        # Check which Observations already in Json
        for value in json_data.values():
            if "Observations" in value:
                for observation in value["Observations"].keys():
                    if observation not in self.observations:
                        self.observations.append(observation)

        for i, image_info in enumerate(self.image_infos):
            frame_num = image_info.frame_num
            frame_data = json_data.get(str(int(frame_num)))
            image_info.image_index = i

            if frame_data == None:
                continue

            if frame_num in self.marked_frames:
                image_info.is_marked = True

            for observation in self.observations:
                coordinate_dict = frame_data["Observations"].get(observation)

                if not coordinate_dict:
                    continue

                damage_info = DamageInfo(observation)
                damage_info.mask_polygon = coordinate_dict["Mask Polygon"]
                damage_info.positive_point_coordinates = coordinate_dict["Points"]["1"]
                damage_info.negative_point_coordinates = coordinate_dict["Points"]["0"]


                for (begin_frame_index, end_frame_index) in self.split_intervals[observation]:
                    if begin_frame_index <= frame_num <= end_frame_index:
                        damage_info.is_in_intervall = True
                    
                        if begin_frame_index == frame_num:
                            damage_info.is_start_of_intervall = True
                        elif end_frame_index == frame_num:
                            damage_info.is_end_of_intervall = True

                image_info.data_coordinates.append(damage_info)


    def __create_window(self):
        self.__create_layout()

        if self.start_observation:
            self.__add_observation(self.start_observation)
            self.start_observation = None
        else:
            self.__create_observation_widgets()

        self.__create_frame_extraction_widgets()
        self.__create_management_widgets()
        self.root.after(200, self.__create_image_grid)


    def __create_layout(self):
        # Configure grid layout for the root window
        self.root.grid_rowconfigure(2, weight=1)  # Middle frame resizes
        self.root.grid_columnconfigure(0, weight=1)  # Frames span full width

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
        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # Bind mouse wheel scrolling
        self.canvas.bind_all("<MouseWheel>", self.__on_mousewheel)

        # Handle window resizing
        self.middle_frame.bind("<Configure>", self.__resize_images)

        # Status Bar
        self.status_bar = tk.Label(self.root, text="Status: Ready", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.grid(row=3, column=0, columnspan=2, sticky="nsew")  # Status bar spans the bottom row

    def __create_menubar(self):
        # Create a menu
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        self.add_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Add Options", menu=self.add_menu)
        self.add_menu.add_command(label="Add <Text>", command=self.__add_observation)
        
        # Add options to change grid size
        grid_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Grid Options", menu=grid_menu)
        grid_menu.add_command(label="Reload Grid", command=self.__create_image_grid)
        grid_menu.add_command(label="Redraw Images", command=self.__draw_overlays)
        grid_menu.add_command(label="Change Grid Size", command=self.__prompt_grid_size)
        grid_menu.add_command(label="Show Damage Infos", command=self.__print_damage_infos)

        left_click_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Frame Properties", menu=left_click_menu)
        left_click_menu.add_command(label="New Split", command=lambda n="Splitting": self.__set_left_click_mode(n))
        left_click_menu.add_command(label="Mark up Frames", command=lambda n="Marking Up": self.__set_left_click_mode(n))
        left_click_menu.add_command(label="Delete Split", command=lambda n="Delete Split": self.__set_left_click_mode(n))
        left_click_menu.add_command(label="Delete Label", command=lambda n="Deleting": self.__set_left_click_mode(n))


    def __create_observation_widgets(self):
        """Destroy all Buttons first and then recreate buttons for all self.observations entries"""

        if len(self.button_states) > 0:
            for button_state in self.button_states:
                button_state.selection_button.destroy()
                button_state.visibility_button.destroy()

        
        colors = [
            "red",  
            "blue",  
            "green",  
            "yellow",  
            "magenta"
        ]

        print(f"creating observation buttons for: {self.observations}")

        new_button_added = False

        for idx, observation in enumerate(self.observations):
            button_index = None
            for i, button_state in enumerate(self.button_states):
                if observation == button_state.button_name:
                    button_index = i
                    break
            
            color = colors[idx % len(colors)]

            if button_index is None:
                new_button = ButtonState(button_name=observation, is_selected=False, is_visible=True, overlay_color=color)
                self.button_states.append(new_button)
                button_index = len(self.button_states) - 1
                new_button_added = True

            # Create the button and the visibility button
            button = tk.Button(self.first_frame, text=observation, command=lambda n=observation: self.__on_observation_button_pressed(n), height=2, width=10)
            button.pack(side="left", padx=5, pady=5)

            visibility_button = tk.Button(self.second_frame, bg=color, command=lambda n=observation: self.__on_visibility_button_pressed(n), height=2, width=10)
            visibility_button.pack(side="left", padx=5, pady=5)

            if self.button_states[button_index].is_visible == True:
                relief = "sunken"
                color = colors[idx % len(colors)]
            else:
                relief = "raised"
                color = "lightgrey"

            visibility_button.config(relief=relief, bg=color)


            if self.button_states[button_index].is_selected == True:
                button.config(relief="sunken")
            else:
                button.config(relief="raised")


            self.button_states[button_index].selection_button = button
            self.button_states[button_index].visibility_button = visibility_button

        # Autoselect button if newly added
        if new_button_added and self.observations:
            self.__on_observation_button_pressed(observation)


    def __create_management_widgets(self):
        """This function creates the Buttons on the top right."""
        if self.advance_buttons == True:
            self.next_button = tk.Button(self.first_frame, text="Next", command=lambda: self.close_window(), height=2, width=10, bg="indianred")
            self.next_button.pack(side="right", padx=5, pady=5)
            self.skip_button = tk.Button(self.first_frame, text="Skip", command=lambda: self.close_window(skip=True), height=2, width=10, bg="indianred")
            self.skip_button.pack(side="right", padx=5, pady=5)

        if self.evaluation_buttons == True:
            self.good_button = tk.Button(self.first_frame, text="Good", command=lambda: self.__eval_video_tracking(state=True), height=2, width=10, bg="lightgray").pack(side="right", padx=5, pady=5)
            self.bad_button = tk.Button(self.first_frame, text="Bad", command=lambda: self.__eval_video_tracking(state=False), height=2, width=10, bg="lightgray").pack(side="right", padx=5, pady=5)

        self.start_tracking_button = tk.Button(self.first_frame, text="Start Tracking", command=lambda: self.track_object_in_video(), height=2, width=10, bg="palegreen").pack(side="right", padx=5, pady=5)
        self.add_split_button = tk.Button(self.first_frame, text="Add new Split", command=lambda n="Splitting": self.__set_left_click_mode(n), height=2, width=10, bg="lightblue").pack(side="right", padx=5, pady=5)

    def __create_frame_extraction_widgets(self):
        self.extract_from_video = tk.Button(self.second_frame, text="Extract from Video", command=lambda: self.open_extraction_window(), height=2, width=23).pack(side="right", padx=5, pady=5)

        if self.quick_extraction_buttons == True:
            self.extract_forwards = tk.Button(self.second_frame, text="> +10s", command=lambda: self.on_extract_frames(10, False), height=2, width=10).pack(side="right", padx=5, pady=5)
            self.extract_backwards = tk.Button(self.second_frame, text="+10s <", command=lambda: self.on_extract_frames(10, True), height=2, width=10).pack(side="right", padx=5, pady=5)           

    def __create_image_grid(self):
        """Puts the images on the grid."""
        self.image_references = []

        orig_width, orig_height = self.image_infos[0].img_size
        ratio = orig_height/orig_width

        canvas_width = self.canvas.winfo_width()
        cell_width = max((canvas_width - self.grid_size*9)//self.grid_size, 1)

        # Clear the scrollable_frame before adding new labels
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        for i, image_info in enumerate(self.image_infos):
            image = image_info.drawn_image.copy()
            try:
                image = image.resize((cell_width, int(cell_width*ratio)), Image.Resampling.LANCZOS)
            except:
                return
            
            photo = ImageTk.PhotoImage(image)

            # Store the reference to the image
            self.image_references.append(photo)

            label = tk.Label(self.scrollable_frame, image=photo)
            label.grid(row=i // self.grid_size, column=i % self.grid_size, padx=2, pady=2, sticky="nsew")
            label.bind("<Button-1>", self.__on_image_left_click)  # Bind click event
            label.bind("<Button-3>", lambda event: self.__set_left_click_mode("Splitting"))

        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def __print_damage_infos(self):
        observation_index = self.observations.index(self.selected_observation)
        for image_info in self.image_infos:
            print(image_info.image_name)
            print(image_info.data_coordinates[observation_index])


    def __draw_overlays(self):
        """
        for every image: Draws their masks and Borders on the shown image.
        """
        try:
            for image_info in self.image_infos:
                DrawImageInfo(image_info)
            
            self.root.after(200, self.__create_image_grid)
        except: pass

    def __add_observation(self, observation=None):
        if observation == None:
            observation = simpledialog.askstring("Add Observation", "Add Observation:")

        counter = 0
        new_observation = f"{observation} {counter}"

        while new_observation in self.observations:
            counter += 1
            new_observation = f"{observation} {counter}" 

        if observation not in self.observations:
            self.observations.append(new_observation)   

        for image_info in self.image_infos:
            for damage_info in image_info.data_coordinates:
                damage_info.is_selected = False

            damage_info = DamageInfo(self.observations[-1])
            damage_info.is_selected = True
            image_info.data_coordinates.append(damage_info)
        
        self.sam_model.reset_predictor_state()
        self.__create_observation_widgets()


    def __mark_up_mode(self, img_index):
        image_info = self.image_infos[img_index]
        image_info.is_marked = not image_info.is_marked
        DrawImageInfo(image_info)

    def __splitting_mode(self, img_index):
        image_info = self.image_infos[img_index]
        observation_index = self.observations.index(self.selected_observation)
        damage_info = image_info.data_coordinates[observation_index]
        

        # If click is in an other intervall
        if damage_info.is_in_intervall:
            if self.split_start:
                self.image_infos[self.split_start].data_coordinates[observation_index].is_start_of_intervall = False
                DrawImageInfo(self.image_infos[self.split_start])
            self.__reset_left_click_modes()
            return

        # If this is the first click
        elif self.split_start is None:
            self.split_start = img_index
            damage_info.is_start_of_intervall = True
            damage_info.is_in_intervall = True
            DrawImageInfo(self.image_infos[img_index])
            damage_info.is_in_intervall = False
            
        else:
            if img_index < self.split_start:
                self.image_infos[self.split_start].data_coordinates[observation_index].is_start_of_intervall = False
                DrawImageInfo(self.image_infos[self.split_start])
                self.__reset_left_click_modes()
                return

            damage_info.is_end_of_intervall = True
            damage_info.is_in_intervall = True
            DrawImageInfo(self.image_infos[img_index])

            for i in range(self.split_start, img_index + 1):
                image_info = self.image_infos[i]
                image_info.data_coordinates[observation_index].is_in_intervall = True
            
            intervall_list = self.split_intervals.get(self.selected_observation, [])
            intervall_list.append((self.image_infos[self.split_start].frame_num, self.image_infos[img_index].frame_num))
            self.split_intervals[self.selected_observation] = intervall_list       
            self.__reset_left_click_modes()

    def __delete_split_mode(self, img_index):
        image_info = self.image_infos[img_index]
        observation_index = self.observations.index(self.selected_observation)
        damage_info = image_info.data_coordinates[observation_index]

        if damage_info.is_in_intervall == False:
            return
        
        start_of_intervall = None
        end_of_intervall = None

        counter = 0
        if damage_info.is_end_of_intervall:
            end_of_intervall = img_index
        else:
            while damage_info.is_end_of_intervall == False:
                counter += 1
                image_info = self.image_infos[img_index + counter]
                damage_info = image_info.data_coordinates[observation_index]
            end_of_intervall = img_index + counter

        image_info = self.image_infos[img_index]
        damage_info = image_info.data_coordinates[observation_index]
        counter = 0
        if damage_info.is_start_of_intervall:
            start_of_intervall = img_index
        else:
            while damage_info.is_start_of_intervall == False:
                counter += 1
                image_info = self.image_infos[img_index - counter]
                damage_info = image_info.data_coordinates[observation_index]
            start_of_intervall = img_index - counter

        for i in range(start_of_intervall, end_of_intervall + 1):
            new_damage_info = DamageInfo(self.selected_observation)
            new_damage_info.is_selected = True
            self.image_infos[i].data_coordinates[observation_index]  = new_damage_info
            DrawImageInfo(self.image_infos[i])

        self.__reset_left_click_modes()
        
    def __delete_mode(self, img_index):
        image_info = self.image_infos[img_index]
        observation_index = self.observations.index(self.selected_observation)
        damage_info = image_info.data_coordinates[observation_index]

        damage_info.positive_point_coordinates = []
        damage_info.negative_point_coordinates = []
        damage_info.mask_polygons = []

        DrawImageInfo(image_info)

    def __on_image_left_click(self, event):
        """
        Depending on what Mode is Currently Active this either:
        - Marking Up:   Marks Frames with a red Border and lists them in the Info part of the Json
        - Splitting:    Creates Splits with the first clicked image being the start and the second the end for that split
        - Delete Split: Deletes Splits when a frame within a Split is clicked
        - Deleting:     Deletes Masks and Points for the clicked Image

        If no Mode is active, it checks if there are Splits in the Image, if yes and the clicked frame is in one, it opens the Annotation Window.
        If no Split exists, it creates one spanning from start to end and opens the Annotation Window.
        If yes and the clicked frame is not in a split, it does nothing.
        """
                
        # Calculate the row and column from the event
        if not (self.root and self.root.winfo_exists()):  # Ensure root still exists
            return
        
        if self.selected_observation == None:
            simpledialog.messagebox.showinfo("Notification", "Please Select Observation first")
            return

        row = event.widget.grid_info()["row"]
        col = event.widget.grid_info()["column"]

        # Rest of the function code
        img_index = (col) + (row * self.grid_size)
        print(f"Clicked Image Index: {img_index}")

        if self.left_click_mode == "Marking Up":
            self.__mark_up_mode(img_index)
        elif self.left_click_mode == "Splitting":
            self.__splitting_mode(img_index)
        elif self.left_click_mode == "Delete Split":
            self.__delete_split_mode(img_index)
        elif self.left_click_mode == "Deleting":
            self.__delete_mode(img_index)
        else:
            intervall_list = self.split_intervals.get(self.selected_observation, [])
            if len(intervall_list) == 0:
                self.__splitting_mode(0)
                self.__splitting_mode(len(self.image_infos) - 1)
                self.__create_image_grid()
                
            for start, end in self.split_intervals[self.selected_observation]:
                if start <= self.image_infos[img_index].frame_num <= end:
                    clicked_intervall = (start, end)
            try:
                if clicked_intervall != self.last_clicked_intervall:   
                    self.sam_model.reset_predictor_state()
            except:
                print("Clicked Image is in no Intervall!")
                return
            
            try:
                self.next_button.config(state=tk.DISABLED)
                self.skip_button.config(state=tk.DISABLED)
            except:
                pass

            self.__open_annotation_window(img_index)
            self.last_clicked_intervall = clicked_intervall
        self.__create_image_grid()

    def __on_mousewheel(self, event):
        # Check if the Ctrl key is held down during the scroll
        ctrl_pressed = event.state & 0x4  # Check if Ctrl is pressed (0x4 is the mask for Ctrl)

        if ctrl_pressed:
            if event.delta < 0:
                if self.grid_size < self.max_grid_size:
                    self.grid_size += 1
            else:
                if self.grid_size > 1:
                    self.grid_size -= 1
            self.__create_image_grid()
        else:
            # Enable mousewheel scrolling
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
    def __on_observation_button_pressed(self, observation):
        button_exists = False
        for button_state in self.button_states:
            if observation == button_state.button_name:
                button_exists = True
        
        if not button_exists:
            print("Button does not exist!")
            return

        for button_state in self.button_states:
            if button_state.button_name == observation:
                button_state.selection_button.config(relief="sunken")
                button_state.is_selected = True
            else:
                button_state.selection_button.config(relief="raised")
                button_state.is_selected = False
        
        for image_info in self.image_infos:
            for damage_info in image_info.data_coordinates:
                if damage_info.damage_name == observation:
                    damage_info.is_selected = True
                else:
                    damage_info.is_selected = False

        self.selected_observation = observation
        self.sam_model.reset_predictor_state()
        self.__reset_left_click_modes()
        self.__draw_overlays()

    def __on_visibility_button_pressed(self, observation):
        observation_index = self.observations.index(observation)
        button_state = self.button_states[observation_index]

        if button_state.is_visible == True:
            button_state.is_visible = False
            button_state.visibility_button.config(relief="raised", bg="lightgrey")
            for image_info in self.image_infos:
                image_info.data_coordinates[observation_index].is_shown = False
        else:
            button_state.is_visible = True
            button_state.visibility_button.config(relief="sunken", bg=self.button_states[observation_index].overlay_color)
            for image_info in self.image_infos:
                image_info.data_coordinates[observation_index].is_shown = True        
        
        self.__draw_overlays()

    def on_extract_frames(self, time, reverse=False):
        self.frame_extraction.extract_further(extra_seconds_to_extract=abs(time), reverse=reverse)

        self.__reinit_frames()
        self.__set_segmenter(self.sam_model)
        self.__draw_overlays()

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

            self.__reinit_frames()
            self.__set_segmenter(self.sam_model)
            self.__draw_overlays()
                    
    def __open_annotation_window(self, index):
        image_info = self.image_infos[index]

        annotation_window = AnnotationWindow()
        annotation_window.set_settings(self.annotation_window_geometry, self.annotation_window_maximized)
        annotation_window.set_image_info(image_info)
        annotation_window.set_segmenter(self.sam_model, index)

        annotation_window.open()

        self.annotation_window_maximized, self.annotation_window_geometry = annotation_window.get_geometry()
        self.__create_image_grid

    def __set_left_click_mode(self, mode):
        """Sets the currently active mode using a status bar and changes its color."""
        mode_color = self.left_click_mode_colors.get(mode, "goldenrod")  # Default color if mode is not found
        self.status_bar.config(text=f"Current Mode: {mode}", bg=mode_color, fg="white")  # Update text and background
        self.left_click_mode = mode


    def __reset_left_click_modes(self, event=None):
        """Resets the currently active mode and restores default appearance."""
        self.left_click_mode = None
        self.split_start = None
        self.status_bar.config(text="Status: Ready", bg="lightgrey", fg="black")  # Reset status bar

            
    def __prompt_grid_size(self):
        # Prompt the user to input new grid dimensions
        grid_size = simpledialog.askinteger("Grid Size", "Enter Grid Size:", minvalue=1, maxvalue=10)
        if grid_size:
            self.grid_size = grid_size
            self.__create_image_grid()

    def __resize_images(self, event=None):
        self.__create_image_grid()

    def __reinit_frames(self):
        # Get Current Frame list:
        frame_name_list = []
        new_frames = []
        for img_info in self.image_infos:
            frame_name = img_info.image_name
            frame_name_list.append(frame_name)

        for file in sorted(os.listdir(self.frame_dir)):
            if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                image_info = None
                if file in frame_name_list:
                    image_info = self.image_infos[frame_name_list.index(file)]
                else:
                    file_path = os.path.join(self.frame_dir, file)
                    image_info = ImageInfo(file_path)

                new_frames.append(image_info)

        self.image_infos = new_frames

    def track_object_in_video(self):
        """Tracks Objects based on their given Points in their intervalls"""

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
                print(f"\nTracking Object {self.selected_observation} form frame {start} to frame {end}!")
                # Get Index first:
                start_index = next((self.image_infos.index(f) for f in self.image_infos if f.get_frame_num() == start), None)
                end_index = next((self.image_infos.index(f) for f in self.image_infos if f.get_frame_num() == end), None)

                # Check if start_index and end_index are valid
                if start_index is None or end_index is None:
                    print(f"Error: Frame indices for start ({start}) or end ({end}) could not be found.")
                    continue

                # Call propagate_through_interval for each interval and accumulate results
                video_segments = self.sam_model.propagate_through_interval(
                    self.image_infos, self.button_states, start_index, end_index
                )
                if video_segments:
                    all_video_segments.update(video_segments)  # Merge results

                self.sam_model.reset_predictor_state()

        
        # Process each frame in all_video_segments
        for out_frame_idx, masks in all_video_segments.items():
            img_view = self.image_infos[out_frame_idx]
            polygons = []
            for mask in masks.values():
                polygon = img_view.draw_and_convert_masks(mask, self.button_states[self.selected_observation]["Color"])
                polygons.append(polygon)
            
            if len(polygons) == 1:
                polygons = polygons[0]
            img_view.add_to_observation(self.selected_observation, "Mask Polygon", polygons)

        self.__draw_overlays()


    def save_to_json(self):
        """Saves the mask and point date saved in every frame to the json"""
        for img_view in self.image_infos:
            data = img_view.get_data()
            for observation, observation_data in data.items():
                self.json_annotation_manager.add_to_frame(frame_name=img_view.get_image_name(),
                                                  observation=observation,
                                                  observation_data=observation_data)
        

        self.json_annotation_manager.add_to_info("Marked Frames", self.marked_frames)
        self.json_annotation_manager.add_to_info("Instance Intervals", self.split_intervals)

        self.json_annotation_manager.save()


    def __eval_video_tracking(self, state = True):
        """state -> if the video tracking result is good (= True) or bad (= False)"""

        state_name = "Good" if state else "Bad"

        self.json_annotation_manager.add_to_info(key="Segmentation Evaluation",
                                         value=state_name)

        self.close_window()


    def remove_image_view(self):
        self.image_infos = None

    def close_window(self, skip=False):
        """When Next or Skip is clicked, the next_callback function is called to ensure the next video is loaded"""
        if skip:
            self.json_annotation_manager.add_to_info(key="Skipped", value="True")
        
        self.next_callback()