import os
import pandas as pd

class TableAndIndex:
    """
    This class handles interacting with the csv, in which all information about the videos is stored in and handles incrementing the index every loop.
    """
    # Better pass 2 separate paths instead of "paths" to avoid them being switched and it being more clear what paths are passed into the class
    def __init__(self, paths):
        self.__output_path = paths["output_path"]
        self.__table_path = paths["table_path"]

        self.__index_path = os.path.join(self.__output_path, "current_index.txt")

        # Load the table of damage entries from a CSV file
        self.__damage_table = pd.read_csv(self.__table_path, delimiter=";")
        self.__total_length = len(self.__damage_table)  # Total number of entries in the table

    def get_output_dir(self):
        return self.__output_path

    # Since you store the current index and only use this function for the current index, I would set
    # the current index as member and avoid passing the row here:
    # get_damage_table_row(self):
    #    if self.current_index >= self.__total_length:
    #       print(f"Error: current index {self.current_index} exceeds total length {self.self.__total_length}")
    #       return None
    #    if not self.__damage_table:
    #       print("Error: Damage table is not set")
    #       return None
    #    return self.__damage_table.iloc[self.current_index].to_dict()
    def get_damage_table_row(self, row) -> dict:
        damage_dict = self.__damage_table.iloc[row].to_dict()
        return damage_dict
    
    def get_total_length(self):
        return self.__total_length

    def get_current_index(self) -> int:
        """
        Reads the current index from a file. This index is used to track the last processed entry in the table.
        Returns the current index (starting at 0). If the index file doesn't exist, returns 0.
        """
        if os.path.exists(self.__index_path):
            with open(self.__index_path, "r") as index_file:
                index_content = index_file.read().strip()
                return int(index_content)
        else:
            return 0
        

    # I think it would make more sense to store the current_index in this class as member
    # and increment it. It is a little bit odd that you store it outside of this class.
    def increment_and_save_current_index(self, current_index:int) -> int:
        """
        Increments the current index and saves it to the index file.
        current_index (int): The index to be incremented and saved.
        """
        # You should check whether the current_index exceeds the __total_length
        current_index += 1
        with open(self.__index_path, "w") as file:
            file.write(str(current_index))

        return current_index