#!/bin/bash
#SBATCH --output=/scratch_net/snapo/mlindner/docs/test_cluster/f5b09068-d395-493c-80e6-7eb0cbb6478a/colmap_ws/log/%j.out
#SBATCH --gres=gpu:1
#SBATCH --mem=32G

#first argument should be the recording folder
recordingfolder=$1

WS_PATH=$recordingfolder/colmap_ws
DATASET_PATH=$WS_PATH/dataset

echo $WS_PATH
echo $DATASET_PATH

colmap feature_extractor \
   --database_path $DATASET_PATH/database.db \
   --image_path $DATASET_PATH/images \
   --ImageReader.single_camera_per_folder true \
   --ImageReader.single_camera_per_image false

colmap exhaustive_matcher \
   --database_path $DATASET_PATH/database.db

mkdir $WS_PATH/colmap_out
mkdir $WS_PATH/colmap_out/sparse

colmap mapper \
    --database_path $DATASET_PATH/database.db \
    --image_path $DATASET_PATH/images \
    --output_path $WS_PATH/colmap_out

mkdir $WS_PATH/colmap_out/dense

colmap image_undistorter \
    --image_path $DATASET_PATH/images \
    --input_path $WS_PATH/colmap_out/sparse/0 \
    --output_path $WS_PATH/colmap_out/dense \
    --output_type COLMAP \

$ colmap patch_match_stereo \
    --workspace_path $WS_PATH/colmap_out/dense \
    --workspace_format COLMAP \
    --PatchMatchStereo.geom_consistency true

$ colmap stereo_fusion \
    --workspace_path $WS_PATH/colmap_out/dense \
    --workspace_format COLMAP \
    --input_type geometric \
    --output_path $WS_PATH/colmap_out/dense/fused.ply

$ colmap poisson_mesher \
    --input_path $WS_PATH/colmap_out/dense/fused.ply \
    --output_path $WS_PATH/colmap_out/dense/meshed-poisson.ply

$ colmap delaunay_mesher \
    --input_path $WS_PATH/colmap_out/dense \
    --output_path$WS_PATH/colmap_out/dense/meshed-delaunay.ply