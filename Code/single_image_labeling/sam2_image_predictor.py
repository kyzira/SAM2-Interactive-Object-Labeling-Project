from sam2.build_sam import build_sam2                       # type: ignore
from sam2.sam2_image_predictor import SAM2ImagePredictor    # type: ignore
import torch
from PIL import Image
import numpy as np



class Sam2ImagePredictor:
    def __init__(self, model_cfg_path: str, sam2_checkpoint_path: str):

        # select the device for computation
        if torch.cuda.is_available():
            device = torch.device("cuda")
        elif torch.backends.mps.is_available():
            device = torch.device("mps")
        else:
            device = torch.device("cpu")
        print(f"using device: {device}")

        if device.type == "cuda":
            # use bfloat16 for the entire notebook
            torch.autocast("cuda", dtype=torch.bfloat16).__enter__()
            # turn on tfloat32 for Ampere GPUs (https://pytorch.org/docs/stable/notes/cuda.html#tensorfloat-32-tf32-on-ampere-devices)
            if torch.cuda.get_device_properties(0).major >= 8:
                torch.backends.cuda.matmul.allow_tf32 = True
                torch.backends.cudnn.allow_tf32 = True

        self.sam2_checkpoint = sam2_checkpoint_path
        self.model_cfg = model_cfg_path
        sam2_model = build_sam2(self.model_cfg, self.sam2_checkpoint, device=device)
        self.predictor = SAM2ImagePredictor(sam2_model)

    def load_image(self, image_info):
        image_path = image_info.image_path
        image = Image.open(image_path)
        image = np.array(image.convert("RGB"))
        self.predictor.set_image(image)


    def add_points(self, image_info, multimask_output=True):
        if not image_info:
            print("Error: Image Info not set")
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

        masks, scores, logits = self.predictor.predict(
        point_coords=points_np,
        point_labels=labels_np,
        multimask_output=multimask_output,
        )

        sorted_ind = np.argsort(scores)[::-1]
        masks = masks[sorted_ind]
        scores = scores[sorted_ind]
        logits = logits[sorted_ind]

        masks.shape  # (number_of_masks) x H x W
        return masks, scores