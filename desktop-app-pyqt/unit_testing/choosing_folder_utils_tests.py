from utils.choosing_folder_utilts import *

# Test matching function
def test_matching_function():
    reads_folder  = r"D:\Zewail\DrEman\Rana-project\tsts"
    matches = find_matching_reads_paired(reads_folder)
    print(matches)


test_matching_function