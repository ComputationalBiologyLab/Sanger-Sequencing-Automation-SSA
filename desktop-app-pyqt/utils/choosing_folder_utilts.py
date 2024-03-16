import os
from typing import Callable, List
from typing import Dict, Tuple


def find_matching_reads_single(reads_folder: str) -> Dict[str, str]:
    """
    Find single reads in the specified folder.

    This function scans a given directory for files ending in '_R.ab1' or '_F.ab1', identifying forward and reverse reads. It then matches the reads based on sample names and returns only those samples that have single reads (either forward or reverse, but not both).

    Args:
        reads_folder (str): The folder containing the read files. It must be a valid directory path.

    Returns:
        Dict[str, str]: A dictionary mapping sample names to their corresponding single read file paths.

    Raises:
        ValueError: If 'reads_folder' is not a valid directory.
    """
    # Validate reads_folder
    if not os.path.isdir(reads_folder):
        raise ValueError(f"The provided 'reads_folder' is not a valid directory: {reads_folder}")

    return _find_matching_reads_single(reads_folder)

def _find_matching_reads_single(reads_folder: str) -> Dict[str, str]:
    """
    Internal function to find single reads in the specified folder.

    Args:
        reads_folder (str): The folder containing the read files.

    Returns:
        Dict[str, str]: A dictionary mapping sample names to their corresponding single read file paths.
    """
    forward_reads: Dict[str, str] = {}
    reverse_reads: Dict[str, str] = {}
    for file_name in os.listdir(reads_folder):
        if file_name.endswith("_R.ab1"):
            sample_name = file_name[:-len("_R.ab1")]
            reverse_reads[sample_name] = os.path.join(reads_folder, file_name)
        elif file_name.endswith("_F.ab1"):
            sample_name = file_name[:-len("_F.ab1")]
            forward_reads[sample_name] = os.path.join(reads_folder, file_name)

    matches = {}
    for sample_name, forward_read in forward_reads.items():
        if sample_name not in reverse_reads:
            matches[sample_name] = forward_read
    return matches


def find_matching_reads_paired(reads_folder: str) -> Dict[str, Tuple[str, str]]:
    """
    Public interface to find matching paired reads in a specified folder.

    Args:
        reads_folder (str): Path to the folder containing read files.

    Returns:
        Dict[str, Tuple[str, str]]: A dictionary mapping sample names to pairs of 
                                    forward and reverse read file paths.

    This function serves as the public interface and validates the input type before 
    calling the internal function `_find_matching_reads_paired`. It ensures that the 
    provided `reads_folder` is a valid string before proceeding.

    Raises:
        TypeError: If `reads_folder` is not a string.
    """
    if not isinstance(reads_folder, str):
        raise TypeError("reads_folder must be a string")
    if not ( os.path.exists(reads_folder) and os.path.isdir(reads_folder)):
        raise ValueError(f"The folder path: {reads_folder} doesn't exist or is not a directory. Please select a valid directory")
    return _find_matching_reads_paired(reads_folder)

def _find_matching_reads_paired(reads_folder: str) -> Dict[str, Tuple[str, str]]:
    """
    Finds matching paired reads in the specified folder.

    This function searches for pairs of forward and reverse read files in the given folder. 
    It assumes a naming convention where forward reads end with "_F.ab1" and reverse reads 
    end with "_R.ab1".

    Args:
        reads_folder (str): The folder containing the read files.

    Returns:
        Dict[str, Tuple[str, str]]: A dictionary mapping sample names to pairs of 
                                    forward and reverse read file paths.

    The function iterates through the files in the specified folder, extracts sample names 
    from the file names, and creates pairs of forward and reverse read file paths. The pairs 
    are stored in a dictionary, and the result is returned.

    Example:
    If there are files "sample1_F.ab1" and "sample1_R.ab1" in the reads_folder, the 
    function would return {'sample1': ('reads_folder/sample1_F.ab1', 'reads_folder/sample1_R.ab1')}.
    """
    forward_reads = {}
    reverse_reads = {}

    for file_name in os.listdir(reads_folder):
        if  file_name.endswith("_R.ab1"):
                sample_name = file_name[:-len("_R.ab1")]
                reverse_reads[sample_name] = os.path.join(reads_folder, file_name)
        elif file_name.endswith("_F.ab1"):
                sample_name = file_name[:-len("_F.ab1")]
                forward_reads[sample_name] = os.path.join(reads_folder, file_name)

    matches = {}
    for sample_name in forward_reads:
        forward_read = forward_reads.get(sample_name)
        reverse_read = reverse_reads.get(sample_name)
        if forward_read and reverse_read:
            matches[sample_name] = (forward_read, reverse_read)
    return matches


