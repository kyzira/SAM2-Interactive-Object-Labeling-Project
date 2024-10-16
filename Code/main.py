import os
import pandas as pd
from extract_frames_from_video import extract_frames_by_damage_time, extract_frames_by_frame
from main_window import ImageDisplayWindow
import yolo_sam_cooperation as yolo
import json

# Configurable options for processing video frames
auto_labeling = False     # Automatically apply YOLO model for damage labeling
test_mode = True          # If True, a test case is run
file_creation = False     # Only in test mode: If True, frames will be extracted and JSON files created
frame_rate = 25           # Frame extraction rate in frames per second (fps)

stop_flag = False         # Global flag to stop the process if required

# Paths for the output directory and the CSV table of damage entries
output_dir = r"C:\Code Python\automation-with-sam2\labeling_project"
table_path = r"C:\Code Python\automation-with-sam2\labeling_project\avg polygons\gesammelte_einträge.csv"

# Directories for saving results and the index file
results_dir = os.path.join(output_dir, "results")
os.makedirs(results_dir, exist_ok=True)
index_path = os.path.join(output_dir, "current_index.txt")

# Load the table of damage entries from a CSV file
usecols = ["Videoname", "Videozeitpunkt (h:min:sec)", "Schadenskürzel", "Videopfad", "Schadensbeschreibung", "Videohash"]
damage_table = pd.read_csv(table_path, usecols=usecols, delimiter=",")
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


def create_json_with_info(current_frame_dir: str, video_name: str, frame_rate: int, time_stamp: str, observation: str, video_path: str, video_hash: int):
    """
    Creates a JSON file containing metadata about the video frames and stores it in the frame directory.
    
    Args:
        current_frame_dir (str): Directory where the frames are saved.
        video_name (str): Name of the video.
        frame_rate (int): The frame extraction rate (fps).
        time_stamp (str): Time of the damage occurrence in the video (format h:min:sec).
        observation (str): The short code describing the type of damage.
        video_path (str): The full path to the video.
        video_hash (int): A hash value representing the video.
    """
    dir_path = os.path.dirname(current_frame_dir)
    json_path = os.path.join(dir_path, f"{str(os.path.basename(dir_path))}.json")
    json_file = dict()
    info_name = f"Info {observation}, at {time_stamp}"
    json_file[info_name] = {
        "Video Name": video_name,
        "Video Path": video_path,
        "Extracted Frame Rate": frame_rate,
        "Time Stamp": time_stamp,
        "Documented Observation": observation,
        "Videohash": video_hash
    }

    with open(json_path, "w") as outfile:
        json.dump(json_file, outfile, indent=4)


def stop_process():
    global stop_flag
    stop_flag = True


if test_mode:
    schadens_kurzel = "BBA"
    current_frame_dir = "C:\\Code Python\\automation-with-sam2\\labeling_project\\test folder\\source images"
    video_path = r"C:\Code Python\automation-with-sam2\labeling_project\test folder\test.mp4"

    if file_creation == True:
        extraction_succesful = extract_frames_by_frame(input_path=video_path, 
                                                        output_path=current_frame_dir, 
                                                        frame_rate = frame_rate,
                                                        start_frame=400,
                                                        end_frame=2000)
        
        # Create Json with arbitrary test numbers
        create_json_with_info(current_frame_dir=current_frame_dir, 
                            video_name=os.path.basename(video_path),
                            frame_rate=frame_rate,
                            time_stamp="00:00:20",
                            observation=schadens_kurzel,
                            video_path=video_path,
                            video_hash = 00000)

    window_title = (schadens_kurzel)
    app = ImageDisplayWindow(
        frame_dir=current_frame_dir, 
        video_path=video_path, 
        frame_rate=frame_rate, 
        window_title=window_title, 
        schadens_kurzel=schadens_kurzel, 
        stop_callback=stop_process
    )
    app.run()

else:
    while current_index <= total_length and not stop_flag: 
        current_index = get_current_index()

        # Prepare everything
        current_video_name = damage_table.iloc[current_index]['Videoname']
        schadens_kurzel  = str(damage_table.iloc[current_index]["Schadenskürzel"])
        video_path = damage_table.iloc[current_index]['Videopfad']
        damage_time = damage_table.iloc[current_index]['Videozeitpunkt (h:min:sec)']

        current_dir = os.path.join(results_dir, current_video_name)
        current_frame_dir = os.path.join(current_dir, "source images")
        
        damage_time_split = damage_time.split(":")
        damage_second = int(damage_time_split[0]) *60*60 + int(damage_time_split[1])*60 + int(damage_time_split[2])



        # Convert video into frames
        extraction_succesful = extract_frames_by_damage_time(input_path=video_path, 
                                                            output_path=current_frame_dir, 
                                                            damage_second=damage_second, 
                                                            frame_rate = frame_rate)

        if not extraction_succesful:
            # Skip this index
            current_index += 1
            continue

        create_json_with_info(current_frame_dir, current_video_name, frame_rate, damage_time, schadens_kurzel, video_path)

        if auto_labeling:
            yolo.main(frame_dir=current_frame_dir, schadens_kurzel=schadens_kurzel)
        else:  
            # Segment manually
            window_title = (schadens_kurzel) + " " + str(damage_table.iloc[current_index]["Schadensbeschreibung"])
            app = ImageDisplayWindow(
                frame_dir=current_frame_dir, 
                video_path=video_path, 
                frame_rate=frame_rate, 
                window_title=window_title, 
                schadens_kurzel=schadens_kurzel, 
                stop_callback=stop_process
            )
            app.run()

        increment_and_save_current_index(current_index)