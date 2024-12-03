from main_window import MainWindow
from table_and_index import TableAndIndex
from frame_extraction import FrameExtraction
from sam2_class import Sam2Class
import yaml
import os
from tkinter import filedialog
from deinterlace_video import DeinterlaceVideo
from small_dataclasses import Setup


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
        deinterlaced_video_dir = os.path.join(table_and_index.get_output_dir(), "deinterlaced videos")
        frame_dir = os.path.join(working_dir, "source images")
        os.makedirs(deinterlaced_video_dir, exist_ok=True)
        os.makedirs(frame_dir, exist_ok=True)

        video_path = damage_table_row["Videopfad"]

        if config["settings"].get("auto_deinterlacing") == True:
            print("Deinterlacing Video...")
            output_path = os.path.join(deinterlaced_video_dir, os.path.basename(video_path))
            DeinterlaceVideo(video_path, output_path)
            video_path = output_path

        frame_extraction = FrameExtraction(video_path=video_path, output_dir=frame_dir, similarity_threshold=config["settings"]["image_similarity_threshold"])
        start_time, end_time = calculate_time_bounds(damage_table_row["Videozeitpunkt (h:min:sec)"], config)
        frame_extraction.extract_frames_by_damage_time(start_time, end_time, config["settings"].get("extraction_frame_per_frames", 25))
        
        setup = Setup(config, frame_dir, sam_model, frame_extraction, damage_table_row)

        main_window = MainWindow()
        main_window.setup(setup, mode)
        main_window.open()


        main_window.save_to_json()

        if main_window.run_next_loop == False:
            break

        damage_table_row = table_and_index.get_damage_table_row()
    

def test_mode(config, mode):
    """
    Test mode function to simulate the behavior of the application using predefined test configurations.
    """
    try:
        # Extract paths and settings from the config file
        test_mode_setup = config.get("test_mode_setup", {})
        test_mode_table = config.get("test_mode_table", {})
        
        frame_dir = test_mode_setup.get("current_frame_dir")
        video_path = test_mode_setup.get("video_path")
        
        # Ensure the frame directory exists
        os.makedirs(frame_dir, exist_ok=True)

        # Initialize the FrameExtraction and extract framess
        frame_extraction = FrameExtraction(video_path=video_path, output_dir=frame_dir, similarity_threshold=config["settings"]["image_similarity_threshold"])

        # Set up the SAM model
        sam_model = Sam2Class(
            checkpoint_filepath=config["sam_model_paths"]["sam2_checkpoint"],
            model_filepath=config["sam_model_paths"]["model_cfg"]
        )
        
        # Prepare the Setup dataclass for the main window
        damage_table_row = test_mode_table
        setup = Setup(config=config, frame_dir=frame_dir, sam_model=sam_model, frame_extraction=frame_extraction, damage_table_row=damage_table_row)
        
        # Initialize and open the main window
        main_window = MainWindow()
        main_window.setup(setup, mode)
        main_window.open()
        
        # Save to JSON after running
        print("Test mode completed. Saving data to JSON.")
        main_window.save_to_json()

    except Exception as e:
        print(f"Error in test_mode: {e}")


def eval_mode(config, mode):
    """
    Eval mode function to loop through all datasets in a selected folder.
    Enables evaluation buttons in the MainWindow.
    """
    results_dir = filedialog.askdirectory(
    title="Select the results Directory",
    initialdir=os.path.dirname(os.path.dirname(os.path.realpath(__file__))),
    )

    # Initialize SAM model
    sam_model = Sam2Class(
        checkpoint_filepath=config["sam_model_paths"]["sam2_checkpoint"],
        model_filepath=config["sam_model_paths"]["model_cfg"]
    )

    if not results_dir:
        print("No folder selected. Exiting folder mode.")
        return
    
    for folder_name in os.listdir(results_dir):
        folder_path = os.path.join(results_dir, folder_name)
        frame_dir = os.path.join(folder_path, "source images")
        if not os.path.isdir(frame_dir):
            continue


        json_path = os.path.join(folder_path, f"{os.path.basename(folder_path)}.json")
        
        if not os.path.exists(frame_dir) or not os.path.exists(json_path):
            print(f"Skipping {folder_path}: Required files (frames or JSON) not found.")
            continue
        
        frame_extraction = FrameExtraction(video_path=None, output_dir=frame_dir, similarity_threshold=config["settings"]["image_similarity_threshold"])

        # Prepare the Setup dataclass for the main window
        setup = Setup(config=config, frame_dir=frame_dir, sam_model=sam_model, frame_extraction=frame_extraction, damage_table_row={})

        # Initialize and open the main window
        main_window = MainWindow()
        main_window.setup(setup, mode)
        main_window.open()

        # Save JSON after running
        print(f"Completed processing for {folder_path}. Saving data to JSON.")
        main_window.save_to_json()

        # If the user exits or cancels, break the loop
        if not main_window.run_next_loop:
            print("User exited folder mode.")
            break


def single_folder_mode(config, mode):
    """
    Folder mode function lets you choose which folder you want to look at at every loop.
    Enables evaluation buttons in the MainWindow.
    """

    # Initialize SAM model
    sam_model = Sam2Class(
        checkpoint_filepath=config["sam_model_paths"]["sam2_checkpoint"],
        model_filepath=config["sam_model_paths"]["model_cfg"]
    )

    while True:
        folder_path = filedialog.askdirectory(
        title="Select the video folder",
        initialdir=os.path.dirname(os.path.dirname(os.path.realpath(__file__))),
        )

        if not folder_path:
            print("No folder selected. Exiting folder mode.")
            return


        frame_dir = os.path.join(folder_path, "source images")
        if not os.path.isdir(frame_dir):
            continue


        json_path = os.path.join(folder_path, f"{os.path.basename(folder_path)}.json")
        
        if not os.path.exists(frame_dir) or not os.path.exists(json_path):
            print(f"Skipping {folder_path}: Required files (frames or JSON) not found.")
            continue
        
        frame_extraction = FrameExtraction(video_path=None, output_dir=frame_dir, similarity_threshold=config["settings"]["image_similarity_threshold"])

        # Prepare the Setup dataclass for the main window
        setup = Setup(config=config, frame_dir=frame_dir, sam_model=sam_model, frame_extraction=frame_extraction, damage_table_row={})

        # Initialize and open the main window
        main_window = MainWindow()
        main_window.setup(setup, mode)
        main_window.open()

        # Save JSON after running
        print(f"Completed processing for {folder_path}. Saving data to JSON.")
        main_window.save_to_json()

        # If the user exits or cancels, break the loop
        if not main_window.run_next_loop:
            print("User exited folder mode.")
            break


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
    elif mode == "eval_mode": 
        eval_mode(config, mode)
    elif mode == "single_folder_mode":
        single_folder_mode(config, mode)
    else:
        print("Error: given mode not known!")
    

if __name__ == "__main__":
    main()
