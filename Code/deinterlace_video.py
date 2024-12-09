import subprocess
import os

class DeinterlaceVideo:
    def __init__(self, video_path, output_path):
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Run the command
        try:
            if not os.path.exists(output_path):
                command = [
                    "ffmpeg",
                    "-hwaccel", "cuda",               # Use CUDA hardware acceleration
                    "-i", video_path,                 # Input video file
                    "-vf", "yadif=0:-1:0",            # Deinterlace filter
                    "-c:v", "mpeg2video",             # Video codec for MPEG output
                    "-q:v", "2",                      # Quality setting
                    "-b:v", "3M",                     # Video bitrate
                    "-c:a", "mp2",                    # Audio codec for MPEG
                    "-b:a", "192k",                   # Audio bitrate
                    output_path                       # Output video file
                ]
                subprocess.run(command, check=True, timeout=25)
                print(f"Deinterlaced video saved as: {output_path}")
            else:
                print(f"Output file already exists: {output_path}")
        except subprocess.CalledProcessError as e:
            print(f"Error occurred while processing: {e}")
        except FileNotFoundError as e:
            print(f"ffmpeg is not installed or not found in the system PATH.\n Error: {e}")
