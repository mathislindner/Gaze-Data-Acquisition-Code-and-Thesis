import ffmpeg
import os

recordings_folder = "mathis/recordings/"
cameras = ["PI left v1 ps1", "PI right v1 ps1", "PI world v1 ps1"]
camera_folders = ["left_eye_frames", "right_eye_frames", "world_frames"]

def extract_one_camera(input_file, output_folder):
    n_of_frames = ffmpeg.probe(input_file)['streams'][0]['nb_frames']
    (
        ffmpeg
        .input(input_file)
    ).output(output_folder + "/" + "%d.png", start_number=0, vframes=n_of_frames, vsync = 2, loglevel="quiet").run()

def extract_frames(recording_id):
    recording_folder = recordings_folder + str(recording_id)
    try:
        os.mkdir(recording_folder + "/left_eye_frames")
        os.mkdir(recording_folder + "/right_eye_frames")
        os.mkdir(recording_folder + "/world_frames")
    except:
        pass

    for i in range(len(cameras)):
        input_file = recording_folder + "/" + cameras[i] + ".mp4"
        output_folder = recording_folder + "/" + camera_folders[i]
        extract_one_camera(input_file, output_folder)