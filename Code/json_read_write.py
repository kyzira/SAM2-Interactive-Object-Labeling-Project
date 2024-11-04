import json
import os
import tkinter as tk

class JsonReadWrite:
    def __init__(self, json_path, info_table={}):
        self.__json_data = dict()
        self.json_path = json_path
        self.info_table = info_table
        self.success = self.load_json_from_file()
        
    def json_read_failed(self):
        # Initialize skip as a mutable container (list) to allow modification inside nested functions
        skip = [False]

        def on_skip_button_click():
            skip[0] = True  # Update the mutable skip variable
            root.destroy()  # Close the tkinter window

        def on_delete_button_click():
            try:
                os.remove(self.json_path)  # Attempt to delete the JSON file
                self.__json_data = {}  # Reset JSON data to avoid errors when trying to access it
                self.load_json_from_file()  # Reload the JSON file after deletion
            except Exception as e:
                print(f"Error deleting JSON file: {e}")  # Handle any deletion errors
            root.destroy()  # Close the tkinter window

        # Set up tkinter window
        root = tk.Tk()
        root.title("Json Read Failed")  # Title of the window
        root.geometry("400x130")  # Size of the window

        # Create a text label
        label = tk.Label(root, text="The Json file couldn't be read. It may be broken or corrupt")
        label.pack(pady=10)  # Add some vertical padding

        # Create the first button
        button1 = tk.Button(root, text="Skip to next Entry", command=on_skip_button_click)
        button1.pack(pady=5)  # Add some vertical padding

        # Create the second button
        button2 = tk.Button(root, text="Delete Json and create new", command=on_delete_button_click)
        button2.pack(pady=5)  # Add some vertical padding

        # Run the application
        root.mainloop()  # Start the tkinter event loop

        return skip[0]  # Return the value of skip


    def get_load_successful(self):
        return self.success
    
    def get_json(self):
        return self.__json_data
        
    def add_frame_to_json(self, frame_name: str, observation: str, polygons = None, pos_points = None, neg_points = None, selection_order = None):
        """
            This function adds an element to the dictionairy which will be saved as a json.
            Depending on which parameters are given the json structure will be created.

            Parameters:
                Needed Parameters:
                    - frame_name:
                        This is the name of the frame like the following: "00000.jpg" or "002413.jpg".
                    - observation:
                        This is the name of the observation
                Optional Parameters:
                    If points are available, either polygon or pos/neg points, they will be saved in the structure.
                    - polygons: 
                        This is a List of Lists. polygons contains multiple singular polygon, which also are lists, but lists of coordinates of the points which form the polygon.
                        for example:
                            [   # polygons
                                [   # polygon
                                    [x,y],  # coordinates
                                    [x,y],  # coordinates
                                    [x,y]   # coordinates
                                ],  # polygon

                                [], # polygon

                                [], # polygon
                            ]   # polygons
                    - pos_points/neg_points:
                        Both are lists of coordinates. They dont form a polygon, but instead just list where a positive/negative point was placed
                    - selection_order:
                        This is an integer with the index, in which order this frame was labeled. This index is only given if the points were set manually.
            
        """

        if frame_name == "" or observation == "":
            print("Error: Frame Name or Observation not set!")

        frame_num = str(int(frame_name.split(".")[0]))

        if frame_num not in self.__json_data.keys():
            frame_class = {
                "File Name": frame_name,
                "Observations": {}
            }
            self.__json_data[frame_num] = frame_class
        
        if observation not in self.__json_data[frame_num]["Observations"]:
            self.__json_data[frame_num]["Observations"][observation] = dict()

        coordinates_dict = self.__json_data[frame_num]["Observations"][observation]
        coordinates_dict["Mask Polygon"] = polygons

        if selection_order == 0:
            selection_order = self.__check_for_selection_order(observation)
            coordinates_dict["Selection Order"] = selection_order

        if pos_points or neg_points:
            coordinates_dict["Points"] = dict()
        if pos_points:
            coordinates_dict["Points"]["1"] = pos_points
        if neg_points:
            coordinates_dict["Points"]["0"] = neg_points
            
    def create_info(self, damage_table):
        observation_name_and_time = f"{damage_table['Label']}, at {damage_table['Videozeitpunkt (h:min:sec)']}"
        # Create a list of relevant keys from config.yaml
        keys_to_include = damage_table["config"]['default_table_columns']

        # Check if "Info" is present in the JSON
        if "Info" in self.__json_data:
            # Check if the observation has already been documented
            if observation_name_and_time in self.__json_data["Info"]["Documented Observations"]:
                return
            else:
                self.__json_data["Info"]["Documented Observations"].append(observation_name_and_time)
        else:
            # Initialize the "Info" dictionary
            self.__json_data["Info"] = {}
            self.__json_data["Info"]["Video Path"] = damage_table["video_path"]  # `video_path` needs to be defined in the scope
            self.__json_data["Info"]["Extracted Frame Rate"] = damage_table["frame_rate"]
            
            for key in keys_to_include:
                if key in damage_table:
                    self.__json_data["Info"][key] = damage_table[key]
            self.__json_data["Info"]["Documented Observations"] = [observation_name_and_time]
        self.save_json_to_file()

    def add_to_info(self, key, value):
        if "Info" in self.__json_data:
            self.__json_data["Info"][key] = value
            self.save_json_to_file()

    def prepare_json_with_frames(self, frame_name_list, damage_list):
        # This function prepares the json with the given frames and damages
        if len(frame_name_list) < 1:
            print("Error: Frame List empty")
        if len(damage_list) < 1:
            print("Error: Damage List empty")

        for frame_name in frame_name_list:
            for damage_name in damage_list:
                self.add_frame_to_json(frame_name=frame_name, observation=damage_name)
        self.save_json_to_file()

    def remove_damages_from_json(self, damage_list, frame_key=None):
        # if a frame key is given, only in that frame will it be deleted, else it will be deleted from every frame

        if len(damage_list) < 1:
            print("Error: No Damages to be deleted")
            return  # Add return to avoid further execution when list is empty
        
        for damage in damage_list:
            print(f"Now deleting {damage}")
            print(frame_key)
            if str(frame_key) in self.__json_data.keys():
                frame = self.__json_data[str(frame_key)]
                if damage in frame["Observations"].keys():
                    del frame["Observations"][damage]
            else:
                for frame in self.__json_data.values():
                    if "Observations" not in frame:
                        continue
                    # Directly access frame instead of self.__json_data[frame]
                    if damage in frame["Observations"].keys():
                        del frame["Observations"][damage]  # Modify the frame directly
        print(f"Successfully Deleted: {damage_list}")
        self.save_json_to_file()
            
    def save_json_to_file(self):
        try:
            with open(self.json_path, "w") as outfile:
                json.dump(self.__json_data, outfile, indent=4)
        except Exception as e:
            print(f"File could not be saved! Error: {e}")

    def load_json_from_file(self):
        if os.path.exists(self.json_path):
            try:
                with open(self.json_path, "r") as file:
                    self.__json_data = json.load(file)
                return 1
            except:
                return 0
        else:
            print("Creating json!")
            self.__json_data = dict()
            self.save_json_to_file()
            if self.info_table != {}:
                self.create_info(self.info_table)

    def add_marked_frames_to_first_index(self, frames_list: list[str]):
        self.__json_data["Info"]["Marked Frames"] = frames_list
        self.save_json_to_file()

    def get_marked_frames_from_first_index(self):
        if "Marked Frames" in self.__json_data["Info"]:
            return self.__json_data["Info"]["Marked Frames"]
        else:
            return []

    def __check_for_selection_order(self, observation):
        # Check the Json, how many frames already were labeled manually
        counter = 0
        for frame in self.__json_data.values():
            if "Observations" not in frame:
                continue
            if observation not in frame["Observations"]:
                continue
            if "Selection Order" not in frame["Observations"][observation]:
                continue
            counter += 1
        return counter