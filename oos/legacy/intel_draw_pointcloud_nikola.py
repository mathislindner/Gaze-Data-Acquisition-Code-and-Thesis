# License: Apache 2.0. See LICENSE file in root directory.
# Copyright(c) 2015-2017 Intel Corporation. All Rights Reserved.

"""
OpenCV and Numpy Point cloud Software Renderer

This sample is mostly for demonstration and educational purposes.
It really doesn't offer the quality or performance that can be
achieved with hardware acceleration.

Usage:
------
Mouse: 
    Drag with left button to rotate around pivot (thick small axes), 
    with right button to translate and the wheel to zoom.

Keyboard: 
    [p]     Pause
    [r]     Reset View
    [d]     Cycle through decimation values
    [z]     Toggle point scaling
    [c]     Toggle color source
    [s]     Save PNG (./out.png)
    [e]     Export points to ply (./out.ply)
    [q\ESC] Quit
"""

import os
import sys
sys.path.insert(1, '/home/nipopovic/Code/gaze_data_acquisition')

import math
import time
import cv2
import numpy as np
import pyrealsense2 as rs

import open3d as o3d

recordings_folder = '/home/nipopovic/MountedDirs/aegis_cvl/aegis_cvl_root/data/mathis/for_nikola'
recording_id = "ff0acdab-123d-41d8-bfd6-b641f99fc8eb"
# recordings_folder = '/home/nipopovic/MountedDirs/aegis_cvl/aegis_cvl_root/data/data_collection/recordings'
# recording_id = '3c9b343b-c076-4c93-9098-fc693503e7ca'

pointcloud_depth_camera_path = os.path.join(recordings_folder, recording_id, "depth_camera_pointcloud.ply")
meshed_depth_camera_path = os.path.join(recordings_folder, recording_id,"meshed_depth_camera.ply")
bag_file_path = os.path.join(recordings_folder, recording_id, "realsensed435.bag")

select_frame = 95


class AppState:

    def __init__(self, *args, **kwargs):
        self.WIN_NAME = 'RealSense'
        self.pitch, self.yaw = math.radians(-10), math.radians(-15)
        self.translation = np.array([0, 0, -1], dtype=np.float32)
        self.distance = 2
        self.prev_mouse = 0, 0
        self.mouse_btns = [False, False, False]
        self.paused = False
        self.decimate = 1
        self.scale = True
        self.color = True

    def reset(self):
        self.pitch, self.yaw, self.distance = 0, 0, 2
        self.translation[:] = 0, 0, -1

    @property
    def rotation(self):
        Rx, _ = cv2.Rodrigues((self.pitch, 0, 0))
        Ry, _ = cv2.Rodrigues((0, self.yaw, 0))
        return np.dot(Ry, Rx).astype(np.float32)

    @property
    def pivot(self):
        return self.translation + np.array((0, 0, self.distance), dtype=np.float32)


def project(v):
    """project 3d vector array to 2d"""
    h, w = out.shape[:2]
    view_aspect = float(h)/w

    # ignore divide by zero for invalid depth
    with np.errstate(divide='ignore', invalid='ignore'):
        proj = v[:, :-1] / v[:, -1, np.newaxis] * \
            (w*view_aspect, h) + (w/2.0, h/2.0)

    # near clipping
    znear = 0.03
    proj[v[:, 2] < znear] = np.nan
    return proj


def view(v):
    """apply view transformation on vector array"""
    return np.dot(v - state.pivot, state.rotation) + state.pivot - state.translation


def line3d(out, pt1, pt2, color=(0x80, 0x80, 0x80), thickness=1):
    """draw a 3d line from pt1 to pt2"""
    p0 = project(pt1.reshape(-1, 3))[0]
    p1 = project(pt2.reshape(-1, 3))[0]
    if np.isnan(p0).any() or np.isnan(p1).any():
        return
    p0 = tuple(p0.astype(int))
    p1 = tuple(p1.astype(int))
    rect = (0, 0, out.shape[1], out.shape[0])
    inside, p0, p1 = cv2.clipLine(rect, p0, p1)
    if inside:
        cv2.line(out, p0, p1, color, thickness, cv2.LINE_AA)


def grid(out, pos, rotation=np.eye(3), size=1, n=10, color=(0x80, 0x80, 0x80)):
    """draw a grid on xz plane"""
    pos = np.array(pos)
    s = size / float(n)
    s2 = 0.5 * size
    for i in range(0, n+1):
        x = -s2 + i*s
        line3d(out, view(pos + np.dot((x, 0, -s2), rotation)),
               view(pos + np.dot((x, 0, s2), rotation)), color)
    for i in range(0, n+1):
        z = -s2 + i*s
        line3d(out, view(pos + np.dot((-s2, 0, z), rotation)),
               view(pos + np.dot((s2, 0, z), rotation)), color)


