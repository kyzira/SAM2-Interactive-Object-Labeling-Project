# How to train SAM2 on custom dataset

Here i will show you how to train sam2 on your labeled custom dataset

## 1. Setup your Machine

Training only works on linux machines, so if on windows [please install wsl2 with ubuntu](https://learn.microsoft.com/en-us/windows/wsl/install).

### 1. CUDA installation

Now in the terminal we need cuda first

``` bash
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2404/x86_64/cuda-keyring_1.1-1_all.deb
sudo apt install ./cuda-keyring_1.1-1_all.deb
sudo apt update
sudo apt install cuda-toolkit
```

Set Cuda in the PATH:

```bash
nano /home/$USER/.bashrc
```

Add at the end of the file

``` bash
export CUDA_HOME=/usr/local/cuda
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/cuda/lib64:/usr/local/cuda/extras/CUPTI/lib64
export PATH=$PATH:$CUDA_HOME/bin
```

Then terminal:

``` bash
source .bashrc
```

Now run

``` bash
nvcc --version
```

### 2. Anaconda Installation

now download anaconda from [here](https://www.anaconda.com/download/success) and put it into your user folder in wsl.

then to run the shell just type in the name of the file. For example:

``` bash
Anaconda-latest-Linux-x86_64.sh
```

Scroll to the bottom of the EULA with enter and type yes and hit enter twice to start the installation.
At the end they will ask if you want to use conda as your standard terminal, just type yes and enter.

Restart your terminal

### 3. Pytorch

Now lets install pytorch. Select Stable, Linux, Conda, Python and the latest Cuda version, copy the command at the bottom and run it.

type `y` when ask if you want to proceed.

### 4. SAM2

[Here is its Github Page](https://github.com/facebookresearch/sam2)

To install it and everything it needs, run the following commands:

```bash
git clone https://github.com/facebookresearch/sam2.git && cd sam2
pip install -e .
pip install -e ".[notebooks]"
cd checkpoints
./download_ckpts.sh
cd ..
pip install -e ".[dev]"
```

## 2. Prepare your Dataset

Your Dataset has to be in a specific format. We will use the MOSE Dataset format

### MOSE Dataset format

This format looks like this:

``` text

├── BinaryMasks
│ │ 
│ ├── <video_name_1>
│ │ ├── 00000.png
│ │ ├── 00001.png
│ │ └── ...
│ │ 
│ ├── <video_name_2>
│ │ ├── 00000.png
│ │ ├── 00001.png
│ │ └── ...
│ │ 
│ ├── <video_name_...>
│ 
└── JPEGImages
  │ 
  ├── <video_name_1>
  │ ├── 00000.jpg
  │ ├── 00001.jpg
  │ └── ...
  │ 
  ├── <video_name_2>
  │ ├── 00000.jpg
  │ ├── 00001.jpg
  │ └── ...
  │ 
  └── <video_name_...>
```

The Masks should be binary images with the mask having values of 1.
Make sure, that the folders do not include a video filetype in their names, e.g. ``video1`` instead of ``video1.mpg``

### Convert Dataset

If you have used this tool to label your data, just run the `prepare_mose_format_dataset.py` file. But first put in the directroy of the labeled results and the output directory.

### Put Converted Dataset into your user folder

After converting dont forget to copy your dataset to the ubuntu user folder.

## 3. Prepare train config

If you have your data ready, now we can prepare the yaml file we are going to run.
Open the file under:
`sam2/sam2/configs/sam2.1_training/sam2.1_hiera_b+_MOSE_finetune.yaml`

On the top of the file you can now input the paths to your dataset images and masks.
From my Experience changing frame num and num of epochs return errors i couldnt handle yet, so i would just leave them as is.
Change `gpus per node` to 1 lower at the bottom and also edit the `save_freq` variable to save your checkpoint every x epochs.

## 4. Run Training

### Run Training

Finally you can run the training with:
Make sure to be in the sam2 root directory

```bash
python training/train.py \
    -c configs/sam2.1_training/sam2.1_hiera_b+_MOSE_finetune.yaml \
    --use-cluster 0 \
    --num-gpus 1
```

### Tensorboard

You can watch live statistics if you open an other terminal and then run:

```bash
tensorboard --logdir sam2/sam2_logs/configs/sam2.1_training/sam2.1_hiera_b+_MOSE_finetune.yaml/tensorboard
```

Now you can ctrl + leftclick the ip adress which pops up and you can see live graphs of the stats.

## 5. Use your Checkpoint

When completed, you can use your new checkpoint, instead of the one from meta. it will be saved under
  ``sam2/sam2_logs/configs/sam2.1_training/sam2.1_hiera_b+_MOSE_finetune.yaml/checkpoints``.

As the model config you have to use `sam2\sam2\configs\sam2.1\sam2.1_hiera_b+.yaml`
