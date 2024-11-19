from sam2.build_sam import build_sam2_video_predictor # type: ignore
import torch
import time
import os

results_dir = r"C:\Users\K3000\Desktop\Label Data\results"

predictor = build_sam2_video_predictor(r"C:\Users\K3000\sam2\sam2\configs\sam2.1\sam2.1_hiera_l.yaml", r"C:\Users\K3000\sam2\checkpoints\sam2.1_hiera_large.pt")


for folder_name in os.listdir(results_dir):
    result_path = os.path.join(results_dir, folder_name) 
    frame_dir = os.path.join(result_path,"source images")

    torch.autocast(device_type="cuda", dtype=torch.bfloat16).__enter__()

    if torch.cuda.get_device_properties(0).major >= 8:
        torch.backends.cuda.matmul.allow_tf32 = True
        torch.backends.cudnn.allow_tf32 = True

    print("Loading Inference state:")
    inference_state = predictor.init_state(video_path=frame_dir)
    print("Wait 2 seconds..")
    time.sleep(2)
    # Reset state
    print("Start Cleanup:")
    predictor.reset_state(inference_state)
    del inference_state
    torch.cuda.empty_cache()
    print("Wait 1 second")
    time.sleep(1)