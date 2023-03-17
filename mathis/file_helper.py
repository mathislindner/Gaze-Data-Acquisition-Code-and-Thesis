import zipfile
import io 
import os
from shutil import move

def unzip_and_move_to_parent(response, parent_folder):
    z = zipfile.ZipFile(io.BytesIO(response))
    z.extractall(parent_folder)
    subfolder_name = os.listdir(parent_folder + "/")[0]
    #move all files to parent folder and delete folder
    for filename in os.listdir(os.path.join(parent_folder, subfolder_name)):
        move(os.path.join(parent_folder, subfolder_name, filename), os.path.join(parent_folder, filename))
    os.rmdir(os.path.join(parent_folder, subfolder_name))