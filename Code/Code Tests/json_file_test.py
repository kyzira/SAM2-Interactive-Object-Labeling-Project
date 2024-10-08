import json


class Damage_info:
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
        self.ids = []  

    def add_info(self, damage_info):
        self.ids.append(damage_info) 

    def to_dict(self):
        return {
            'Kürzel': self.type_of_damage,
            **{str(index): damage_info.to_dict() for index, damage_info in enumerate(self.ids)} 
        }


class Frame:
    def __init__(self, name):
        self.name = name 
        self.damages = {}

    def add_damage(self, damage):
        self.damages.append(damage)  

    def to_dict(self):
        return {
            'Frame': self.name,
            'Befunde': [damage.to_dict() for damage in self.damages] 
        }
    