def find_num_single_files(folder_path):
    return len(find_matching_reads_single(folder_path))


def find_num_pair_files(folder_path):
    return len(find_matching_reads_paired(folder_path))

def find_num_files(folder_path):
    return find_num_single_files(folder_path), find_num_pair_files(folder_path)


def find_gen_files(folder_path: str, is_blastnr: bool, is_blastnt: bool, is_blastBoth, matching_func: Callable[[str], Dict[str, Tuple[str, str]]]) -> List[str]:
    """
    Finds and lists directories within the specified folder that meet certain criteria.

    Args:
        folder_path (str): Path to the folder where subdirectories are to be searched.
        blast_option (str): BLAST option ('Blastnt', 'Blastnr', or 'Both').
        matching_func (Callable): A function that processes the folder_path and returns a list of files.

    Returns:
        List[str]: A list of folder names within the specified folder that meet the criteria defined by
                blast_option and the matching_func.

    Raises:
        ValueError: If folder_path is not a valid string or does not exist as a directory.
        ValueError: If blast_option is not one of the valid values: 'Blastnt', 'Blastnr', or 'Both'.
    """
    if (not isinstance(folder_path, str)) or not (os.path.exists(folder_path) and os.path.isdir(folder_path)):
        raise ValueError(f"The folder path: {folder_path} doesn't exist or is not a directory. Please select a valid directory")
    # if not (blast_option =="Blastnt" or blast_option == "Blastnr" or blast_option == "Both"):
    #     raise ValueError(f"blast_option can have only theses values: Blastnt, Blastnr, Both; however, the provided is {blast_option}")
    return _find_gen_files(folder_path, is_blastnr, is_blastnt, is_blastBoth, matching_func)

def _find_gen_files(folder_path: str, is_blastnr: bool, is_blastnt: bool, is_blastBoth, matching_func: Callable[[str], Dict[str, Tuple[str, str]]]) -> List[str]:
    """
    Internal function to find directories within the specified folder based on certain criteria.

    Args:
        folder_path (str): Path to the folder where subdirectories are to be searched.
        blast_option (str): BLAST option ('Blastnt', 'Blastnr', or 'Both').
        matching_func (Callable): A function that processes the folder_path and returns a list of files.

    Returns:
        List[str]: A list of folder names within the specified folder that meet the criteria defined by
                blast_option and the matching_func.
    """
    folders_gen: List[str] = []
    folders: List[str] = [f for f in os.listdir(folder_path) if os.path.isdir(os.path.join(folder_path, f))] # # Find all subdirectories in folder_path
    files_single: Dict[str, Tuple[str, str]] = matching_func(folder_path) # files that are either single or pair locations
    folders = [folder for folder in folders if folder in files_single.keys()] # only the folders that are related to the files that need to be processed
    for folder in folders:
        nr_file_path = os.path.join(folder_path, folder, "blast_results_nr.xml")
        nt_file_path = os.path.join(folder_path, folder, "blast_results_nt.xml")
        if is_blastnt:
            if os.path.exists(nt_file_path):
                folders_gen.append(folder)
        elif is_blastnr:
            if os.path.exists(nr_file_path):
                folders_gen.append(folder)
        elif is_blastBoth:
            if os.path.exists(nr_file_path) and os.path.exists(nt_file_path):
                folders_gen.append(folder)
    return folders_gen

