from constants import *
import numpy as np
import pandas as pd
import open3d as o3d
from colmap_testing.colmap_helpers import read_write_model
import os

recording_id = "ff0acdab-123d-41d8-bfd6-b641f99fc8eb"
recording_path = os.path.join(recordings_folder, recording_id)

meshed_depth_camera_path = os.path.join(recording_path,"meshed_depth_camera.ply")
pointcloud_colmap_path =os.path.join(recording_path, "colmap_ws/automatic_recontructor/dense/0/fused.ply")

cameras, images, points_3d = read_write_model.read_model(os.path.join(recording_path, "colmap_ws/colmap_out_1/sparse"), ".bin")
#read numpy depth_array.npz
depth_camera_distances = np.load(os.path.join(recording_path, "depth_array.npz"))
file_name = depth_camera_distances.files[0]
depth_camera_distances = depth_camera_distances[file_name][90] #depth_camera_distances[file_name][90] is the depth array of the 90th frame
##############################################################################################################

#for every colmap point find the corresponding point in the meshed depth camera
for key in images:
    if images[key].camera_id == 2:
        depth_image_key = key
        break
#depth_camera f, cx, cy, k1, k2
depth_camera = cameras[2]
depth_camera_intrinsics = cameras[2].params
depth_image_qvec = images[depth_image_key].qvec
depth_image_tvec = images[depth_image_key].tvec
distortion_coefficients = np.array([depth_camera_intrinsics[3], depth_camera_intrinsics[3]])

##############################################################################################################
#get indices that are not -1 in images[depth_image_key].point3D_ids
indices_of_nonzero = [i for i in range (len(images[depth_image_key].point3D_ids)) if images[depth_image_key].point3D_ids[i] != -1]

pixel_location_of_visible_points_by_depth_camera  = images[depth_image_key].xys[indices_of_nonzero]
#round pixel locations
pixel_location_of_visible_points_by_depth_camera = np.round(pixel_location_of_visible_points_by_depth_camera).astype(int)

#get point ids of visible points
point_ids = images[depth_image_key].point3D_ids[indices_of_nonzero]
visible_3Dpoints_by_depth_camera = []
for i in range(len(indices_of_nonzero)):
    visible_3Dpoints_by_depth_camera.append(points_3d[point_ids[i]].xyz)
visible_3Dpoints_by_depth_camera = np.array(visible_3Dpoints_by_depth_camera)
#calculate the distance between the camera and
distances_to_visible_points_by_depth_camera = np.linalg.norm(visible_3Dpoints_by_depth_camera - depth_image_tvec, axis=1)

##############################################################################################################
#find the corresponding depths from the depth array using the pixel_location_of_visible_points_by_depth_camera
depths_of_visible_points_by_depth_camera = np.zeros_like(distances_to_visible_points_by_depth_camera)
for i in range(len(pixel_location_of_visible_points_by_depth_camera)):
    x,y = pixel_location_of_visible_points_by_depth_camera[i]
    depths_of_visible_points_by_depth_camera[i] = depth_camera_distances[y][x]
##############################################################################################################
#if the depth is 0, then discard the point from both the visible points and the distances
indices_of_nonzero_depths = [i for i in range(len(depths_of_visible_points_by_depth_camera)) if depths_of_visible_points_by_depth_camera[i] != 0]
distances_to_visible_points_by_depth_camera = distances_to_visible_points_by_depth_camera[indices_of_nonzero_depths]
depths_of_visible_points_by_depth_camera = depths_of_visible_points_by_depth_camera[indices_of_nonzero_depths]

#convert to numpy array
visible_3Dpoints_by_depth_camera = np.array(visible_3Dpoints_by_depth_camera)
distances_to_visible_points_by_depth_camera = np.array(distances_to_visible_points_by_depth_camera)
depths_of_visible_points_by_depth_camera = np.array(depths_of_visible_points_by_depth_camera)
#calculate scale
scale = np.mean(distances_to_visible_points_by_depth_camera/depths_of_visible_points_by_depth_camera)
print(scale)
#apply scale to all points in colmap pointcloud

#meshed_depth_camera = o3d.io.read_triangle_mesh(meshed_depth_camera_path)
#pointcloud_colmap = o3d.io.read_point_cloud(pointcloud_colmap_path)