def axes(out, pos, rotation=np.eye(3), size=0.075, thickness=2):
    """draw 3d axes"""
    line3d(out, pos, pos +
           np.dot((0, 0, size), rotation), (0xff, 0, 0), thickness)
    line3d(out, pos, pos +
           np.dot((0, size, 0), rotation), (0, 0xff, 0), thickness)
    line3d(out, pos, pos +
           np.dot((size, 0, 0), rotation), (0, 0, 0xff), thickness)


def frustum(out, intrinsics, color=(0x40, 0x40, 0x40)):
    """draw camera's frustum"""
    orig = view([0, 0, 0])
    w, h = intrinsics.width, intrinsics.height

    for d in range(1, 6, 2):
        def get_point(x, y):
            p = rs.rs2_deproject_pixel_to_point(intrinsics, [x, y], d)
            line3d(out, orig, view(p), color)
            return p

        top_left = get_point(0, 0)
        top_right = get_point(w, 0)
        bottom_right = get_point(w, h)
        bottom_left = get_point(0, h)

        line3d(out, view(top_left), view(top_right), color)
        line3d(out, view(top_right), view(bottom_right), color)
        line3d(out, view(bottom_right), view(bottom_left), color)
        line3d(out, view(bottom_left), view(top_left), color)


def pointcloud(out, verts, texcoords, color, painter=True):
    """draw point cloud with optional painter's algorithm"""
    if painter:
        # Painter's algo, sort points from back to front

        # get reverse sorted indices by z (in view-space)
        # https://gist.github.com/stevenvo/e3dad127598842459b68
        v = view(verts)
        s = v[:, 2].argsort()[::-1]
        proj = project(v[s])
    else:
        proj = project(view(verts))

    if state.scale:
        proj *= 0.5**state.decimate

    h, w = out.shape[:2]

    # proj now contains 2d image coordinates
    j, i = proj.astype(np.uint32).T

    # create a mask to ignore out-of-bound indices
    im = (i >= 0) & (i < h)
    jm = (j >= 0) & (j < w)
    m = im & jm

    cw, ch = color.shape[:2][::-1]
    if painter:
        # sort texcoord with same indices as above
        # texcoords are [0..1] and relative to top-left pixel corner,
        # multiply by size and add 0.5 to center
        v, u = (texcoords[s] * (cw, ch) + 0.5).astype(np.uint32).T
    else:
        v, u = (texcoords * (cw, ch) + 0.5).astype(np.uint32).T
    # clip texcoords to image
    np.clip(u, 0, ch-1, out=u)
    np.clip(v, 0, cw-1, out=v)

    # perform uv-mapping
    out[i[m], j[m]] = color[u[m], v[m]]

###############################################################################

def plot_o3d_geometries(geometries_list, plotly=False):        
    if plotly:
        o3d.visualization.draw_plotly(geometries_list,  width=1920, height=1080)
    else:    
        vis = o3d.visualization.Visualizer()
        vis.create_window()

        for g in geometries_list:
            vis.add_geometry(g)

        vis.poll_events()
        vis.update_renderer()
        vis.run()
        vis.destroy_window()


state = AppState()

# Configure depth and color streams
pipeline = rs.pipeline()
config = rs.config()
config.enable_device_from_file(bag_file_path, repeat_playback=False)

pipeline_wrapper = rs.pipeline_wrapper(pipeline)
pipeline_profile = config.resolve(pipeline_wrapper)
device = pipeline_profile.get_device()

found_rgb = False
for s in device.sensors:
    if s.get_info(rs.camera_info.name) == 'RGB Camera':
        found_rgb = True
        break
if not found_rgb:
    print("The demo requires Depth camera with Color sensor")
    exit(0)

# Start streaming
profile = pipeline.start(config)

playback = profile.get_device().as_playback()
playback.set_real_time(False)

# Get stream profile and camera intrinsics
profile = pipeline.get_active_profile()
depth_profile = rs.video_stream_profile(profile.get_stream(rs.stream.depth))
depth_intrinsics = depth_profile.get_intrinsics()
color_profile = rs.video_stream_profile(profile.get_stream(rs.stream.color))
color_intrinsics = color_profile.get_intrinsics()
w, h = depth_intrinsics.width, depth_intrinsics.height
depth_scale = profile.get_device().first_depth_sensor().get_depth_scale()
#color_profile.get_extrinsics_to(depth_profile)

# Processing blocks
pc = rs.pointcloud()
colorizer = rs.colorizer()
# TODO REMOVE
# decimate = rs.decimation_filter()
# decimate.set_option(rs.option.filter_magnitude, 2 ** state.decimate)
# TODO REMOVE

# Create an align object
# rs.align allows us to perform alignment of depth frames to others frames
# The "align_to" is the stream type to which we plan to align depth frames.
align_to = rs.stream.color
align = rs.align(align_to)

