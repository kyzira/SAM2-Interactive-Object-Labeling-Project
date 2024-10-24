import os
import pandas as pd
from extract_frames_from_video import extract_frames_by_damage_time, extract_frames_by_frame
from main_window import ImageDisplayWindow
import json
import numpy as np
import yaml

# Load configuration from config.yaml
script_dir = os.path.dirname(os.path.abspath(__file__))  # Get the directory of the current script
config_path = os.path.join(script_dir, "..", "config.yaml")  # Adjust the path as needed
with open(config_path, 'r') as config_file:
    config = yaml.safe_load(config_file)

# Configurable options for processing video frames from config.yaml
auto_mode = config['mode'].get('auto_mode', False)  # Defaulting to False if not in config
test_mode = config['mode'].get('test_mode', False)   # Fetching the test_mode from YAML
view_mode = config["mode"].get("view_mode", False)
frame_rate = config['test_mode_setup'].get('Extracted Frame Rate', 25)  # Fetching frame rate from test_mode setup

stop_flag = False  # Global flag to stop the process if required

# Paths for the output directory and the CSV table of damage entries from config.yaml
output_dir = config['default_paths'].get('output_path')
table_path = config['default_paths'].get('table_path')

sam_paths = config.get("sam_model_paths")
# Directories for saving results and the index file
results_dir = os.path.join(output_dir, "results")
os.makedirs(results_dir, exist_ok=True)
index_path = os.path.join(output_dir, "current_index.txt")

# Load the table of damage entries from a CSV file
damage_table = pd.read_csv(table_path, delimiter=";")
total_length = len(damage_table)  # Total number of entries in the table

def get_current_index():
    """
    Reads the current index from a file. This index is used to track the last processed entry in the table.
    Returns the current index (starting at 0). If the index file doesn't exist, returns 0.
    """
    if os.path.exists(index_path):
        with open(index_path, "r") as index_file:
            index_content = index_file.read().strip()
            return int(index_content)
    else:
        return 0

def increment_and_save_current_index(current_index):
    """
    Increments the current index and saves it to the index file.
    current_index (int): The index to be incremented and saved.
    """
    current_index += 1
    with open(index_path, "w") as file:
        file.write(str(current_index))

def create_json_with_info(current_frame_dir: str, frame_rate: int, damage_table_at_index: pd.Series):
    """
    Creates a JSON file containing metadata about the video frames and stores it in the frame directory.
    """
    dir_path = os.path.dirname(current_frame_dir)
    json_path = os.path.join(dir_path, f"{str(os.path.basename(dir_path))}.json")
    if os.path.exists(json_path):
        with open(json_path, "r") as file:
            json_file = json.load(file)
    else:
        json_file = dict()
    
    observation_name_and_time = f"{damage_table_at_index['Schadenskürzel']}, at {damage_table_at_index['Videozeitpunkt (h:min:sec)']}"

    # Convert Pandas-specific types to Python types
    damage_info_converted = damage_table_at_index.apply(lambda x: int(x) if isinstance(x, (np.int64, np.int32)) else x)

    # Create a list of relevant keys from config.yaml
    keys_to_include = config['default_table_columns']

    # Check if "Info" is present in the JSON
    if "Info" in json_file:
        # Check if the observation has already been documented
        if observation_name_and_time in json_file["Info"]["Documented Observations"]:
            return
        else:
            json_file["Info"]["Documented Observations"].append(observation_name_and_time)
    else:
        # Initialize the "Info" dictionary
        json_file["Info"] = {}
        json_file["Info"]["Video Path"] = video_path  # `video_path` needs to be defined in the scope
        json_file["Info"]["Extracted Frame Rate"] = frame_rate
        
        for key in keys_to_include:
            if key in damage_info_converted:
                json_file["Info"][key] = damage_info_converted[key]
        
        json_file["Info"]["Documented Observations"] = [observation_name_and_time]

    # Write the JSON to the file
    with open(json_path, "w") as outfile:
        json.dump(json_file, outfile, indent=4)

def stop_process():
    global stop_flag
    stop_flag = True



if test_mode:
    # Using test_mode_setup values from config.yaml
    current_frame_dir = config['test_mode_setup']['current_frame_dir']
    video_path = config['test_mode_setup']['video_path']

    extraction_successful = extract_frames_by_frame(input_path=video_path, 
                                                    output_path=current_frame_dir, 
                                                    frame_rate=frame_rate,
                                                    start_frame=400,
                                                    end_frame=2000)

    # Using test_mode_table values from config.yaml
    damage_table = pd.Series(config['test_mode_table'])

    # Create JSON with test numbers
    create_json_with_info(current_frame_dir, frame_rate, damage_table)

    window_title = damage_table['Schadenskürzel']
    app = ImageDisplayWindow(
        frame_dir=current_frame_dir, 
        video_path=video_path, 
        frame_rate=frame_rate, 
        window_title=window_title, 
        stop_callback=stop_process,
        sam_paths=sam_paths
    )
    app.run()

else:
    current_index = get_current_index()
    while current_index <= total_length and not stop_flag: 
        current_index = get_current_index()

        # Prepare everything
        current_video_name = damage_table.iloc[current_index]['Videoname']
        schadens_kurzel = str(damage_table.iloc[current_index]["Schadenskürzel"])
        video_path = damage_table.iloc[current_index]['Videopfad']
        damage_time = damage_table.iloc[current_index]['Videozeitpunkt (h:min:sec)']

        current_dir = os.path.join(results_dir, current_video_name)
        current_frame_dir = os.path.join(current_dir, "source images")

        damage_time_split = damage_time.split(":")
        damage_second = int(damage_time_split[0]) * 60 * 60 + int(damage_time_split[1]) * 60 + int(damage_time_split[2])

        # Convert video into frames
        extraction_successful = extract_frames_by_damage_time(input_path=video_path, 
                                                               output_path=current_frame_dir, 
                                                               damage_second=damage_second, 
                                                               frame_rate=frame_rate)

        if not extraction_successful:
            # Skip this index
            increment_and_save_current_index(current_index)
            continue

        create_json_with_info(current_frame_dir, frame_rate, damage_table.iloc[current_index])

        if auto_mode:
            print()
            # yolo.main(frame_dir=current_frame_dir, schadens_kurzel=schadens_kurzel)
        else:  
            # Segment manually
            window_title = schadens_kurzel
            app = ImageDisplayWindow(
                frame_dir=current_frame_dir, 
                video_path=video_path, 
                frame_rate=frame_rate, 
                window_title=window_title, 
                schadens_kurzel=schadens_kurzel, 
                stop_callback=stop_process,
                sam_paths=sam_paths
            )
            app.run()

        increment_and_save_current_index(current_index)