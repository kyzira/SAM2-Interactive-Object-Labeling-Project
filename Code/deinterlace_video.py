import subprocess
import os

class DeinterlaceVideo:
    def __init__(self, video_path, output_path):
        # Run the command
        try:
            if not os.path.exists(output_path):
                command = [
                    "ffmpeg",
                    "-i", video_path,  # Input video file
                    "-vf", "yadif",  # Deinterlace filter
                    output_path  # Output video file
                ]
                subprocess.run(command, check=True)
                print(f"Deinterlaced video saved as: {output_path}")
        except subprocess.CalledProcessError as e:
            print(f"Error occurred while processing: {e}")
        except FileNotFoundError:
            print("ffmpeg is not installed or not found in the system PATH.")