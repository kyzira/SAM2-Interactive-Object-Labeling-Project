from extract_frames_from_video import extract_frames_by_frame, get_total_frames
from frame_info_struct import FrameInfoStruct
import json

class LoadMoreFrames:
    """
    A class that handles the extraction of additional frames from a video, 
    either backwards or forwards, based on the current set of loaded frames.

    This class takes a FrameInfoStruct object to manage information about the 
    currently loaded frames. It automatically detects the frame rate and the range 
    of frames that are already loaded, and provides methods to extract additional 
    frames either before or after the currently loaded frames.
    
    Attributes:
        frame_info_struct (FrameInfoStruct): An object that contains details 
                                             about the current set of frames.
        __frame_rate (int): The rate at which frames are extracted.
        __first_frame (int): The first frame of the currently loaded frames.
        __last_frame (int): The last frame of the currently loaded frames.
    """

    def __init__(self, frame_info_struct: FrameInfoStruct):
        self.frame_info_struct = frame_info_struct
        self.__frame_rate, self.__first_frame, self.__last_frame = self.__detect_framerate_and_first_last_frame()

    def __detect_framerate_and_first_last_frame(self):
        frame_list = []
        frame_names = self.frame_info_struct.get_frame_name_list()
        if not frame_names:
            print("Frame name list is empty")
            return 0, 0, 0

        for frame_name in frame_names:
            frame_number = int(frame_name.split(".")[0])
            frame_list.append(frame_number)

        json_path = self.frame_info_struct.json_path
        with open(json_path, "r") as file:
            json_data = json.load(file)

        for key in json_data.keys():
            if "Info" in key:
                frame_rate = json_data[key]["Extracted Frame Rate"]
        
        frame_list = sorted(frame_list)
        return frame_rate, frame_list[0], frame_list[-1]

    def extract_backwards(self, video_path: str, num_of_extra_frames: int):
            """
            Extracts additional frames from the video in the reverse direction.

            The method extracts 'num_of_extra_frames' frames from the video starting 
            from the first currently loaded frame and moving backwards. If the start 
            of the video is reached, it stops extracting.

            Args:
                video_path (str): Path to the video file from which frames will be extracted.
                num_of_extra_frames (int): The number of frames to extract backwards.
            """
            self.__frame_rate, self.__first_frame, self.__last_frame = self.__detect_framerate_and_first_last_frame()
            if video_path == "":
                print("Error: Video Path not valid!")
                return

            if num_of_extra_frames <= 0:
                print("Error: Invalid amount of frames to extract")

            end_frame = self.__first_frame - self.__frame_rate
            if end_frame < 1:
                return
            else:
                start_frame = end_frame - num_of_extra_frames * self.__frame_rate
                start_frame = max(start_frame, 0)

            try:
                extract_frames_by_frame(input_path=video_path, 
                            output_path=self.frame_info_struct.frame_dir, 
                            start_frame=start_frame,
                            end_frame=end_frame,
                            frame_rate=self.__frame_rate)
            except:
                 print("Error while converting")
        
    def extract_forwards(self, video_path: str, num_of_extra_frames: int):
            """
            Extracts additional frames from the video in the forward direction.

            The method extracts 'num_of_extra_frames' frames from the video starting 
            after the last currently loaded frame and moving forwards. If the end 
            of the video is reached, it stops extracting.

            Args:
                video_path (str): Path to the video file from which frames will be extracted.
                num_of_extra_frames (int): The number of frames to extract forwards.
            """
            self.__frame_rate, self.__first_frame, self.__last_frame = self.__detect_framerate_and_first_last_frame()
            if video_path == "":
                print("Error: Video Path not valid!")
                return

            if num_of_extra_frames <= 0:
                print("Error: Invalid amount of frames to extract")

            start_frame = self.__last_frame + self.__frame_rate
            total_frames = get_total_frames(video_path)
            if start_frame > total_frames:
                return
            else:
                end_frame = start_frame + num_of_extra_frames * self.__frame_rate
                end_frame = min(end_frame, total_frames)

            extract_frames_by_frame(input_path=video_path, 
                        output_path=self.frame_info_struct.frame_dir, 
                        start_frame=start_frame,
                        end_frame=end_frame,
                        frame_rate=self.__frame_rate)