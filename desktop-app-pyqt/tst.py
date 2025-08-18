import PyQt5
print(PyQt5.__file__)
# from utils.choosing_folder_utilts import *
# from logic.ssa_logic import *
# # Test matching function
# def test_matching_function():
#     reads_folder  = r"D:\Zewail\DrEman\Rana-project\tsts22"
#     matches = find_matching_reads_paired(reads_folder)
#     print(matches)

# should exist 23 35 43 
# nt 27 44
# nr 28 36
# both 34
# just nt: show 23 28 35 36 43  45(no folder) 49(empty folder) no 27 44 34
# find_matching_reads_paired_proc(r"D:\Zewail\DrEman\Rana-project\tsts2", is_blastnr= False, is_blastnt= True, is_blast_both= False, is_overwrite= True)
# just nt: show 23 27 35 43 44 45(no folder) 49(empty folder) no 28 36 34
# find_matching_reads_paired_proc(r"D:\Zewail\DrEman\Rana-project\tsts2", is_blastnr= True, is_blastnt= False, is_blast_both= False, is_overwrite= True)
# show all no 34
# find_matching_reads_paired_proc(r"D:\Zewail\DrEman\Rana-project\tsts2", is_blastnr= True, is_blastnt= False, is_blast_both= True, is_overwrite= False)

# test_matching_function()
    
# reads_folder  = r"D:\Zewail\DrEman\Rana-project\tsts"
# print(find_matching_reads_single(reads_folder))


# should exist 11 12
# nt 4 6
# nr 7 8
# both 9 10
# should show /11 /12 /4 /6 overwriite(7 8 9 10) not 7 8 9 10
# find_matching_reads_single_proc(
#     r"D:\Zewail\DrEman\Rana-project\tsts",
#     is_blastnr = True,
#     is_blastnt= False,
#     is_blastBoth = False,
#     is_overwrite= False
# )

# should show 11 12 7 8 overwriite(9 10 4 6) not 9 10 4 6
# find_matching_reads_single_proc(
#     r"D:\Zewail\DrEman\Rana-project\tsts",
#     is_blastnr = False,
#     is_blastnt= True,
#     is_blastBoth = False,
#     is_overwrite= False
# )

# should show 9 10 overwriite(9 10 4 6) not 9 10
# find_matching_reads_single_proc(
#     r"D:\Zewail\DrEman\Rana-project\tsts",
#     is_blastnr = False,
#     is_blastnt= False,
#     is_blastBoth = True,
#     is_overwrite= False
# )
cpu
###
search
#####

# Large dataset: No timeout
# nt 21
# nr 48