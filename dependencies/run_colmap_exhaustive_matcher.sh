#!/bin/bash
#SBATCH --output=/scratch_net/snapo/mlindner/docs/gaze_data_acquisition/colmap_log/%j.out
#SBATCH --gres=gpu:1 
#SBATCH --mem=32G

#first argument should be the ws path
EM_WS_PATH=$1
#move the images to a temporary folder on scratch_net
#run colmap on the cluster
#when the job is finished move the results back to the recording folder
#move the results back to the recording folder

echo "running Exhaustive Matcher on $EM_WS_PATH"

COLMAP_OUT_PATH=$EM_WS_PATH/exhaustive_matcher_out
IMAGES_PATH=$EM_WS_PATH/all_images
DATABASE_PATH=$EM_WS_PATH/database.db

colmap feature_extractor \
   --database_path $DATABASE_PATH \
   --image_path $IMAGES_PATH \
   --image_list_path $EM_WS_PATH/world_images.txt \
   --ImageReader.single_camera_per_image false \
   --ImageReader.single_camera_per_folder true \
   --ImageReader.camera_model PINHOLE \
   --ImageReader.camera_params "766.9718099563071, 766.4976087911597, 553.5783632028212, 543.5611312035519"

#--ImageReader.camera_params "766.9718099563071, 766.4976087911597, 553.5783632028212, 543.5611312035519 -0.12655976442606495, 0.10005168479218503, 0.018027947115818958, 0.20383603573095524, 0.009269605268511599, 0.06444225697498311"
#--ImageReader.camera_params "766.9718099563071, 766.4976087911597, 553.5783632028212, 543.5611312035519 -0.12655976442606495, 0.10005168479218503, 0.000304737963431893, 0.000547257749681634, 0.018027947115818958, 0.20383603573095524, 0.009269605268511599, 0.06444225697498311"

colmap exhaustive_matcher \
   --database_path $DATABASE_PATH

mkdir $COLMAP_OUT_PATH
mkdir $COLMAP_OUT_PATH/only_world
mkdir $COLMAP_OUT_PATH/only_world/sparse

colmap mapper \
    --database_path $DATABASE_PATH \
    --image_path $IMAGES_PATH \
    --output_path $COLMAP_OUT_PATH/only_world/sparse \
    --image_list_path $EM_WS_PATH/world_images.txt 
#################################################################################################
colmap feature_extractor \
   --database_path $DATABASE_PATH \
   --image_path $IMAGES_PATH \
   --image_list_path $EM_WS_PATH/depth_images.txt \
   --ImageReader.single_camera_per_image false \
   --ImageReader.single_camera_per_folder true \
   --ImageReader.camera_model PINHOLE \
   --ImageReader.camera_params "766.9718099563071, 766.4976087911597, 553.5783632028212, 543.5611312035519"\
   --ImageReader.camera_params "616.2463989257812, 616.6265258789062, 312.24853515625, 250.3607940673828"\
   #--ImageReader.camera_model SIMPLE_RADIAL \
   #--ImageReader.camera_params "615.901118, 320, 240, 0.042837"

colmap exhaustive_matcher \
   --database_path $DATABASE_PATH

mkdir $COLMAP_OUT_PATH/world_and_depth
mkdir $COLMAP_OUT_PATH/world_and_depth/sparse

colmap mapper \
    --database_path $DATABASE_PATH \
    --input_path $COLMAP_OUT_PATH/only_world/sparse/0 \
    --image_path $IMAGES_PATH \
    --output_path $COLMAP_OUT_PATH/world_and_depth/sparse \
    --image_list_path $EM_WS_PATH/depth_images.txt \
    --Mapper.ba_refine_extra_params 0 \
    --Mapper.ba_refine_focal_length 0 \

set -e

colmap bundle_adjuster \
    --input_path $COLMAP_OUT_PATH/world_and_depth/sparse \
    --output_path $COLMAP_OUT_PATH/world_and_depth/sparse \
    --BundleAdjustment.refine_extra_params 0 \
    --BundleAdjustment.refine_focal_length 0  \
    --BundleAdjustment.refine_extrinsics 0 

#create text file that says that the exhaustive matching is done
touch $EM_WS_PATH/exhaustive_matching_done.txt

##################################################################################################




#--Mapper.ba_refine_extra_params 0 \
#--Mapper.ba_refine_focal_length 0



#mkdir $WS_PATH/colmap_out/dense
#colmap image_undistorter \
#    --image_path $DATASET_PATH/images \
#    --input_path $WS_PATH/colmap_out/sparse/0 \
#    --output_path $WS_PATH/colmap_out/dense \
#    --output_type COLMAP
#
#colmap patch_match_stereo \
#    --workspace_path $WS_PATH/colmap_out/dense \
#    --workspace_format COLMAP \
#    --PatchMatchStereo.geom_consistency true
#
#colmap stereo_fusion \
#    --workspace_path $WS_PATH/colmap_out/dense \
#    --workspace_format COLMAP \
#    --input_type geometric \
#    --output_path $WS_PATH/colmap_out/dense/fused.ply
#
#colmap poisson_mesher \
#    --input_path $WS_PATH/colmap_out/dense/fused.ply \
#    --output_path $WS_PATH/colmap_out/dense/meshed-poisson.ply