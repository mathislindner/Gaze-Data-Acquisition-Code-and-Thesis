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

#TODO: instead of just using the 90th frame, average over a few frames from the beginning of the recording
def get_depth_distances_array(recording_path):
    depth_camera_distances = np.load(os.path.join(recording_path, "depth_array.npz"))
    file_name = depth_camera_distances.files[0]
    return depth_camera_distances[file_name][95] #depth_camera_distances[file_name][95] is the depth array of the 90th frame

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
    for image_id in images:
        if images[image_id].name == "depth_rgb.png":
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
############################################################################################################

#input are numpy arrays of shape pointcloud: (n, 3), R: (3, 3), t: (3), scale: float
def transform_pointcloud(pointcloud, R, t, scale):
    t = -t.T @ R
    #transformation_matrix = np.eye(4)
    #scaling_matrix = np.eye(4)*scale
    #transformation_matrix[:3, :3] = R
    #transformation_matrix[:3, 3] = t 
    #transformation_matrix[3, 3] = 1
    #transformation_matrix = scaling_matrix @ transformation_matrix
    #pointcloud = np.vstack((pointcloud.T, np.ones(pointcloud.shape[0])))
    #pointcloud = transformation_matrix.T @ pointcloud 
    #pointcloud = pointcloud[:3,:].T

    M = np.array([[1, 0, 0], [0, -1, 0], [0, 0, -1]])
    pointcloud = np.matmul(M, pointcloud.T).T
    # apply all three transformations seperately to debug
    pointcloud = np.matmul(R, pointcloud.T).T
    pointcloud = np.add(pointcloud, t)
    pointcloud = pointcloud * scale


    #mirror on x,y plane
    #
    
    return pointcloud

#from colmap to depth camera
def get_rotation_and_translation_matrix(colmap_cameras, colmap_images):
    colmap_depth_image = get_colmap_depth_image(colmap_images)
    q_vec = colmap_depth_image.qvec
    t_vec = colmap_depth_image.tvec
    
    camera_orientation = read_write_model.qvec2rotmat(q_vec)
    camera_position = t_vec

    #convert to depth camera coordinate system
    #FIXME invert rotation and translation
    rotation = camera_orientation
    translation = camera_position
    
    return rotation, translation

#returns the transformed colmap pointcloud and colors as o3d pointcloud
def get_transformed_colmap_as_o3d(colmap_cameras, colmap_images, colmap_points, scale):
    colmap_point_ids = list(colmap_points.keys())
    colmap_xyz = np.array([colmap_points[point_id].xyz for point_id in colmap_point_ids])
    colmap_rgb_colors = np.array([colmap_points[point_id].rgb for point_id in colmap_point_ids])
    rotation, translation = get_rotation_and_translation_matrix(colmap_cameras, colmap_images)
    transformed_colmap_points = transform_pointcloud(colmap_xyz, rotation, translation, scale)

    #colmap_camera_point_xyz = get_colmap_depth_image(colmap_images).tvec
    #colmap_camera_point_transformed = transform_pointcloud(colmap_camera_point_xyz, rotation, translation, scale)

    o3d_pointcloud = o3d.geometry.PointCloud()
    o3d_pointcloud.points = o3d.utility.Vector3dVector(transformed_colmap_points)
    o3d_pointcloud.colors = o3d.utility.Vector3dVector(colmap_rgb_colors)
    return o3d_pointcloud

#returns the transformed colmap pointcloud and colors as o3d pointcloud
def get_transformed_colmap_ply_as_o3d(colmap_cameras, colmap_images, colmap_points, scale):
    #colmap_point_ids = list(colmap_points.keys())
    colmap_fused_ply = o3d.io.read_point_cloud(os.path.join(recording_path, 'colmap_ws', 'automatic_recontructor','dense','0',"fused.ply"))
    colmap_xyz = np.asarray(colmap_fused_ply.points)
    colmap_rgb_colors = np.asarray(colmap_fused_ply.colors)

    #colmap_xyz = np.array([colmap_points[point_id].xyz for point_id in colmap_point_ids])
    #colmap_rgb_colors = np.array([colmap_points[point_id].rgb for point_id in colmap_point_ids])
    rotation, translation = get_rotation_and_translation_matrix(colmap_cameras, colmap_images)
    transformed_colmap_points = transform_pointcloud(colmap_xyz, rotation, translation, scale)

    #colmap_camera_point_xyz = get_colmap_depth_image(colmap_images).tvec
    #colmap_camera_point_transformed = transform_pointcloud(colmap_camera_point_xyz, rotation, translation, scale)

    o3d_pointcloud = o3d.geometry.PointCloud()
    o3d_pointcloud.points = o3d.utility.Vector3dVector(transformed_colmap_points)
    o3d_pointcloud.colors = o3d.utility.Vector3dVector(colmap_rgb_colors)
    return o3d_pointcloud

def get_depth_camera_pointcloud_as_o3d(recording_path, nr_points=50000):
    path = os.path.join(recording_path,"meshed_depth_camera.ply")
    mesh = o3d.io.read_triangle_mesh(path)
    pointcloud  = mesh.sample_points_uniformly(number_of_points=nr_points)
    return pointcloud

depth_pointcloud = get_depth_camera_pointcloud_as_o3d(recording_path)
sparse_camera_pointcloud = get_transformed_colmap_as_o3d(sparse_cameras, sparse_images, sparse_points, sparse_scale)
dense_camera_pointcloud = get_transformed_colmap_as_o3d(dense_cameras, dense_images, dense_points, dense_scale)
dense_camera_ply_pointcloud = get_transformed_colmap_ply_as_o3d(dense_cameras, dense_images, dense_points, dense_scale).voxel_down_sample(voxel_size=0.05)

o3d.visualization.draw_plotly([depth_pointcloud, dense_camera_pointcloud],  width=1920, height=1080)
o3d.visualization.draw_plotly([depth_pointcloud, sparse_camera_pointcloud],  width=1920, height=1080)
o3d.visualization.draw_plotly([depth_pointcloud, dense_camera_ply_pointcloud],  width=1920, height=1080)