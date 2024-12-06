import torch
from sam2.build_sam import build_sam2_video_predictor # type: ignore
import numpy as np
import gc
from image_info import ImageInfo

class Sam2Class:
    """
    This Class manages the interaction with SAM2.
    Here the given parameters will be formattet correctly and when propagating through the video, will set up SAM according to the intervall it currently tracks.
    """
    def __init__(self, checkpoint_filepath: str, model_filepath: str):
        # Initialize the predictor as needed

        self.frame_dir = None
        torch.autocast(device_type="cuda", dtype=torch.bfloat16).__enter__()
        self.initialized = False

        self.__setup_torch()
        self.initialized = self.__load_model(checkpoint_filepath, model_filepath)

        if not self.initialized:
            raise Exception("Error: Segmentation Model couldnt be loaded!")
        
    def load(self, frame_dir=None):
        """
            Initialize SAM2:
                Load the images from the given directory and set inference state to its starting values.
            Needed:
                - When initializing SAM2
                - When changing the frame_dir, or the images in it.
        """
        if not frame_dir and not self.frame_dir:
            print("Error: No frame directory given!")
            return
        
        elif frame_dir:
            self.frame_dir = frame_dir

        self.inference_state = self.predictor.init_state(video_path=self.frame_dir)
        self.reset_predictor_state()

    def add_points(self, image_info: ImageInfo):
        """
            Adds points to a specific frame for a specific object class to SAM2.
            The points describe SAM where the Object is, and where it is not. 
            Depending on these added points the tracking is done.
        """

        if not image_info:
            print("Error: Image Info not set")
            return

        if not self.initialized:
            print("Error: Sam not initialized correctly")
            return
        
        points, labels, selected_object_id = None, None, None
        for i, damage_info in enumerate(image_info.data_coordinates):
            if damage_info.is_selected == True:
                selected_object_id = i

                points = damage_info.positive_point_coordinates + damage_info.negative_point_coordinates
                labels = [1] * len(damage_info.positive_point_coordinates) + [0] * len(damage_info.negative_point_coordinates)
                break

        frame_index = image_info.image_index

        if points is None or labels is None or frame_index is None:
            print(f"Error: Points {points}, labels {labels} or frame index {frame_index} is None!")
            return

        points_np = np.array(points, dtype=np.float32)
        labels_np = np.array(labels, dtype=np.float32)
        
        _, out_obj_ids, out_mask_logits = self.predictor.add_new_points_or_box(
            inference_state=self.inference_state,
            frame_idx=frame_index,
            obj_id=selected_object_id,
            points=points_np,
            labels=labels_np,
        )

        mask = (out_mask_logits[0] > 0.0).cpu().numpy()
        obj_id = out_obj_ids[0]

        if obj_id != selected_object_id:
            print("Error: Class object IDs are not the same!")

        return mask
    
    def track_objects(self, frame_infos: list, start_frame_index: int, end_frame_index: int) -> dict:
        """
        This goes through the list of all frames from start_frame_index to end_frame_index,
        and first inputs all Points that were found in that intervall and second starts tracking for the selected object.
        Args:
            frame_infos (list): List of ImageInfo instances
            start_frame_index (int): First frame to consider in tracking
            end_frame_index (int): Last frame to consider in tracking
        Returns:
            dict: keys are frame indices, values are the masks
        """
                
        if not self.initialized:
            print("Error: SAM not Initialized!")
            return
        
        # Reset SAM and add points from the middle frame
        self.reset_predictor_state()
        
        frame_indexes_with_points = self.__get_frame_infos_with_points_from_intervall(frame_infos, start_frame_index, end_frame_index)

        if len(frame_indexes_with_points) < 1:
            return None

        starting_point_index = frame_indexes_with_points[0]

        # Add all points
        for index in frame_indexes_with_points:
            self.add_points(frame_infos[index])

        # Calculate max_frame_num_to_track based on interval limits
        max_frame_num_to_track_forwards = end_frame_index - starting_point_index
        max_frame_num_to_track_backwards = starting_point_index - start_frame_index

        return self.__track(starting_point_index, max_frame_num_to_track_forwards, max_frame_num_to_track_backwards)
    
    
    def reset_predictor_state(self):
        """
            Resets the predictors state:
                After Tracking has started, it is not possible to add new or other Objects to SAM.
                So the predictor must be reset to either add or remove Objects.
        """
        self.predictor.reset_state(self.inference_state)

    def cleanup(self):
        """
        Ensure cleanup is performed when the object is destroyed.
        Clean up GPU resources by deleting the predictor and clearing CUDA cache.
        """
        try:
            # Delete the predictor to release GPU memory
            self.predictor.reset_state(self.inference_state)

            # Clear CUDA cache
            gc.collect()
            torch.cuda.empty_cache()
            print("Resources cleaned up successfully.")
        except Exception as e:
            print(f"Error during cleanup: {e}")

    def __del__(self):
        self.cleanup()

    # Better make a private functions all call them in here:
    def __setup_torch(self):
        torch.autocast(device_type="cuda", dtype=torch.bfloat16).__enter__()
        if torch.cuda.get_device_properties(0).major >= 8:
            torch.backends.cuda.matmul.allow_tf32 = True
            torch.backends.cudnn.allow_tf32 = True
    
    def __load_model(self, checkpoint_filepath: str, model_filepath: str) -> bool:
        # check if both paths are not empty and exist, else print error and return False
        self.predictor = build_sam2_video_predictor(model_filepath, checkpoint_filepath)
        return True

    def __track(self, starting_point_index: int, max_frame_num_to_track_forwards: int, max_frame_num_to_track_backwards: int) -> dict:
        # Track forward and backward from the middle frame within the interval
        video_segments = dict()
        
        if max_frame_num_to_track_forwards > 0:
            # Forward tracking from the middle frame
            for out_frame_idx, out_obj_ids, out_mask_logits in self.predictor.propagate_in_video(self.inference_state, start_frame_idx=starting_point_index, max_frame_num_to_track=max_frame_num_to_track_forwards):
                video_segments[out_frame_idx] = {
                    out_obj_id: (out_mask_logits[i] > 0.0).cpu().numpy()
                    for i, out_obj_id in enumerate(out_obj_ids)
                }

        if max_frame_num_to_track_backwards > 0:
            # Backward tracking within the interval
            for out_frame_idx, out_obj_ids, out_mask_logits in self.predictor.propagate_in_video(self.inference_state, start_frame_idx=starting_point_index, max_frame_num_to_track=max_frame_num_to_track_backwards, reverse=True):
                if out_frame_idx not in video_segments:
                    video_segments[out_frame_idx] = {}
                for i, out_obj_id in enumerate(out_obj_ids):
                    if out_obj_id not in video_segments[out_frame_idx]:
                        video_segments[out_frame_idx][out_obj_id] = (out_mask_logits[i] > 0.0).cpu().numpy()

        return video_segments

    def __get_frame_infos_with_points_from_intervall(self, frame_infos: list, start_frame_index: int, end_frame_index: int) -> list[int]:
        """
        This goes through the list of all frames and saves the indexes of frames, in which points are saved.
        Args:
            frame_infos (list): List of ImageInfo instances
            start_frame_index (int): First frame to consider in tracking
            end_frame_index (int): Last frame to consider in tracking
        Returns:
            list[int]: List of frame indexes where the selected observation contains points. 
                    Returns an empty list if no such frames are found.
        """
        frames_with_points = []

        selected_observation = None
        i = 0

        while selected_observation == None:
            image_info = frame_infos[i]
            i += 1
            for index, damage_info in enumerate(image_info.data_coordinates):
                if damage_info.is_selected == True:
                    selected_observation = damage_info.damage_name
                    damage_index = index

        try:
            print(f"Object to track: {selected_observation} with index {damage_index}")
        except Exception as e:
            print(f"{e}")
            return

        # Collect frames within the interval and check for points on the selected observation
        for frame_index in range(start_frame_index, end_frame_index +1):
            image_info = frame_infos[frame_index]

            if len(image_info.data_coordinates) < damage_index:
                print(f"Entries in data coordinates: {len(image_info.data_coordinates)}")
                continue

            damage_info = image_info.data_coordinates[damage_index]

            positive_points = damage_info.positive_point_coordinates
            negative_points = damage_info.negative_point_coordinates

            if len(positive_points) > 0 or len(negative_points) > 0:
                frames_with_points.append(frame_index)

        if frames_with_points == []:
            print("No frames with points found in the specified interval.")

        return frames_with_points