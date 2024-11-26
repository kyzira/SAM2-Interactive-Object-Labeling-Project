import cv2
import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
from PIL import Image, ImageTk
import os
from skimage.metrics import structural_similarity as ssim
import time


class FrameExtraction:
    """
    This class loads the video and extracts frames in ranges set in the config file, or from a given to a given frame.
    When extract from video player function is loaded, it opens the VideoPlayer class and enables getting frames through the video player
    """
    def __init__(self, video_path, output_dir, similarity_threshold=0.8):
        self.video_path = video_path
        self.output_dir = output_dir
        self.similarity_threshold = similarity_threshold
        self.start_second = None
        self.end_second = None
        self.fps = None

    def extract_from_video_player(self):
        root = tk.Toplevel()
        player = VideoPlayer(root, self.video_path, self.start_second)
        root.mainloop()
        try:
            if root.winfo_exists():
                start_frame, end_frame = player.get_result()
                root.destroy()
                if start_frame is not None and end_frame is not None:
                    return start_frame, end_frame
        except:
            pass

        return 0, 0

    def extract_frames_by_damage_time(self, start_seconds: int, end_seconds: int, frame_rate: int):

        if not self.fps:
            cap = cv2.VideoCapture(self.video_path)
            if not cap.isOpened():
                print(f"Error opening video file: {self.video_path}")
                return False
            self.fps = cap.get(cv2.CAP_PROP_FPS)
            cap.release()
        
        start_frame = start_seconds * self.fps
        end_frame = end_seconds * self.fps

        self.extract_frames(int(start_frame), int(end_frame), int(frame_rate))

    def extract_frames(self, start_frame: int, end_frame: int, frame_rate: int) -> bool:

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

        for frame_number in range(start_frame, end_frame, frame_rate):
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            ret, frame = cap.read()

            if not ret:
                print(f"Failed to read frame {frame_number}.")
                break
            
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
    
    def extract_further(self, extra_seconds_to_extract: int, reverse = False):
        if not(self.start_second or self.end_second):
            return

        if reverse:
            end = self.start_second
            start = self.start_second - extra_seconds_to_extract
            self.start_second = start
        else:
            start = self.end_second
            end = self.end_second + extra_seconds_to_extract
            self.end_second = end

        self.extract_frames_by_damage_time(int(start), int(end), frame_rate=25)

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
    

