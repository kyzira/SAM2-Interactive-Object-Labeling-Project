import cv2
import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
from PIL import Image, ImageTk
import os
from skimage.metrics import structural_similarity as ssim
import time


# It is confusing that this class has different functions that state to "extract" something, but one time they return start and end frame numbers and
# the other time they extract frames and store them to the hard disk. You terms should be unambigious and clear, at least in the scope of a class. 
# Another thing is that this class has two purposes: 1st loading a video and extracting frames and 2nd opening a dialog showing a video player letting you select 
# start and end frame numbers.
# To solve all of those problems, the VideoPlayer should be moved outside of this class and just use it to determine start and end frame numbers. Then you can use 
# those start and end frame numbers to call the extract_frames function of this class. By that the only purpose of this class is to extract the actual frames and 
# "extracting" always means "extract frame from video and store them on hard disk".
#
# And there is another thing you have to consider: does it make sense to store start_second and end_second inside this class? Since your extract functions always expect
# start and end frames to be passed from outside, what purpose do those two member variables have, which state do they contain? So you have to decide: if you want to
# store those two variables inside this class, then you should implement setter functions for them and your extract function should use those instead of passed parameters.
# Or you store them outside and pass them to the extract function.
# The way your class is right know makes it convenient to store everything you need inside this class, but the idea and structure is not clear and consistent in that way.
class FrameExtraction:
    """
    This class loads the video and extracts frames in ranges set in the config file, or from a given to a given frame.
    When extract from video player function is loaded, it opens the VideoPlayer class and enables getting frames through the video player.
    """
    # Specify parameter variable types, i.e. video_path: str
    def __init__(self, video_path, output_dir, similarity_threshold=0.8):
        self.video_path = video_path
        self.output_dir = output_dir
        self.similarity_threshold = similarity_threshold
        self.start_second = None
        self.end_second = None
        self.fps = None

    # You once use the term "extract" to extract start and end frames and another time to extract frames and store them to the hard disk.
    # You terms should be unambigious and clear.
    def extract_from_video_player(self):
        # Creating the tk.Toplevel and calling mainloop should be done in the open function of VideoPlayer
        root = tk.Toplevel()
        player = VideoPlayer(root, self.video_path, self.start_second)
        root.mainloop()
        try:
            if root.winfo_exists():
                start_frame, end_frame = player.get_result()
                # Why do you explicitely call destroy? The root object should be deleted automatically after leaving the "extract_from_video_player" function
                root.destroy()
                if start_frame is not None and end_frame is not None:
                    return start_frame, end_frame
        except:
            pass

        return 0, 0

    # You once use the term "start_seconds" and another time you use "start_second", this should be uniform (I would prefer "start_second") (analog for "end_seconds")
    def extract_frames_by_damage_time(self, start_seconds: int, end_seconds: int, frame_rate: int):
        if not self.fps:
            # Better determine and initialize fps in another function which is directly called in the constructor. This
            # function should only have the purpose to extract the frames.
            cap = cv2.VideoCapture(self.video_path)
            if not cap.isOpened():
                print(f"Error opening video file: {self.video_path}")
                return False
            self.fps = cap.get(cv2.CAP_PROP_FPS)
            cap.release()
        
        start_frame = start_seconds * self.fps
        end_frame = end_seconds * self.fps

        self.extract_frames(int(start_frame), int(end_frame), int(frame_rate))

    # In what case is it necessary to specify the frame_rate manually? You already got self.fps with the frame rate of the video
    def extract_frames(self, start_frame: int, end_frame: int, frame_rate: int) -> bool:

        # Always declare a variable just before you use it. Moreover a better variable name would be "previous_frame"
        last_frame = None
        
        cap = cv2.VideoCapture(self.video_path)
        if not cap.isOpened():
            print(f"Error opening video file: {self.video_path}")
            return False

        # Get total number of frames
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        print(f"Total frames in video: {total_frames}")

        # Better make a check here whether end_frame is bigger than total_frames and print an error message, so that you directly notice if something unexpected happens

        start_frame = max(start_frame, 0)
        end_frame = min(end_frame, total_frames)

        print(f"Extracting frames from {start_frame} to {end_frame}.")

        # Extract frames in the specified range
        counter_pos = 0
        counter_skipped = 0
        avg_similarity = 0

        for frame_number in range(start_frame, end_frame, frame_rate):
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            success, frame = cap.read()
            if not success:
                print(f"Failed to read frame {frame_number}.")
                # In this case "extract_frames" function returns True, but since the function failed, it should return False instead.
                # So you could just do the following instead of "break":
                # cap.release()
                # return False
                break
            
            if last_frame is not None:
                similarity_index = self.__check_for_similarity(last_frame, frame)
            if last_frame is not None and similarity_index > self.similarity_threshold:
                counter_skipped += 1
                avg_similarity = similarity_index if avg_similarity == 0 else (avg_similarity + similarity_index) / 2
                continue

            # Since you dynamically write files based on output_dir, you need to check whether the output dir is valid at the beginning of this function
            output_filename = os.path.join(self.output_dir, f'{frame_number:05d}.jpg')
            cv2.imwrite(output_filename, frame)
            
            counter_pos += 1
            last_frame = frame

        cap.release()

        print(f"Frames have been saved to {self.output_dir}.\nSuccessfully Extracted {counter_pos} Frames, Skipped {counter_skipped} Frames with Avg Similarity of {int(round(avg_similarity, 2) * 100)}%\n")
        return True
    
    # This function is not necessary and hard to understand on first glance, better define getter functions for self.start_second and self.end_second and directly call extract_frames_by_damage_time:
    # frame_extraction.extract_frames_by_damage_time(frame_extraction.start_second()+10, frame_extraction.end_second()+10)
    # By this, the class is more lightweighted and its usage is always the same and is easy to understand.
    def extract_further(self, extra_seconds_to_extract: int, reverse = False):
        if not(self.start_second or self.end_second):
            # better print an error message here, so the user/programmer directly knows that something has gone wrong
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
    

