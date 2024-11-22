import torch
from sam2.build_sam import build_sam2_video_predictor # type: ignore
import numpy as np
import gc

class Sam2Class:
    """
    This Class manages the interaction with SAM2.
    Here the given parameters will be formattet correctly and when propagating through the video, will set up SAM according to the intervall it currently tracks.
    """
    # Better pass 2 separate paths instead of "sam_paths" to avoid them being switched: "checkpoint_filepath" and "model_filepath".
    # To differ between paths containing a directory or a file location, use "path" or "filepath"
    def __init__(self, sam_paths):
        # Check whether the files at the passed file paths exist

        # Initialize the predictor as needed
        if not sam_paths:
            # Do not hardcode the filepaths in this class, if you want to do that do it somewhere outside, because it is very unexpected from outside that this happens
            sam2_checkpoint = r"C:\Users\K3000\sam2\checkpoints\sam2.1_hiera_tiny.pt"
            model_cfg = "configs/sam2.1/sam2.1_hiera_t.yaml"
        else:
            sam2_checkpoint = sam_paths["sam2_checkpoint"]
            model_cfg = sam_paths["model_cfg"]

        self.frame_dir = None
        torch.autocast(device_type="cuda", dtype=torch.bfloat16).__enter__()
        self.initialized = False

        if torch.cuda.get_device_properties(0).major >= 8:
            torch.backends.cuda.matmul.allow_tf32 = True
            torch.backends.cudnn.allow_tf32 = True

        self.predictor = build_sam2_video_predictor(model_cfg, sam2_checkpoint)

        # Better make a private functions all call them in here:
        # def __setup_torch():
        #     torch.autocast(device_type="cuda", dtype=torch.bfloat16).__enter__()
        #     if torch.cuda.get_device_properties(0).major >= 8:
        #         torch.backends.cuda.matmul.allow_tf32 = True
        #         torch.backends.cudnn.allow_tf32 = True
        
        # def __load_model(checkpoint_filepath: str, model_filepath: str) -> bool:
        #     # check if both paths are not empty and exist, else print error and return False
        #     self.predictor = build_sam2_video_predictor(checkpoint_filepath, model_filepath)
        #     return True

    # Maybe you should just call the function "load", because the user must not know about what exactly happens with them inside this class
    # This makes it simpler from outside.
    # Also rename "frame_dir" to "frame_path"
    def init_predictor_state(self, frame_dir=None):
        """
            Initialize SAM2:
                Load the images from the given directory and set inference state to its starting values.
            Needed:
                - When initializing SAM2
                - When changing the frame_dir, or the images in it.
        """
        try:
            # Better:
            # if not frame_path:
            #    print(f"Cannot load images because frame path does not exist: {frame_path}")
            #    return False
            # 
            # self.frame_path = frame_path
            # etc.
            if frame_dir:
                self.frame_dir = frame_dir
                
            print("SAM initialized")
            self.inference_state = self.predictor.init_state(video_path=self.frame_dir)
            self.initialized = True
        except Exception as e:
            print(f"Error: Initializing failed: {e}")

    # This function is only used inside this class, so make it private
    def reset_predictor_state(self):
        """
            Resets the predictors state:
                After Tracking has started, it is not possible to add new or other Objects to SAM.
                So the predictor must be reset to either add or remove Objects.
        """
        self.predictor.reset_state(self.inference_state)

    # Just pass the points, labels and frame_index separate, this is of no benefit.
    # Since points, labels and frame_index all belong together, it even would be better to make an extra 
    # dataclass containing those values. Dict is very useful to make a quick "class", but the problem is that
    # you only know its structure if you search for the place where it is defined or you debug through the code.
    # You can define the following data class in this file, import it in the class that calls this function, fill
    # it there and pass the data class as parameter to this function:
    # from dataclasses import dataclass
    # @dataclass
    # class SamPoint:
    #     x: flat
    #     y: float
    #     frame_index: int
    #     object_class_id: int
    #     label: str
    #
    # Outside of class:
    # point_1 = SamPoint(0.3, 0.5, 2, 0, "Crack")
    # sam_model.add_points([point_1])
    # 
    # def add_points(points: list[SamPoint]) -> bool:

    # Also: Why is it called "add_point" but you pass multiple points? Better call it add_points
    def add_point(self, points_labels_and_frame_index: dict, object_class_id: int):
        """
            Adds points to a specific frame for a specific object class to SAM2.
            The points describe SAM where the Object is, and where it isnt. 
            Depending on these added points the tracking is done.

            points_labels_and_frame_index -> a dict with the keys:  Points = [[x1, y1], ...], Labels = [int, int, ...], Image Index = int
        """

        if not points_labels_and_frame_index:
            print("Error: points, labels or frame index not set")
            return

        if not self.initialized:
            print("Error: Sam not initialized correctly")
            return
        
        points = points_labels_and_frame_index.get("Points")
        labels = points_labels_and_frame_index.get("Labels")
        frame_index = points_labels_and_frame_index.get("Image Index")

        if points is None or labels is None or frame_index is None:
            print(f"Error: Points {points}, labels {labels} or frame index {frame_index} is None!")
            return

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

        # What does it mean if they are not the same? Is it a good idea to still return the mask in this case?
        if obj_id != object_class_id:
            print("Error: Class object IDs are not the same!")
        
        return mask

    # If it's deprecated why is it still used?
    # A better function name would be "track_objects"
    def propagate_in_video(self) -> dict:
        "Deprecated Function, used to track through whole video"

        # Why don't you call self.reset_predictor_state() in this function?
        # What if propagate_through_interval was already called before this function was called? 

        # If SAM is not initialized, does it really make sense to continue this function?
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
    
    # 1. Rename "start" and "end" to "start_frame_index"/"end_frame_index".
    # 2. Also better call it something like "track_objects", the parameters "start_frame_index"/"end_frame_index" should be self explaining.
    # 3. Since "button_states" thematically has nothing to do with tracking the object, find a way to only pass the actual
    # thematically relevant info or set it in another function
    # 4. This function is pretty long, it probably makes sense to break it down into multiple private methods processing intermediate steps
    def propagate_through_interval(self, frames, button_states, start: int, end: int) -> dict:
        if not self.initialized:
            print("Error: SAM not Initialized!")
            return
        
        # Reset SAM and add points from the middle frame
        self.reset_predictor_state()
        
        print(f"Tracking from Frame {start} to {end}")
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