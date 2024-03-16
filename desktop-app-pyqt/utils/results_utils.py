import os

def find_folders_gen(folder_path):
    print("find_folders_gen", folder_path)
    folders_gen = []
    folders = [f for f in os.listdir(folder_path) if os.path.isdir(os.path.join(folder_path, f))]
    for folder in folders:
        nt_file_path = os.path.join(folder_path, folder, "blast_results_nt.xml")
        if os.path.exists(nt_file_path):
            folders_gen.append(folder)
        
    return folders_gen
