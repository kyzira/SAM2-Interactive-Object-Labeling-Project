import cv2
import numpy as np
import os
import subprocess
import tempfile
import shutil


def detect_interlacing(frame, threshold=5000000):
    even_lines = frame[0::2, :, :]
    odd_lines = frame[1::2, :, :]
    interlace_artifacts = np.sum(np.abs(even_lines.astype(int) - odd_lines.astype(int)))
    return interlace_artifacts > threshold


def split_video(video_path, output_dir, min_interval_duration=0.4):
    video = cv2.VideoCapture(video_path)
    if not video.isOpened():
        raise Exception("Video could not be opened.")
    
    os.makedirs(output_dir, exist_ok=True)
    fps = video.get(cv2.CAP_PROP_FPS)
    total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    
    interlaced_segments = []
    current_segment = None
    frame_count = 0
    puffer = fps

    while True:
        ret, frame = video.read()
        if not ret or frame is None:
            break

        if detect_interlacing(frame):
            if current_segment is None:
                current_segment = [frame_count, frame_count]
            else:
                current_segment[1] = frame_count
                puffer = fps
        else:
            if current_segment is not None:
                if puffer > 0:
                    puffer -= 1
                else:
                    interlaced_segments.append(current_segment)
                    current_segment = None
                    puffer = fps

        frame_count += 1

    if current_segment is not None:
        interlaced_segments.append(current_segment)

    # Convert frame numbers to time intervals
    interlaced_intervals = []
    for start_frame, end_frame in interlaced_segments:
        start_time = start_frame / fps
        end_time = end_frame / fps
        duration = end_time - start_time

        if duration >= min_interval_duration:
            rounded_start = int(start_time)
            rounded_end = int(end_time) + 1
            if rounded_end > rounded_start:
                interlaced_intervals.append((rounded_start, rounded_end))

    video.release()
    return interlaced_intervals


def deinterlace_segments(video_path, interlaced_intervals, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    deinterlaced_files = []
    for i, (start_time, end_time) in enumerate(interlaced_intervals):
        duration = end_time - start_time
        output_file = os.path.join(output_dir, f"deinterlaced_{i:02d}.mp4")

        ffmpeg_command = [
            "ffmpeg", "-y", "-i", video_path,
            "-vf", "yadif",
            "-ss", str(start_time),
            "-t", str(duration),
            "-c:v", "libx264", "-preset", "fast",
            "-crf", "18", "-c:a", "aac", output_file
        ]
        subprocess.run(ffmpeg_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        deinterlaced_files.append((start_time, end_time, output_file))
    return deinterlaced_files


def merge_video(video_path, deinterlaced_files, interlaced_intervals, output_dir, output_file):
    os.makedirs(output_dir, exist_ok=True)
    concat_file_path = os.path.join(output_dir, "concat_list.txt")
    fps = cv2.VideoCapture(video_path).get(cv2.CAP_PROP_FPS)
    total_duration = int(cv2.VideoCapture(video_path).get(cv2.CAP_PROP_FRAME_COUNT) / fps)

    non_interlaced_intervals = []
    prev_end = 0

    for start_time, end_time in interlaced_intervals:
        if start_time > prev_end:
            non_interlaced_intervals.append((prev_end, start_time))
        prev_end = end_time

    if prev_end < total_duration:
        non_interlaced_intervals.append((prev_end, total_duration))

    temp_files = []
    all_intervals = []

    for start_time, end_time in non_interlaced_intervals:
        duration = end_time - start_time
        output_name = os.path.join(output_dir, f"original_{start_time:06d}_{end_time:06d}.mp4")
        extract_command = [
            "ffmpeg", "-y", "-i", video_path,
            "-ss", str(start_time), "-t", str(duration),
            "-c", "copy", output_name
        ]
        subprocess.run(extract_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        temp_files.append(output_name)
        all_intervals.append((start_time, end_time, output_name))

    for start_time, end_time, deinterlaced_file in deinterlaced_files:
        temp_files.append(deinterlaced_file)
        all_intervals.append((start_time, end_time, deinterlaced_file))

    all_intervals.sort(key=lambda x: x[0])

    with open(concat_file_path, "w") as f:
        for _, _, file_path in all_intervals:
            f.write(f"file '{file_path.replace(os.sep, '/')}'\n")

    concat_command = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", concat_file_path, "-c", "copy", output_file
    ]
    subprocess.run(concat_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print(f"Deinterlaced video saved to: {output_file}")

    for temp_file in temp_files:
        if os.path.exists(temp_file):
            os.remove(temp_file)


def main():
    temp_dir = tempfile.mkdtemp()

    video_path = r"C:\Users\K3000\Videos\SAM2 Tests\test.mp4"
    output_dir = temp_dir
    output_file = r"C:\Users\K3000\Videos\SAM2 Tests\test_deinterlaced.mp4"

    try:
        interlaced_intervals = split_video(video_path, output_dir)

        print(f"Interlaced Intervals: {interlaced_intervals}")
        if not interlaced_intervals:
            print("No interlaced segments detected.")
            return

        deinterlaced_files = deinterlace_segments(video_path, interlaced_intervals, output_dir)
        merge_video(video_path, deinterlaced_files, interlaced_intervals, output_dir, output_file)
        print(f"Deinterlaced video saved: {output_file}")
    finally:
        shutil.rmtree(temp_dir)


if __name__ == "__main__":
    main()
