import os
from PIL import Image


class FrameInfoStruct:
    def __init__(self, frame_dir):
        self.frame_dir = frame_dir
        self.working_dir = os.path.dirname(frame_dir)
        self.__frame_names = []
        self.__frames = []
        self.__frame_paths = []
        self.__extract_info()
        self.masks = dict()

    def __extract_info(self):
        for file in os.listdir(self.frame_dir):
            file_path = os.path.join(self.frame_dir, file)

            if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                self.__frame_names.append(file)
                self.__frame_paths.append(file_path)
                self.__frames.append(Image.open(file_path))
    
    def get_frame_name_list(self):
        return self.__frame_names

    def get_frames(self):
        return self.__frames
