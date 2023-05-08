from colmap_testing.colmap_helpers import read_write_model
import os
import cv2
import numpy as np
from constants import *
import open3d as o3d
import plotly

recording_id = "ff0acdab-123d-41d8-bfd6-b641f99fc8eb"
recording_path = os.path.join(recordings_folder, recording_id)

meshed_depth_camera_path = os.path.join(recording_path,"meshed_depth_camera.ply")
pointcloud_colmap_path =os.path.join(recording_path, "colmap_ws/automatic_recontructor/dense/0/fused.ply")

meshed_depth = o3d.io.read_triangle_mesh(meshed_depth_camera_path)
pointcloud_colmap = o3d.io.read_point_cloud(pointcloud_colmap_path)

#covnert meshed depth_camera to pointcloud
pointcloud_depth_camera = meshed_depth.sample_points_uniformly(number_of_points=250000)

print(pointcloud_depth_camera)
print(pointcloud_colmap)

#only keep one out of 10 points
#meshed_depth = meshed_depth.voxel_down_sample(voxel_size=0.1)
#pointcloud_colmap = pointcloud_colmap.voxel_down_sample(voxel_size=0.1)

#plot pointclouds
#o3d.visualization.draw_plotly([pointcloud_colmap], width=1920, height=1080)
#o3d.visualization.draw_plotly([pointcloud_depth_camera], width=1920, height=1080)

#initial guess of transformation from colmap to meshed depth
#guess: rotation around x axis by 180 degrees and scale of 0.25
transformation_guess = np.array([[0.25, 0., 0., 0.],
                                    [0., -0.25, 0., 0.],
                                    [0., 0., -0.25, 0.],
                                    [0., 0., 0., 1.]])
#apply transformation guess to pointcloud_colmap

criteria = o3d.pipelines.registration.ICPConvergenceCriteria(max_iteration=10000)
threshold = 0.5
registration_result = o3d.pipelines.registration.registration_icp(
    pointcloud_colmap, pointcloud_depth_camera, threshold, transformation_guess,
    o3d.pipelines.registration.TransformationEstimationPointToPoint(with_scaling=True),
    o3d.pipelines.registration.ICPConvergenceCriteria())

transformation = registration_result.transformation
#transform pointcloud_colmap
pointcloud_colmap.transform(transformation)

#plot pointclouds in one plot

#subsample pointclouds for better visualization
pointcloud_colmap = pointcloud_colmap.voxel_down_sample(voxel_size=0.01)
pointcloud_depth_camera = pointcloud_depth_camera.voxel_down_sample(voxel_size=0.01)
#print pointclouds
print("pointclouds after registration")
print(pointcloud_colmap)
print(pointcloud_depth_camera)

o3d.visualization.draw_plotly([pointcloud_colmap, pointcloud_depth_camera], width=1920, height=1080)

