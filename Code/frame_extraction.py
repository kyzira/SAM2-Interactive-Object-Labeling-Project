import cv2
import os
from skimage.metrics import structural_similarity as ssim


class FrameExtraction:
    """
    This class loads the video and extracts frames in ranges set in the config file, or from a given to a given frame.
    When extract from video player function is loaded, it opens the VideoPlayer class and enables getting frames through the video player
    """
    def __init__(self, video_path, output_dir, similarity_threshold=0.8):
        self.video_path = video_path
        self.output_dir = output_dir
        self.similarity_threshold = similarity_threshold
        self.fps = None
        self.do_histogram = False
        self.extraction_rate = None

    def get_fps(self):
        return self.fps
    
    def extract_frames_by_damage_time(self, start_seconds: int, end_seconds: int, extraction_rate: int, auto_histogram = None):
        if not self.fps:
            cap = cv2.VideoCapture(self.video_path)
            if not cap.isOpened():
                print(f"Error opening video file: {self.video_path}")
                return False
            self.fps = cap.get(cv2.CAP_PROP_FPS)
            cap.release()
        
        if auto_histogram is not None:
            self.do_histogram = auto_histogram

        if extraction_rate:
            self.extraction_rate = extraction_rate

        start_frame = start_seconds * self.fps
        end_frame = end_seconds * self.fps

        self.__extract_frames(int(start_frame), int(end_frame), int(extraction_rate))

    def extract_video_segment_by_similarity(self, start_second: int, end_second: int, frame_count: int, extraction_rate: int, direction: str = "forward"):
        """
        Identify and extract a video segment from the earliest dissimilar frame
        to the reference frame based on similarity checks.

        :param start_second: The starting time in seconds.
        :param end_second: The ending time in seconds.
        :param frame_count: Number of frames to analyze.
        :param extraction_rate: Number of frames to skip between analyses.
        :param direction: Direction to analyze ("forward" or "backward").
        """
        if not self.fps:
            cap = cv2.VideoCapture(self.video_path)
            if not cap.isOpened():
                print(f"Error opening video file: {self.video_path}")
                return False
            self.fps = cap.get(cv2.CAP_PROP_FPS)
            cap.release()

        cap = cv2.VideoCapture(self.video_path)
        if not cap.isOpened():
            print(f"Error opening video file: {self.video_path}")
            return False

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        start_frame = int(start_second * self.fps)
        end_frame = int(end_second * self.fps)

        # Determine direction and boundaries
        looking_range = None
        if direction == "forward":
            next_frame = min(end_frame, total_frames - 1)
        elif direction == "backward":
            next_frame = max(start_frame, 0)
        else:
            print("Invalid direction specified. Use 'forward' or 'backward'.")
            cap.release()
            return False

        last_frame = None
        dissimilar_start = None

        extractable_frame_counter = 0

        while True:
            if extractable_frame_counter >= frame_count:
                break
            
            if direction == "forward":
                next_frame += extraction_rate
            elif direction == "backward":
                next_frame -= extraction_rate

            if next_frame < 0 or next_frame > total_frames:
                break

            cap.set(cv2.CAP_PROP_POS_FRAMES, next_frame)
            ret, frame = cap.read()

            if not ret:
                print(f"Failed to read frame {next_frame}.")
                break
            
            # Apply histogram equalization
            frame = self.__apply_histogram_equalization(frame)

            # Check similarity
            if last_frame is not None:
                similarity_index = self.__check_for_similarity(last_frame, frame)
                if similarity_index < self.similarity_threshold:
                    extractable_frame_counter += 1

            last_frame = frame

        cap.release()

        if direction == "forward":
            end_frame = next_frame
        elif direction == "backward":
            start_frame = next_frame

        return self.__extract_frames(start_frame, end_frame, extraction_rate)

    def __extract_frames(self, start_frame: int, end_frame: int, extraction_rate: int) -> bool:

        last_frame = None
        
        cap = cv2.VideoCapture(self.video_path)
        if not cap.isOpened():
            print(f"Error opening video file: {self.video_path}")
            return False

        # Get total number of frames
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        print(f"Total frames in video: {total_frames}")

        start_frame = max(start_frame, 0)
        end_frame = min(end_frame, total_frames)

        print(f"Extracting frames from {start_frame} to {end_frame}.")

        # Extract frames in the specified range
        counter_pos = 0
        counter_skipped = 0
        avg_similarity = 0

        for frame_number in range(start_frame, end_frame+1, extraction_rate):
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            ret, frame = cap.read()

            if not ret:
                print(f"Failed to read frame {frame_number}.")
                break
            
            if self.do_histogram:
                frame = self.__apply_histogram_equalization(frame)
            
            if last_frame is not None:
                similarity_index = self.__check_for_similarity(last_frame, frame)
            if last_frame is not None and similarity_index > self.similarity_threshold:
                counter_skipped += 1
                avg_similarity = similarity_index if avg_similarity == 0 else (avg_similarity + similarity_index) / 2
                continue

            output_filename = os.path.join(self.output_dir, f'{frame_number:05d}.jpg')
            cv2.imwrite(output_filename, frame)
            
            counter_pos += 1
            last_frame = frame

        cap.release()

        print(f"Frames have been saved to {self.output_dir}.\nSuccessfully Extracted {counter_pos} Frames, Skipped {counter_skipped} Frames with Avg Similarity of {int(round(avg_similarity, 2) * 100)}%\n")
        return True

    def __apply_histogram_equalization(self, frame):
        """
        Apply histogram equalization to the frame.
        """
        # Convert to YUV color space
        yuv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2YUV)

        # Equalize the histogram of the Y channel
        yuv_frame[:, :, 0] = cv2.equalizeHist(yuv_frame[:, :, 0])

        # Convert back to BGR color space
        equalized_frame = cv2.cvtColor(yuv_frame, cv2.COLOR_YUV2BGR)
        return equalized_frame
    
    def __check_for_similarity(self, frame1, frame2):
        """
        Compares two frames and checks for similarity.
        """

        # Resize frames to the same size if necessary
        if frame1.shape != frame2.shape:
            frame1 = cv2.resize(frame1, (frame2.shape[1], frame2.shape[0]))

        # Convert frames to grayscale for SSIM comparison
        gray_frame1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
        gray_frame2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)

        # Compute SSIM between the two frames
        similarity_index = ssim(gray_frame1, gray_frame2)

        return similarity_index