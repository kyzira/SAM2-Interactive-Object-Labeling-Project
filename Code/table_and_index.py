import os
import pandas as pd

class TableAndIndex:
    """
    This Class handles interacting with the csv, in which all information about the videos is stored in and handles incrementing the index every loop
    """
    def __init__(self, output_path: str, table_path: str, table_delimiter=";"):
        self.__output_path = output_path
        self.__table_path = table_path

        
        self.__index_path = os.path.join(self.__output_path, "current_index.txt")
        self.__current_index = self.get_current_index()

        # Load the table of damage entries from a CSV file
        self.__damage_table = pd.read_csv(self.__table_path, delimiter=table_delimiter)
        self.__total_length = len(self.__damage_table)  # Total number of entries in the table

    def get_output_dir(self):
        return self.__output_path

    def get_damage_table_row(self):
        self.__increment_and_save_current_index()

        if self.__current_index >= self.__total_length:
           print(f"Error: current index {self.__current_index} exceeds total length {self.__total_length}")
           return None

        return self.__damage_table.iloc[self.__current_index].to_dict()
    
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

    def __increment_and_save_current_index(self):
        """
        Increments the current index and saves it to the index file.
        """
        self.__current_index += 1
        with open(self.__index_path, "w") as file:
            file.write(str(self.__current_index))