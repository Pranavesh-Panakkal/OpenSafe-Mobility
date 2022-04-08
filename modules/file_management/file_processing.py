# Title     : All modules related to file processing
# Objective :
# Created by: Pranavesh Panakkal
# Created on: 12/6/2021
# Version   :
# Dev log   :
""""""
import os
from pathlib import Path
import shutil
from tqdm import tqdm


# def list_all_files_with_an_extension(pth_folder: str, file_extension: str = ".png") -> list:
#     """
#     List all files with an extension in a folder
#     :param pth_folder: Path to the directory to look for the files
#     :param file_extension: File extension. The file should end with this extension. "XXX.png" will also work
#     :return:
#     """
#     # Adjust to the list
#     if isinstance(file_extension, str):
#         file_extension = [file_extension]
#     # Placeholder
#     list_files = []
#     # Walk through dir and sub dire
#     for root, dirs, files in os.walk(pth_folder):
#         for file in files:
#             if any([file.endswith(_ext) for _ext in file_extension]):
#                 list_files.append(os.path.join(root, file))
#     # Return the list of paths
#     return list_files


def list_all_files_with_an_extension(
    pth_folder: str, file_extension: str = ".png"
) -> list:
    """ """
    # Placeholder
    list_files = []
    # Walk throught dir and sub dire
    for root, dirs, files in os.walk(pth_folder):
        for file in files:
            if file.endswith(file_extension):
                list_files.append(os.path.join(root, file))
    # Return the list of paths
    return [os.path.basename(x) for x in list_files]


# def list_all_files_with_an_extension(pth_folder: str, file_extension: str = ".png") -> list:
#     """
#     List all files with an extension in a folder
#     :param pth_folder: Path to the directory to look for the files
#     :param file_extension: File extension. The file should end with this extension. "XXX.png" will also work
#     :return:
#     """
#     # Placeholder
#     list_files = []
#     # Walk through dir and sub dire
#     for root, dirs, files in os.walk(pth_folder):
#         for file in files:
#             if file.endswith(file_extension):
#                 list_files.append(os.path.join(root, file))
#     # Return the list of paths
#     return list_files


def create_a_folder_if_it_doesnt_exist(
    path_to_new_folder: str, remove_folder_if_it_exist: bool = False
) -> None:
    """
    Creates a folder it it does not exist
    :param path_to_new_folder: Path to the folder
    :param remove_folder_if_it_exist: Remove the folder and its contents if it already exist
    :return:
    """
    if remove_folder_if_it_exist:
        remove_folder_if_exist(path_to_new_folder)
    # ignore FileExistsError, Make parents
    Path(path_to_new_folder).mkdir(parents=True, exist_ok=True)


def remove_folder_if_exist(path_to_file: str) -> None:
    """
    Delete a folder it if exists
    :param path_to_file: Path to the folder
    :return:
    """
    if os.path.exists(path_to_file):
        try:
            os.remove(path_to_file)
        except:
            pass


def add_an_extension_to_end_of_a_file(
    input_folder: str, input_file_extension: str, extension_to_add: str
) -> None:
    """
    Rename all files in a folder by adding an extension at the end
    :param input_folder:
    :param input_file_extension:
    :param extension_to_add:
    :return:
    """
    # Get all extensions from the current input folder
    list_of_files = list_all_files_with_an_extension(input_folder, input_file_extension)
    # Create output file destination
    for a_file in list_of_files:
        os.rename(a_file, a_file + extension_to_add)


def save_files_in_separate_folders(
    list_of_file_paths: list,
    folder_to_store: str,
    new_folder_prefix: str,
    max_num_files_per_folder: int,
) -> None:
    """
    Copy a list of files to separate folders. Each folder will contain a maximum of 'max_num_files_per_folder' files
    :param list_of_file_paths: list of file paths
    :param folder_to_store: folder to create sub-folders
    :param new_folder_prefix: folder name to prefix
    :param max_num_files_per_folder: maximum numbers of files per folder
    :return: None
    """
    # Divide the list into chunks of max size
    counter = 1
    for i in tqdm(range(0, len(list_of_file_paths), max_num_files_per_folder)):
        # Get the list of files
        _list_of_files = list_of_file_paths[i : i + max_num_files_per_folder]
        # Get a folder name
        folder_name = os.path.join(folder_to_store, f"{new_folder_prefix}_{counter}")
        # Make folder if it doesn't exist
        create_a_folder_if_it_doesnt_exist(
            path_to_new_folder=folder_name, remove_folder_if_it_exist=True
        )
        # Now copy the files to the folder
        [shutil.copy(file_, folder_name) for file_ in _list_of_files]
        counter += 1


def copy_files_with_an_extension_to_another_folder(
    source_folder: str,
    destination_folder: str,
    file_extension: str or list = ".png",
    replace_destination_folder: bool = False,
) -> list:
    """
    Copy files with an extension to another folder. The destination folder will be created if it doesn't exist.
    :param source_folder: Source folder to look for files
    :param destination_folder: Destination to copy the files to
    :param file_extension: File extension to be used to copy files
    :param replace_destination_folder: If True, replaces the destination file by deleting it. Use with care.
    :return: None
    """
    # Get list of all files in the folder
    _list_files = list_all_files_with_an_extension(
        pth_folder=source_folder, file_extension=file_extension
    )
    # Make sure the destination file exist
    create_a_folder_if_it_doesnt_exist(
        path_to_new_folder=destination_folder,
        remove_folder_if_it_exist=replace_destination_folder,
    )
    # Now copy the files
    [shutil.copy(src=src_file, dst=destination_folder) for src_file in _list_files]
    # Return
    return _list_files


def list_all_folders_in_a_directory(path_folder: str, filter: callable = None) -> list:
    """
    Get a list of folders in a directory
    :param path_folder: Path to the folder
    :return: a list of folder paths
    """
    list_folders = [e for e in Path(path_folder).iterdir() if e.is_dir()]

    if filter:
        list_folders = [e for e in list_folders if filter(e)]

    return list_folders


def remove_all_contents_of_a_folder(folder_path: str) -> None:
    """
    Remove all contents of a folder
    :param folder_path: Folder to remove all contents from
    :return:
    """
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print("Failed to delete %s. Reason: %s" % (file_path, e))