def find_gen_single_files(folder_path: str, is_blastnr: bool, is_blastnt: bool, is_blast_both: bool) -> List[str]:
    """
    Find generated single files based on the specified BLAST option.

    Args:
        folder_path (str): The path to the folder where files are located.
        blast_option (str): The BLAST option to be considered.

    Returns:
        Set[str]: A set of file names that match the given BLAST option.

    Raises:
        ValueError: If the folder_path is not a valid directory.
        ValueError: If blast_option is not valid.
    """
    if not os.path.isdir(folder_path):
        raise ValueError("Provided folder path is not a valid directory")
    
    valid_blast_options = {"Blastnr", "Blastnt", "Both"}
    # if blast_option not in valid_blast_options:
    #     raise ValueError(f"Invalid BLAST option. Valid options are: {valid_blast_options}")

    return _find_gen_single_files(folder_path, is_blastnr, is_blastnt, is_blast_both)

def _find_gen_single_files(folder_path, is_blastnr: bool, is_blastnt: bool, is_blast_both):
    """
    Internal function to find generated single files based on the specified BLAST option.

    Args:
        folder_path (str): The path to the folder where files are located.
        blast_option (str): The BLAST option to be considered.

    Returns:
        Set[str]: A set of file names that match the given BLAST option.
    """
    return find_gen_files(folder_path, is_blastnr, is_blastnt, is_blast_both, find_matching_reads_single)

def find_gen_pair_files(folder_path: str, is_blastnr: bool, is_blastnt: bool, is_blastnt_nr) -> List[str]:
    """
    Public interface to find directories with paired files based on BLAST options.

    Args:
        folder_path (str): Path to the folder where subdirectories are to be searched.
        blast_option (str): BLAST option ('Blastnt', 'Blastnr', or 'Both').

    Returns:
        List[str]: A list of folder names within the specified folder that meet the criteria defined by
                the blast_option and contain paired files.
    """
    if not isinstance(folder_path, str):
        raise TypeError("folder_path must be a string.")
    # if blast_option not in ["Blastnt", "Blastnr", "Both"]:
    #     raise ValueError("blast_option must be 'Blastnt', 'Blastnr', or 'Both'.")

    return _find_gen_pair_files(folder_path, is_blastnr, is_blastnt, is_blastnt_nr)

def _find_gen_pair_files(folder_path: str, is_blastnr: bool, is_blastnt: bool, is_blastnt_nr) -> List[str]:
    """
    Internal helper function to find directories with paired files based on BLAST options.

    This function is a wrapper around find_gen_files with a specific file matching function
    tailored for paired files.

    Args:
        folder_path (str): Path to the folder where subdirectories are to be searched.
        blast_option (str): BLAST option ('Blastnt', 'Blastnr', or 'Both').

    Returns:
        List[str]: A list of folder names within the specified folder that meet the criteria defined by
                the blast_option and contain paired files.
    """
    return find_gen_files(folder_path, is_blastnr, is_blastnt, is_blastnt_nr, find_matching_reads_paired)

def find_num_gen_single_files(folder_path, is_blastnr: bool, is_blastnt: bool, is_blastnt_nr):
    return len(find_gen_files(folder_path, is_blastnr, is_blastnt, is_blastnt_nr, find_matching_reads_single))

def find_num_gen_pair_files(folder_path, is_blastnr: bool, is_blastnt: bool, is_blastnt_nr: bool):
    return len(find_gen_files(folder_path, is_blastnr, is_blastnt, is_blastnt_nr, find_matching_reads_paired))


def find_num_files_gen(folder_path, is_blastnr: bool, is_blastnt: bool, is_blastnt_nr: bool):
    return find_num_gen_single_files(folder_path, is_blastnr, is_blastnt, is_blastnt_nr), find_num_gen_pair_files(folder_path, is_blastnr, is_blastnt, is_blastnt_nr)