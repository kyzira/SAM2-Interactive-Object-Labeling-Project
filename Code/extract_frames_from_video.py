import os
import cv2

def extract_frames_by_frame(input_path: str, output_path: str, start_frame=0, end_frame=None, frame_rate=1):
    if input_path == "":
        print("Error: Input path is empty!")
        return False

    if output_path == "":
        # Split the input path to get the base name and create frame directory
        base_name = os.path.basename(input_path)
        input_dir = os.path.dirname(input_path)
        output_path = os.path.join(input_dir, f"{base_name}")
        print(f"Error: Output path is empty!\nSaving Images in: {output_path}")
        
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

        output_filename = os.path.join(frame_dir, f'{frame_number:05d}.jpg')
        cv2.imwrite(output_filename, frame)
        print(f"Saved frame {frame_number} to {output_filename}")

    cap.release()
    print(f"Frames have been saved to {frame_dir}.")
    return True


def extract_frames_by_damage_time(input_path: str, output_path: str, damage_second=None, rewind_seconds=40, proceed_seconds=10, frame_rate=1):
    if input_path == "":
        print("Error: Input path is empty!")
        return

    if output_path == "":
        # Split the input path to get the base name and create frame directory
        base_name = os.path.basename(input_path)
        input_dir = os.path.dirname(input_path)
        output_path = os.path.join(input_dir, f"{base_name}")
        print(f"Error: Output path is empty!\nSaving Images in: {output_path}")
        

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

        output_filename = os.path.join(frame_dir, f'{frame_number:05d}.jpg')
        cv2.imwrite(output_filename, frame)
        print(f"Saved frame {frame_number} to {output_filename}")

    cap.release()
    print(f"Frames have been saved to {frame_dir}.")
    return True



def get_total_frames(video_path):
    
    video_capture = cv2.VideoCapture(video_path)
    total_frames = int(video_capture.get(cv2.CAP_PROP_FRAME_COUNT))
    video_capture.release()

    return total_frames