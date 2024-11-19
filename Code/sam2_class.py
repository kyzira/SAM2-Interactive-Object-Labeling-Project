import torch
from sam2.build_sam import build_sam2_video_predictor # type: ignore
import numpy as np
import gc

class Sam2Class:
    def __init__(self, frame_dir, sam_paths):
        # Initialize the predictor as needed
        if not sam_paths:
            sam2_checkpoint = r"C:\Users\K3000\sam2\checkpoints\sam2.1_hiera_tiny.pt"
            model_cfg = "configs/sam2.1/sam2.1_hiera_t.yaml"
        else:
            sam2_checkpoint = sam_paths["sam2_checkpoint"]
            model_cfg = sam_paths["model_cfg"]

        self.frame_dir = frame_dir
        torch.autocast(device_type="cuda", dtype=torch.bfloat16).__enter__()
        self.initialized = False

        if torch.cuda.get_device_properties(0).major >= 8:
            torch.backends.cuda.matmul.allow_tf32 = True
            torch.backends.cudnn.allow_tf32 = True

        self.predictor = build_sam2_video_predictor(model_cfg, sam2_checkpoint)
        self.init_predictor_state()

    def init_predictor_state(self):
        """
            Initialize SAM2:
                Load the images from the given directory and set inference state to its starting values.
            Needed:
                - When initializing SAM2
                - When changing the frame_dir, or the images in it.
        """
        try:
            print("SAM initialized")
            self.inference_state = self.predictor.init_state(video_path=self.frame_dir)
            self.initialized = True
        except Exception as e:
            print(f"Error: Initializing failed: {e}")

    def reset_predictor_state(self):
        """
            Resets the predictors state:
                After Tracking has started, it is not possible to add new or other Objects to SAM.
                So the predictor must be reset to either add or remove Objects.
        """
        self.predictor.reset_state(self.inference_state)

    def add_point(self, points_labels_and_frame_index: dict, object_class_id: int):
        """
            Adds points to a specific frame for a specific object class to SAM2.
            The points describe SAM where the Object is, and where it isnt. 
            Depending on these added points the tracking is done.

            Needed parameters:
                - points_labels_and_sequence_index:
                    This is a dictionairy containing 3 items:
                    - "Punkte": 
                        This is a list containing tuples with the Coordinates of the points.
                        They are in the following format: (x, y), x and y in pixels from the top left of the image.
                    - "Labels": 
                        This is a list containing "0" and "1" depending if the corresponding point in "Punkte" is a
                        "positive" or "negative" point for the selected object class
                    - "Image Index":
                        This is an integer, only to track to which image the other 2 lists belong to

                - object_class_id:
                    This is an integer, only to differentiate objects, when tracking multiple objects at the same time.
                    The Value is an arbitrary number.
        """

        if not points_labels_and_frame_index:
            print("Error: points, labels or frame index not set")
            return

        if not self.initialized:
            print("Error: Sam not initialized correctly")
            return
        
        points = points_labels_and_frame_index["Points"]
        labels = points_labels_and_frame_index["Labels"]
        frame_index = points_labels_and_frame_index["Image Index"]
        
        

        points_np = np.array(points, dtype=np.float32)
        labels_np = np.array(labels, dtype=np.float32)
        
        _, out_obj_ids, out_mask_logits = self.predictor.add_new_points_or_box(
            inference_state=self.inference_state,
            frame_idx=frame_index,
            obj_id=object_class_id,
            points=points_np,
            labels=labels_np,
        )

        mask = (out_mask_logits[0] > 0.0).cpu().numpy()
        obj_id = out_obj_ids[0]

        if obj_id != object_class_id:
            print("Error: Class object IDs are not the same!")
        
        return mask

    def propagate_in_video(self) -> dict:
        if self.initialized == False:
            print("Error: Sam not Initialized!")

        video_segments = dict()

        for out_frame_idx, out_obj_ids, out_mask_logits in self.predictor.propagate_in_video(self.inference_state):
            video_segments[out_frame_idx] = {
                out_obj_id: (out_mask_logits[i] > 0.0).cpu().numpy()
                for i, out_obj_id in enumerate(out_obj_ids)
            }

        for out_frame_idx, out_obj_ids, out_mask_logits in self.predictor.propagate_in_video(self.inference_state, reverse=True):
            if out_frame_idx not in video_segments:
                video_segments[out_frame_idx] = {}
            for i, out_obj_id in enumerate(out_obj_ids):
                if out_obj_id not in video_segments[out_frame_idx]:
                    video_segments[out_frame_idx][out_obj_id] = (out_mask_logits[i] > 0.0).cpu().numpy()
                else:
                    # Optionally merge or update masks if needed
                    video_segments[out_frame_idx][out_obj_id] = np.maximum(
                        video_segments[out_frame_idx][out_obj_id],
                        (out_mask_logits[i] > 0.0).cpu().numpy()
                    )

        return video_segments
    

    def propagate_through_interval(self, frames, button_states, start: int, end: int) -> dict:
        if not self.initialized:
            print("Error: SAM not Initialized!")
            return
        
        # Reset SAM and add points from the middle frame
        self.reset_predictor_state()
        
        print(f"Start Frame Num {start} until {end}")
        object_class_id = 0
        selected_observation = None

        for observation, button in button_states.items():
            if button.get("Selected") == True:
                selected_observation = observation
                break
            else:
                object_class_id += 1

        print(f"Tracking Object {selected_observation}, with id {object_class_id}")

        new_frame_list = []
        frames_with_points = []

        # Collect frames within the interval and check for points on the selected observation
        for frame_index in range(start, end+1):
            img_view = frames[frame_index]

            new_frame_list.append(img_view)
            data = img_view.get_data()

            if not data.get(selected_observation):
                continue

            # Check if there are positive or negative points for this observation
            if "Points" not in data[selected_observation]:
                continue

            pos = data[selected_observation]["Points"].get("1")
            neg = data[selected_observation]["Points"].get("0")

            if pos or neg:
                frames_with_points.append(frame_index)


        if frames_with_points == []:
            print("No frames with points found in the specified interval.")
            return

        first_index = frames_with_points[0]

        # Add all points
        for index in frames_with_points:
            frame_data = frames[index].get_data()[selected_observation]
            points = []
            labels = []

            # Add points for key "1" if it exists
            if "1" in frame_data["Points"]:
                points += frame_data["Points"]["1"]
                labels += [1] * len(frame_data["Points"]["1"])

            # Add points for key "0" if it exists
            if "0" in frame_data["Points"]:
                points += frame_data["Points"]["0"]
                labels += [0] * len(frame_data["Points"]["0"])

            print(f"Adding Points {points} with labels {labels} for index {index}")
            self.add_point(
                {"Points": points, "Labels": labels, "Image Index": index},
                object_class_id=object_class_id
            )

        # Calculate max_frame_num_to_track based on interval limits
        
        max_frame_num_to_track_forwards = end - first_index
        max_frame_num_to_track_backwards = first_index - start

        # Track forward and backward from the middle frame within the interval
        video_segments = dict()
        
        # Forward tracking from the middle frame
        for out_frame_idx, out_obj_ids, out_mask_logits in self.predictor.propagate_in_video(self.inference_state, 
                                                                                             start_frame_idx=first_index, 
                                                                                             max_frame_num_to_track=max_frame_num_to_track_forwards):
            video_segments[out_frame_idx] = {
                out_obj_id: (out_mask_logits[i] > 0.0).cpu().numpy()
                for i, out_obj_id in enumerate(out_obj_ids)
            }

        if first_index != start:
            # Backward tracking within the interval
            for out_frame_idx, out_obj_ids, out_mask_logits in self.predictor.propagate_in_video(self.inference_state, 
                                                                                                 start_frame_idx=first_index, 
                                                                                                 max_frame_num_to_track=max_frame_num_to_track_backwards, 
                                                                                                 reverse=True):
                if out_frame_idx not in video_segments:
                    video_segments[out_frame_idx] = {}
                for i, out_obj_id in enumerate(out_obj_ids):
                    if out_obj_id not in video_segments[out_frame_idx]:
                        video_segments[out_frame_idx][out_obj_id] = (out_mask_logits[i] > 0.0).cpu().numpy()

        return video_segments


    def cleanup(self):
        """
        Clean up GPU resources by deleting the predictor and clearing CUDA cache.
        """
        try:
            # Delete the predictor to release GPU memory
            self.predictor.reset_state(self.inference_state)

            del self.predictor
            del self.inference_state

            # Clear CUDA cache
            gc.collect()
            torch.cuda.empty_cache()
            print("Resources cleaned up successfully.")
        except Exception as e:
            print(f"Error during cleanup: {e}")

    def __del__(self):
        """
        Ensure cleanup is performed when the object is destroyed.
        """
        self.cleanup()