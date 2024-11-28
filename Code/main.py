from main_window import MainWindow
from table_and_index import TableAndIndex
from frame_extraction import FrameExtraction
from sam2_class import Sam2Class
import tkinter as tk
from tkinter import filedialog
import yaml
import os
from dataclasses import dataclass, field


@dataclass
class Setup:
    config: dict
    frame_dir: str
    sam_model: Sam2Class
    damage_table_row: dict = field(default_factory=dict)



def load_config() -> dict:
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

def list_mode(config, mode):
    table_and_index = TableAndIndex(output_path=config["default_paths"]["output_path"], table_path=config["default_paths"]["table_path"])
    damage_table_row = table_and_index.get_damage_table_row()

    sam_model = Sam2Class(checkpoint_filepath=config["sam_model_paths"]["sam2_checkpoint"], model_filepath=config["sam_model_paths"]["model_cfg"])

    while damage_table_row:

        working_dir = os.path.join(table_and_index.get_output_dir(), "results", damage_table_row["Videoname"])
        frame_dir = os.path.join(working_dir, "source images")
        os.makedirs(frame_dir, exist_ok=True)

        frame_extraction = FrameExtraction(video_path=damage_table_row["Videopfad"], output_dir=frame_dir, similarity_threshold=config["settings"]["image_similarity_threshold"])
        start_time, end_time = calculate_time_bounds(damage_table_row["Videozeitpunkt (h:min:sec)"], config)
        frame_extraction.extract_frames_by_damage_time(start_time, end_time, config["settings"].get("extraction_frame_per_frames", 25))
        
        setup = Setup(config, frame_dir, sam_model, damage_table_row)

        main_window = MainWindow()
        main_window.setup(setup, mode)
        main_window.open()

        print("the main has advanced")
        main_window.save_to_json()

        damage_table_row = table_and_index.get_damage_table_row()
    

def test_mode(config, mode):
    print

def folder_mode(config, mode):
    print




def close_window(app):
    """Close the Tkinter window and save the JSON data."""
    app.save_to_json()
    app.root.destroy()
    app.remove_image_view()
    print("Window closed and data saved to JSON")


def main():
    """Main entry point for the script."""
    config = load_config()
    mode = config.get("mode")


    if mode == "test_mode": 
        test_mode(config, mode)
    elif mode == "list_mode": 
        list_mode(config, mode)
    elif mode == "folder_mode": 
        folder_mode(config, mode)

    


if __name__ == "__main__":
    main()
