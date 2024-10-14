import json
import os

class Coordinates:
    def __init__(self, maske = [], pos_punkte = None, neg_punkte = None, index = None):
        self.maske = maske
        self.pos_punkte = pos_punkte
        self.neg_punkte = neg_punkte
        self.index = index
            
    def to_dict(self):
        if self.pos_punkte and self.neg_punkte:
            return {
                "Index" : self.index,
                "Maske": self.maske,
                "Punkte":{
                "1": self.pos_punkte,
                "0": self.neg_punkte
                }
            }
        else: 
            return{
                "Maske": self.maske,
            }


class Damage:
    def __init__(self, type_of_damage):
        self.type_of_damage = type_of_damage
        self.damage_info = dict()

    def add_info(self, damage_info):
        self.damage_info = damage_info

    def to_dict(self):
        return self.damage_info.to_dict()



class Frame:
    def __init__(self, name):
        self.name = name
        self.damages = dict()

    def add_damage(self, damage):
        self.damages[damage.type_of_damage] = damage

    def to_dict(self):
        return {
            "File Name": self.name,
            "Observations": {damage.type_of_damage: damage.to_dict() for damage in self.damages.values()}
        }
    

class JsonReadWrite:
    def __init__(self, json_path):
        self.__json_data = dict()
        self.json_path = json_path
        self.load_json_from_file()
        
    def add_frame_to_json(self, frame_name, damage, polygon = None, pos_punkte = None, neg_punkte = None, index = None):
        frame_num = str(int(frame_name.split(".")[0]))
        if frame_num not in self.__json_data.keys():
            coordinates_class = Coordinates(maske=polygon, pos_punkte=pos_punkte, neg_punkte=neg_punkte, index=index)
            damage_class = Damage(damage)
            damage_class.add_info(coordinates_class)
            frame_class = Frame(frame_name)
            frame_class.add_damage(damage_class)
            self.__json_data[frame_num] = frame_class.to_dict()
        else:
            if damage not in self.__json_data[frame_num]["Observations"]:
                self.__json_data[frame_num]["Observations"][damage] = dict()

            coordinates_dict = self.__json_data[frame_num]["Observations"][damage]

            if polygon:
                coordinates_dict["Maske"] = polygon

            if pos_punkte or neg_punkte:
                coordinates_dict["Index"] = index
                coordinates_dict["Punkte"] = dict()
                coordinates_dict["Punkte"]["0"] = neg_punkte
                coordinates_dict["Punkte"]["1"] = pos_punkte


    def remove_damages_from_json(self, damage_list):
        # delete all entries from json
        for damage in damage_list:
            for image in self.__json_data:
                if damage in self.__json_data[image]["Observations"]:
                    del self.__json_data[image]["Observations"][damage]
        self.save_json_to_file()


            
    def save_json_to_file(self):
        with open(self.json_path, "w") as outfile:
            json.dump(self.__json_data, outfile, indent=4)


    def load_json_from_file(self):
        if os.path.exists(self.json_path):
            with open(self.json_path, "r") as file:
                self.__json_data = json.load(file)
        else:
            self.__json_data = dict()
        

    def prepare_json_with_frames(self, frame_name_list, damage_list):
        for frame_name in frame_name_list:
            frame = Frame(frame_name)
            for damage_name in damage_list:
                damage = Damage(damage_name)
                empty_coordinates = Coordinates()
                damage.add_info(empty_coordinates)
                frame.add_damage(damage)
            self.__json_data[str(int(frame.name.split(".")[0]))] = frame.to_dict()
        self.save_json_to_file()

        
    def get_json(self):
        return self.__json_data