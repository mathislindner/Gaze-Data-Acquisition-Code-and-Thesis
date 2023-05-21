#!/bin/bash
#SBATCH --output=/scratch_net/snapo/mlindner/docs/gaze_data_acquisition/colmap_log/%j.out
#SBATCH --gres=gpu:1 
#SBATCH --mem=32G

#first argument should be the recording folder
AR_WS_PATH=$1

echo "running Automatic Reconstructor on $AR_WS_PATH"

mkdir $AR_WS_PATH/automatic_recontructor_out

set -e
colmap automatic_reconstructor \
    --workspace_path $AR_WS_PATH/automatic_recontructor_out \
    --image_path $AR_WS_PATH/all_images 

touch $AR_WS_PATH/automatic_reconstruction_done.txt