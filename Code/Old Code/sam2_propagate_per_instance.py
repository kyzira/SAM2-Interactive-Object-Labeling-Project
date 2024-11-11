from sam2_class import Sam
import shutil
import os
import tempfile


class SamInstanceSegmentation:
    def __init__(self, sam_model: Sam, frame_dir = None, frame_name_list = None, json_data = {}, observation = None):
        self.sam_model = sam_model
        self.frame_dir = frame_dir
        self.frame_name_list = frame_name_list
        self.json_data = json_data
        self.frame_range = []
        self.polygons = {}
        self.observation = observation
        self.tracking_splits_list = []

        info = json_data.get("Info")
        if info:
            dict = info.get("Tracking Splits")
            if dict:
                list = dict.get(observation)
                if dict:
                    self.tracking_splits_list = list

    def start_process_for_all_instances(self):
        first_name = None
        last_name = None

        if self.tracking_splits_list is None:
            print("Error: Instance list is not given!")
            return

        # If tracking_splits_list is empty, use the first and last frame names directly
        if not self.tracking_splits_list:
            first_name = self.frame_name_list[0]
            last_name = self.frame_name_list[-1]
            temp_dir = tempfile.mkdtemp()
            self.__copy_frames_to_temp_folder(first_name, last_name, temp_dir)
            self.__reset_sam(temp_dir)
            self.__add_points(first_name, last_name)
            self.__propagate_and_save()
            self.__cleanup(temp_dir)
        else:
            # Iterate over tracking_splits_list, setting first_name and last_name in each iteration
            for counter, entry in enumerate(self.tracking_splits_list):
                first_name = f'{int(entry):05d}.jpg'
                last_name = (
                    self.frame_name_list[-1] if counter == len(self.tracking_splits_list) - 1
                    else f'{self.tracking_splits_list[counter + 1]:05d}.jpg'
                )
                temp_dir = tempfile.mkdtemp()
                self.__copy_frames_to_temp_folder(first_name, last_name, temp_dir)
                self.__reset_sam(temp_dir)
                self.__add_points(first_name, last_name)
                self.__propagate_and_save()
                self.__cleanup(temp_dir)
    

    def get_predictions(self):
        return self.polygons

    def __reset_sam(self, temp_dir):
        self.sam_model.frame_dir = temp_dir
        self.sam_model.init_predictor_state()

    def __add_points(self, first_name, last_name):
        # Get indices for the range
        start_index = self.frame_name_list.index(first_name)
        end_index = self.frame_name_list.index(last_name)
        self.frame_range = self.frame_name_list[start_index:end_index + 1]

        # Iterate over each item in json_data
        for values in self.json_data.values():
            file_name = values.get("File Name", None)
            if file_name not in self.frame_range:
                continue
            observation_info = values["Observations"].get(self.observation, None)
            if observation_info == None:
                continue
            if observation_info.get("Points", None) == None:
                continue
            pos_points = observation_info["Points"].get("1", [])
            neg_points = observation_info["Points"].get("0", [])

            points_list = []
            labels_list = []

            for i in pos_points:
                points_list.append(i)
                labels_list.append(1)
            for i in neg_points:
                points_list.append(i)
                labels_list.append(0)

            points_labels_frame_dict = {
                "Points" : points_list,
                "Labels" : labels_list,
                "Image Index" : self.frame_range.index(file_name)
            }

            self.sam_model.add_point(points_labels_frame_dict, 0)

    def __propagate_and_save(self):
        video_segments = self.sam_model.propagate_in_video()
        for i in range(len(self.frame_range)):
            self.polygons[self.frame_name_list.index(self.frame_range[i])] = video_segments[i]

    def __cleanup(self, temp_dir):
        # Delete the temporary directory and all its contents
        shutil.rmtree(temp_dir)
        print(f"Temporary directory at {temp_dir} deleted.")

    def __copy_frames_to_temp_folder(self, first_name, last_name, temp_dir):
        start_index = self.frame_name_list.index(first_name)
        end_index = self.frame_name_list.index(last_name)

        for i in range(start_index, end_index + 1):
            frame_path = os.path.join(self.frame_dir, self.frame_name_list[i])
            shutil.copy(frame_path, temp_dir)
            print(f"Copied {self.frame_name_list[i]} to {temp_dir}")
