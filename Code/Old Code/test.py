import tkinter as tk
from tkinter import simpledialog

class ImageGridApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Grid Layout with Clickable Images and Menu")
        self.current_rows = 3  # Default grid size
        self.current_columns = 3
        self.create_widgets()

    def create_widgets(self):
        # Configure grid layout for the root window
        self.root.grid_rowconfigure(2, weight=1)  # Middle frame resizes
        self.root.grid_columnconfigure(0, weight=1)  # Frames span full width

        # Create a menu
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # Add options to change grid size
        grid_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Options", menu=grid_menu)
        grid_menu.add_command(label="Change Grid Size", command=self.prompt_grid_size)

        # Top frame
        self.first_row_frame = tk.Frame(self.root, bg="lightblue", height=50)
        self.first_row_frame.grid(row=0, column=0, columnspan=2, sticky="nsew")
        self.first_row_frame.grid_columnconfigure(0, weight=1)
        tk.Button(self.first_row_frame, text="Button 1").grid(row=0, column=0, padx=5, pady=5)

        # Top frame
        self.second_row_frame = tk.Frame(self.root, bg="lightblue", height=50)
        self.second_row_frame.grid(row=1, column=0, columnspan=2, sticky="nsew")
        self.second_row_frame.grid_columnconfigure(0, weight=1)
        tk.Button(self.second_row_frame, text="Button 2").pack(side="left", padx=5, pady=5)


        # Configure columns to evenly split top frames
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)

        # Middle frame for images with dynamic grid
        self.middle_frame = tk.Frame(self.root, bg="white")
        self.middle_frame.grid(row=2, column=0, columnspan=2, sticky="nsew")
        self.update_image_grid(self.current_rows, self.current_columns)

        # Bottom frame
        self.bottom_frame = tk.Frame(self.root, bg="lightgrey", height=50)
        self.bottom_frame.grid(row=3, column=0, columnspan=2, sticky="nsew")
        tk.Button(self.bottom_frame, text="Bottom Button").pack(pady=10)

    def update_image_grid(self, rows, columns):
        # Clear existing widgets in the middle frame
        for widget in self.middle_frame.winfo_children():
            widget.destroy()

        # Create a grid of labels as image placeholders with click events
        for r in range(rows):
            self.middle_frame.grid_rowconfigure(r, weight=1)
            for c in range(columns):
                self.middle_frame.grid_columnconfigure(c, weight=1)
                label = tk.Label(self.middle_frame, text=f"Image {r+1},{c+1}", bg="white", borderwidth=1, relief="solid")
                label.grid(row=r, column=c, sticky="nsew", padx=5, pady=5)
                # Bind click event to each label
                label.bind("<Button-1>", lambda e, row=r, col=c: self.on_image_click(row, col))

    def on_image_click(self, row, col):
        # Display the row and column of the clicked image
        print(f"Image at Row {row+1}, Column {col+1} clicked!")

    def prompt_grid_size(self):
        # Prompt the user to input new grid dimensions
        rows = simpledialog.askinteger("Grid Rows", "Enter number of rows:", minvalue=1, maxvalue=10)
        columns = simpledialog.askinteger("Grid Columns", "Enter number of columns:", minvalue=1, maxvalue=10)
        if rows and columns:
            self.current_rows = rows
            self.current_columns = columns
            self.update_image_grid(rows, columns)

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("800x600")
    app = ImageGridApp(root)
    root.mainloop()
