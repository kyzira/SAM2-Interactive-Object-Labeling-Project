from main_window import ImageGridApp
from table_and_index import TableAndIndex
from frame_extraction import FrameExtraction
from sam2_class import Sam
import tkinter as tk
from tkinter import filedialog
import yaml
import os


def load_settings() -> dict:
    script_dir = os.path.dirname(os.path.abspath(__file__))  # Get the directory of the current script
    config_path = os.path.join(script_dir, "..", "config.yaml")  # Adjust the path as needed
    with open(config_path, 'r') as config_file:
        config = yaml.safe_load(config_file)
    return config

def extract_frames(frame_extraction: FrameExtraction, table_row: dict, config: dict) -> bool:
    video_zeitpunkt = table_row["Videozeitpunkt (h:min:sec)"].split(":")
    sekunde_zeitpunkt = int(video_zeitpunkt[0]) * 60 * 60 + int(video_zeitpunkt[1]) * 60 + int(video_zeitpunkt[2])
    start_zeitpunkt = sekunde_zeitpunkt - config["settings"].get("frame_extraction_puffer_before", 60)
    end_zeitpunkt = sekunde_zeitpunkt + config["settings"].get("frame_extraction_puffer_after", 10)
    try:
        frame_extraction.extract_frames_by_damage_time(start_zeitpunkt, end_zeitpunkt, config["settings"].get("extraction_frame_per_frames", 25))
        return True
    except Exception as e:
        print(f"An unknown error occurred: {e}")
        return False

def test_mode(config):
    frame_dir = r"C:\Code Python\SAM2-Interactive-Object-Labeling-Project\labeling_project\test folder\source images"
    sam_model = Sam(frame_dir, config["sam_model_paths"])

    # Define a function to close the window and update the loop control variable
    def close_window():
        app.save_to_json()
        app.root.destroy()
        print("Grid Window closed and data saved to Json")

    # Define the callback function that will trigger the next loop iteration
    def run_next_loop():
        close_window()  # Close the current window 

    root = tk.Tk()
    app = ImageGridApp(root, sam_model, run_next_loop)
    app.init_frames(frame_dir)
    app.init_settings(settings=config["settings"])
    app.init_json(config["test_mode_table"])
    app.init_add_observations_menu(config["object_add_buttons"])
    app.draw_overlays_on_image_views()
    app.root.protocol("WM_DELETE_WINDOW", close_window)

    root.mainloop()  # Start the Tkinter event loop




def list_mode(config):
    # Define a function to close the window and update the loop control variable
    def close_window():
        app.save_to_json()
        app.root.destroy()
        print("Grid Window closed and data saved to Json")

    table_and_index = TableAndIndex(config["default_paths"])

    current_index = table_and_index.get_current_index()
    max_index = table_and_index.get_total_length()
    next_run = True

    while next_run and current_index < max_index:
        # Initialize the flag for each iteration of the loop
        next_run = False

        # Define the callback function that will trigger the next loop iteration
        def run_next_loop():
            nonlocal next_run
            next_run = True
            close_window()  # Close the current window to start the next one




        table_row = table_and_index.get_damage_table_row(current_index)
        print(current_index)

        working_dir = os.path.join(table_and_index.get_output_dir(), "results", table_row["Videoname"])
        os.makedirs(working_dir, exist_ok=True)
        frame_dir = os.path.join(working_dir, "source images")
        os.makedirs(frame_dir, exist_ok=True)

        frame_extraction = FrameExtraction(video_path=table_row["Videopfad"], output_dir=frame_dir, similarity_threshold=config["settings"]["image_similarity_threshold"])

        extract_frames(frame_extraction, table_row, config)
        

        sam_model = Sam(frame_dir, config["sam_model_paths"])

        root = tk.Tk()
        app = ImageGridApp(root=root, 
                            sam_model=sam_model, 
                            start_observation=table_row.get("Label"),
                            next_callback=run_next_loop)
        app.init_frames(frame_dir)
        app.init_settings(settings=config["settings"])
        app.init_json(table_row)
        app.init_add_observations_menu(config["object_add_buttons"])
        app.draw_overlays_on_image_views()
        app.init_frame_extraction_buttons(frame_extraction, True)
        app.root.protocol("WM_DELETE_WINDOW", close_window)

        root.mainloop()  # Start the Tkinter event loop

        current_index = table_and_index.increment_and_save_current_index(current_index)



def folder_mode(config):
    # Define a function to close the window and update the loop control variable
    def close_window():
        app.save_to_json()
        app.root.destroy()
        print("Grid Window closed and data saved to Json")

    over_dir = filedialog.askdirectory(title="Select the Directory with the labelled folders inside",initialdir=os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

    for folder_name in os.listdir(over_dir):
        frame_dir = os.path.join(over_dir, folder_name) 

        if not os.path.isdir(frame_dir):
            continue

        sam_model = Sam(frame_dir, config["sam_model_paths"])


        # Initialize the flag for each iteration of the loop
        next_run = False

        # Define the callback function that will trigger the next loop iteration
        def run_next_loop():
            nonlocal next_run
            next_run = True
            close_window()  # Close the current window to start the next one


        root = tk.Tk()
        app = ImageGridApp(root=root, 
                            sam_model=sam_model, 
                            next_callback=run_next_loop)
        app.init_frames(frame_dir)
        app.init_settings(settings=config["settings"])
        app.init_json()
        app.init_add_observations_menu(config["object_add_buttons"])
        app.draw_overlays_on_image_views()
        app.root.protocol("WM_DELETE_WINDOW", close_window)

        root.mainloop()  # Start the Tkinter event loop

        if not next_run:
            break






def main():
    config = load_settings()
    mode = config["mode"]

    if mode == "test_mode":
        test_mode(config)
    elif mode == "list_mode":
        list_mode(config)
    elif mode == "folder_mode":
        folder_mode(config)
    elif mode == "auto_mode":
        print



if __name__ == "__main__":
    main()
