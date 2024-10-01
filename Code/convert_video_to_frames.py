import os
import cv2


def convert_video(input_path="", output_path="", start_frame=None, end_frame=None, damage_second=None, frame_rate=1):
    if input_path == "":
        input_path = input("Video Path (without quotes): ").strip()

    rewind_seconds = 40
    proceed_seconds = 10


    # Split the input path to get the base name and create frame directory
    path_splits = os.path.normpath(input_path).split(os.path.sep)
    base_name = os.path.splitext(path_splits[-1])[0]
    input_dir = os.path.dirname(input_path)

    if output_path == "":
        output_path = os.path.join(input_dir, f"{base_name}")

    frame_dir = output_path
    os.makedirs(frame_dir, exist_ok=True)

    # Open the video file
    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        print(f"Error opening video file: {input_path}")
        return
    
    # Get total number of frames in the video
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print(f"Total frames in video: {total_frames}")
    

    if damage_second and not (start_frame and end_frame):
        fps = cap.get(cv2.CAP_PROP_FPS)
        damage_frame = damage_second * fps
        start_frame = max(0, int(damage_frame - rewind_seconds * fps))
        end_frame = min(total_frames, int(damage_frame - proceed_seconds * fps))
        print(f"Damage Second: {damage_second} Damage Frame: {damage_frame}")


    elif not (start_frame and end_frame):
        start_frame = 0
        end_frame = total_frames


    end_frame = min(total_frames, end_frame)


    print(f"Extracting frames from {start_frame} to {end_frame} with a frame rate of {frame_rate}.")

    frame_number = start_frame

    for frame_number in range(start_frame, end_frame, frame_rate):
        # Set the position of the next frame
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
    return frame_dir, input_path


def rename_images_in_directory(directory):
    files = os.listdir(directory)
    image_files = [f for f in files if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp'))]
    image_files.sort()

    # Rename images
    for index, file_name in enumerate(image_files):
        new_file_name = f"{index:05d}.jpg"
        old_file_path = os.path.join(directory, file_name)
        new_file_path = os.path.join(directory, new_file_name)
        img = cv2.imread(old_file_path)
        if img is not None:
            cv2.imwrite(new_file_path, img)
            os.remove(old_file_path)
            print(f"Renamed {file_name} to {new_file_name}")
        else:
            print(f"Failed to load {file_name}")







if __name__ == "__main__":
    convert_video(r"C:\Users\K3000\Videos\Filme\SD\Ohne OSD\KI_1.MPG", 0, 250, 5)


