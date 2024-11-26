from main_window import MainWindow
from table_and_index import TableAndIndex
from frame_extraction import FrameExtraction
from sam2_class import Sam2Class
import tkinter as tk
from tkinter import filedialog
import yaml
import os


def load_settings() -> dict:
    """Load the configuration settings from a YAML file."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, "..", "config.yaml")
    with open(config_path, 'r') as config_file:
        return yaml.safe_load(config_file)

def calculate_time_bounds(video_time: str, config: dict) -> tuple:
    """Calculate start and end times for frame extraction."""
    h, m, s = map(int, video_time.split(":"))
    timestamp = h * 3600 + m * 60 + s
    start_time = timestamp - config["settings"].get("frame_extraction_puffer_before", 60)
    end_time = timestamp + config["settings"].get("frame_extraction_puffer_after", 10)
    return start_time, end_time

def extract_frames(frame_extraction: FrameExtraction, table_row: dict, config: dict) -> bool:
    """Extract frames using FrameExtraction."""
    start_time, end_time = calculate_time_bounds(
        table_row["Videozeitpunkt (h:min:sec)"], config
    )
    frame_extraction.start_second = start_time
    frame_extraction.end_second = end_time

    try:
        frame_extraction.extract_frames_by_damage_time(
            start_time, end_time, config["settings"].get("extraction_frame_per_frames", 25)
        )
        return True
    except Exception as e:
        print(f"Error during frame extraction: {e}")
        return False

def setup_main_window(root, sam_model, config, frame_dir, json_data=None, start_observation=None, next_callback=None, **kwargs):
    """Set up and initialize the MainWindow."""
    app = MainWindow(root, sam_model, next_callback, start_observation)
    app.init_frames(frame_dir)
    app.init_settings(settings=config["settings"])
    app.init_json(json_data)
    app.init_add_observations_menu(config["object_add_buttons"], **kwargs)
    app.draw_overlays_on_image_views()
    return app

def test_mode(config):
    """Run the application in test mode."""
    frame_dir = r"C:\Code Python\SAM2-Interactive-Object-Labeling-Project\labeling_project\test folder\source images"
    sam_model = Sam2Class(config["sam_model_paths"])
    sam_model.init_predictor_state(frame_dir)

    root = tk.Tk()
    app = setup_main_window(
        root, sam_model, config, frame_dir, config["test_mode_table"], disable_next_buttons=True
    )
    app.root.protocol("WM_DELETE_WINDOW", lambda: close_window(app))
    root.mainloop()

def list_mode(config):
    """Run the application in list mode."""
    table_and_index = TableAndIndex(config["default_paths"])
    sam_model = Sam2Class(config["sam_model_paths"])

    current_index = table_and_index.get_current_index()
    max_index = table_and_index.get_total_length()

    while current_index < max_index:
        next_run = False  # Reset the loop control variable
        table_row = table_and_index.get_damage_table_row(current_index)
        working_dir = os.path.join(
            table_and_index.get_output_dir(), "results", table_row["Videoname"]
        )
        frame_dir = os.path.join(working_dir, "source images")
        os.makedirs(frame_dir, exist_ok=True)

        frame_extraction = FrameExtraction(
            video_path=table_row["Videopfad"],
            output_dir=frame_dir,
            similarity_threshold=config["settings"]["image_similarity_threshold"],
        )
        extract_frames(frame_extraction, table_row, config)
        sam_model.init_predictor_state(frame_dir)

        root = tk.Tk()

        def run_next_loop():
            nonlocal next_run
            next_run = True
            close_window(app)

        app = setup_main_window(
            root,
            sam_model,
            config,
            frame_dir,
            table_row,
            start_observation=table_row.get("Label"),
            next_callback=run_next_loop,
        )
        app.init_frame_extraction_buttons(frame_extraction, True)
        app.root.protocol("WM_DELETE_WINDOW", lambda: close_window(app))
        root.mainloop()

        if not next_run:
            break  # Exit the loop if the user decides not to continue

        current_index = table_and_index.increment_and_save_current_index(current_index)
        del app
        del sam_model.inference_state

def folder_mode(config):
    """Run the application in folder mode. This enables the Evaluation Buttons"""
    results_dir = filedialog.askdirectory(
        title="Select the results Directory",
        initialdir=os.path.dirname(os.path.dirname(os.path.realpath(__file__))),
    )
    sam_model = Sam2Class(config["sam_model_paths"])

    for folder_name in os.listdir(results_dir):
        next_run = False  # Reset the loop control variable
        result_path = os.path.join(results_dir, folder_name)
        frame_dir = os.path.join(result_path, "source images")
        if not os.path.isdir(frame_dir):
            continue

        sam_model.init_predictor_state(frame_dir)
        root = tk.Tk()

        def run_next_loop():
            nonlocal next_run
            next_run = True
            close_window(app)

        app = setup_main_window(
            root,
            sam_model,
            config,
            frame_dir,
            enable_evaluation_buttons=True,
            next_callback=run_next_loop,
        )
        app.root.protocol("WM_DELETE_WINDOW", lambda: close_window(app))
        root.mainloop()

        if not next_run:
            break  # Exit the loop if the user decides not to continue

        del app
        del sam_model.inference_state


def close_window(app):
    """Close the Tkinter window and save the JSON data."""
    app.save_to_json()
    app.root.destroy()
    app.remove_image_view()
    print("Window closed and data saved to JSON")

def main():
    """Main entry point for the script."""
    config = load_settings()
    mode_dispatcher = {
        "test_mode": test_mode,
        "list_mode": list_mode,
        "folder_mode": folder_mode,
    }
    mode = config.get("mode")
    mode_dispatcher.get(mode, lambda x: print(f"Invalid mode: {mode}"))(config)

if __name__ == "__main__":
    main()
