"""
This Code reads the csv list of all damages, opens it in SAM2 to label it and if finished opens the next damage.
"""

import os
import pandas as pd
import convert_video_to_frames as conv
import sam2_interface as sam2
import yolo_integration as yolo


# True if yolo should provide points for SAM2 or False if you want to select yourself 
auto_labeling = False




output_dir = r"C:\Code Python\automation-with-sam2\labeling_project"
results_dir = os.path.join(output_dir, "results")
os.makedirs(results_dir, exist_ok=True)



index_path = os.path.join(output_dir, "current_index.txt")
# table_path = os.path.join(output_dir, "alle_schaeden_gleichmaessige_liste.csv")
table_path = r"C:\Code Python\automation-with-sam2\labeling_project\avg polygons\gesammelte_einträge.csv"



usecols = ["Videoname", "Videozeitpunkt (h:min:sec)", "Schadenskürzel", "Videopfad", "Schadensbeschreibung"]
damage_table = pd.read_csv(table_path, usecols=usecols, delimiter=",")

if os.path.exists(index_path):
    with open(index_path, "r") as index_file:
        index_content = index_file.read().strip() 
        current_index = int(index_content)
else:
    current_index = 0

total_length = len(damage_table)



label_csv_header = ["Damage Type", "Start Frame", "End Frame", "Point in Frame", "X Coordinates", "Y Coordinates", "Point Label"]




while current_index <= total_length:
    # Update index text file
    with open(index_path, "w") as file:
        file.write(str(current_index))


    # Prepare everything
    current_video_name = damage_table.iloc[current_index]['Videoname']
    current_dir = os.path.join(results_dir, current_video_name)
    schadens_kurzel  = str(damage_table.iloc[current_index]["Schadenskürzel"])


    current_frame_dir = os.path.join(current_dir, "source images")


    input_path = damage_table.iloc[current_index]['Videopfad']

    damage_time = damage_table.iloc[current_index]['Videozeitpunkt (h:min:sec)']
    damage_time_split = damage_time.split(":")
    damage_second = int(damage_time_split[0]) *60*60 + int(damage_time_split[1])*60 + int(damage_time_split[2])

    frame_rate = 25


    # Convert video into frames
    conv.convert_video(input_path=input_path, output_path=current_frame_dir, damage_second=damage_second, frame_rate = frame_rate)
    
    

    if auto_labeling:
        state = yolo.main(frame_dir=current_frame_dir, schadens_kurzel=schadens_kurzel)
    else:
        # Segment yourself:
        window_title = (schadens_kurzel) + " " + str(damage_table.iloc[current_index]["Schadensbeschreibung"])
        app = sam2.ImageDisplayApp(frame_dir = current_frame_dir, video_path = input_path, frame_rate = frame_rate, window_title = window_title, schadens_kurzel = schadens_kurzel)
        app.run()
        state = True


    current_index += 1