# 1. The VideoPlayer class should be better moved into a separate file, so you can easily find it if you want to inspect/revise it.
# If you want to pack different classes together, you can move them into a directory, but this would be overkill here.
# 2. The class name should imply that it is a dialog or window, so "VideoPlayerDialog" or "VideoPlayerWindow" would be better
# 3. The main functionalities of a dialog is open and close, so I would implement an open function (setting up tk.Toplevel(), calling load_video and starting main_loop) and
# a close function calling self.root.quit().
# 5. All functions except for open and close should be private, since the dialog just needs a video path to work. Everything
# else takes place inside the class. You could argue that the close function should also be private, but since this is a crucial
# dialog function it may make sense to be called from outside.
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
        # Why is the frame rate hardcoded and not determined by the video?
        self.frame_rate = 30
        self.start_second = start_second

        self.setup_ui()
        
        if video_path:
            self.load_video(video_path)
    
    # Function should be private
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
    
    # This function does not extract frames, it sets the current frame numbers and closes the dialog.
    # Since you already stored the start and end frame numbers in start_frame_var and stop_frame_var, you do not need start_frame and end_frame additionally.
    # Better rename this function "close" and just call self.root.quit.
    # To solve the problem about invalid frame numbers you could disable the "Extract" button in set_start_frame or set_end_frame functions,
    # if self.start_frame_var.get() or self.end_frame_var.get() fail.
    def extract_frames(self):
        try:
            start = int(self.start_frame_var.get())
            stop = int(self.stop_frame_var.get())
            self.start_frame = start
            self.stop_frame = stop
            self.root.quit()
        except ValueError:
            print("Please enter valid frame numbers")
    

    # Better implement two separate getter functions for start and end frames,
    # So you do not get an obscured tuple, where you do not directly know whats inside.
    # An example would be:
    # def start_frame() -> int:
    #    try:
    #       frame_number = int(self.start_frame_var.get())
    #    if frame_number <= 0:
    #       return None
    #    return frame_number
    #    except ValueError:
    #       return None
    def get_result(self):
        start = (int(self.start_frame/self.frame_rate)*self.frame_rate)
        end = (int(self.stop_frame/self.frame_rate)*self.frame_rate)

        return start, end
