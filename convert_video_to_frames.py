import os
import cv2


def convert_video(input_path = "", start_frame = 0, end_frame = -1, frame_rate = 1):
    if input_path == "":
        input_path = input("Video Path (without quotes): ").strip()

    path_splits = os.path.normpath(input_path).split(os.path.sep)
    base_name = os.path.splitext(path_splits[-1])[0]
    input_dir = os.path.dirname(input_path)
    frame_dir = os.path.join(input_dir, f"{base_name}")
    os.makedirs(frame_dir, exist_ok=True)
    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        print(f"Error opening video file: {input_path}")
        return
    print("Successfully opened the video! \nSaving frames:")
    frame_number = start_frame


    while True:
        ret, frame = cap.read()

        if not ret or frame_number >= end_frame:
            break

        output_filename = os.path.join(frame_dir, f'{frame_number:05d}.jpg')
        cv2.imwrite(output_filename, frame)

        # Move to the next frame according to the frame_rate
        frame_number += frame_rate
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)

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


convert_video(r"C:\Users\K3000\Videos\Filme\SD\Ohne OSD\KI_1.MPG", 0, 250, 5)


