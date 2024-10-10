import torch
from sam2.build_sam import build_sam2_video_predictor # type: ignore
import numpy as np

class Sam:
    def __init__(self, frame_dir):
        # Initialize the predictor as needed
        sam2_checkpoint = r"C:\Users\K3000\sam2\checkpoints\sam2.1_hiera_large.pt"
        model_cfg = "configs/sam2.1/sam2.1_hiera_l.yaml"

        torch.autocast(device_type="cuda", dtype=torch.bfloat16).__enter__()

        if torch.cuda.get_device_properties(0).major >= 8:
            torch.backends.cuda.matmul.allow_tf32 = True
            torch.backends.cudnn.allow_tf32 = True

        self.predictor = build_sam2_video_predictor(model_cfg, sam2_checkpoint)
        self.inference_state = self.predictor.init_state(video_path=frame_dir)
        self.reset_predictor_state()


    def reset_predictor_state(self):
        self.predictor.reset_state(self.inference_state)


    def add_point_return_mask(self, points, labels, frame_number, ann_obj_id):

        points_np = np.array(points, dtype=np.float32)
        labels_np = np.array(labels, dtype=np.float32)
        
        _, out_obj_ids, out_mask_logits = self.predictor.add_new_points_or_box(
            inference_state=self.inference_state,
            frame_idx=frame_number,
            obj_id=ann_obj_id,
            points=points_np,
            labels=labels_np,
        )

        mask = (out_mask_logits[0] > 0.0).cpu().numpy()
        obj_id = out_obj_ids[0]
        return mask, obj_id


    def propagate_in_video(self):
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