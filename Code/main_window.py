import tkinter as tk
from tkinter import simpledialog
from PIL import Image, ImageTk
import os
from image_view import ImageView
from annotation_window import AnnotationWindow
from math import sqrt
from json_read_write import JsonReadWrite


class ImageGridApp:
    def __init__(self, root, sam_model):
        self.root = root
        self.root.title("Grid SAM Labeling Tool")

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
        self.buttons = {}

        self.left_click_modes = {
            "Splitting" : False,
            "Deleting Split" : False,
            "Deleting" : False,
            "Marking Up" : False
        }
        self.left_click_mode_colors = {
            "Splitting" : "lightblue",
            "Deleting Split" : "indigo",
            "Deleting" : "darkred",
            "Marking Up" : "lightcoral"
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
        
        self.root.after(100, self.draw_images)
        self.create_bottom_row_widgets(slider_max=(len(self.frames) - (self.grid_size * self.grid_size)))

    def init_settings(self, settings:dict):
        window_width = settings.get("window_width", 0)
        window_height = settings.get("window_height", 0)

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

    def init_json(self, default_table_columns=[], table_row={}):
        json_dir = os.path.dirname(self.frame_dir)
        json_path = os.path.join(json_dir, f"{os.path.basename(json_dir)}.json")

        self.json_read_write = JsonReadWrite(json_path, default_table_columns, table_row)

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
        grid_menu.add_command(label="Reload Grid", command=self.draw_images)
        grid_menu.add_command(label="Change Grid Size", command=self.prompt_grid_size)

        left_click_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Left Click Options", menu=left_click_menu)
        left_click_menu.add_command(label="Mark up Frames", command=lambda n="Marking Up": self.set_left_click_mode(n))
        left_click_menu.add_command(label="New Split", command=lambda n="Splitting": self.set_left_click_mode(n))
        left_click_menu.add_command(label="Delete Split", command=lambda n="Deleting Split": self.set_left_click_mode(n))
        left_click_menu.add_command(label="Delete Label", command=lambda n="Deleting": self.set_left_click_mode(n))

        # Top frame
        self.first_row_frame = tk.Frame(self.root, bg="lightgrey", height=50)
        self.first_row_frame.grid(row=0, column=0, columnspan=2, sticky="nsew")
        self.first_row_frame.grid_columnconfigure(0, weight=1)
        

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

        for observation in self.observations:
            if observation not in self.buttons:
                self.buttons[observation] = {}

            # Create the button
            button = tk.Button(
                self.first_row_frame,
                text=observation,
                command=lambda n=observation: self.on_observation_button_pressed(n),
                height=2,
                width=10
            )
            button.pack(side="left", padx=5, pady=5)

            self.buttons[observation]["Button"] = button
            
            # Ensure the button stays in the same state as it was before, only reset if the state is new
            if "Selected" not in self.buttons[observation]:
                self.buttons[observation]["Selected"] = False
                button.config(relief="raised")  # Default state for new button
            elif self.buttons[observation]["Selected"]:
                button.config(relief="sunken")  # Selected state

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

            self.buttons[observation]["Visibility Button"] = button

            # Handle the button's visibility and state
            if self.buttons[observation].get("Visible") == True:
                self.buttons[observation]["Visibility Button"].config(relief="sunken", bg=color)
            elif self.buttons[observation].get("Visible") == False:
                self.buttons[observation]["Visibility Button"].config(relief="raised", bg="lightgrey")
            else:
                self.buttons[observation]["Visible"] = True
                self.buttons[observation]["Visibility Button"].config(relief="sunken", bg=color)

            self.buttons[observation]["Color"] = color



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

            image_view.reset_drawn_image()

            for observation, observation_data in frame_data["Observations"].items():
                color = self.buttons[observation].get("Color", "red")

                image_view.draw_polygon(observation_data.get("Mask Polygon"), color)

                if self.buttons[observation].get("Selected", False):
                    image_view.draw_points(observation_data.get("Points"))
                    # image_view.draw_borders()
        
        self.root.after(100, self.draw_images)



    def on_image_left_click(self, row, col):
        img_index = (self.slider.get()) + (col) + (row * self.grid_size)
        print(f"Clicked Image Index: {img_index}")
        
        if self.left_click_modes.get("Marking Up"):
            print
        elif self.left_click_modes.get("Splitting"):
            print
        elif self.left_click_modes.get("Delete Split"):
            print
        elif self.left_click_modes.get("Deleting"):
            print            
        else:
            self.open_annotation_window(img_index)
    
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
            self.draw_images()
        else:
            if self.grid_size == self.max_grid_size:
                return
            
            if event.delta > 0:
                self.set_scale_value(add_value=1)
            else:
                self.set_scale_value(add_value=-1)

    def on_slider_change(self, value):
        self.draw_images(value)

    def on_annotation_window_close(self):
        # Clean up any resources or state related to the AnnotationWindow
        self.annotation_window.annotation_window.destroy()
        self.annotation_window = None
        print("Annotation Window closed")

        # save settings

    def on_observation_button_pressed(self, observation):
        if observation not in self.buttons:
            return

        for button in self.buttons.values():
            button["Button"].config(relief="raised")
            button["Selected"] = False

        self.buttons[observation]["Selected"] = True
        self.buttons[observation]["Button"].config(relief="sunken")


    def on_visibility_button_pressed(self, observation):
        visible = self.buttons[observation]["Visible"]

        if visible == False:
            self.buttons[observation]["Visible"] = True
            self.buttons[observation]["Visibility Button"].config(relief="sunken", bg=self.buttons[observation]["Color"])
        elif visible == True:
            self.buttons[observation]["Visible"] = False
            self.buttons[observation]["Visibility Button"].config(relief="raised", bg="lightgrey")
            
    def open_annotation_window(self, index):
        img_view = self.frames[index]
        frame_num = img_view.get_frame_num()
        json_data = self.json_read_write.get_json()
        frame_data = json_data.get(frame_num, {})

        # Create a new AnnotationWindow instance
        self.annotation_window = AnnotationWindow(frame_data)
        self.annotation_window.init_image(img_view, color="red")
        self.annotation_window.init_window({})
        self.annotation_window.init_sam(index, 1, self.sam_model)

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

    def reset_left_click_modes(self, event):
        for keys in self.left_click_modes.keys():
            self.left_click_modes[keys] = False
        
        self.middle_frame.config(background="white")

        

    def update_grid(self, grid_size=None):
        if grid_size is None:
            grid_size = self.grid_size
        else:
            self.grid_size = grid_size

        # Clear existing widgets in the middle frame
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

        return cell_width, cell_height  # Return cell dimensions for use in redraw_images


    def draw_images(self, start_index=0):
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
                    label.grid(row=r, column=c, sticky="nsew", padx=5, pady=5)

                    # Bind click event to each label
                    label.bind("<Button-1>", lambda e, row=r, col=c: self.on_image_left_click(row, col))

                    image_index += 1
                else:
                    # Display "No Image" text if no image is available
                    label = tk.Label(self.middle_frame, text="No Image", borderwidth=1, relief="solid", anchor="center")
                    label.grid(row=r, column=c, sticky="nsew", padx=5, pady=5)


    def prompt_grid_size(self):
        # Prompt the user to input new grid dimensions
        grid_size = simpledialog.askinteger("Grid Size", "Enter Grid Size:", minvalue=1, maxvalue=10)
        if grid_size:
            self.grid_size = grid_size
            self.draw_images()

    def set_scale_value(self, value=None, add_value=None):
        max_value = self.slider.cget("to")
        
        if add_value and not value:
            value = self.slider.get() + add_value
            value = min(value, max_value)
            value = max(value, 0)
        if value >= 0:
            self.slider.set(value)

        self.on_slider_change(value)



if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("800x600")
    app = ImageGridApp(root)
    app.init_frames(r"C:\Code Python\SAM2-Interactive-Object-Labeling-Project\labeling_project\test folder\source images")
    root.mainloop()