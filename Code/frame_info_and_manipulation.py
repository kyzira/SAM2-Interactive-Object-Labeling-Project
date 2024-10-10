import os
from PIL import Image
from convert_video_to_frames import convert_video, get_total_frames


class FrameInfoStruct:
    def __init__(self, frame_dir):
        self.frame_dir = frame_dir
        self.working_dir = os.path.dirname(frame_dir)
        self.__frame_names = []
        self.__frames = []
        self.__frame_paths = []
        self.__get_info()
        self.masks = dict()

    def __get_info(self):
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


class LoadFrames:
    def __init__(self, frame_info_struct):
        self.frame_info_struct = frame_info_struct
        self.__frame_rate, self.__first_frame, self.__last_frame = self.__detect_framerate_and_first_last_frame()


    def __detect_framerate_and_first_last_frame(self):
        frame_list = []
        frame_names = self.frame_info_struct.get_frame_name_list()
        for frame_name in frame_names:
            if frame_name == "000000.jpg":
                frame_number = 0
            else:
                frame_number = int(frame_name.split(".")[0].lstrip("0"))

            frame_list.append(frame_number)

        frame_list = sorted(frame_list)
        frame_rate = frame_list[1] - frame_list[0]
        return frame_rate, frame_list[0], frame_list[-1]


    def extract_backwards(self, video_path, num_of_extra_frames):
            end_frame = self.__first_frame - self.__frame_rate
            if end_frame < 1:
                return
            else:
                start_frame = end_frame - num_of_extra_frames * self.__frame_rate
                start_frame = max(start_frame, 0)

            convert_video(input_path=video_path, 
                        output_path=self.frame_info_struct.frame_dir, 
                        start_frame=start_frame,
                        end_frame=end_frame,
                        frame_rate=self.__frame_rate)
        
    
    def extract_forwards(self, video_path, num_of_extra_frames):
            start_frame = self.__last_frame + self.__frame_rate
            total_frames = get_total_frames(video_path)
            if start_frame > total_frames:
                return
            else:
                end_frame = start_frame + num_of_extra_frames * self.__frame_rate
                end_frame = min(end_frame, total_frames)

            convert_video(input_path=video_path, 
                        output_path=self.frame_info_struct.frame_dir, 
                        start_frame=start_frame,
                        end_frame=end_frame,
                        frame_rate=self.__frame_rate)