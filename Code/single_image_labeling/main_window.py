import tkinter as tk
from tkinter import simpledialog, messagebox, ttk
from PIL import Image, ImageTk
import os
from image_info import ImageInfo
from draw_image_info import DrawImageInfo
from damage_info import DamageInfo
from annotation_window import AnnotationWindow
from math import sqrt
from json_annotation_manager import JsonAnnotationManager
from frame_extraction import FrameExtraction
from video_player_window import VideoPlayerWindow
from sam2_class import Sam2Class
import cv2
import numpy as np
from deinterlace_video import DeinterlaceVideo
from small_dataclasses import Setup, ButtonState

class MainWindow:
    """
    This Window shows an Grid of Images.
    """
    def __init__(self):
        super().__init__()

        self.root = tk.Tk()
        self.root.title("Grid SAM Labeling Tool")

        self.image_info = None
        self.frame_dir = None
        self.json_annotation_manager = None

        self.root.bind("<Escape>", self.__reset_left_click_modes)

        self.sam_model = None
        self.annotation_window = None

        self.observations = []
        self.start_observation = None

        self.advance_buttons = None
        self.evaluation_buttons = None

        self.button_states = []
        self.selected_observation = None

        self.split_intervals = {}
        self.marked_frames = []
        self.split_start = None

        self.left_click_mode = None
        self.is_deinterlaced = False

        self.left_click_mode_colors = {
            "Splitting" : "blue",
            "Delete Split" : "indigo",
            "Deleting" : "darkred",
            "Marking Up" : "red"
        }
        self.annotation_window_geometry = None
        self.annotation_window_maximized = False

        self.is_set = False
        self.run_next_loop = False

    def setup(self, setup: Setup, mode: str):
        self.setup_var = setup
        self.mode_var = mode
        self.__set_frames(setup.frame_dir)
        self.__set_settings(setup.config["settings"])
        self.__set_segmenter(setup.sam_model)
        self.__set_predefined_object_classes(setup.config["object_add_buttons"])
        self.__set_start_observation(setup.damage_table_row.get("Label"))
        self.__set_json(setup.damage_table_row)
        self.__set_extra_buttons(mode)
        self.__set_frame_extractor(setup.frame_extraction)

        self.is_set = True
        self.is_deinterlaced = setup.config["settings"].get("auto_deinterlacing", False)
        self.video_path = setup.damage_table_row.get("Videopfad")

    def open(self):
        if self.is_set == False:
            print("Error: Setup not run!")
            return
 
        self.__draw_overlays()
        self.__create_window()
        self.root.title(self.frame_dir)

        self.root.protocol("WM_DELETE_WINDOW", lambda: self.__close_window())
        self.root.mainloop()

    def save_to_json(self):
        """Saves the mask and point date saved in every frame to the json"""
        for image_info in self.image_infos:
            self.json_annotation_manager.add_to_frame(image_info)
        
        self.json_annotation_manager.add_to_info("Marked Frames", self.marked_frames)
        self.json_annotation_manager.add_to_info("Instance Intervals", self.split_intervals)

        self.json_annotation_manager.save()

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

    def __set_frame_extractor(self, frame_extractor: FrameExtraction):
        self.frame_extractor = frame_extractor

        if self.quick_extraction_buttons:
            self.__reset_video_second()
        
    def __set_settings(self, settings: dict):
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
            self.max_grid_size = int(sqrt(len(self.image_infos))) + 3
        
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

    def __set_segmenter(self, sam_model: Sam2Class):
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

        if predefined_object_classes == ["BAB", "BBA", "BCA"]:
            self.add_menu.add_command(label=f"Add Riss", command=lambda n="BAB": self.__add_observation(observation=n))
            self.add_menu.add_command(label=f"Add Wurzel", command=lambda n="BBA": self.__add_observation(observation=n))
            self.add_menu.add_command(label=f"Add Anschluss", command=lambda n="BCA": self.__add_observation(observation=n))
        else:
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
        elif mode == "eval_mode":
            advance_buttons = True
            evaluation_buttons = True
            quick_extraction_buttons = False
        else:
            advance_buttons = False
            evaluation_buttons = False
            quick_extraction_buttons = False

        self.advance_buttons = advance_buttons
        self.evaluation_buttons = evaluation_buttons
        self.quick_extraction_buttons = quick_extraction_buttons

    def __switch_deinterlaced_video(self):
        # First deinterlace video
        self.status_bar.config(text="Status: Switching to/from deinterlaced mode", bg="yellow", fg="black")
        self.root.update()

        if self.is_deinterlaced == False:
            output_dir = os.path.join(self.frame_dir, "..", "..", "..", "deinterlaced videos")
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, os.path.basename(self.video_path))
            DeinterlaceVideo(self.video_path, output_path)
            text = "de-interlaced video"
            self.is_deinterlaced = True
        else:
            text = "original video"
            output_path = self.video_path
            self.is_deinterlaced = False

        self.interlace_status.config(text=text)
        
        # Delete images
        for file in os.listdir(self.frame_dir):
            file_path = os.path.join(self.frame_dir, file)
            try:
                if os.path.isfile(file_path):  # Check if it's a file
                    os.remove(file_path)
            except Exception as e:
                print(f"Error deleting file {file_path}: {e}")

        print(f"Extracting from Video: {output_path}")
        self.frame_extractor.video_path = output_path

        self.frame_extractor.extract_frames_by_damage_time(self.video_start_second, self.video_end_second, self.frame_extractor.extraction_rate)
        self.__reinit_frames()
        self.__reset_video_second()
        self.__draw_overlays()
        self.status_bar.config(text="Status: Ready", bg="lightgrey", fg="black")

    def __switch_histogram_equalization(self):

        self.status_bar.config(text="Status: Switching to/from histogram mode", bg="yellow", fg="black")
        self.root.update()

        # Delete images
        for file in os.listdir(self.frame_dir):
            file_path = os.path.join(self.frame_dir, file)
            try:
                if os.path.isfile(file_path):  # Check if it's a file
                    os.remove(file_path)
            except Exception as e:
                print(f"Error deleting file {file_path}: {e}")

        self.frame_extractor.do_histogram = not self.frame_extractor.do_histogram
        self.frame_extractor.extract_frames_by_damage_time(self.video_start_second, self.video_end_second, self.frame_extractor.extraction_rate)


        self.__reinit_frames()
        self.__reset_video_second()
        self.__draw_overlays()
        self.status_bar.config(text="Status: Ready", bg="lightgrey", fg="black")

    def __load_data_from_json(self):
        """
        Loads Masks and Point for every Frame and loads marked frames and instance intervall from the Info.
        """
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

            if i < len(self.image_infos) -1:
                next_frame_num = self.image_infos[i+1].frame_num
            elif i == len(self.image_infos) -1:
                next_frame_num = self.image_infos[i].frame_num + 1

            frame_data = json_data.get(str(frame_num)) or json_data.get(frame_num)
            image_info.image_index = i


            if frame_data == None:
                for observation in self.observations:
                    damage_info = DamageInfo(observation)
                    image_info.data_coordinates.append(damage_info)
                continue

            if frame_num in self.marked_frames:
                image_info.is_marked = True

            for observation in self.observations:
                new_intervalls = []
                coordinate_dict = frame_data["Observations"].get(observation, dict())
                
                damage_info = DamageInfo(observation)

                if coordinate_dict == dict():
                    image_info.data_coordinates.append(damage_info)
                    continue
                
                damage_info.mask_polygon = coordinate_dict.get("Mask Polygon")
                if "Points" in coordinate_dict:
                    damage_info.positive_point_coordinates = coordinate_dict["Points"].get("1")
                    damage_info.negative_point_coordinates = coordinate_dict["Points"].get("0")

                # When frames are skipped due to similarity, we have to adjust the split intervals
                for begin_frame_num, end_frame_num in self.split_intervals[observation]:
                    val1 = begin_frame_num
                    val2 = end_frame_num
                    print(f"current frame num: {frame_num}, next_frame_num: {next_frame_num}, begin: {begin_frame_num}, end: {end_frame_num}")

                    if frame_num <= begin_frame_num and begin_frame_num < next_frame_num:
                        val1 = frame_num
                        damage_info.is_start_of_intervall = True

                    if frame_num <= end_frame_num and end_frame_num < next_frame_num:
                        val2 = frame_num
                        damage_info.is_end_of_intervall = True

                    new_intervalls.append(val1, val2)

                self.split_intervals[observation] = new_intervalls
                image_info.data_coordinates.append(damage_info)

        # Move start and end of intervall into shown bounds
        smallest_frame_num = self.image_infos[0].frame_num
        largest_frame_num = self.image_infos[-1].frame_num
        
        for index, observation in enumerate(self.observations):
            new_intervalls = []
            for begin_frame_num, end_frame_num in self.split_intervals[observation]:
                val1 = begin_frame_num
                val2 = end_frame_num
                if begin_frame_num <= smallest_frame_num <= end_frame_num:
                    val1 = smallest_frame_num
                    self.image_infos[0].data_coordinates[index].is_start_of_intervall = True
                if begin_frame_num <= largest_frame_num <= end_frame_num:
                    val2 = largest_frame_num
                    self.image_infos[-1].data_coordinates[index].is_end_of_intervall = True
                new_intervalls.append((val1, val2))
            self.split_intervals[observation] = new_intervalls

    def __reload_from_json(self):
        json_data = self.json_annotation_manager.get_json()
        
        self.marked_frames = json_data["Info"].get("Marked Frames", [])
        self.split_intervals = json_data["Info"].get("Instance Intervals", {})

        for i, image_info in enumerate(self.image_infos):
            frame_data = None
            frame_num = image_info.frame_num

            if i < len(self.image_infos) -1:
                next_frame_num = self.image_infos[i+1].frame_num
            elif i == len(self.image_infos) -1:
                next_frame_num = self.image_infos[i].frame_num + 1

            if json_data.get(str(frame_num)):
                frame_data = json_data.get(str(frame_num))
            elif json_data.get(frame_num):
                frame_data = json_data.get(frame_num)
            else: continue

            image_info.image_index = i

            if frame_num in self.marked_frames:
                image_info.is_marked = True

            for data_index, observation in enumerate(self.observations):
                new_intervalls = []
                coordinate_dict = frame_data["Observations"].get(observation)
                
                if coordinate_dict is None:
                    continue
                
                damage_info = image_info.data_coordinates[data_index]

                if coordinate_dict.get("Mask Polygon"):
                    damage_info.mask_polygon = coordinate_dict.get("Mask Polygon")

                if "Points" in coordinate_dict:
                    damage_info.positive_point_coordinates = coordinate_dict["Points"].get("1")
                    damage_info.negative_point_coordinates = coordinate_dict["Points"].get("0")

                # When frames are skipped due to similarity, we have to adjust the split intervals
                for begin_frame_num, end_frame_num in self.split_intervals[observation]:
                    val1 = begin_frame_num
                    val2 = end_frame_num

                    if frame_num <= begin_frame_num and begin_frame_num < next_frame_num:
                        val1 = frame_num
                        damage_info.is_start_of_intervall = True

                    if frame_num <= end_frame_num and end_frame_num < next_frame_num:
                        val2 = frame_num
                        damage_info.is_end_of_intervall = True

                    new_intervalls.append((val1, val2))

                self.split_intervals[observation] = new_intervalls

        # Move start and end of intervall into shown bounds
        smallest_frame_num = self.image_infos[0].frame_num
        largest_frame_num = self.image_infos[-1].frame_num
        
        for index, observation in enumerate(self.observations):
            new_intervalls = []
            for begin_frame_num, end_frame_num in self.split_intervals[observation]:
                val1 = begin_frame_num
                val2 = end_frame_num
                if begin_frame_num <= smallest_frame_num <= end_frame_num:
                    val1 = smallest_frame_num
                    self.image_infos[0].data_coordinates[index].is_start_of_intervall = True
                if begin_frame_num <= largest_frame_num <= end_frame_num:
                    val2 = largest_frame_num
                    self.image_infos[-1].data_coordinates[index].is_end_of_intervall = True
                new_intervalls.append((val1, val2))
            self.split_intervals[observation] = new_intervalls
        
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

        # Status bar frame
        self.status_bar_frame = tk.Frame(self.root, bd=1, relief=tk.SUNKEN)
        self.status_bar_frame.grid(row=3, column=0, columnspan=2, sticky="nsew")  # Status bar spans the bottom row

        # Left-aligned label
        self.status_bar = tk.Label(self.status_bar_frame, text="Status: Ready", anchor=tk.W)
        self.status_bar.grid(row=0, column=0, sticky="nsew", padx=10)

        if self.is_deinterlaced:
            text = "de-interlaced video"
        else:
            text = "original video"

        # Right-aligned label
        self.interlace_status = tk.Label(self.status_bar_frame, text=text, anchor=tk.E)
        self.interlace_status.grid(row=0, column=1, sticky="e", padx=10)

        # Configure grid weights to make the left label expand
        self.status_bar_frame.columnconfigure(0, weight=1)  # Left label stretches
        self.status_bar_frame.columnconfigure(1, weight=0)  # Right label stays fixed

    def __create_menubar(self):
        # Create a menu
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        self.add_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Add Observation", menu=self.add_menu)
        self.add_menu.add_command(label="Add <Text>", command=self.__add_observation)
        
        # Add options to change grid size
        grid_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Options", menu=grid_menu)
        grid_menu.add_command(label="Reload Grid", command=self.__create_image_grid)
        grid_menu.add_command(label="Change Grid Size", command=self.__prompt_grid_size)
        grid_menu.add_command(label="Open frames folder", command=self.__open_frames_dir)
        grid_menu.add_command(label="Switch to/from interlaced Video", command=self.__switch_deinterlaced_video)
        grid_menu.add_command(label="Switch to/from histogram equalization", command=self.__switch_histogram_equalization)

        left_click_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Select Mode", menu=left_click_menu)
        left_click_menu.add_command(label="New Split", command=lambda n="Splitting": self.__set_left_click_mode(n))
        left_click_menu.add_command(label="Mark up Frames", command=lambda n="Marking Up": self.__set_left_click_mode(n))
        left_click_menu.add_command(label="Delete Split", command=lambda n="Delete Split": self.__set_left_click_mode(n))
        left_click_menu.add_command(label="Delete Mask and Points", command=lambda n="Deleting": self.__set_left_click_mode(n))

    def __create_observation_widgets(self):
        """Destroy all Buttons first and then recreate buttons for all self.observations entries"""

        if len(self.button_states) > 0:
            for button_state in self.button_states:
                button_state.selection_button.destroy()
                button_state.visibility_button.destroy()
   
        colors = ["red", "blue", "green", "yellow", "magenta"]

        print(f"creating observation buttons for: {self.observations}")
        new_button_added = False
        rightclick = "<Button-3>"

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
            button.config(relief="sunken") if self.button_states[button_index].is_selected else button.config(relief="raised")

            self.button_states[button_index].selection_button = button
            self.button_states[button_index].visibility_button = visibility_button
            button.bind(rightclick, lambda event, obs=observation: self.__delete_observation(event, obs))

        # Autoselect button if newly added
        if new_button_added and self.observations:
            self.__on_observation_button_pressed(observation)

    def __create_management_widgets(self):
        """This function creates the Buttons on the top right."""
        if self.advance_buttons == True:
            self.next_button = tk.Button(self.first_frame, text="Next", command=lambda: self.__close_window(run_next_loop=True), height=2, width=10, bg="indianred")
            self.next_button.pack(side="right", padx=5, pady=5)
            self.skip_button = tk.Button(self.first_frame, text="Skip", command=lambda: self.__close_window(run_next_loop=True, set_skip=True), height=2, width=10, bg="indianred")
            self.skip_button.pack(side="right", padx=5, pady=5)

        if self.evaluation_buttons == True:
            self.good_button = tk.Button(self.first_frame, text="Good", command=lambda: self.__eval_video_tracking(state=True), height=2, width=10, bg="lightgray").pack(side="right", padx=5, pady=5)
            self.bad_button = tk.Button(self.first_frame, text="Bad", command=lambda: self.__eval_video_tracking(state=False), height=2, width=10, bg="lightgray").pack(side="right", padx=5, pady=5)

        self.start_tracking_button = tk.Button(self.first_frame, text="Start Tracking", command=lambda: self.__track_object_in_video(), height=2, width=10, bg="palegreen").pack(side="right", padx=5, pady=5)
        self.add_split_button = tk.Button(self.first_frame, text="Add new Split", command=lambda n="Splitting": self.__set_left_click_mode(n), height=2, width=10, bg="lightblue").pack(side="right", padx=5, pady=5)

    def __create_frame_extraction_widgets(self):
        self.extract_from_video = tk.Button(self.second_frame, text="Extract from Video", command=lambda: self.__open_extraction_window(), height=2, width=23).pack(side="right", padx=5, pady=5)

        if self.quick_extraction_buttons == True:
            self.extract_forwards = tk.Button(self.second_frame, text="> +10 Frames", command=lambda: self.__on_extract_frames(10, "forward"), height=2, width=10).pack(side="right", padx=5, pady=5)
            self.extract_backwards = tk.Button(self.second_frame, text="+10 Frames <", command=lambda: self.__on_extract_frames(10, "backward"), height=2, width=10).pack(side="right", padx=5, pady=5)           

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

    def __open_frames_dir(self):
        os.startfile(self.frame_dir)

    def __draw_overlays(self):
        """
        for every image: Draws their masks and Borders on the shown image.
        """
        try:
            for image_info in self.image_infos:
                DrawImageInfo(image_info)
            
            self.root.after(200, self.__create_image_grid)
        except Exception as e:
            print(f"Error: Cant draw Overlay: {e}")

    def __add_observation(self, observation=None, skip_reset = False, skip_counting = False):
        if observation == None:
            observation = simpledialog.askstring("Add Observation", "Add Observation:")

        counter = 0
        new_observation = f"{observation} {counter}"

        while new_observation in self.observations:
            counter += 1
            new_observation = f"{observation} {counter}" 

        if skip_counting:
            new_observation = observation

        if observation not in self.observations:
            self.observations.append(new_observation)   

        for image_info in self.image_infos:
            for damage_info in image_info.data_coordinates:
                damage_info.is_selected = False

            damage_info = DamageInfo(self.observations[-1])
            damage_info.is_selected = True
            image_info.data_coordinates.append(damage_info)
        
        if skip_reset == False:
            self.sam_model.reset_predictor_state()
            self.__create_observation_widgets()

    def __mark_up_mode(self, img_index):
        if img_index is None:
            print("Error: No image index given!")
            return
        
        image_info = self.image_infos[img_index]
        image_info.is_marked = not image_info.is_marked
        DrawImageInfo(image_info)

    def __splitting_mode(self, img_index):
        if img_index is None:
            print("Error: No image index given!")
            return
        
        image_info = self.image_infos[img_index]
        observation_index = self.observations.index(self.selected_observation)
        damage_info = image_info.data_coordinates[observation_index]
        
        # If click is in an other intervall
        frame_num = image_info.frame_num
        split_intervals = self.split_intervals.get(self.selected_observation, [])

        for (start_frame_num, end_frame_num) in split_intervals:
            if frame_num < start_frame_num:
                continue
            if frame_num > end_frame_num:
                continue

            if self.split_start:
                self.image_infos[self.split_start].data_coordinates[observation_index].is_start_of_intervall = False
                DrawImageInfo(self.image_infos[self.split_start])
            self.__reset_left_click_modes()
            return

        # If this is the first click
        if self.split_start is None:
            self.split_start = img_index
            damage_info.is_start_of_intervall = True
            DrawImageInfo(self.image_infos[img_index])
            
        else:
            if img_index < self.split_start:
                self.image_infos[self.split_start].data_coordinates[observation_index].is_start_of_intervall = False
                DrawImageInfo(self.image_infos[self.split_start])
                self.__reset_left_click_modes()
                return

            damage_info.is_end_of_intervall = True
            DrawImageInfo(self.image_infos[img_index])

            intervall_list = self.split_intervals.get(self.selected_observation, [])
            intervall_list.append((self.image_infos[self.split_start].frame_num, self.image_infos[img_index].frame_num))
            self.split_intervals[self.selected_observation] = intervall_list   
            self.__reset_left_click_modes()

    def __delete_observation(self, event = None, observation = None):
        if not observation:
            print("Error: No Observation given!")
            return

        response = messagebox.askyesno("Confirm Deletion", f"Are you sure you want to delete '{observation}'?")
        if response:  # If the user clicked "Yes"
            for image_info in self.image_infos:
                image_info.remove_observation(observation)
            
            self.observations.remove(observation)

            for button in self.button_states:
                if button.button_name == observation:
                    button.selection_button.destroy()
                    button.visibility_button.destroy()
                    self.button_states.remove(button)
                    if len(self.button_states) == 0:
                        self.selected_observation = None
                    break

            self.sam_model.reset_predictor_state()
            self.__create_observation_widgets()
            self.__draw_overlays()
            
    def __delete_split_mode(self, img_index):
        if img_index is None:
            print("Error: No image index given!")
            return
        
        image_info = self.image_infos[img_index]
        observation_index = self.observations.index(self.selected_observation)

        # If click is in an intervall
        frame_num = image_info.frame_num
        split_intervals = self.split_intervals.get(self.selected_observation, [])
        intervall = None

        for (start_frame_num, end_frame_num) in split_intervals:
            if frame_num < start_frame_num:
                continue
            if frame_num > end_frame_num:
                continue
            intervall = (start_frame_num, end_frame_num)
            break
        
        if intervall is None:
            return

        for i in range(intervall[0], intervall[1] + 1):
            new_damage_info = DamageInfo(self.selected_observation)
            new_damage_info.is_selected = True
            self.image_infos[i].data_coordinates[observation_index]  = new_damage_info
            DrawImageInfo(self.image_infos[i])

        self.split_intervals[self.selected_observation].remove(intervall)
        self.__reset_left_click_modes()
        
    def __delete_mode(self, img_index):
        """
        Deletes Point and Mask data from clicked image
        """
        if img_index is None:
            print("Error: No image index given!")
            return
        
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
            simpledialog.messagebox.showinfo("no observation selected", "please select or create Observation first")
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

    def __on_extract_frames(self, to_extract_frames: int, direction="forward"):
        """
        This function extracts extra seconds from the video.
        Args:
            to_extract_frames: The given integer is the amount of frames to extract going from the beginning or the end of the cut frames
            direction:  Correct inputs are "forward" and "backward"
                        This determines, if the extra frames are cut from the end going to the end or from the beginning and going to the start of the video
            
        """
        self.status_bar.config(text="Status: Extracting Frames", bg="lightgreen", fg="black")
        self.root.update()
        i = 0
        for i, filename in enumerate(os.listdir(self.frame_dir)):
            file_path = os.path.join(self.frame_dir, filename)  # Get full file path
            try:
                if os.path.isfile(file_path):  # Check if it's a file
                    os.remove(file_path)  # Delete the file
            except Exception as e:
                print(f"Error deleting {file_path}: {e}")

        print(f"removed {i} images!")

        self.frame_extractor.extract_video_segment_by_similarity(self.video_start_second, self.video_end_second, to_extract_frames, 25, direction)

        self.__reinit_frames()
        self.__reset_video_second()
        self.__draw_overlays()
        self.status_bar.config(text="Status: Ready", bg="lightgrey", fg="black")



    def __open_extraction_window(self):
        self.status_bar.config(text="Status: Extracting Frames", bg="lightgreen", fg="black")
        video_player = VideoPlayerWindow(self.frame_extractor.video_path, self.video_start_second)
        video_player.open()
        start_second, end_second = video_player.get_result()

        if start_second is None or end_second is None:
            self.status_bar.config(text="Status: Ready", bg="lightgrey", fg="black")
            return
        
        # Delete images
        for file in os.listdir(self.frame_dir):
            file_path = os.path.join(self.frame_dir, file)
            try:
                if os.path.isfile(file_path):  # Check if it's a file
                    os.remove(file_path)
            except Exception as e:
                print(f"Error deleting file {file_path}: {e}")

        self.frame_extractor.extract_frames_by_damage_time(start_second, end_second, extraction_rate=25)
        self.__reinit_frames()
        self.__reset_video_second()
        self.__draw_overlays()
        self.status_bar.config(text="Status: Ready", bg="lightgrey", fg="black")
                    
    def __open_annotation_window(self, index):
        if index is None:
            print("Error: Can not open annotation window, no index is given!")
            return
        
        image_info = self.image_infos[index]
        self.status_bar.config(text="Status: Labeling Frames", bg="lightgreen", fg="black")

        annotation_window = AnnotationWindow()
        annotation_window.set_settings(self.annotation_window_geometry, self.annotation_window_maximized)
        annotation_window.set_image_info(image_info)
        annotation_window.set_segmenter(self.sam_model, index)

        annotation_window.open()

        self.status_bar.config(text="Status: Ready", bg="lightgrey", fg="black")
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

    def __reset_video_second(self):
        fps = self.frame_extractor.get_fps()
        start_frame = self.image_infos[0].frame_num
        end_frame = self.image_infos[-1].frame_num
        self.video_start_second = int(start_frame / fps)
        self.video_end_second = int(end_frame / fps)

    def __prompt_grid_size(self):
        # Prompt the user to input new grid dimensions
        grid_size = simpledialog.askinteger("Grid Size", "Enter Grid Size:", minvalue=1, maxvalue=10)
        if grid_size:
            self.grid_size = grid_size
            self.__create_image_grid()

    def __resize_images(self, event=None):
        self.__create_image_grid()

    # def __reinit_frames(self):
    #     """
    #     Reinitialize the frames and reload all associated data.
    #     """
    #     try:
    #         # Save observations before clearing
    #         old_observations = self.observations.copy()
    #         selected_observation = self.selected_observation

    #         # Save current data to JSON
    #         self.save_to_json()

    #         # Reinitialize frames
    #         self.__set_frames(self.frame_dir)

    #         # Reload JSON data after frames are reset
    #         self.__load_data_from_json()

    #         # Ensure the segmenter state is reset
    #         self.sam_model.load(self.frame_dir)

    #         # Re-add old observations
    #         for observation in old_observations:
    #             if observation not in self.observations:
    #                 print(f"Re-adding observation: {observation}")
    #                 self.__add_observation(observation)

    #         # Re-select the previously selected observation, if any
    #         if selected_observation:
    #             self.__on_observation_button_pressed(selected_observation)

    #         # Redraw overlays
    #         self.__draw_overlays()

    #         print("Frames reinitialized successfully.")

    #         print(f"Observations: {self.observations}, Intervalls: {self.split_intervals}")
    #     except Exception as e:
    #         print(f"Error during frame reinitialization: {e}")


    def __reinit_frames(self):
        """
        Reinitialize the frames and reload all associated data.
        """
        try:
            # Save observations before clearing
            old_observations = self.observations.copy()
            selected_observation = self.selected_observation

            # Save current data to JSON
            self.save_to_json()

            # Reinitialize frames
            self.__set_frames(self.frame_dir)

            # Re-add observations
            self.observations = []
            for observation in old_observations:
                    self.__add_observation(observation, skip_reset = True, skip_counting = True)

            # Ensure the segmenter state is reset
            self.sam_model.load(self.frame_dir)

            self.__reload_from_json()

            # Re-select the previously selected observation, if any
            if selected_observation:
                self.__on_observation_button_pressed(selected_observation)

            # Redraw overlays
            self.__draw_overlays()

            print("Frames reinitialized successfully.")

            print(f"Observations: {self.observations}, Intervalls: {self.split_intervals}")
        except Exception as e:
            print(f"Error during frame reinitialization: {e}")



    def __track_object_in_video(self):
        """Tracks Objects based on their given Points in their intervalls"""

        # Initialize a dictionary to store all tracked segments
        all_video_segments = dict()
        self.status_bar.config(text="Status: Tracking Object", bg="lightgreen", fg="black")
        self.root.update()

        try:
            self.next_button.config(state=tk.NORMAL)
        except:
            pass

        if self.selected_observation not in self.split_intervals.keys() or len(self.split_intervals[self.selected_observation]) == 0:
            print("Error: No splits available!")
            return

        # If the selected observation has intervals
        for (start_frame_num, end_frame_num) in self.split_intervals[self.selected_observation]:
            print(f"\nTracking Object {self.selected_observation} form frame {start_frame_num} to frame {end_frame_num}")

            # Get Index first:
            start_frame_index = None
            end_frame_index = None
            for index, image_info in enumerate(self.image_infos):
                frame_num = int(image_info.frame_num)
                if int(start_frame_num) == frame_num:
                    start_frame_index = index
                elif int(end_frame_num) == frame_num:
                    end_frame_index = index
                
                if start_frame_index and end_frame_index:
                    break

            # Check if start_frame_index and end_frame_num are valid
            if start_frame_index is None or end_frame_index is None:
                print(f"Error: Frame indices for start ({start_frame_num}) or end ({end_frame_num}) could not be found.")
                print(f"found ones are: {start_frame_index} and {end_frame_index}")
                continue

            # Call propagate_through_interval for each interval and accumulate results
            video_segments = self.sam_model.track_objects(self.image_infos, start_frame_index, end_frame_index)

            if video_segments:
                all_video_segments.update(video_segments)  # Merge results

            self.sam_model.reset_predictor_state()

        self.status_bar.config(text="Status: Ready", bg="lightgray", fg="black")
        
        selected_observation_index = self.observations.index(self.selected_observation)
        # Process each frame in all_video_segments
        for out_frame_idx, masks in all_video_segments.items():
            image_info = self.image_infos[out_frame_idx]
            polygons = []

            for mask in masks.values():
                mask = np.squeeze(mask)  # Squeeze to remove dimensions of size 1
                
                # Extract contours using OpenCV
                contours, _ = cv2.findContours(mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

                for contour in contours:
                    # Simplify the contour using approxPolyDP
                    epsilon = 0.0005 * cv2.arcLength(contour, True)  # Adjust epsilon for simplification level
                    simplified_contour = cv2.approxPolyDP(contour, epsilon, True)

                    # Convert contour points to a list of tuples
                    simplified_contour = [(int(point[0][0]), int(point[0][1])) for point in simplified_contour]
                    polygons.append(simplified_contour)
            image_info.data_coordinates[selected_observation_index].mask_polygon = polygons
        self.__draw_overlays()

    def __eval_video_tracking(self, state = True):
        """state -> if the video tracking result is good (= True) or bad (= False)"""
        state_name = "Good" if state else "Bad"
        self.json_annotation_manager.add_to_info(key="Segmentation Evaluation", value=state_name)
        self.__close_window(run_next_loop=True)

    def __close_window(self, run_next_loop=False, set_skip=False):
        """When Next or Skip is clicked, the run_next_loop bool is set to true to ensure the next video is loaded"""
        if set_skip:
            self.json_annotation_manager.add_to_info(key="Skipped", value="True")

        self.run_next_loop = run_next_loop
        
        self.sam_model.cleanup()
        self.root.quit()
        self.root.destroy()
