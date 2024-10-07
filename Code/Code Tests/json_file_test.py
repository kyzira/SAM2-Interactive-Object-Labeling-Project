import json

class Gesetzte_Punkte:
    def __init__(self, pos_punkte, neg_punkte):
        self.pos_punkte = pos_punkte
        self.neg_punkte = neg_punkte

    def to_dict(self):
        return {
            '1': self.pos_punkte,
            '0': self.neg_punkte
        }


class Damage_info:
    def __init__(self, maske, punkte_klasse):
        self.punkte = punkte_klasse 
        self.maske = maske
    
    def to_dict(self):
        return {
            'Maske': self.maske,
            'Punkte': self.punkte.to_dict() 
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
            'Instanz': [damage_info.to_dict() for damage_info in self.ids]  
        }


class Frame:
    def __init__(self, name):
        self.name = name 
        self.damages = [] 

    def add_damage(self, damage):
        self.damages.append(damage)  

    def to_dict(self):
        return {
            'Frame': self.name,
            'Befunde': [damage.to_dict() for damage in self.damages] 
        }





test1 = Gesetzte_Punkte([1, 2, 3, 4], [5, 6, 7, 8])
test2 = Damage_info([0, 0, 0, 0, 0, 0, 0, 0], test1)
test3 = Damage("Crack")
test3.add_info(test2)
frame = Frame("Frame 1.jpg")
frame.add_damage(test3)





# Convert Frame object to dictionary and save to JSON
with open("frame_data.json", "w") as json_file:
    json.dump(frame.to_dict(), json_file, indent=4)

# Load from JSON and reconstruct the Frame object
with open("frame_data.json", "r") as json_file:
    loaded_data = json.load(json_file)

# Reconstruct the Frame object from loaded data
loaded_frame = Frame(loaded_data['name'])

# Reconstruct Damages and Damage_info objects
for damage_data in loaded_data['damages']:
    damage = Damage(damage_data['type_of_damage'])
    for info_data in damage_data['ids']:
        punkte = Gesetzte_Punkte(info_data['punkte']['pos_punkte'], info_data['punkte']['neg_punkte'])
        damage_info = Damage_info(info_data['maske'], punkte)
        damage.add_info(damage_info)
    loaded_frame.add_damage(damage)

# Check if loaded data matches original data
print(loaded_frame.to_dict())
