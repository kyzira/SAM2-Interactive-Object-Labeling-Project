from tkinter import filedialog
from tkinter import ttk
from PIL import Image, ImageTk
import cv2
import tkinter as tk
import time



class VideoPlayerWindow:
    """
    This class opens a video player, which lets you set a start and end for frame extraction
    """
    def __init__(self, video_path=None, start_second = 0):
        self.root = None

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
        self.end_second = None

    def open(self):
        self.root = tk.Toplevel()
        self.root.title("Video Player")
        self.__setup_ui()
        self.root.protocol("WM_DELETE_WINDOW", self.__on_close)
        if self.video_path:
            self.__load_video(self.video_path)
        self.root.mainloop()

    def get_result(self) -> tuple:
        """
        Returns start and end in seconds
        """
        return self.start_second, self.end_second
    
    def __on_close(self):
        self.start_second = None
        self.end_second = None

        self.root.quit()
        self.root.destroy()

    def __setup_ui(self):
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
            self.load_btn = ttk.Button(controls_frame, text="Load Video", command=self.__load_video)
            self.load_btn.grid(row=0, column=0, padx=5)
        
        self.play_btn = ttk.Button(controls_frame, text="Play", command=self.__toggle_play)
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
                                      command=self.__set_start_frame)
        self.set_start_btn.grid(row=0, column=2, padx=5)
        
        # Stop frame controls
        stop_frame_group = ttk.Frame(frame_select_frame)
        stop_frame_group.grid(row=0, column=1, padx=10)
        
        ttk.Label(stop_frame_group, text="Stop Frame:").grid(row=0, column=0, padx=5)
        self.stop_frame_var = tk.StringVar(value="0")
        self.stop_frame_entry = ttk.Entry(stop_frame_group, textvariable=self.stop_frame_var, width=10)
        self.stop_frame_entry.grid(row=0, column=1, padx=5)
        
        self.set_stop_btn = ttk.Button(stop_frame_group, text="Set Current", 
                                     command=self.__set_stop_frame)
        self.set_stop_btn.grid(row=0, column=2, padx=5)
        
        # Extract button
        self.extract_btn = ttk.Button(frame_select_frame, text="Extract", command=self.__on_extract_frames)
        self.extract_btn.grid(row=0, column=2, padx=20)
        
        # Progress slider
        self.slider = ttk.Scale(main_frame, from_=0, to=100, orient='horizontal', 
                              command=self.__slider_changed)
        self.slider.grid(row=3, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=5)
        
        # Frame counter
        self.frame_label = ttk.Label(main_frame, text="Frame: 0 / 0")
        self.frame_label.grid(row=4, column=0, columnspan=4, pady=5)

        # Frame counter
        self.first_frame_label = ttk.Label(main_frame, text=f"First Frame was {self.start_frame}")
        self.first_frame_label.grid(row=4, column=3, columnspan=4, pady=5)
    
    def __set_start_frame(self):
        self.start_frame = self.current_frame
        self.start_frame_var.set(str(self.current_frame))
    
    def __set_stop_frame(self):
        self.stop_frame = self.current_frame
        self.stop_frame_var.set(str(self.current_frame))
        
    def __load_video(self, video_path=None):
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

            self.start_frame = self.start_second * self.frame_rate
            self.first_frame_label.config(text=f"First Frame was {self.start_frame}")

            self.__slider_changed(self.start_frame)
            self.slider.set(self.start_frame)
            
    def __toggle_play(self):
        if self.video is None:
            return
        
        self.is_playing = not self.is_playing
        self.play_btn.configure(text="Pause" if self.is_playing else "Play")
        
        if self.is_playing:
            self.__play_video()
    
    def __play_video(self):
        while self.is_playing and self.video is not None:
            if self.current_frame >= self.total_frames - 1:
                self.current_frame = 0
                self.video.set(cv2.CAP_PROP_POS_FRAMES, 0)
            
            ret, frame = self.video.read()
            if not ret:
                self.is_playing = False
                break
                
            self.current_frame = int(self.video.get(cv2.CAP_PROP_POS_FRAMES))
            self.__update_frame(frame)
            self.slider.set(self.current_frame)
            self.__update_frame_label()
            
            # Update the GUI
            self.root.update()
            time.sleep(1/self.frame_rate)
    
    def __update_frame(self, frame=None):
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
    
    def __slider_changed(self, value):
        if self.video is not None:
            self.current_frame = int(float(value))
            self.__update_frame()
            self.__update_frame_label()
    
    def __update_frame_label(self):
        self.frame_label.configure(text=f"Frame: {self.current_frame} / {self.total_frames-1}")
    
    def __on_extract_frames(self):
        if self.start_frame >= self.stop_frame:
            print("Error: Start and End not correctly set!")
            return
        try:
            self.start_frame = int(self.start_frame_var.get())
            self.stop_frame = int(self.stop_frame_var.get())

            self.start_second = int(self.start_frame/self.frame_rate)
            self.end_second = int(self.stop_frame/self.frame_rate)

            self.root.quit()
            self.root.destroy()
        except ValueError:
            print("Please enter valid frame numbers")