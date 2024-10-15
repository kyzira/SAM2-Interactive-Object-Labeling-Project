import json
import os


class JsonReadWrite:
    def __init__(self, json_path):
        self.__json_data = dict()
        # ToDo: if self.json_path.parent_dir_exists():
        self.json_path = json_path
        self.load_json_from_file()

    def get_json(self):
        return self.__json_data
        
    def add_frame_to_json(self, frame_name: str, observation: str, polygons = None, pos_points = None, neg_points = None, sequence_index = None):
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
                    - sequence_index:
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

        if polygons:
            coordinates_dict["Maske"] = polygons

        if pos_points or neg_points:
            coordinates_dict["Points"] = dict()
        if pos_points:
            coordinates_dict["Points"]["1"] = pos_points
        if neg_points:
            coordinates_dict["Points"]["0"] = neg_points

        if sequence_index:
            coordinates_dict["Selection Order"] = sequence_index

        if (pos_points or neg_points) and not sequence_index:
            print("Index is not set despite pos_points or neg_points is set")

    def prepare_json_with_frames(self, frame_name_list, damage_list):
        """
            This function prepares the json with the given frames and damages
        """
        for frame_name in frame_name_list:
            for damage_name in damage_list:
                self.add_frame_to_json(frame_name=frame_name, observation=damage_name)
        self.save_json_to_file()

    def remove_damages_from_json(self, damage_list):
        # delete all entries from json
        for damage in damage_list:
            for frame in self.__json_data:
                if damage in self.__json_data[frame]["Observations"]:
                    del self.__json_data[frame]["Observations"][damage]
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