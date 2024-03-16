import shutil
import os

source_file = r"D:\Zewail\DrEman\Rana-project\tst_singe_more50\Sample46_F.ab1"
destination_folder = r"D:\Zewail\DrEman\Rana-project\tst_singe_more50"

# Create destination folder if it doesn't exist
if not os.path.exists(destination_folder):
    os.makedirs(destination_folder)

# Copy the file 120 times
for i in range(1, 121):
    if i  == 46: continue
    new_file_name = f"sample{i}_F.ab1"
    destination_path = os.path.join(destination_folder, new_file_name)
    shutil.copyfile(source_file, destination_path)

print("Files copied successfully.")
