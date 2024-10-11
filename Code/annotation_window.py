import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from PIL import Image, ImageTk, ImageDraw


class AnnotationWindow:
    def __init__(self, annotation_window, img, index):
        self.annotation_window = annotation_window
        
        # Create a canvas
        self.canvas = tk.Canvas(self.annotation_window)
        self.canvas.pack()

        # Example image (you need to load this from somewhere, e.g., self.image)
        # Assuming self.image is set elsewhere, you must define it before this step
        self.image = img # Example, replace with actual image
        self.tk_image = ImageTk.PhotoImage(self.image)

        # Display the image on the canvas
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)

        # Bind mouse click and key press events (optional, for future use)
        # self.canvas.bind('<Button-1>', self.on_click)
        # self.canvas.bind('<Key>', self.on_key_press)

        # Add a protocol to handle window close
        self.annotation_window.protocol("WM_DELETE_WINDOW", self.on_close)

    def on_close(self):
        # This function is called when the annotation window is closed
        self.annotation_window.destroy()

    def display_image(self, image, img_index):
        # Convert the PIL image to a NumPy array
        image_np = np.array(image)

        # Display the image
        self.subplot.imshow(image_np, aspect='equal')

        # Create a canvas for the Matplotlib figure in the new window
        canvas = FigureCanvasTkAgg()
        canvas.draw()
        canvas.get_tk_widget().pack(side=tk.LEFT, fill=tk.BOTH, expand=1)

     # Define event handlers
    # def on_click(event):
    #     if event.xdata is not None and event.ydata is not None:
    #         ix, iy = int(event.xdata), int(event.ydata)
    #         if event.button == 1:  # Left click
    #             print(f"Left click at ({ix}, {iy}) - 1")
    #             self.points.append([ix, iy])
    #             self.labels.append(1)
    #         elif event.button == 3:  # Right click
    #             print(f"Right click at ({ix}, {iy}) - 0")
    #             self.points.append([ix, iy])
    #             self.labels.append(0)
    #         update_mask(frame_number)

    # def on_key_press(event):
    #     if event.key == "backspace":
    #         if self.points:
    #             self.points.pop()
    #             self.labels.pop()
    #             update_mask(frame_number)
    #         else:
    #             # Clear the mask and show the original image if no points are left
    #             ax.clear()
    #             ax.imshow(image_np, aspect='equal')
    #             ax.axis('off')
    #             canvas.draw()

    # def update_mask(frame_number):
    #     if self.points and self.labels:
    #         # Clear previous plot and update the mask
    #         ax.clear()
    #         ax.imshow(image_np, aspect='equal')  # Maintain aspect ratio
    #         ax.axis('off')  # Ensure axes are completely off
    #         show_points(points_np, labels_np, ax)
    #         show_mask(, ax, )
    #         canvas.draw()
    #     else:
    #         # If no points are left, clear the mask and show the original image
    #         ax.clear()
    #         ax.imshow(image_np, aspect='equal')
    #         ax.axis('off')
    #         canvas.draw()

    # def show_mask(mask, ax, obj_id=None, random_color=False):
    #     if random_color:
    #         color = np.concatenate([np.random.random(3), np.array([0.6])], axis=0)
    #     else:
    #         cmap = plt.get_cmap("tab10")
    #         cmap_idx = 0 if obj_id is None else obj_id
    #         color = np.array([*cmap(cmap_idx)[:3], 0.6])
    #     h, w = mask.shape[-2:]
    #     mask_image = mask.reshape(h, w, 1) * color.reshape(1, 1, -1)
    #     ax.imshow(mask_image, alpha=0.5)

    # def show_points(coords, labels, ax, marker_size=200):
    #     pos_points = coords[labels == 1]
    #     neg_points = coords[labels == 0]
    #     ax.scatter(pos_points[:, 0], pos_points[:, 1], color='green', marker='*', s=marker_size, edgecolor='white', linewidth=1.25)
    #     ax.scatter(neg_points[:, 0], neg_points[:, 1], color='red', marker='*', s=marker_size, edgecolor='white', linewidth=1.25)

    # def on_close():
    #     self.wait_label.config(text="")
    #     self.frame_for_point = frame_number
    #     annotation_window.destroy()
    #     self.show_propagated_images()