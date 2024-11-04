import cv2
import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
from PIL import Image, ImageTk

class VideoPlayer:
    def __init__(self, root, video_path=None, start_frame=0):
        self.root = root
        self.root.title("Select Start and End Frames")
        self.root.geometry("1200x1000")

        # Video display label
        self.video_label = tk.Label(root)
        self.video_label.pack(expand=True)

        frame_info_frame = tk.Frame(root)
        frame_info_frame.pack(fill="x")

        if start_frame:
            self.start_info_label = tk.Label(frame_info_frame, text=f"first frame was frame {start_frame}")
            self.start_info_label.pack(pady=10, side="left")

        # Current Frame Label
        self.current_frame_label = tk.Label(frame_info_frame, text="Current Frame: 0")
        self.current_frame_label.pack(pady=10, side="left")

        self.end_label = tk.Label(frame_info_frame, text="")
        self.end_label.pack(pady=10, padx=30, side="right")

        self.start_label = tk.Label(frame_info_frame, text="")
        self.start_label.pack(pady=10, padx=30, side="right")

        # Control Buttons
        control_frame = tk.Frame(root)
        control_frame.pack()

        self.play_button = tk.Button(control_frame, text="Play/Pause", command=self.toggle_play)
        self.play_button.grid(row=0, column=3, padx=5, pady=5)

        self.backward_button = tk.Button(control_frame, text="<< 10s", command=self.skip_backward)
        self.backward_button.grid(row=0, column=1, padx=5, pady=5)

        self.forward_button = tk.Button(control_frame, text="10s >>", command=self.skip_forward)
        self.forward_button.grid(row=0, column=2, padx=5, pady=5)

        self.set_start_button = tk.Button(control_frame, text="Set Start", command=self.set_start)
        self.set_start_button.grid(row=0, column=4, padx=5, pady=5)

        self.set_end_button = tk.Button(control_frame, text="Set End", command=self.set_end)
        self.set_end_button.grid(row=0, column=5, padx=5, pady=5)

        self.cancel_button = tk.Button(control_frame, text="Cancel", command=self.cancel)
        self.cancel_button.grid(row=0, column=6, padx=5, pady=5)

        self.cancel_button = tk.Button(control_frame, text="Extract", command=self.extract)
        self.cancel_button.grid(row=0, column=7, padx=5, pady=5)

        # Video Slider and Canvas for Bars
        self.canvas = tk.Canvas(root, height=20)  # Height for the bar
        self.canvas.pack(fill=tk.X, padx=10, pady=10)
        self.slider = ttk.Scale(root, from_=0, to=100, orient=tk.HORIZONTAL, command=self.seek)
        self.slider.pack(fill=tk.X, padx=10, pady=10)

        # Video variables
        self.video_path = video_path
        self.cap = None
        self.playing = True
        self.video_length = 0
        self.current_pos = start_frame
        self.start_pos = None
        self.end_pos = None
        self.fps = None
        self.extract_possible = False

        # Prompt to load video on start
        self.load_video()

        # Bind resizing event
        self.root.bind("<Configure>", self.on_resize)

    def get_start_and_end_frame(self):
        return self.start_pos, self.end_pos

    def cancel(self):
        self.start_pos = None
        self.end_pos = None
        self.root.destroy()

    def extract(self):
        if self.start_pos is None or self.end_pos is None:
            print("Error: Start or End is not set!")
        else:
            self.extract_possible = True
        self.root.destroy()

    def load_video(self):
        if self.video_path is None:
            self.video_path = filedialog.askopenfilename(filetypes=[("Video files", "*.mp4;*.avi;*.mov")])

        if self.video_path:
            self.cap = cv2.VideoCapture(self.video_path)
            self.video_length = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
            self.fps = self.cap.get(cv2.CAP_PROP_FPS)
            self.slider.config(to=self.video_length)
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.current_pos)
            self.play_video()
            self.root.after(100, self.toggle_play)

    def toggle_play(self):
        self.playing = not self.playing
        if self.playing:
            self.play_button.config(bg="green")
            self.play_video()
        else:
            self.play_button.config(bg="red")

    def skip_backward(self):
        self.current_pos = max(0, self.current_pos - int(10 * self.fps))
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.current_pos)
        self.update_slider()
        self.display_frame()

    def skip_forward(self):
        self.current_pos = min(self.video_length, self.current_pos + int(10 * self.fps))
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.current_pos)
        self.update_slider()
        self.display_frame()

    def set_start(self):
        self.start_pos = self.current_pos
        if self.end_pos:
            if self.start_pos > self.end_pos:
                self.end_pos = None
        
        self.update_status_label()
        self.update_bars()  # Update the bars after setting the start
        print(f"Start position set to frame: {self.start_pos}")

    def set_end(self):
        self.end_pos = self.current_pos
        self.update_status_label()
        self.update_bars()  # Update the bars after setting the end
        print(f"End position set to frame: {self.end_pos}")

    def update_status_label(self):
        if self.start_pos is not None:
            start_time = self.start_pos / self.fps 
            start_frame = self.start_pos
            self.start_label.config(text=f"Start: {int(start_time/(60*60)):02}:{int(start_time/60):02}:{int(start_time%60):02}, Frame: {start_frame}")

        if self.end_pos is not None:
            end_time = self.end_pos / self.fps
            end_frame = self.end_pos
            self.end_label.config(text=f"End: {int(end_time/(60*60)):02}:{int(end_time/60):02}:{int(end_time%60):02}, Frame: {end_frame}")

    def update_bars(self):
        # Clear the canvas
        self.canvas.delete("all")
        if self.start_pos is not None:
            # Calculate the position for the start bar
            start_x = (self.start_pos / self.video_length) * self.canvas.winfo_width()
            self.canvas.create_rectangle(start_x, 0, start_x + 3, 20, fill="green", outline="")  # Slim green bar for start

        if self.end_pos is not None:
            # Calculate the position for the end bar
            end_x = (self.end_pos / self.video_length) * self.canvas.winfo_width()
            self.canvas.create_rectangle(end_x, 0, end_x + 3, 20, fill="red", outline="")  # Slim red bar for end

    def update_current_frame_label(self):
        self.current_frame_label.config(text=f"Current Frame: {self.current_pos}")

    def update_slider(self):
        self.slider.set(self.current_pos)

    def play_video(self):
        if not self.cap or not self.playing:
            return

        ret, frame = self.cap.read()
        if not ret:
            self.pause_video()
            return

        width = self.root.winfo_width()
        height = self.root.winfo_height() - 180  # Adjust height for controls

        if width > 0 and height > 0:
            frame = cv2.resize(frame, (width, height))
        else:
            self.root.after(100, self.play_video)
            return

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(frame)
        image_tk = ImageTk.PhotoImage(image)
        self.video_label.config(image=image_tk)
        self.video_label.image = image_tk

        self.current_pos = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))
        self.update_slider()
        self.update_current_frame_label()

        delay = int((1000 / self.fps) * 0.8)
        self.root.after(delay, self.play_video)

    def seek(self, value):
        self.current_pos = int(float(value))
        if self.cap:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.current_pos)
            self.display_frame()

    def display_frame(self):
        if self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                width = self.root.winfo_width()
                height = self.root.winfo_height() - 180  # Adjust height for controls

                if width > 0 and height > 0:
                    frame = cv2.resize(frame, (width, height))
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    image = Image.fromarray(frame)
                    image_tk = ImageTk.PhotoImage(image)
                    self.video_label.config(image=image_tk)
                    self.video_label.image = image_tk

                self.update_current_frame_label()

    def on_close(self):
        self.playing = False
        if self.cap:
            self.cap.release()
        self.root.destroy()
        if self.extract_possible == False:
            self.cancel()

    def on_resize(self, event):
        self.display_frame()  # Update the video display on window resize

if __name__ == "__main__":
    root = tk.Tk()
    player = VideoPlayer(root, start_frame=0)
    root.protocol("WM_DELETE_WINDOW", player.on_close)
    root.mainloop()
