import os


def del_temp_files(file_path: str) -> None:
    "delete file in given path"
    if os.path.isfile(file_path):
        os.remove(file_path)
    else:
        print("path is not a file")
        pass
