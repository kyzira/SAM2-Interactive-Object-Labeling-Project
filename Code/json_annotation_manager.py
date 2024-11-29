import json
import os
from image_info import ImageInfo


class JsonAnnotationManager:
    def __init__(self):
        self.__json_data = dict()
        self.__json_filepath = ""

    def load(self, json_filepath: str) -> bool:
        self.__json_filepath = json_filepath
        if not os.path.exists(json_filepath):
            self.save()

        try:
            with open(json_filepath, "r") as file:
                self.__json_data = json.load(file)
                print("JSON loaded Successfully")
                return True
        except Exception as error_message:
            print(f"Error opening JSON file \"{json_filepath}\": {error_message}")
            return False
        
    def save(self) -> bool:
        try:
            with open(self.__json_filepath, "w") as outfile:
                json.dump(self.__json_data, outfile, indent=4)
                return True
        except Exception as e:
            print(f"File could not be saved! Error: {e}")
            return False
        
    def get_json(self):
        return self.__json_data.copy()

    def set_info(self, damage_info: dict) -> bool:
        if not self.__is_loaded:
            print("Cannot add damage info, because no JSON file is openend")
            return False
        
        if damage_info == {}:
            return
        
        observation_name_and_time = f"{damage_info['Label']}, at {damage_info['Videozeitpunkt (h:min:sec)']}"
        
        # Create a list of relevant keys from config.yaml
        info_already_existing = "Info" in self.__json_data
        if info_already_existing:
            observation_already_documented = observation_name_and_time in self.__json_data["Info"]["Documented Observations"]
            if not observation_already_documented:
                self.__json_data["Info"]["Documented Observations"].append(observation_name_and_time)
            self.save()
            return True
        
        # Initialize the "Info" dictionary
        self.__json_data["Info"] = {}
        for key in damage_info.keys():
            if not damage_info[key]:
                 self.__json_data["Info"][key] = 0
            else:
                self.__json_data["Info"][key] = damage_info[key]
        self.__json_data["Info"]["Documented Observations"] = [observation_name_and_time]
        # self.save()

    def get_marked_frame_list(self) -> list:
        return self.__json_data["Info"].get("Marked Frames", [])
    
    def get_intervalls(self, observation=None):
        """
        Gets the Intervalls from the Info part of the json.
        observation (str): if an observation is given a list containing the start- and endpoints of the intervalls will be returned, 
        else an dict with all observations as keys, and their respective lists as values will be returned.
        """
        if observation == None:
            return self.__json_data["Info"].get("Intervalls", {})
        else:
            return self.__json_data["Info"]["Intervalls"].get(observation, [])

    def add_to_info(self, key, value):
        if key is None or value is None:
            print(f"Error: Key: {key} or Value {value} is None!")
            return

        if "Info" not in self.__json_data:
            self.__json_data["Info"] = {}

        self.__json_data["Info"][key] = value
        self.save()
        
    def add_to_frame(self, image_info: ImageInfo):
        """
            This function adds an element to the dictionairy which will be saved as a json.
            Depending on which parameters are given the json structure will be created.
        """
        if image_info is None:
            print("Error: image_info not set!")

        # If that key doesnt exist yet, create it
        frame_num = image_info.frame_num
        if frame_num not in self.__json_data.keys():
            self.__json_data[frame_num] = {
                "File Name": image_info.image_name,
                "Observations": {}
            }
        
        for damage_info in image_info.data_coordinates:
            self.__json_data[frame_num]["Observations"][damage_info.damage_name] = damage_info.get_dict()

    def reset(self) -> None:
        self.__json_data = dict()
        self.__json_filepath = ""

    def __is_loaded(self) -> bool:
        return self.__json_data and self.__json_filepath