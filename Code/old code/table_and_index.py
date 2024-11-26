import os
import pandas as pd

class TableAndIndex:
    """
    This Class handles interacting with the csv, in which all information about the videos is stored in and handles incrementing the index every loop
    """
    def __init__(self, paths):
        self.__output_path = paths["output_path"]
        self.__table_path = paths["table_path"]

        self.__index_path = os.path.join(self.__output_path, "current_index.txt")

        # Load the table of damage entries from a CSV file
        self.__damage_table = pd.read_csv(self.__table_path, delimiter=";")
        self.__total_length = len(self.__damage_table)  # Total number of entries in the table

    def get_output_dir(self):
        return self.__output_path

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
        

    def increment_and_save_current_index(self, current_index:int) -> int:
        """
        Increments the current index and saves it to the index file.
        current_index (int): The index to be incremented and saved.
        """
        current_index += 1
        with open(self.__index_path, "w") as file:
            file.write(str(current_index))

        return current_index