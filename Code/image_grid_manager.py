import threading
from PIL import Image, ImageTk, ImageDraw

class ImageGridManager:
    def __init__(self, canvas, image_slider, grid_entry, frame_info, json, observations, checkbox_vars, radio_var):
        self.canvas = canvas
        self.image_slider = image_slider
        self.grid_entry = grid_entry
        self.frame_info = frame_info
        self.json = json
        self.observations = observations
        self.checkbox_vars = checkbox_vars
        self.radio_var = radio_var
        self.image_refs = []
        self.marked_frames = []
        self.initialized = True  # Assuming the manager is initialized for demonstration

    def reload_grid_and_images(self):

        def seperate_thread():
            grid_size = int(self.grid_entry.get())

            if grid_size < 1:
                print(f"Error: Gridsize invalid: {grid_size}")
                return

            images_per_grid = grid_size * grid_size
            slider_max = max(0, len(self.frame_info.get_frame_name_list()) - images_per_grid)
            self.image_slider.config(from_=0, to=slider_max)

            self.show_selected_images()

        threading.Thread(target=seperate_thread).start()

    def get_canvas_info(self):
        # Get canvas size
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        if canvas_width <= 0 or canvas_height <= 0:
            return

        try:
            grid_size = int(self.grid_entry.get())
        except ValueError:
            print("Invalid input. Please enter a valid integer.")
            return

        if grid_size <= 0:
            return

        cell_width = canvas_width / grid_size
        cell_height = canvas_height / grid_size

        return cell_width, cell_height, grid_size

    def show_selected_images(self, start_index=None):
        """Displays images in a grid format on the canvas."""
        if not self.initialized:
            return

        if start_index is None:
            start_index = self.image_slider.get()

        self.image_refs = []

        image_list = self.frame_info.get_frames()
        image_names = self.frame_info.get_frame_name_list()

        self.canvas.delete("all")
        cell_width, cell_height, grid_size = self.get_canvas_info()

        json_data = self.json.get_json()

        for i in range(grid_size * grid_size):
            index = int(start_index + i)

            if index >= len(image_list):
                break

            img = image_list[index]
            img_name = image_names[index]

            # Add mask if available
            if json_data:
                for frame in json_data.values():
                    if "File Name" not in frame:
                        continue
                    if img_name in frame["File Name"]:
                        masked_img = self.draw_mask_on_image(img, frame)
                        img = masked_img

            # Resize the image
            img = img.resize((int(cell_width), int(cell_height)), Image.Resampling.LANCZOS)
            tk_img = ImageTk.PhotoImage(img)

            self.image_refs.append(tk_img)

            # Place the image on the canvas
            row = i // grid_size
            col = i % grid_size
            x_position = col * cell_width
            y_position = row * cell_height
            self.canvas.create_image(x_position + cell_width // 2, y_position + cell_height // 2, image=tk_img)

    def draw_mask_on_image(self, img, frame):
        # Define a set of colors for different mask.json files
        colors = [
            (255, 0, 0, 100),   # Red with transparency
            (0, 0, 255, 100),   # Blue with transparency
            (0, 255, 0, 100),   # Green with transparency
            (255, 255, 0, 100), # Yellow with transparency
            (255, 0, 255, 100)  # Magenta with transparency
        ]

        if frame["File Name"] in self.marked_frames:
            # Draw Red border around image
            border_thickness = 5
            img_width, img_height = img.size
            overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
            overlay_draw = ImageDraw.Draw(overlay)
            overlay_draw.rectangle(
                [(0, 0), (img_width, border_thickness)],
                fill=(255, 0, 0, 255)  # Red color
            )
            overlay_draw.rectangle(
                [(0, 0), (border_thickness, img_height)],
                fill=(255, 0, 0, 255)  # Red color
            )
            overlay_draw.rectangle(
                [(img_width - border_thickness, 0), (img_width, img_height)],
                fill=(255, 0, 0, 255)  # Red color
            )
            overlay_draw.rectangle(
                [(0, img_height - border_thickness), (img_width, img_height)],
                fill=(255, 0, 0, 255)  # Red color
            )
            img = Image.alpha_composite(img.convert("RGBA"), overlay)

        observation_list = self.observations.get_observation_list()

        for kuerzel in observation_list:
            # Create a transparent overlay for polygons
            overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
            overlay_draw = ImageDraw.Draw(overlay, "RGBA")

            if "Observations" not in frame:
                return

            if kuerzel in frame["Observations"]:
                schaden_data = frame["Observations"][kuerzel]

                if schaden_data.keys() is None:
                    continue

                # Check if "Mask Polygon" exists
                if "Mask Polygon" in schaden_data:
                    polygons = schaden_data["Mask Polygon"]
                else:
                    polygons = None

                observation_index = observation_list.index(kuerzel)
                color = colors[observation_index % len(colors)]

                # Use get method for checkbox_vars
                checkbox_var = self.checkbox_vars.get(kuerzel)
                if checkbox_var and checkbox_var.get():
                    # Draw polygons
                    if polygons:
                        for polygon in polygons:
                            polygon_tuples = [tuple(point) for point in polygon]
                            if len(polygon_tuples) > 3:
                                overlay_draw.polygon(polygon_tuples, outline=color[:3], fill=color)

                    # Call the new function to draw points and selection order
                    if kuerzel == self.radio_var.get():
                        self.draw_points_on_image(overlay_draw, schaden_data, img)

            # Composite the overlay with the original image
            if img.mode != "RGBA":
                img = img.convert("RGBA")
            img = Image.alpha_composite(img, overlay)
            img = img.convert("RGB")

        return img


    def draw_points_on_image(self, overlay_draw, schaden_data, img):
        # Check if "Points" exists
        if "Points" in schaden_data:
            points = schaden_data["Points"]
            pos_points = points.get("1", [])
            neg_points = points.get("0", [])
        else:
            pos_points = None
            neg_points = None

        # Draw positive points (green circles)
        if pos_points:
            for point in pos_points:
                x, y = point
                radius = 5
                overlay_draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=(0, 255, 0, 255))

        # Draw negative points (red circles)
        if neg_points:
            for point in neg_points:
                x, y = point
                radius = 5
                overlay_draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=(255, 0, 0, 255))

        # Draw yellow border if this is the first labeled image (selection order 0)
        if "Selection Order" in schaden_data and schaden_data["Selection Order"] == 0:
            border_thickness = 3
            img_width, img_height = img.size
            overlay_draw.rectangle(
                [(border_thickness // 2, border_thickness // 2),
                 (img_width - border_thickness // 2, img_height - border_thickness // 2)],
                outline=(255, 255, 0, 255),  # Yellow color
                width=border_thickness
            )

    def slider_update(self, current_index):
        """Update image display when the slider is moved."""
        self.show_selected_images(int(float(current_index)))

    def prev_images(self):
        """Go to the previous set of images."""
        grid_size = int(self.grid_entry.get())
        current_index = self.image_slider.get()
        new_index = int(max(0, current_index - grid_size))
        self.show_selected_images(new_index)
        self.image_slider.set(new_index)  # Update slider

    def next_images(self):
        """Go to the next set of images."""
        grid_size = int(self.grid_entry.get())
        images_per_grid = grid_size * grid_size
        current_index = self.image_slider.get()
        max_value = len(self.frame_info.get_frame_name_list()) - images_per_grid
        new_index = int(min(max_value, current_index + grid_size))
        self.show_selected_images(new_index)
        self.image_slider.set(new_index)  # Update slider

    def mark_up_image(self, event):
        """Handle right click events on the canvas."""
        x, y = event.x, event.y
        cell_width, cell_height, grid_size = self.get_canvas_info()
        row = int(y // cell_height)
        col = int(x // cell_width)
        start_index = int(self.image_slider.get())
        # Calculate the index of the clicked image
        img_index = row * grid_size + col + start_index
        print(f"Marked Image index: {img_index}")

        shown_frame_names = self.frame_info.get_frame_name_list()
        frame_name = shown_frame_names[img_index]

        if frame_name in self.marked_frames:
            self.marked_frames.remove(frame_name)
        else:
            self.marked_frames.append(frame_name)

        print(self.marked_frames)
        self.json.add_marked_frames_to_first_index(self.marked_frames)
        self.reload_grid_and_images()