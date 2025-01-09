import os

def save_uploaded_resume_temp(uploaded_file, temp_folder="temp"):
    """
    Save the uploaded resume as a temporary file.
    """
    if not os.path.exists(temp_folder):
        os.makedirs(temp_folder)
    temp_file_path = os.path.join(temp_folder, uploaded_file.name)
    with open(temp_file_path, "wb") as f:
        f.write(uploaded_file.read())
    return temp_file_path

def read_file(file_path):
    """
    Read the file content.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    return content