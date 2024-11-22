import json
import os
from datetime import datetime


# You can easily improve the structure of this class and make it much simpler by the following way:
# class JsonAnnotationManager:
# def __init__(self):
#     self.__json_data = dict()
#     self.__json_filepath = ""

# def load(self, json_filepath: str) -> bool:
#     if not os.path.exists(json_filepath):
#         print(f"Cannot open JSON, because it does not exist: {json_filepath}")
#         return False
#     try:
#         with open(json_filepath, "r") as file:
#             self.__json_data = json.load(file)
#             self.__json_filepath = json_filepath
#             print("JSON loaded Successfully")
#             return True
#     except Exception as error_message:
#         print(f"Error opening JSON file \"{json_filepath}\": {error_message}")
#         return False
    
# def is_loaded(self) -> bool:
#     return self.__json_data and self.__json_filepath

# def reset(self) -> None:
#     self.__json_data = dict()
#     self.__json_filepath = ""
    
# def add_damage_info(self, damage_info: dict) -> bool:
#     if not self.is_loaded:
#         print("Cannot add damage info, because no JSON file is openend")
#         return False
    
#     observation_name_and_time = f"{damage_info['Label']}, at {damage_info['Videozeitpunkt (h:min:sec)']}"
    
#     # Create a list of relevant keys from config.yaml
#     info_already_existing = "Info" in self.__json_data
#     if info_already_existing:
#         observation_already_documented = observation_name_and_time in self.__json_data["Info"]["Documented Observations"]
#         if not observation_already_documented:
#             self.__json_data["Info"]["Documented Observations"].append(observation_name_and_time)
#         self.save_json_to_file()
#         return True
    
#     # Initialize the "Info" dictionary
#     self.__json_data["Info"] = {}
#     for key in damage_info.keys():
#         self.__json_data["Info"][key] = damage_info[key]
#     self.__json_data["Info"]["Documented Observations"] = [observation_name_and_time]
#     self.save_json_to_file()
#
# etc.

# Since this class does not just read/write generic JSON files but JSONS with annotations, i would rename it something like 
# "JsonAnnotationManager" ("manager" also not good since it can mean anything, but I can't think of anything better)
class JsonReadWrite:
    """
    This class handles interaction with the dict in which all data is stored and its json file, in which it will be stored.
    """
    # In the context of this class "table_row" does not make any sense. Since a table row contains infos about a damage "damage_info" would be better.
    # Furthermore I think it would also be better to also rename the JSON key "info" to "damage_infos"
    def __init__(self, json_path, table_row={}):
        self.__json_data = dict()
        self.json_path = json_path
        self.table_row = table_row
        self.load_json_from_file()

    def get_json(self):
        return self.__json_data.copy()
    
    def get_marked_frames_from_info(self):
        return self.__json_data["Info"].get("Marked Frames", [])
    
    def get_intervalls_from_info(self, observation=None):
        if observation == None:
            return self.__json_data["Info"].get("Intervalls")
        else:
            return self.__json_data["Info"]["Intervalls"].get(observation)
        
    def reset_json(self):
        self.__json_data = dict()

    def load_json_from_file(self):
        if os.path.exists(self.json_path):
            try:
                with open(self.json_path, "r") as file:
                    self.__json_data = json.load(file)
                    print("Json Loaded Successfully")
                return 
            except json.JSONDecodeError:
                print("Error: JSON is corrupt or broken.\nBacking it up and creating a new JSON!")
                self.__backup_and_reset_json()    
        
        # You function name is "load from file", it is very unexpected that this function creates a new json
        # Better make two functions: 
        # If the JSON file does not exist, create it with default info_table
        self.__json_data = dict()
        self.save_json_to_file()
        if self.table_row != {}:
            self.__create_info()
        return
    
    def set_json(self, json={}):
        self.__json_data = json
        self.save_json_to_file()
    
    def save_json_to_file(self):
        try:
            with open(self.json_path, "w") as outfile:
                json.dump(self.__json_data, outfile, indent=4)
        except Exception as e:
            print(f"File could not be saved! Error: {e}")

    def add_to_info(self, key, value):
        if key is None or value is None:
            print(f"Error: Key: {key} or Value {value} is None!")
            return

        if "Info" not in self.__json_data:
            self.__json_data["Info"] = {}

        self.__json_data["Info"][key] = value
        self.save_json_to_file()

        
    def add_intervalls_to_info(self, observation: str, intervall_list: list[(int,int)]):
        intervalls = self.__json_data["Info"].get("Intervalls", {})
        intervalls[observation] = intervall_list
        self.__json_data["Info"]["Intervalls"] = intervalls
        self.save_json_to_file()
        
    def add_to_frame(self, frame_name: str, observation: str, observation_data: dict):
        """
            This function adds an element to the dictionairy which will be saved as a json.
            Depending on which parameters are given the json structure will be created.
        """

        if frame_name == "" or observation == "":
            print("Error: Frame Name or Observation not set!")

        frame_num = str(int(frame_name.split(".")[0]))

        if frame_num not in self.__json_data.keys():
            self.__json_data[frame_num] = {
                "File Name": frame_name,
                "Observations": {}
            }
        
        if observation not in self.__json_data[frame_num]["Observations"]:
            self.__json_data[frame_num]["Observations"][observation] = dict()

        coordinates_dict = self.__json_data[frame_num]["Observations"][observation]

        polygons = observation_data.get("Mask Polygon")
        points = observation_data.get("Points")
        

        if polygons:
            coordinates_dict["Mask Polygon"] = polygons

        if points:
            coordinates_dict["Points"] = dict()
            selection_order = self.__check_for_selection_order(observation)
            coordinates_dict["Selection Order"] = selection_order
            pos_points = points.get("1")
            neg_points = points.get("0")
            
            if pos_points:
                coordinates_dict["Points"]["1"] = pos_points
            if neg_points:
                coordinates_dict["Points"]["0"] = neg_points
            

    def remove_damages_from_json(self, damage_list, frame_key=None):
        # if a frame key is given, only in that frame will it be deleted, else it will be deleted from every frame

        if len(damage_list) < 1:
            print("Error: No Damages to be deleted")
            return  # Add return to avoid further execution when list is empty
        
        for damage in damage_list:
            if str(frame_key) in self.__json_data.keys():
                frame = self.__json_data[str(frame_key)]
                if damage in frame["Observations"].keys():
                    del frame["Observations"][damage]
            elif frame_key == None:
                for frame in self.__json_data.values():
                    if "Observations" not in frame:
                        continue
                    # Directly access frame instead of self.__json_data[frame]
                    if damage in frame["Observations"].keys():
                        del frame["Observations"][damage]  # Modify the frame directly
        print(f"Successfully Deleted: {damage_list}")
        self.save_json_to_file()
            

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
    

    def __create_info(self):
        damage_table = self.table_row
        observation_name_and_time = f"{damage_table['Label']}, at {damage_table['Videozeitpunkt (h:min:sec)']}"
        # Create a list of relevant keys from config.yaml

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
    
            for key in damage_table.keys():
                self.__json_data["Info"][key] = damage_table[key]
            self.__json_data["Info"]["Documented Observations"] = [observation_name_and_time]
        self.save_json_to_file()
        

    def __backup_and_reset_json(self):
        # Rename the corrupt JSON file with a timestamp
        backup_name = f"{self.json_path}_backup_{datetime.now().strftime('%Y%m%d%H%M%S')}.json"
        os.rename(self.json_path, backup_name)
        
        # Reset __json_data to default info_table and save as a new JSON
        self.save_json_to_file()