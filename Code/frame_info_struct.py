import os
from PIL import Image


class FrameInfoStruct:
    """
    A class for managing and storing information about frames extracted from a video.

    This class handles the collection of frame file names, paths, and loaded image objects
    from a specified directory. It also sets up the working directory and prepares a path 
    for a potential JSON file related to the frames.

    Attributes:
        frame_dir (str): The directory where the extracted frames are located.
        working_dir (str): The directory where the frame directory is located.
        json_path (str): The path to the JSON file that may store additional information 
                         related to the frames.
        masks (dict): A dictionary that can store mask information (initialized empty).
        __frame_names (list): A private list of the names of all image files (frames) 
                              in the frame directory.
        __frames (list): A private list of Image objects loaded from the frame files.
        __frame_paths (list): A private list of full paths to the image files.
    """
    
    def __init__(self, frame_dir):
        self.frame_dir = frame_dir
        self.working_dir = os.path.dirname(frame_dir)
        self.json_path = os.path.join(self.working_dir, f"{os.path.basename(self.working_dir)}.json")
        self.__frame_names = []
        self.__frames = []
        self.__frame_paths = []
        self.__extract_info()
        self.masks = dict()


    def get_frame_name_list(self):
        return self.__frame_names

    def get_frames(self):
        return self.__frames

    def __extract_info(self):
        for file in os.listdir(self.frame_dir):
            file_path = os.path.join(self.frame_dir, file)

            if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                self.__frame_names.append(file)
                self.__frame_paths.append(file_path)
                self.__frames.append(Image.open(file_path))