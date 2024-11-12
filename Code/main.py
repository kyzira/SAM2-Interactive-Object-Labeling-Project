from main_window import ImageGridApp
import tkinter as tk
from sam2_class import Sam
import yaml
import os


def load_settings() -> dict:
    script_dir = os.path.dirname(os.path.abspath(__file__))  # Get the directory of the current script
    config_path = os.path.join(script_dir, "..", "config.yaml")  # Adjust the path as needed
    with open(config_path, 'r') as config_file:
        config = yaml.safe_load(config_file)
    return config

list_test = {
    "Video Path": "C:\\Code Python\\SAM2-Interactive-Object-Labeling-Project\\labeling_project\\test folder\\test.mp4",
    "Extracted Frame Rate": 25,
    "Inspektions-ID": 1,
    "Videoname": "test.mp4",
    "Rohrmaterial": "Stein",
    "Inspekteur-Name": "Batagan",
    "Rohrprofil": "Rund",
    "Rohrhoehe (mm)": 1,
    "Rohrbreite (mm)": 1,
    "Videohash": 12345,
    "Label": "BBA",
    "Videozeitpunkt (h:min:sec)": "00:00:20",
}

def main():
    config = load_settings()
    frame_dir = r"C:\Code Python\SAM2-Interactive-Object-Labeling-Project\labeling_project\test folder\source images"
    sam_model = Sam(frame_dir, config["sam_model_paths"])

    # Define a function to close the window and update the loop control variable
    def close_window():
        app.save_to_json()
        app.root.destroy()
        print("Grid Window closed and data saved to Json")

    while True:
        # Initialize the flag for each iteration of the loop
        next_run = False

        # Define the callback function that will trigger the next loop iteration
        def run_next_loop():
            nonlocal next_run
            next_run = True
            close_window()  # Close the current window to start the next one

        root = tk.Tk()
        app = ImageGridApp(root, sam_model, run_next_loop)
        app.init_frames(frame_dir)
        app.init_settings(settings=config["settings"])
        app.init_add_observations_menu(config["object_add_buttons"])
        app.init_json(list_test)
        app.root.protocol("WM_DELETE_WINDOW", close_window)

        root.mainloop()  # Start the Tkinter event loop

        # Exit the loop if `next_run` is not set to True
        if not next_run:
            break

if __name__ == "__main__":
    main()
