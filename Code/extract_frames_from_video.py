import os
import cv2
from skimage.metrics import structural_similarity as ssim


def check_for_similarity(frame1, frame2, threshold=0.8):
    """
    Compares two frames and checks for similarity.

    Args:
        frame1: The first frame (image).
        frame2: The second frame (image).
        threshold: The similarity threshold (default is 0.95).

    Returns:
        bool: True if the frames are similar (above threshold), False otherwise.
    """
    # Resize frames to the same size if necessary
    if frame1.shape != frame2.shape:
        frame1 = cv2.resize(frame1, (frame2.shape[1], frame2.shape[0]))

    # Convert frames to grayscale for SSIM comparison
    gray_frame1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
    gray_frame2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)

    # Compute SSIM between the two frames
    similarity_index = ssim(gray_frame1, gray_frame2)

    print(f"SSIM: {similarity_index}")
    return similarity_index > threshold

def extract_frames_by_frame(input_path: str, output_path: str, start_frame=0, end_frame=None, frame_rate=1, threshold=0.8):
    """
    Extracts frames from a video file.

    This function takes the video located at 'input_path' and saves individual frames to 'output_path'. 
    Frames are extracted from 'start_frame' up to 'end_frame' with a specified 'frame_rate'. 
    If no 'end_frame' is provided, it defaults to the total number of frames in the video. 
    If 'output_path' is empty, the frames are saved in a directory with the same name as the video file.
    
    Args:
        input_path (str): The path to the input video file.
        output_path (str): The directory where the extracted frames will be saved.
        start_frame (int): The starting frame for extraction (default is 0).
        end_frame (int): The last frame to extract (default is the last frame of the video).
        frame_rate (int): The interval between frames to be extracted (default is 1, i.e., every frame).
    
    Returns:
        bool: True if the extraction is successful, False otherwise.
    """

    if input_path == "":
        print("Error: Input path is empty!")
        return False

    if output_path == "":
        # Split the input path to get the base name and create frame directory
        base_name = os.path.basename(input_path)
        input_dir = os.path.dirname(input_path)
        output_path = os.path.join(input_dir, f"{base_name}")
        print(f"Error: Output path is empty!\nSaving Images in: {output_path}")
        
    last_frame = None

    frame_dir = output_path
    os.makedirs(frame_dir, exist_ok=True)

    # Open the video file
    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        print(f"Error opening video file: {input_path}")
        return False

    # Get total number of frames in the video
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print(f"Total frames in video: {total_frames}")

    if end_frame is None:
        end_frame = total_frames
    else:
        end_frame = min(total_frames, end_frame)

    print(f"Extracting frames from {start_frame} to {end_frame} with a frame rate of {frame_rate}.")

    # Extract frames in the specified range
    for frame_number in range(start_frame, end_frame, frame_rate):
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        ret, frame = cap.read()

        if not ret:
            print(f"Failed to read frame {frame_number}.")
            break

        if last_frame is not None and check_for_similarity(last_frame, frame, threshold):
            print(f"Frame {frame_number} is similar to the last saved frame. Skipping...")
            continue

        output_filename = os.path.join(frame_dir, f'{frame_number:05d}.jpg')
        cv2.imwrite(output_filename, frame)
        print(f"Saved frame {frame_number} to {output_filename}")

        last_frame = frame

    cap.release()
    print(f"Frames have been saved to {frame_dir}.")
    return True


def extract_frames_by_damage_time(input_path: str, output_path: str, damage_second=None, rewind_seconds=40, proceed_seconds=10, frame_rate=1, threshold=0.8):
    """
    Extracts frames surrounding a specified timestamp (damage second) in a video.

    This function extracts frames from the video at 'input_path' based on a given 'damage_second' timestamp. 
    It rewinds by 'rewind_seconds' before the damage second and proceeds for 'proceed_seconds' after. 
    Frames are saved to 'output_path', or to a directory with the same name as the video file if 'output_path' is empty. 
    Frames are extracted at the interval specified by 'frame_rate'.
    
    Args:
        input_path (str): The path to the input video file.
        output_path (str): The directory where the extracted frames will be saved.
        damage_second (int): The timestamp of the event (in seconds) around which frames will be extracted.
        rewind_seconds (int): The number of seconds to rewind before 'damage_second' (default is 40).
        proceed_seconds (int): The number of seconds to extract after 'damage_second' (default is 10).
        frame_rate (int): The interval between frames to be extracted (default is 1, i.e., every frame).
    
    Returns:
        bool: True if the extraction is successful, False otherwise.
    """
    if input_path == "":
        print("Error: Input path is empty!")
        return

    if output_path == "":
        # Split the input path to get the base name and create frame directory
        base_name = os.path.basename(input_path)
        input_dir = os.path.dirname(input_path)
        output_path = os.path.join(input_dir, f"{base_name}")
        print(f"Error: Output path is empty!\nSaving Images in: {output_path}")
        
    last_frame = None

    frame_dir = output_path
    os.makedirs(frame_dir, exist_ok=True)

    # Open the video file
    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        print(f"Error opening video file: {input_path}")
        return False

    # Get total number of frames and FPS
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    print(f"Total frames in video: {total_frames}, FPS: {fps}")

    # Calculate the damage frame and range to extract
    damage_frame = damage_second * fps
    if damage_frame > total_frames:
        print("Error: Damage second exceeds total video length!")
        return False

    start_frame = max(0, int(damage_frame - rewind_seconds * fps))
    end_frame = min(total_frames, int(damage_frame + proceed_seconds * fps))

    print(f"Extracting frames from {start_frame} to {end_frame} around damage time at {damage_second}s.")

    # Extract frames in the specified range
    for frame_number in range(start_frame, end_frame, frame_rate):
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        ret, frame = cap.read()

        if not ret:
            print(f"Failed to read frame {frame_number}.")
            break
        
        if last_frame is not None and check_for_similarity(last_frame, frame, threshold):
            print(f"Frame {frame_number} is similar to the last saved frame. Skipping...")
            continue

        output_filename = os.path.join(frame_dir, f'{frame_number:05d}.jpg')
        cv2.imwrite(output_filename, frame)
        print(f"Saved frame {frame_number} to {output_filename}")

        last_frame = frame


    cap.release()
    print(f"Frames have been saved to {frame_dir}.")
    return True



def get_total_frames(video_path):
    
    video_capture = cv2.VideoCapture(video_path)
    total_frames = int(video_capture.get(cv2.CAP_PROP_FRAME_COUNT))
    video_capture.release()

    return total_frames