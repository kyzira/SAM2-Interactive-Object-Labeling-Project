import json
import os


class JsonReadWrite:
    def __init__(self, json_path):
        self.__json_data = dict()
        self.json_path = json_path
        self.load_json_from_file()

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

        
        if (pos_points or neg_points) and not selection_order:
            print("Index is not set despite pos_points or neg_points is set")

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
            with open(self.json_path, "r") as file:
                self.__json_data = json.load(file)
        else:
            print("Error: file does not exist! Creating emtpy .json")
            self.__json_data = dict()
            self.save_json_to_file()

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