from main_window import ImageGridApp
import tkinter as tk
from sam2_class import Sam
import yaml
import os

def close_window():
    app.root.destroy()
    print("Grid Window closed")

def load_settings() -> dict:
    script_dir = os.path.dirname(os.path.abspath(__file__))  # Get the directory of the current script
    config_path = os.path.join(script_dir, "..", "config.yaml")  # Adjust the path as needed
    with open(config_path, 'r') as config_file:
        config = yaml.safe_load(config_file)
    return config

config = load_settings()

frame_dir = r"C:\Code Python\SAM2-Interactive-Object-Labeling-Project\labeling_project\test folder\source images"

sam_model = Sam(frame_dir, config["sam_model_paths"])


root = tk.Tk()
app = ImageGridApp(root, sam_model)
app.init_frames(r"C:\Code Python\SAM2-Interactive-Object-Labeling-Project\labeling_project\test folder\source images")
app.init_settings(settings=config["settings"])
app.init_add_observations_menu(["BCA", "BBA"])
app.init_json()
app.root.protocol("WM_DELETE_WINDOW", close_window)
root.mainloop()
