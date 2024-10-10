import json
import os

class Coordinates:
    def __init__(self, maske = [], pos_punkte = [], neg_punkte = []):
        self.maske = maske
        self.pos_punkte = pos_punkte
        self.neg_punkte = neg_punkte
            
    def to_dict(self):
        return {
            'Maske': self.maske,
            'Punkte':{
            '1': self.pos_punkte,
            '0': self.neg_punkte
            }
        }


class Damage:
    def __init__(self, type_of_damage):
        self.type_of_damage = type_of_damage
        self.damage_info_list = []  

    def add_info(self, damage_info):
        self.damage_info_list.append(damage_info) 

    def to_dict(self):
        return {
            **{str(index): damage_info.to_dict() for index, damage_info in enumerate(self.damage_info_list)} 
        }


class Frame:
    def __init__(self, name):
        self.name = name
        self.damages = dict()

    def add_damage(self, damage):
        self.damages[damage.type_of_damage] = damage

    def to_dict(self):
        return {
            'File Name': self.name,
            'Observations': {damage.type_of_damage: damage.to_dict() for damage in self.damages.values()}
        }
    

class JsonReadWrite:
    def __init__(self, json_path):
        self.__json_data = dict()
        self.json_path = json_path
        self.load_json_from_file()
        
    def add_to_json(self, frame_class, damage_class, coordinates_class):
        damage_class.add_info(coordinates_class)
        frame_class.add_damage(damage_class)
        self.__json_data[int(frame_class.name.split(".")[0])] = frame_class.to_dict()

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
            with open(self.json_path, 'r') as file:
                self.__json_data = json.load(file)
        else:
            self.__json_data = dict()
        
        self.get_json()


    def get_json(self):
        return self.__json_data