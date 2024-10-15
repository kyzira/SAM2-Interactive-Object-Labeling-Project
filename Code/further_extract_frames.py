from extract_frames_from_video import extract_frames_by_frame, get_total_frames
from frame_info_struct import FrameInfoStruct


class LoadMoreFrames:
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

        frame_list = sorted(frame_list)
        frame_rate = frame_list[1] - frame_list[0]
        return frame_rate, frame_list[0], frame_list[-1]

    def extract_backwards(self, video_path: str, num_of_extra_frames: int):
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