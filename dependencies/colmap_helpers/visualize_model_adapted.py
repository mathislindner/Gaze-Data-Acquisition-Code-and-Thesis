# Copyright (c) 2023, ETH Zurich and UNC Chapel Hill.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#
#     * Neither the name of ETH Zurich and UNC Chapel Hill nor the names of
#       its contributors may be used to endorse or promote products derived
#       from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDERS OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

import numpy as np
import open3d

from read_write_model import read_model, qvec2rotmat


class Model:
    def __init__(self):
        self.cameras = []
        self.images = []
        self.points3D = []
        self.__vis = None

    def read_model(self, path, ext=""):
        self.cameras, self.images, self.points3D = read_model(path, ext)

    def load_points(self, min_track_len=3, remove_statistical_outlier=True):
        pcd = open3d.geometry.PointCloud()

        xyz = []
        rgb = []
        for point3D in self.points3D.values():
            track_len = len(point3D.point2D_idxs)
            if track_len < min_track_len:
                continue
            xyz.append(point3D.xyz)
            rgb.append(point3D.rgb / 255)

        pcd.points = open3d.utility.Vector3dVector(xyz)
        pcd.colors = open3d.utility.Vector3dVector(rgb)

        # remove obvious outliers
        if remove_statistical_outlier:
            [pcd, _] = pcd.remove_statistical_outlier(nb_neighbors=20,
                                                      std_ratio=2.0)
        
        return pcd

    def load_cameras(self, scale=1):
        frames = []
        for img in self.images.values():
            # rotation
            R = qvec2rotmat(img.qvec)

            # translation
            t = img.tvec

            # invert
            t = -R.T @ t
            R = R.T

            # intrinsics
            cam = self.cameras[img.camera_id]

            if cam.model in ("SIMPLE_PINHOLE", "SIMPLE_RADIAL", "RADIAL"):
                fx = fy = cam.params[0]
                cx = cam.params[1]
                cy = cam.params[2]
            elif cam.model in ("PINHOLE", "OPENCV", "OPENCV_FISHEYE", "FULL_OPENCV"):
                fx = cam.params[0]
                fy = cam.params[1]
                cx = cam.params[2]
                cy = cam.params[3]
            else:
                raise Exception("Camera model not supported")

            # intrinsics
            K = np.identity(3)
            K[0, 0] = fx
            K[1, 1] = fy
            K[0, 2] = cx
            K[1, 2] = cy

            # create axis, plane and pyramed geometries that will be drawn
            cam_model = draw_camera(K, R, t, cam.width, cam.height, scale)
            frames.extend(cam_model)

        return frames

    # def create_window(self):
    #     self.__vis = open3d.visualization.Visualizer()
    #     self.__vis.create_window()

    # def add_geometry_list(self, geometry_list):
    #     for g in geometry_list:
    #         # open3d.visualization.draw_geometries([g])
    #         self.__vis.add_geometry(g)

    # def show(self):
    #     self.__vis.poll_events()
    #     self.__vis.update_renderer()
    #     self.__vis.run()
    #     self.__vis.destroy_window()


def draw_camera(K, R, t, w, h,
                scale=1, color=[0.8, 0.2, 0.8]):
    """Create axis, plane and pyramed geometries in Open3D format.
    :param K: calibration matrix (camera intrinsics)
    :param R: rotation matrix
    :param t: translation
    :param w: image width
    :param h: image height
    :param scale: camera model scale
    :param color: color of the image plane and pyramid lines
    :return: camera model geometries (axis, plane and pyramid)
    """

    # intrinsics
    K = K.copy() / scale
    Kinv = np.linalg.inv(K)

    # 4x4 transformation
    T = np.column_stack((R, t))
    T = np.vstack((T, (0, 0, 0, 1)))

    # axis
    axis = open3d.geometry.TriangleMesh.create_coordinate_frame(size=0.5 * scale)
    axis.transform(T)

    # points in pixel
    points_pixel = [
        [0, 0, 0],
        [0, 0, 1],
        [w, 0, 1],
        [0, h, 1],
        [w, h, 1],
    ]

    # pixel to camera coordinate system
    points = [Kinv @ p for p in points_pixel]

    # image plane
    width = abs(points[1][0]) + abs(points[3][0])
    height = abs(points[1][1]) + abs(points[3][1])
    plane = open3d.geometry.TriangleMesh.create_box(width, height, depth=1e-6)
    plane.paint_uniform_color(color)
    plane.translate([points[1][0], points[1][1], scale])
    plane.transform(T)

    # pyramid
    points_in_world = [(R @ p + t) for p in points]
    lines = [
        [0, 1],
        [0, 2],
        [0, 3],
        [0, 4],
    ]
    colors = [color for i in range(len(lines))]
    line_set = open3d.geometry.LineSet(
        points=open3d.utility.Vector3dVector(points_in_world),
        lines=open3d.utility.Vector2iVector(lines))
    line_set.colors = open3d.utility.Vector3dVector(colors)

    # return as list in Open3D format
    return [axis, plane, line_set]


def main():
    plotly_mod = False
    input_model_path = '/home/nipopovic/MountedDirs/aegis_cvl/aegis_cvl_root/data/mathis/for_nikola/ff0acdab-123d-41d8-bfd6-b641f99fc8eb/colmap_ws/colmap_out_1/sparse'
    input_model_path = '/home/nipopovic/MountedDirs/aegis_cvl/aegis_cvl_root/data/mathis/for_nikola/3c9b343b-c076-4c93-9098-fc693503e7ca/colmap_EM_ws/exhaustive_matcher_out/world_and_depth/sparse'
    # [".bin", ".txt"]
    extension = ".bin"


    # read COLMAP model
    model = Model()
    model.read_model(input_model_path, ext=extension)

    print(" ")
    print("drawing colmap pointcloud:", input_model_path)
    print("num_cameras:", len(model.cameras))
    print("num_images:", len(model.images))
    print("num_points3D:", len(model.points3D))
    print(" ")

    # display using Open3D visualization tools
    geometry_list = []
    pcd = model.load_points()
    geometry_list.append(pcd)
    frames = model.load_cameras(scale=0.25)
    geometry_list.extend(frames)

    if plotly_mod:
        open3d.visualization.draw_plotly(geometry_list,  width=1920, height=1080)
    else:
        
        vis = open3d.visualization.Visualizer()
        vis.create_window()

        for g in geometry_list:
            # open3d.visualization.draw_geometries([g])
            vis.add_geometry(g)

        vis.poll_events()
        vis.update_renderer()
        vis.run()
        vis.destroy_window()


if __name__ == "__main__":
    main()