class VideoPlayer:
    """
    This class opens a video player, which lets you set a start and end for frame extraction
    """
    def __init__(self, root, video_path=None, start_second = 0):
        self.root = root
        self.root.title("Video Player")
        
        # Video variables
        self.video_path = video_path
        self.video = None
        self.total_frames = 0
        self.current_frame = 0
        self.start_frame = 0
        self.stop_frame = 0
        self.is_playing = False
        self.frame_rate = 30
        self.start_second = start_second

        self.setup_ui()
        
        if video_path:
            self.load_video(video_path)
        
    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Video display
        self.canvas = tk.Canvas(main_frame, width=640, height=480, bg='black')
        self.canvas.grid(row=0, column=0, columnspan=4, pady=5)
        
        # Controls frame
        controls_frame = ttk.Frame(main_frame)
        controls_frame.grid(row=1, column=0, columnspan=4, pady=5)
        
        # Buttons
        if self.video_path == None:
            self.load_btn = ttk.Button(controls_frame, text="Load Video", command=self.load_video)
            self.load_btn.grid(row=0, column=0, padx=5)
        
        self.play_btn = ttk.Button(controls_frame, text="Play", command=self.toggle_play)
        self.play_btn.grid(row=0, column=1, padx=5)
        
        # Frame selection frame
        frame_select_frame = ttk.Frame(main_frame)
        frame_select_frame.grid(row=2, column=0, columnspan=4, pady=5)
        
        # Start frame controls
        start_frame_group = ttk.Frame(frame_select_frame)
        start_frame_group.grid(row=0, column=0, padx=10)
        
        ttk.Label(start_frame_group, text="Start Frame:").grid(row=0, column=0, padx=5)
        self.start_frame_var = tk.StringVar(value="0")
        self.start_frame_entry = ttk.Entry(start_frame_group, textvariable=self.start_frame_var, width=10)
        self.start_frame_entry.grid(row=0, column=1, padx=5)
        
        self.set_start_btn = ttk.Button(start_frame_group, text="Set Current", 
                                      command=self.set_start_frame)
        self.set_start_btn.grid(row=0, column=2, padx=5)
        
        # Stop frame controls
        stop_frame_group = ttk.Frame(frame_select_frame)
        stop_frame_group.grid(row=0, column=1, padx=10)
        
        ttk.Label(stop_frame_group, text="Stop Frame:").grid(row=0, column=0, padx=5)
        self.stop_frame_var = tk.StringVar(value="0")
        self.stop_frame_entry = ttk.Entry(stop_frame_group, textvariable=self.stop_frame_var, width=10)
        self.stop_frame_entry.grid(row=0, column=1, padx=5)
        
        self.set_stop_btn = ttk.Button(stop_frame_group, text="Set Current", 
                                     command=self.set_stop_frame)
        self.set_stop_btn.grid(row=0, column=2, padx=5)
        
        # Extract button
        self.extract_btn = ttk.Button(frame_select_frame, text="Extract", command=self.extract_frames)
        self.extract_btn.grid(row=0, column=2, padx=20)
        
        # Progress slider
        self.slider = ttk.Scale(main_frame, from_=0, to=100, orient='horizontal', 
                              command=self.slider_changed)
        self.slider.grid(row=3, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=5)
        
        # Frame counter
        self.frame_label = ttk.Label(main_frame, text="Frame: 0 / 0")
        self.frame_label.grid(row=4, column=0, columnspan=4, pady=5)

        # Frame counter
        self.first_frame_label = ttk.Label(main_frame, text=f"First Frame was {self.start_frame}")
        self.first_frame_label.grid(row=4, column=3, columnspan=4, pady=5)
    
    def set_start_frame(self):
        self.start_frame = self.current_frame
        self.start_frame_var.set(str(self.current_frame))
    
    def set_stop_frame(self):
        self.stop_frame = self.current_frame
        self.stop_frame_var.set(str(self.current_frame))
        
    def load_video(self, video_path=None):
        if video_path is None:
            video_path = filedialog.askopenfilename(
                filetypes=[("Video files", "*.mp4 *.avi *.mkv")])
        
        if video_path:
            self.video_path = video_path
            if self.video is not None:
                self.video.release()
            
            self.video = cv2.VideoCapture(video_path)
            self.total_frames = int(self.video.get(cv2.CAP_PROP_FRAME_COUNT))

            self.frame_rate = int(self.video.get(cv2.CAP_PROP_FPS))
            self.current_frame = 0
            self.slider.configure(to=self.total_frames-1)
            self.stop_frame_var.set(str(self.total_frames-1))
            self.stop_frame = self.total_frames-1

            self.start_frame = self.start_second * self.frame_rate
            self.first_frame_label.config(text=f"First Frame was {self.start_frame}")

            self.slider_changed(self.start_frame)
            self.slider.set(self.start_frame)
            
    def toggle_play(self):
        if self.video is None:
            return
        
        self.is_playing = not self.is_playing
        self.play_btn.configure(text="Pause" if self.is_playing else "Play")
        
        if self.is_playing:
            self.play_video()
    
    def play_video(self):
        while self.is_playing and self.video is not None:
            if self.current_frame >= self.total_frames - 1:
                self.current_frame = 0
                self.video.set(cv2.CAP_PROP_POS_FRAMES, 0)
            
            ret, frame = self.video.read()
            if not ret:
                self.is_playing = False
                break
                
            self.current_frame = int(self.video.get(cv2.CAP_PROP_POS_FRAMES))
            self.update_frame(frame)
            self.slider.set(self.current_frame)
            self.update_frame_label()
            
            # Update the GUI
            self.root.update()
            time.sleep(1/self.frame_rate)
    
    def update_frame(self, frame=None):
        if frame is None and self.video is not None:
            self.video.set(cv2.CAP_PROP_POS_FRAMES, self.current_frame)
            ret, frame = self.video.read()
            if not ret:
                return
        
        if frame is not None:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = cv2.resize(frame, (640, 480))
            photo = ImageTk.PhotoImage(image=Image.fromarray(frame))
            self.canvas.create_image(0, 0, image=photo, anchor=tk.NW)
            self.canvas.image = photo
    
    def slider_changed(self, value):
        if self.video is not None:
            self.current_frame = int(float(value))
            self.update_frame()
            self.update_frame_label()
    
    def update_frame_label(self):
        self.frame_label.configure(text=f"Frame: {self.current_frame} / {self.total_frames-1}")
    
    def extract_frames(self):
        try:
            start = int(self.start_frame_var.get())
            stop = int(self.stop_frame_var.get())
            self.start_frame = start
            self.stop_frame = stop
            self.root.quit()
        except ValueError:
            print("Please enter valid frame numbers")
    
    def get_result(self):
        start = (int(self.start_frame/self.frame_rate)*self.frame_rate)
        end = (int(self.stop_frame/self.frame_rate)*self.frame_rate)

        return start, end
