#!/bin/bash
#SBATCH --output=/scratch_net/snapo/mlindner/docs/gaze_data_acquisition/mathis/colmap_log/%j.out
#SBATCH --gres=gpu:1 
#SBATCH --mem=32G

#first argument should be the recording folder
recordingfolder=$1

WS_PATH=$recordingfolder/colmap_ws

echo $WS_PATH

colmap automatic_reconstructor \
    --workspace_path $WS_PATH/automatic_recontructor_out \
    --image_path $WS_PATH/all_images 