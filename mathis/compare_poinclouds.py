from constants import *
import numpy as np
import pandas as pd
import open3d as o3d
from colmap_testing.colmap_helpers import read_write_model
import os

recording_id = "ff0acdab-123d-41d8-bfd6-b641f99fc8eb"
recording_path = os.path.join(recordings_folder, recording_id)

def get_colmap_sparse_model(recording_path):
    path = os.path.join(recording_path, "colmap_ws/colmap_out_1/sparse")
    cameras, images, points_3d = read_write_model.read_model(path, ".bin")
    return cameras, images, points_3d

def get_colmap_dense_model(recording_path):
    path = os.path.join(recording_path, "colmap_ws/automatic_recontructor/dense/0/sparse")
    cameras, images, points_3d = read_write_model.read_model(path, ".bin")
    return cameras, images, points_3d

def get_depth_distances_array(recording_path):
    depth_camera_distances = np.load(os.path.join(recording_path, "depth_array.npz"))
    file_name = depth_camera_distances.files[0]
    return depth_camera_distances[file_name][90] #depth_camera_distances[file_name][90] is the depth array of the 90th frame
    

def get_depth_camera_pointcloud(recording_path, nr_points=20000):
    path = os.path.join(recording_path,"meshed_depth_camera.ply")
    mesh = o3d.io.read_triangle_mesh(path)
    pointcloud  = mesh.sample_points_uniformly(number_of_points=nr_points)
    return pointcloud

#transform pointcloud to different coordinate system
#pointcloud being a 3d numpy array
def transform_pointcloud_numpy(pointcloud, R, t):
    pointcloud = np.matmul(R, pointcloud.T).T
    pointcloud = pointcloud + t
    return pointcloud

def get_pointcloud_o3d(points_3d, colors):
    pointcloud = o3d.geometry.PointCloud()
    pointcloud.points = o3d.utility.Vector3dVector(points_3d[:, :3])
    pointcloud.colors = o3d.utility.Vector3dVector(colors)
    return pointcloud

#pointclouds being a list of o3d pointclouds
def draw_pointclouds(pointclouds):
    o3d.visualization.draw_plotly(pointclouds)

#returns the colmap image dict
def get_colmap_depth_image(images):
    depth_image_id = None
    for image_id in images:
        if images[image_id].name == "depth_rgb.png":
            depth_image_id = image_id
            break
    return images[image_id]

#returns the depths of the points thatare non zero in from the depth array
def get_depths_and_colmap_point_ids(colmap_depth_image, colmap_points, depth_array):
    #get the visible points
    visible_colmap_point_ids, depths = [], []
    for point_ids, pixel_location in zip(colmap_depth_image.point3D_ids, colmap_depth_image.xys):
        if point_ids != -1:
            pixel_location = np.round(pixel_location).astype(int) #round pixel locations
            x = pixel_location[0]
            y = pixel_location[1]
            if depth_array[y, x] != 0:
                visible_colmap_point_ids.append(point_ids)
                depths.append(depth_array[y, x])
                
    return np.array(depths), np.array(visible_colmap_point_ids)

    

def get_scale(colmap_cameras, colmap_images, colmap_points, depth_array):
    colmap_depth_image = get_colmap_depth_image(colmap_images)
    depths, point_ids = get_depths_and_colmap_point_ids(colmap_depth_image, colmap_points, depth_array)
    visible_3Dpoints_by_depth_camera = np.array([colmap_points[point_id].xyz for point_id in point_ids])
    camera_position = colmap_depth_image.tvec
    #calculate distance between camera and points
    distances = np.linalg.norm(visible_3Dpoints_by_depth_camera - camera_position, axis=1)
    #calculate scale
    scale = np.mean(depths / distances)
    return scale / 1000 #convert to meters (because the pointcloud is in meters)
############################################################################################################
sparse_cameras, sparse_images, sparse_points = get_colmap_sparse_model(recording_path)
dense_cameras, dense_images, dense_points = get_colmap_dense_model(recording_path)
depth_distances_array = get_depth_distances_array(recording_path)


sparse_scale = get_scale(sparse_cameras, sparse_images, sparse_points, depth_distances_array)
dense_scale = get_scale(dense_cameras, dense_images, dense_points, depth_distances_array)

print("sparse scale: ", sparse_scale)
print("dense scale: ", dense_scale)

