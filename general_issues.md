General issues:

- show video name and reference point (i.e. video time) for better orientation (maybe in title of main window), so you know what kind of data is shown/edited
- remove .pyc files from repo
- each class should have a documentation at the top of its file
- rename file "sam2_class"  and class "Sam2Class", because a variable name should not contain its type (provides no added value)
  => maybe name it "Sam" or "Segmenter"
- Error log in list_mode when the last list element was tracked and you press "Next": Error during cleanup: 'Sam2Class' object has no attribute 'inference_state'
- If a second list element having the same video gets stored to the same JSON but has another damage class, then the masks get assigned to the already existing info, actually another "info" element should be added containing all the meta data of this damage
- Use term "filepath" for a path to a file (i.e. "C:/Goerkem/rules.txt") and "path" else (i.e. "C:/Goerkem/")
- The following Order of functions inside a class is crucial:
  - 1. Magic functions
  - 2. Public functions
  - 3. Private functions

General suggestions:
- Build Sam2Predictor outside Sam class and set it in sam class from outside
  => in the `main.py::list_mode` you can create a new sam class each loop run and pass the predictor each time
  => then the sam class should automatically get deleted and you do not have to explicitely call "del" on it at the end of the loop run
- It would make more sense to store current_index.txt at the same location as the csv file of the table path, because it only makes sense in combination with this file
- Take care of making functions private if they should only be used internally
- Getter functions do not need to contain "get" (does not bring any benefit), so better rename them, i.e. get_damage_table_row() => damage_table_row()
- What do you think about renaming "geometry_data" (i.e. annotation_window_geometry_data) into "window_properties"? In my opinion "geometry" is a bit confusing in the context of the program,
  I first thought this is about the mask polygons. By naming it "window_properties" you directly know the context and understand it refers to the window
- You sometimes call the index of a frame "frame_index" (in annotation_window.py), sometimes "frame" (in frame_extration.py) and sometimes "frame_number" (in image_view.py). Keep things coherent and give the same kind of data the same name, here  "frame_index", i.e. "start_frame_index"
- Function documentation should be enclosed with """ instead of # (i.e. in annotation_window::__create_propagated_image)
- You should always set a type hint for the parameters and return value of a function, so the viewer can directly understand the inputs and outputs of a function, i.e.:  
  ``` python
  def get_image_size(self, img_index: int) -> tuple[int, int]:
  ```
- I personally prefer calling functions from imported modules as the following, so you directly understand where the called function origins from:
  ``` python
  import skimage
  similarity_index = skimage.metrics.structural_similarity(gray_frame1, gray_frame2)
  ```
  instead of
  ``` python
  from skimage.metrics import structural_similarity as ssim
  similarity_index = ssim(gray_frame1, gray_frame2)
  ```
  But I leave that to you, since most code examples do it like you did.


Questions:
- Why are there always pairs of coordinates in "Mask Polygon": [[ [694,63],[694,64] ], [[645,43],[647,43] ], ...