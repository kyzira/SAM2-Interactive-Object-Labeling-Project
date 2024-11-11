from PIL import Image, ImageDraw, ImageTk

class OverlayLibrary:
    def __init__(self):
        self.colors = [
            (255, 0, 0, 100),   # Red with transparency
            (0, 0, 255, 100),   # Blue with transparency
            (0, 255, 0, 100),   # Green with transparency
            (255, 255, 0, 100), # Yellow with transparency
            (255, 0, 255, 100)  # Magenta with transparency
        ]

    def draw_border(self, img, color=(255, 0, 0, 100), side="all", thickness=5):
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        img_width, img_height = img.size

        if side == "all":
            # Draw a border around the image
            overlay_draw.rectangle([(0, 0), (img_width, thickness)], fill=color)
            overlay_draw.rectangle([(0, 0), (thickness, img_height)], fill=color)
            overlay_draw.rectangle([(img_width - thickness, 0), (img_width, img_height)], fill=color)
            overlay_draw.rectangle([(0, img_height - thickness), (img_width, img_height)], fill=color)
        
        elif side == "top":
            # Draw a border on the top side the image
            overlay_draw.rectangle([(0, 0), (img_width, thickness)], fill=color)

        elif side == "bottom":
            # Draw a border on the bottom side the image
            overlay_draw.rectangle([(0, img_height - thickness), (img_width, img_height)], fill=color)

        elif side == "left":
            # Draw a border on the left side the image
            overlay_draw.rectangle([(0, 0), (thickness, img_height)], fill=color)

        elif side == "right":
            # Draw a border on the right side the image
            overlay_draw.rectangle([(img_width - thickness, 0), (img_width, img_height)], fill=color)
    
        return overlay

    def draw_polygons(self, img, polygons, color):
        for polygon in polygons:
            polygon_tuples = [tuple(point) for point in polygon]
            if len(polygon_tuples) > 3:
                overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
                overlay_draw = ImageDraw.Draw(overlay, "RGBA")
                overlay_draw.polygon(polygon, outline=color[:3], fill=color)
        return overlay

    def draw_points(self, img, points, color, radius=5):
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        for point in points:
            x, y = point
            overlay_draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=color)
        return overlay


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
        self.initialized = True
        self.image_layers = {}
        self.overlay_library = OverlayLibrary()  # Create an instance of OverlayLibrary

    def load_json(self):
        observation_list = self.observations.get_observation_list()

        for value in self.json.values():
            frame_name = value.get("File Name")
            img = self.image_layers.get(frame_name)
            if not frame_name:
                continue
            if not img:
                continue

            for observation in value["Observations"].keys():
                polygons = value[observation].get("Mask Polygon")
                points = value[observation].get("Points")
                sel_order = value[observation].get("Selection Order")

                if polygons:
                    observation_index = observation_list.index(observation)
                    color = self.overlay_library.colors[observation_index % len(self.overlay_library.colors)]
                    overlay = self.overlay_library.draw_polygons(img, polygons, color)
                    self.image_layers["Mask"][observation] = overlay
                
                if points:
                    pos_points = points.get("1")
                    neg_points = points.get("0")

                    if pos_points:
                        overlay_pos = self.overlay_library.draw_points(img, pos_points, (0, 255, 0, 255))
                    
                    if neg_points:
                        overlay_neg = self.overlay_library.draw_points(img, neg_points, (255, 0, 0, 255))
                    
                    overlay = Image.alpha_composite(overlay_pos, overlay_neg)
                    self.image_layers["Overlay"][observation] = overlay







    def create_base_layer(self):
        frames = self.frame_info.get_frames()
        frame_names = self.frame_info.get_frame_name_list()

        for frame, frame_name in zip(frames, frame_names):
            self.image_layers[frame_name] = {"Base" : frame,
                                             "Mask" : {},
                                             "Overlay": {},
                                             "Combined" : frame}
            
    def add_mask_layers(self, frame_name, observation, mask):
        self.image_layers[frame_name]["Mask"][observation] = mask

    def add_overlay_layers(self, frame_name, observation, overlay_type, overlay):
        self.image_layers[frame_name]["Overlay"][observation][overlay_type] = overlay   

    def delete_layer(self, frame_name, layer_type, layer):

    def combine_layers(self):
        for frame_name in self.image_layers.keys():
            base_img = self.image_layers[frame_name]["Base"].copy()

            # Add masks
            for mask in self.image_layers[frame_name]['Mask'].values():
                base_img = Image.alpha_composite(base_img.convert("RGBA"), mask)

            # Add overlays
            for overlay in self.image_layers[frame_name]['Overlay'].values():
                base_img = Image.alpha_composite(base_img.convert("RGBA"), overlay)

            self.image_layers[frame_name]["Combined"] = base_img

    def show_selected_images(self, start_index=None):
        if not self.initialized:
            return

        if start_index is None:
            start_index = self.image_slider.get()

        self.image_refs = []
        image_list = self.frame_info.get_frames()
        image_names = self.frame_info.get_frame_name_list()

        self.canvas.delete("all")
        cell_width, cell_height, grid_size = self.get_canvas_info()

        for i in range(grid_size * grid_size):
            index = int(start_index + i)

            if index >= len(image_list):
                break

            img_name = image_names[index]
            img = self.image_layers[img_name]["Combined"]

            if cell_width > 0 and cell_height > 0:
                img = img.resize((int(cell_width), int(cell_height)), Image.Resampling.LANCZOS)
            else:
                print("Error: Canvas dimensions or grid size are invalid.")
                return
            tk_img = ImageTk.PhotoImage(img)

            self.image_refs.append(tk_img)
            row = i // grid_size
            col = i % grid_size
            x_position = col * cell_width
            y_position = row * cell_height
            self.canvas.create_image(x_position + cell_width // 2, y_position + cell_height // 2, image=tk_img)


    def draw_points_on_image(self, overlay_draw, schaden_data, img):

    def draw_tracking_splits(self, tracking_splits, img, frame):

    def draw_mask_on_image(self, img, frame):

    def reload_grid_and_images(self):
        grid_size = int(self.grid_entry.get())

        if grid_size < 1:
            print(f"Error: Gridsize invalid: {grid_size}")
            return

        images_per_grid = grid_size * grid_size
        slider_max = max(0, len(self.frame_info.get_frame_name_list()) - images_per_grid)
        self.image_slider.config(from_=0, to=slider_max)

        self.show_selected_images()

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


    def get_canvas_info(self):
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

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

    def get_clicked_image_index(self, x, y):
        cell_width, cell_height, grid_size = self.get_canvas_info()
        row = int(y // cell_height)
        col = int(x // cell_width)
        start_index = int(self.image_slider.get())
        # Calculate the index of the clicked image
        return row * grid_size + col + start_index

    def mark_up_image(self, event):
        """Handle right click events on the canvas."""
        img_index = self.get_clicked_image_index(event.x, event.y)
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


    def delete_label(self, event):
        """Handle right click events on the canvas."""
        img_index = self.get_clicked_image_index(event.x, event.y)

        image_names = self.frame_info.get_frame_name_list()
        img_num = int(image_names[img_index].split(".")[0])   
        kuerzel = self.radio_var.get()

        self.json.remove_damages_from_json([kuerzel],frame_key=img_num)
        print(f"Deleted Label for Image index: {img_index}")
        self.reload_grid_and_images()