import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk  # Requires Pillow library

class ScrollableImageGrid(tk.Tk):
    def __init__(self, image_count, grid_width=3, image_height=100):
        super().__init__()
        self.title("Scrollable Image Grid")

        # Initial configurations
        self.image_count = image_count
        self.grid_width = grid_width
        self.image_height = image_height

        # Main frame setup
        main_frame = tk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Canvas and scrollbar setup
        self.canvas = tk.Canvas(main_frame, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=self.canvas.yview)
        
        # Place scrollbar to the right of the canvas without overlapping
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Scrollable frame within canvas
        self.scrollable_frame = tk.Frame(self.canvas)
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # Bind mouse wheel scrolling
        self.canvas.bind_all("<MouseWheel>", self.on_mousewheel)

        # Handle window resizing
        self.bind("<Configure>", self.resize_images)

        # Display the images
        self.images = []
        self.image_labels = []
        self.create_image_grid()

    def create_image_grid(self):
        # Generate placeholders and place them in the grid
        for i in range(self.image_count):
            img = self.create_placeholder_image(self.image_height)
            self.images.append(img)
            
            label = tk.Label(self.scrollable_frame, image=img)
            label.grid(row=i // self.grid_width, column=i % self.grid_width, padx=5, pady=5, sticky="nsew")
            label.bind("<Button-1>", lambda e, i=i: self.on_image_click(i))  # Bind click event
            
            self.image_labels.append(label)

    def create_placeholder_image(self, height):
        # Generate a placeholder image with dynamic width
        canvas_width = self.canvas.winfo_width() - self.scrollbar.winfo_width()  # Adjust for scrollbar width
        width = max((canvas_width - 30) // self.grid_width, 1) if canvas_width > 0 else 100  # Leave a bit of margin
        image = Image.new("RGB", (width, height), color=(150, 150, 250))
        return ImageTk.PhotoImage(image)

    def resize_images(self, event=None):
        # Adjust image width on window resize
        for i, label in enumerate(self.image_labels):
            new_img = self.create_placeholder_image(self.image_height)
            self.images[i] = new_img  # Update image reference
            label.configure(image=new_img)  # Update displayed image

    def on_image_click(self, image_index):
        print(f"Image {image_index + 1} clicked.")

    def on_mousewheel(self, event):
        # Enable mousewheel scrolling
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

if __name__ == "__main__":
    app = ScrollableImageGrid(image_count=20, grid_width=4)
    app.mainloop()