out = np.empty((h, w, 3), dtype=np.uint8)
i=-1
while True:
    # Grab camera data
    if not state.paused:
        # Wait for a coherent pair of frames: depth and color
        try:
            frames = pipeline.wait_for_frames()
            # Align the depth frame to color frame
            playback.pause() #added this because else the frames are not saved correctly: https://stackoverflow.com/questions/58482414/frame-didnt-arrived-within-5000-while-reading-bag-file-pyrealsense2
        except:
            break
        
        i += 1
        if not i == select_frame:
            print('skip')
            playback.resume()
            continue

        aligned_frames = align.process(frames)

        depth_frame = frames.get_depth_frame()
        color_frame = frames.get_color_frame()
        aligned_depth_frame = aligned_frames.get_depth_frame()
        aligned_color_frame = aligned_frames.get_color_frame()
        # depth_frame.as_depth_frame().get_distance(100,100)

        if not color_frame or not depth_frame:
            playback.resume()
            continue

        print(f'\nFrame number: i:{i} rgb:{color_frame.frame_number}, depth:{depth_frame.frame_number}')

        # depth_frame = decimate.process(depth_frame)

        # # Grab new intrinsics (may be changed by decimation)
        # depth_intrinsics = rs.video_stream_profile(
        #     depth_frame.profile).get_intrinsics()
        
        w, h = depth_intrinsics.width, depth_intrinsics.height

        depth_image = np.asanyarray(depth_frame.get_data())
        color_image = np.asanyarray(color_frame.get_data())
        aligned_depth_image = np.asanyarray(aligned_depth_frame.get_data())
        aligned_color_image = np.asanyarray(aligned_color_frame.get_data())

        # import matplotlib.pyplot as plt
        # plt.imshow(color_image)
        # plt.imshow(depth_image, alpha=0.6)
        # plt.show()
        # plt.close()
        # plt.imshow(aligned_color_image)
        # plt.imshow(aligned_depth_image, alpha=0.6)
        # plt.show()
        # plt.close()

        # TODO #################################################################
        # Create grid of pixel center positions in the uv space
        u_min = 0; u_max  = w
        v_min = 0; v_max  = h
        half_du = 0.5
        half_dv = 0.5
        u_linspace = np.linspace(u_min + half_du, u_max - half_du, w)
        v_linspace = np.linspace(v_min + half_dv, v_max - half_dv, h)
        # Reverse vertical coordinate because [H=0,W=0] 
        # corresponds to (u=-1, v=1).
        u, v = np.meshgrid(u_linspace, v_linspace)
        x = (u - color_intrinsics.ppx) / color_intrinsics.fx
        y = (v - color_intrinsics.ppy) / color_intrinsics.fy
        # Add 3rd coordinate and reshape to vector
        xyz_3d = (aligned_depth_image[..., None] * depth_scale) * np.dstack((x, y, np.ones_like(u)))
        xyz_3d = xyz_3d.reshape((h*w, 3))
        rgb_3d = aligned_color_image.reshape((h*w, 3))/255.0
        # TODO #################################################################

        o3d_pointcloud = o3d.geometry.PointCloud()
        o3d_pointcloud.points = o3d.utility.Vector3dVector(xyz_3d)
        o3d_pointcloud.colors = o3d.utility.Vector3dVector(rgb_3d)
        plot_o3d_geometries([o3d_pointcloud], plotly=True)
        
        ########################################################################

        depth_colormap = np.asanyarray(
            colorizer.colorize(depth_frame).get_data())

        if state.color:
            mapped_frame, color_source = color_frame, color_image
        else:
            mapped_frame, color_source = depth_frame, depth_colormap

        points = pc.calculate(depth_frame)
        pc.map_to(mapped_frame)


        # Pointcloud data to arrays
        v, t = points.get_vertices(), points.get_texture_coordinates()
        verts = np.asanyarray(v).view(np.float32).reshape(-1, 3)  # xyz
        texcoords = np.asanyarray(t).view(np.float32).reshape(-1, 2)  # uv


        o3d_pointcloud = o3d.geometry.PointCloud()
        o3d_pointcloud.points = o3d.utility.Vector3dVector(verts)
        #o3d_pointcloud.colors = o3d.utility.Vector3dVector(colmap_rgb_colors)
        plot_o3d_geometries([o3d_pointcloud], plotly=True)

        exit()

        playback.resume()
    # Render
    now = time.time()

    out.fill(0)

    grid(out, (0, 0.5, 1), size=1, n=10)
    frustum(out, depth_intrinsics)
    axes(out, view([0, 0, 0]), state.rotation, size=0.1, thickness=1)

    if not state.scale or out.shape[:2] == (h, w):
        pointcloud(out, verts, texcoords, color_source)
    else:
        tmp = np.zeros((h, w, 3), dtype=np.uint8)
        pointcloud(tmp, verts, texcoords, color_source)
        tmp = cv2.resize(
            tmp, out.shape[:2][::-1], interpolation=cv2.INTER_NEAREST)
        np.putmask(out, tmp > 0, tmp)

    if any(state.mouse_btns):
        axes(out, view(state.pivot), state.rotation, thickness=4)

    

    dt = time.time() - now


# Stop streaming
pipeline.stop()