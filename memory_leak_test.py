from sam2.build_sam import build_sam2_video_predictor # type: ignore
import torch

frame_dir = r"C:\Code Python\SAM2-Interactive-Object-Labeling-Project\labeling_project\test folder\source images"

while True:
    torch.autocast(device_type="cuda", dtype=torch.bfloat16).__enter__()

    if torch.cuda.get_device_properties(0).major >= 8:
        torch.backends.cuda.matmul.allow_tf32 = True
        torch.backends.cudnn.allow_tf32 = True

    predictor = build_sam2_video_predictor(r"C:\Users\K3000\sam2\sam2\configs\sam2.1\sam2.1_hiera_l.yaml", r"C:\Users\K3000\sam2\checkpoints\sam2.1_hiera_large.pt")
    inference_state = predictor.init_state(video_path=frame_dir)


    # Reset state
    print("Cleanup:")
    predictor.reset_state(inference_state)

    del predictor
    del inference_state

    torch.cuda.empty_cache()