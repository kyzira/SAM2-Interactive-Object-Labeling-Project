import torch
from sam2.build_sam import build_sam2_video_predictor # type: ignore
import numpy as np

class Sam:
    def __init__(self, frame_dir):
        # Initialize the predictor as needed
        sam2_checkpoint = r"C:\Users\K3000\sam2\checkpoints\sam2.1_hiera_large.pt"
        model_cfg = "configs/sam2.1/sam2.1_hiera_l.yaml"

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
                    - "Index":
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

    def propagate_in_video(self):
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