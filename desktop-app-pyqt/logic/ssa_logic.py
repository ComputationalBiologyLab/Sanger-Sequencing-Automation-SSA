"""Provide the logic for the automation for pipeline of sanger analysis .

This module allows usage of all the pipeline to work with GUI.

The module contains the following functions:


"""

import os
from Bio import SeqIO
from Bio.Blast import NCBIWWW
import tkinter as tk
import time
import concurrent.futures
import threading
from utils.ssa_utils import extract_filename, write_log
from utils.choosing_folder_utilts import *

import os
from Bio import SeqIO
from Bio.SeqRecord import SeqRecord
from Bio.Seq import Seq

from PyQt5.QtCore import QObject, pyqtSignal


from typing import Dict, Tuple
import signal
from threading import Thread, Event

import xml.etree.ElementTree as ET
import csv


total_num_samples = 0
num_finish = 0
thread_lock_num_finish = threading.Lock()
INTERVAL_TIME: int = 240 * 2
thread_lock_interval_time = threading.Lock()
last_thread_creation_time = time.time()
thread_lock_last_thread_creation_time = threading.Lock()

MAX_BLAST_REQUESTS_PER_DAY: int = 100  # The maximum number of BLAST requests allowed per day.
blast_req_sent: int = 0  # Counter for the number of BLAST requests sent in the current day.
start_time_day: float = time.time()  # Timestamp marking the start of the current day for tracking BLAST requests.
thread_lock_max_day: threading.Lock = threading.Lock()  # A lock to ensure thread-safe access to `blast_req_sent`.

is_mode_ab1 = True; # user can select folder either to have all ab1 or all fastq


failed_files = set()

files_with_error = []
class TimeoutException(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutException


signal.signal(signal.SIGALRM, timeout_handler)

def find_matching_reads_paired_proc(reads_folder:str, is_blastnr: bool, is_blastnt: bool, is_blast_both: bool, is_overwrite: bool, is_mode_ab1) -> Dict[str, Tuple[str, str]]: 
    """
    Public interface to find matching paired reads in a specified folder.

    This function checks input validity and then delegates the task of finding paired reads to the internal function `_find_matching_reads_paired_proc`.

    Args:
        reads_folder (str): Path to the folder containing read files.
        is_blastnr (bool): Indicates whether Blastnr processing is to be performed.
        is_blastnt (bool): Indicates whether Blastnt processing is to be performed.
        is_overwrite (bool): Flag to indicate whether existing processed files should be overwritten.

    Returns:
        Dict[str, Tuple[str, str]]: A dictionary mapping each sample name to a tuple of paths to the forward and reverse read files.

    Raises:
        ValueError: If `reads_folder` does not exist or is not a directory.
        TypeError: If `is_blastnr`, `is_blastnt`, or `is_overwrite` are not boolean values.

    Note:
        This is the function that should be called externally. The internal function `_find_matching_reads_paired_proc` is intended for internal use only.
    """
    if (not isinstance(reads_folder, str)):
        raise ValueError(f"The reads_folder must be str")
    if  not (os.path.exists(reads_folder) and os.path.isdir(reads_folder)):
        raise ValueError(f"The folder path: {reads_folder} doesn't exist or is not a directory. Please select a valid directory")
    if not isinstance(is_blastnr, bool):
        raise TypeError("is_blastnr must be a boolean value")
    if not isinstance(is_blastnt, bool):
        raise TypeError("is_blastnt must be a boolean value")
    if not isinstance(is_overwrite, bool):
        raise TypeError("is_overwrite must be a boolean value")
    if not isinstance(is_blast_both, bool):
        raise TypeError("is_blast_both must be a boolean value")
    if is_mode_ab1:
        return _find_matching_reads_paired_proc(reads_folder, is_blastnr, is_blastnt, is_blast_both, is_overwrite)
    else:
        return _find_matching_reads_paired_proc_fastq(reads_folder, is_blastnr, is_blastnt, is_blast_both, is_overwrite)

def _find_matching_reads_paired_proc(reads_folder:str, is_blastnr: bool, is_blastnt: bool, is_blast_both: bool, is_overwrite: bool) -> Dict[str, Tuple[str, str]]:
    """
    Internal function to find matching paired reads in the specified folder.

    This function searches for paired read files in the given folder, and pairs them based on sample names extracted from the file names.

    Args:
        reads_folder (str): Path to the folder containing read files.
        is_blastnr (bool): Indicates whether Blastnr processing is to be performed.
        is_blastnt (bool): Indicates whether Blastnt processing is to be performed.
        is_overwrite (bool): Flag to indicate whether existing processed files should be overwritten.

    Returns:
        Dict[str, Tuple[str, str]]: A dictionary mapping each sample name to a tuple of paths to the forward and reverse read files.
    """
    forward_reads: Dict[str, str] = {}
    reverse_reads: Dict[str, str] = {}
    blast_str: str = calc_blast_str(is_blastnr=is_blastnr, is_blastnt=is_blastnt, is_blast_both = is_blast_both)
    gen_folders: List[str] = find_gen_pair_files(reads_folder, is_blastnt = is_blastnt, is_blastnr = is_blastnr, is_blastnt_nr = is_blast_both)
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
            if is_overwrite or (not is_overwrite and sample_name not in gen_folders):
                matches[sample_name] = (forward_read, reverse_read)
            
    write_log("Paired files that are going to be processed: ", matches)
    return matches


def _find_matching_reads_paired_proc_fastq(reads_folder:str, is_blastnr: bool, is_blastnt: bool, is_blast_both: bool, is_overwrite: bool) -> Dict[str, Tuple[str, str]]:
    """
    Internal function to find matching paired reads in the specified folder.

    This function searches for paired read files in the given folder, and pairs them based on sample names extracted from the file names.

    Args:
        reads_folder (str): Path to the folder containing read files.
        is_blastnr (bool): Indicates whether Blastnr processing is to be performed.
        is_blastnt (bool): Indicates whether Blastnt processing is to be performed.
        is_overwrite (bool): Flag to indicate whether existing processed files should be overwritten.

    Returns:
        Dict[str, Tuple[str, str]]: A dictionary mapping each sample name to a tuple of paths to the forward and reverse read files.
    """
    forward_reads: Dict[str, str] = {}
    reverse_reads: Dict[str, str] = {}
    blast_str: str = calc_blast_str(is_blastnr=is_blastnr, is_blastnt=is_blastnt, is_blast_both = is_blast_both)
    gen_folders: List[str] = find_gen_pair_files(reads_folder, is_blastnt = is_blastnt, is_blastnr = is_blastnr, is_blastnt_nr = is_blast_both)
    for file_name in os.listdir(reads_folder):
        if  file_name.endswith("R.fastq"):
                sample_name = file_name[:-len("R.fastq")]
                reverse_reads[sample_name] = os.path.join(reads_folder, file_name)
        elif file_name.endswith("F.fastq"):
                sample_name = file_name[:-len("F.fastq")]
                forward_reads[sample_name] = os.path.join(reads_folder, file_name)

    matches = {}
    for sample_name in forward_reads:
        forward_read = forward_reads.get(sample_name)
        reverse_read = reverse_reads.get(sample_name)
        if forward_read and reverse_read:
            if is_overwrite or (not is_overwrite and sample_name not in gen_folders):
                matches[sample_name] = (forward_read, reverse_read)
            
    write_log("Paired files that are going to be processed: ", matches)
    return matches


def _find_matching_reads_paired_proc_fastq(reads_folder:str, is_blastnr: bool, is_blastnt: bool, is_blast_both: bool, is_overwrite: bool) -> Dict[str, Tuple[str, str]]:
    """
    Internal function to find matching paired reads in the specified folder.

    This function searches for paired read files in the given folder, and pairs them based on sample names extracted from the file names.

    Args:
        reads_folder (str): Path to the folder containing read files.
        is_blastnr (bool): Indicates whether Blastnr processing is to be performed.
        is_blastnt (bool): Indicates whether Blastnt processing is to be performed.
        is_overwrite (bool): Flag to indicate whether existing processed files should be overwritten.

    Returns:
        Dict[str, Tuple[str, str]]: A dictionary mapping each sample name to a tuple of paths to the forward and reverse read files.
    """
    forward_reads: Dict[str, str] = {}
    reverse_reads: Dict[str, str] = {}
    blast_str: str = calc_blast_str(is_blastnr=is_blastnr, is_blastnt=is_blastnt, is_blast_both = is_blast_both)
    gen_folders: List[str] = find_gen_pair_files(reads_folder, is_blastnt = is_blastnt, is_blastnr = is_blastnr, is_blastnt_nr = is_blast_both)
    for file_name in os.listdir(reads_folder):
        if  file_name.endswith("R.fastq"):
                sample_name = file_name[:-len("R.fastq")]
                reverse_reads[sample_name] = os.path.join(reads_folder, file_name)
        elif file_name.endswith("F.fastq"):
                sample_name = file_name[:-len("F.fastq")]
                forward_reads[sample_name] = os.path.join(reads_folder, file_name)

    matches = {}
    for sample_name in forward_reads:
        forward_read = forward_reads.get(sample_name)
        reverse_read = reverse_reads.get(sample_name)
        if forward_read and reverse_read:
            if is_overwrite or (not is_overwrite and sample_name not in gen_folders):
                matches[sample_name] = (forward_read, reverse_read)
            
    write_log("Paired files that are going to be processed: ", matches)
    return matches

    
def calc_blast_str(is_blastnr: bool, is_blastnt: bool, is_blast_both: bool) -> str:
    if is_blast_both and not is_blastnt  and not is_blastnr: return "Both"
    if is_blastnt and not is_blast_both and not is_blastnr: return "Blastnt"
    if is_blastnr and not is_blast_both and not is_blastnt: return "Blastnr"
    raise ValueError("The combinations for is_blastnr, is_blastnt, is_blast_both is not valid, only one must be True and all others must be False")


def convert_ab1_to_fastq_paired(forward_ab1: str, reverse_ab1: str, output_folder: str) -> Tuple[str, str]:
    """
    Wrapper function to convert paired AB1 files to FASTQ format.

    Args:
        forward_ab1 (str): Path to the forward AB1 file.
        reverse_ab1 (str): Path to the reverse AB1 file.
        output_folder (str): The output folder for the converted FASTQ files.

    Returns:
        Tuple[str, str]: Paths to the converted forward and reverse FASTQ files.

    Raises:
        ValueError: If the input file paths or output folder path are not valid.
    """
    if not (os.path.isfile(forward_ab1) and forward_ab1.endswith(".ab1")):
        raise ValueError(f"The forward AB1 file path is not valid: {forward_ab1}")
    
    if not (os.path.isfile(reverse_ab1) and reverse_ab1.endswith(".ab1")):
        raise ValueError(f"The reverse AB1 file path is not valid: {reverse_ab1}")

    if not (os.path.isdir(output_folder) and os.access(output_folder, os.W_OK)):
        raise ValueError(f"The output folder path is not valid or not writable: {output_folder}")
    return _convert_ab1_to_fastq_paired(forward_ab1, reverse_ab1, output_folder)

def _convert_ab1_to_fastq_paired(forward_ab1: str, reverse_ab1: str, output_folder: str) -> Tuple[str, str]:
    """Convert AB1 files to FASTQ format for paired-end reads.

    This function assumes that the input files are in the AB1 format and
    generates corresponding FASTQ files for forward and reverse reads.

    Args:
        forward_ab1 (str): Path to the forward AB1 file.
        reverse_ab1 (str): Path to the reverse AB1 file.
        output_folder (str): The output folder for the converted FASTQ files.

    Returns:
        Tuple[str, str]: Paths to the converted forward and reverse FASTQ files.
    """
    forward_fastq: str = os.path.join(output_folder, os.path.basename(forward_ab1[:-6] + "F.fastq"))
    reverse_fastq: str = os.path.join(output_folder, os.path.basename(reverse_ab1[:-6] + "R.fastq"))

    SeqIO.convert(forward_ab1, "abi", forward_fastq, "fastq")
    SeqIO.convert(reverse_ab1, "abi", reverse_fastq, "fastq")
    return forward_fastq, reverse_fastq


def reverse_complement(input_file: str, output_folder: str) -> str:
    """
    Generate the reverse complement of a FASTQ file.

    Args:
        input_file (str): Path to the input FASTQ file.
        output_folder (str): The output folder for the reverse complemented FASTQ file.

    Returns:
        str: Path to the reverse complemented FASTQ file.

    Raises:
        ValueError: If the input file path or output folder path are not valid.
    """
    # Validate input_file and output_folder
    if not (os.path.isfile(input_file) and input_file.lower().endswith((".fastq", ".fq"))):
        raise ValueError(f"The input file path is not a valid FASTQ file: {input_file}")
    
    if not (os.path.isdir(output_folder) and os.access(output_folder, os.W_OK)):
        raise ValueError(f"The output folder path is not valid or not writable: {output_folder}")

    return _reverse_complement(input_file, output_folder)

def _reverse_complement(input_file: str, output_folder: str) -> str:
    """Internal function to generate the reverse complement of a FASTQ file."""
    # Create the output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)

    # Create the output file path
    output_file: str = os.path.join(output_folder, os.path.basename(input_file[:-6] + "_RevComp.fastq"))

    # Read input FASTQ file, generate reverse complement, and write to output file
    with open(input_file, "r") as input_handle, open(output_file, "w") as output_handle:
        for record in SeqIO.parse(input_handle, "fastq"):
            reversed_seq = record.seq.reverse_complement()
            record.seq = reversed_seq
            SeqIO.write(record, output_handle, "fastq")
    write_log(f"File: {extract_filename(input_file)}, has finished reverse_complement")
    return output_file


def trim_fastq(input_file: str, output_folder: str) -> str:
    """
    Trim low-quality bases from a FASTQ file.

    Args:
        input_file (str): Path to the input FASTQ file.
        output_folder (str): The output folder for the trimmed FASTQ file.

    Returns:
        str: Path to the trimmed FASTQ file.

    Raises:
        ValueError: If the input file path or output folder path are not valid.
    """
    if not (os.path.isfile(input_file) and input_file.lower().endswith((".fastq", ".fq"))):
        raise ValueError(f"The input file path is not a valid FASTQ file: {input_file}")
    
    if not (os.path.isdir(output_folder) and os.access(output_folder, os.W_OK)):
        raise ValueError(f"The output folder path is not valid or not writable: {output_folder}")

    return _trim_fastq(input_file, output_folder)

def _trim_fastq(input_file: str, output_folder: str) -> str:
    """Internal function to trim low-quality bases from a FASTQ file."""
    os.makedirs(output_folder, exist_ok=True)
    # Create the output file path
    output_file: str = os.path.join(output_folder, os.path.basename(input_file[:-6] + "_Trimmed.fastq"))
    # Read input FASTQ file, trim low-quality bases, and write to output file
    with open(input_file, "r") as input_handle, open(output_file, "w") as output_handle:
        for record in SeqIO.parse(input_handle, "fastq"):
            # Adjust the trimming parameters as needed
            trimmed_seq = record.seq  # Modify this line based on your trimming logic
            trimmed_record = record.__class__(trimmed_seq, id=record.id, name=record.name, description=record.description,
                                            letter_annotations=record.letter_annotations)
            SeqIO.write(trimmed_record, output_handle, "fastq")
    return output_file



def run_merger(forward_file: str, reverse_file: str, output_folder: str) -> str:
    """
    Run a sequence merger to generate a consensus sequence.

    Args:
        forward_file (str): Path to the forward FASTQ file.
        reverse_file (str): Path to the reverse FASTQ file.
        output_folder (str): The output folder for the consensus sequence.

    Returns:
        str: Path to the consensus FASTA file.

    Raises:
        ValueError: If any of the input arguments are not valid.
    """
    # Validate input arguments
    if not (os.path.isfile(forward_file) and forward_file.lower().endswith((".fastq", ".fq"))):
        raise ValueError(f"The forward file path is not a valid FASTQ file: {forward_file}")

    if not (os.path.isfile(reverse_file) and reverse_file.lower().endswith((".fastq", ".fq"))):
        raise ValueError(f"The reverse file path is not a valid FASTQ file: {reverse_file}")

    if not (os.path.isdir(output_folder) and os.access(output_folder, os.W_OK)):
        raise ValueError(f"The output folder path is not valid or not writable: {output_folder}")

    return _run_merger(forward_file, reverse_file, output_folder)

def _run_merger(forward_file: str, reverse_file: str, output_folder: str) -> str:
    """Internal function to run a sequence merger and generate a consensus sequence."""
    # Create the output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)
    # Create the output file paths
    consensus_alignment_file = os.path.join(output_folder, os.path.basename(forward_file[:-6] + "_ConsensusAlignment.aln"))
    consensus_fasta_file = os.path.join(output_folder, os.path.basename(forward_file[:-6] + "_Consensus.fasta"))
    # Read forward and reverse FASTQ files
    forward_records = list(SeqIO.parse(forward_file, "fastq"))
    reverse_records = list(SeqIO.parse(reverse_file, "fastq"))
    # Merge sequences and create consensus FASTA file
    consensus_records = []
    for forward_record, reverse_record in zip(forward_records, reverse_records):
        consensus_seq = forward_record.seq + reverse_record.seq.reverse_complement()
        consensus_record = SeqRecord(consensus_seq, id=forward_record.id, description=forward_record.description)
        consensus_records.append(consensus_record)
    # Write consensus FASTA file
    with open(consensus_fasta_file, "w") as output_handle:
        SeqIO.write(consensus_records, output_handle, "fasta")
    write_log("Performed consensus sequence generation on file: ", extract_filename(forward_file))
    return consensus_fasta_file

def run_blast_pair(input_file: str, program: str, database: str, output_folder: str) -> str:
    """
    Run a BLAST search.

    Args:
        input_file (str): Path to the input FASTA file.
        program (str): The BLAST program (e.g., "blastn" or "blastx").
        database (str): The BLAST database (e.g., "nt" or "nr").
        output_folder (str): The output folder for BLAST results.

    Returns:
        str: Path to the BLAST results file in XML format.

    Raises:
        ValueError: If any of the input arguments are not valid.
    """
    # Validate input arguments
    write_log("in run_blast_pair [1]")
    # if not (os.path.isfile(input_file) and input_file.lower().endswith((".fasta", ".fa", ".fna"))):
    #     raise ValueError(f"The input file path is not a valid FASTA file: {input_file}")
    # write_log("in run_blast_pair [2]")
    # if program.lower() not in ["blastn", "blastx"]:
    #     raise ValueError(f"Invalid BLAST program: {program}. Supported programs are 'blastn' and 'blastx'.")
    # write_log("in run_blast_pair [3]")
    # if database.lower() not in ["nt", "nr"]:
    #     raise ValueError(f"Invalid BLAST database: {database}. Supported databases are 'nt' and 'nr'.")
    # write_log("in run_blast_pair [4]")
    # if not os.path.isdir(output_folder):
    #     raise ValueError(f"The output folder path is not valid: {output_folder}")
    write_log("in run_blast_pair [5]")
    return _run_blast_pair(input_file, program, database, output_folder)

def _run_blast_pair(input_file: str, program: str, database: str, output_folder: str) -> str:
    """
    Internal function to run a BLAST search.

    This function is responsible for performing the actual BLAST search based on the provided parameters.
    It is meant to be used internally and should not be called directly.

    Args:
        input_file (str): Path to the input FASTA file.
        program (str): The BLAST program (e.g., "blastn" or "blastx").
        database (str): The BLAST database (e.g., "nt" or "nr").
        output_folder (str): The output folder for BLAST results.

    Returns:
        str: Path to the BLAST results file in XML format.
    """
    write_log("in _run_blast_pair [1]")

    if is_send_blast():  # Am I allowed to send new blast request today?
        result_file = os.path.join(output_folder, f"blast_results_{database}.xml")
        input_record = SeqIO.read(input_file, format="fasta")
        sleep_for_interval_bet_reqs_if_necessay(input_file, "pair")
        write_log(f"(pair) File: {extract_filename(input_file)} will send qlblast request now")
        
        result_handle = None
        retry_count = 0
        max_retries = 1
        timeout = 30 * 60  # 7 minutes in seconds

        while retry_count < max_retries:
            result_event = Event()
            result_thread = Thread(target=lambda: result_event.set(NCBIWWW.qblast(program, database, input_record.format("fasta"))))

            result_thread.start()
            result_thread.join(timeout)

            if result_event.is_set():
                result_handle = result_event.get()
                break
            else:
                retry_count += 1
                write_log(f"Retrying BLAST request for {extract_filename(input_file)} (Attempt {retry_count}/{max_retries})")
                result_thread.join()  # Ensure thread is terminated before retrying

        if result_handle:
            confirm_blast_sent()
            write_log(f"(pair) File: {extract_filename(input_file)} got the results from qblast")
            with open(result_file, "w") as out_handle:
                out_handle.write(result_handle.read())
            result_handle.close()
            has_error, error_message = parse_blast_result(result_file)
            if has_error:
                store_error_details(input_file, program, database, output_folder, result_file, error_message, "pair")
            return result_file
        else:
            write_log(f"(pair) Failed to get BLAST results after {max_retries} attempts for file {extract_filename(input_file)}")
    else:
        return sleep_till_end_of_day_then_search_again_pair(input_file, program, database, output_folder)

def sleep_for_interval_bet_reqs_if_necessay(input_file: str, single_or_pair_txt: str)-> None:
    """
    Ensure a time interval between consecutive BLAST requests.

    This function checks the time elapsed since the last BLAST request and, if necessary, 
    puts the current thread to sleep to maintain a minimum interval between requests. 
    This is particularly useful when multiple threads are making BLAST requests 
    to avoid overloading the server or violating usage policies.

    Args:
        input_file (str): Path to the input FASTA file, used for logging purposes.

    Returns:
        None

    Note:
        This function assumes that the global variables `last_thread_creation_time` and `INTERVAL_TIME`
        are defined and accessible. It also uses a thread lock `thread_lock_interval_time` to 
        ensure thread-safe operations.

    Raises:
        None
    """
    write_log(f"({single_or_pair_txt}) File: {extract_filename(input_file)} is trying to get acccess to blast ")
    print("[1]")
    global thread_lock_interval_time
    global last_thread_creation_time
    print("[2]")
    with thread_lock_interval_time:
        print("[3]", time.time(), last_thread_creation_time, INTERVAL_TIME, time.time() - last_thread_creation_time, time.time() - last_thread_creation_time < INTERVAL_TIME)
        while time.time() - last_thread_creation_time < INTERVAL_TIME:
            print("[4]")
            time_since_last_thread = time.time() - last_thread_creation_time
            sleep_time = INTERVAL_TIME - time_since_last_thread
            write_log(f"(f{single_or_pair_txt}) File: {extract_filename(input_file)} will sleep for {sleep_time} seconds")
            # time.sleep(sleep_time)
            final_end_time = time.time() + sleep_time
            while time.time() < final_end_time:
                continue
                
            write_log(f"(f{single_or_pair_txt}) File: {extract_filename(input_file)} Woke up after {sleep_time} seconds")
        with thread_lock_last_thread_creation_time:
            last_thread_creation_time = time.time()  

def sleep_till_end_of_day_then_search_again_pair(input_file: str, program: str, database: str, output_folder: str) -> str:
    """
    Sleep until the end of the day, reset BLAST request counter, and restart the BLAST search.

    This function is invoked when the daily limit of BLAST requests has been reached. It calculates the remaining time
    until the end of the day, sleeps for that duration, resets the BLAST request counter, and then restarts the BLAST search.

    Args:
        input_file (str): Path to the input FASTA file.
        program (str): The BLAST program (e.g., "blastn" or "blastx").
        database (str): The BLAST database (e.g., "nt" or "nr").
        output_folder (str): The output folder for BLAST results.

    Returns:
        str: Path to the BLAST results file in XML format, generated after the reset and restart.

    Note:
        This function assumes that the global variables `blast_req_sent`, `MAX_BLAST_REQUESTS_PER_DAY`, 
        `start_time_day`, and `last_thread_creation_time` are defined and accessible.

    Raises:
        None
    """
    elapsed_time = time.time() - start_time_day
    period_to_sleep_day = max(24 * 3600 - elapsed_time, 0)
    write_log(f"A {blast_req_sent} requests have been sent, and I can't send more than {MAX_BLAST_REQUESTS_PER_DAY} requests, \
                        So I will sleep for the rest of the day. I will sleep for {period_to_sleep_day} seconds.")
    time.sleep(period_to_sleep_day)
    write_log(f"I need to wake up now, I will call reset_blast_sent()")
    # wake up
    reset_blast_sent()
    return run_blast_pair(input_file, program, database, output_folder)

def process_sample_paired(
    sample_name: str,
    forward_read: str,
    reverse_read: str,
    output_folder: str,
    update_pb: Callable,
    skip_middle_stages: bool,
    is_blastnr: bool,
    is_blastnt: bool,
    is_blastBoth: bool,
    is_mode_ab1: bool,
) -> None:
    """
    Process a paired-end sample, including conversion, trimming, merging, and BLAST.

    Args:
        sample_name (str): The name of the sample.
        forward_read (str): Path to the forward read file.
        reverse_read (str): Path to the reverse read file.
        output_folder (str): The output folder for sample processing.
        update_pb (Callable): Function to update the progress bar.
        skip_middle_stages (bool): Flag to skip intermediate processing stages.
        is_blastnr (bool): Flag indicating whether to perform BLASTn.
        is_blastnt (bool): Flag indicating whether to perform BLASTx.
        is_blastBoth (bool): Flag indicating whether to perform both BLASTn and BLASTx.

    Returns:
        None

    Raises:
        ValueError: If any of the input arguments are not valid.
    """
    # Validate input arguments
    if not all(os.path.exists(path) for path in [forward_read, reverse_read, output_folder]):
        raise ValueError("Invalid file paths. Ensure that all input files and output folders exist.")

    if not callable(update_pb):
        raise ValueError("The 'update_pb' parameter must be a callable function.")
    if not ((is_blastBoth and not is_blastnt  and not is_blastnr) or 
            (is_blastnt and not is_blastBoth and not is_blastnr) or 
            (is_blastnr and not is_blastnt  and not is_blastBoth)):
        raise ValueError("The combinations for is_blastnr, is_blastnt, is_blast_both is not valid, only one must be True and all others must be False")

    # Call the internal processing function
    
    if is_mode_ab1:
        _process_sample_paired(
            sample_name, forward_read, reverse_read, output_folder,
            update_pb, skip_middle_stages, is_blastnr, is_blastnt, is_blastBoth
        )
    else:
        print("before _process_sample_pairedJJJJJ", is_mode_ab1)
        _process_sample_paired_fastq(
            sample_name, forward_read, reverse_read, output_folder,
            update_pb, skip_middle_stages, is_blastnr, is_blastnt, is_blastBoth, is_mode_ab1
        )

def _process_sample_paired(
    sample_name: str,
    forward_read: str,
    reverse_read: str,
    output_folder: str,
    update_pb: Callable,
    skip_middle_stages: bool,
    is_blastnr: bool,
    is_blastnt: bool,
    is_blastBoth: bool
) -> None:
    """
    Process a paired-end sample, including conversion, trimming, merging, and BLAST.

    Args:
        sample_name (str): The name of the sample.
        forward_read (str): Path to the forward read file.
        reverse_read (str): Path to the reverse read file.
        output_folder (str): The output folder for sample processing.
        update_pb (Callable): Function to update the progress bar.
        skip_middle_stages (bool): Flag to skip intermediate processing stages.
        is_blastnr (bool): Flag for running BLAST with nr database.
        is_blastnt (bool): Flag for running BLAST with nt database.
        is_blastBoth (bool): Flag for running BLAST with both databases.

    Returns:
        None
    """
    write_log("(pair) process_sample_paired for {sample_name}", f"For skip parameter: {skip_middle_stages}")
    if skip_middle_stages:
        # blastnt_results_file, blastnr_results_file = process_sample_paired_no_middle_stage(is_blastnr, is_blastnt, is_blastBoth, forward_read, reverse_read, output_folder, update_pb)
        write_log("(pair) {sample_name} with no middle stage: it's like single, so it will be converted to single")
        blastnt_results_file, blastnr_results_file = process_sample_single(sample_name, forward_read, output_folder, update_pb, is_blastnr, is_blastnt, is_blastBoth, is_mode_ab1)
    else:
        blastnt_results_file, blastnr_results_file = process_sample_paired_middle_stage(sample_name, is_blastnr, is_blastnt, is_blastBoth, forward_read, reverse_read, output_folder, update_pb, is_mode_ab1)
        
    # refresh_gui(update_pb)
    write_log_process_pair_single_blast_results(is_blastnr, is_blastnt, is_blastBoth, blastnt_results_file, blastnr_results_file)
    
    
    
def _process_sample_paired_fastq(
    sample_name: str,
    forward_read: str,
    reverse_read: str,
    output_folder: str,
    update_pb: Callable,
    skip_middle_stages: bool,
    is_blastnr: bool,
    is_blastnt: bool,
    is_blastBoth: bool,
    is_mode_ab1: bool
) -> None:
    """
    Process a paired-end sample, including conversion, trimming, merging, and BLAST.

    Args:
        sample_name (str): The name of the sample.
        forward_read (str): Path to the forward read file.
        reverse_read (str): Path to the reverse read file.
        output_folder (str): The output folder for sample processing.
        update_pb (Callable): Function to update the progress bar.
        skip_middle_stages (bool): Flag to skip intermediate processing stages.
        is_blastnr (bool): Flag for running BLAST with nr database.
        is_blastnt (bool): Flag for running BLAST with nt database.
        is_blastBoth (bool): Flag for running BLAST with both databases.

    Returns:
        None
    """
    print("_process_sample_paired_fastqUUUU")
    write_log("(pair) process_sample_paired for {sample_name}", f"For skip parameter: {skip_middle_stages}")
    print("skip_middle_stages", skip_middle_stages)
    print("aka [5]")
    if skip_middle_stages:
        # blastnt_results_file, blastnr_results_file = process_sample_paired_no_middle_stage(is_blastnr, is_blastnt, is_blastBoth, forward_read, reverse_read, output_folder, update_pb)
        write_log("(pair) {sample_name} with no middle stage: it's like single, so it will be converted to single")
        blastnt_results_file, blastnr_results_file = process_sample_single(sample_name, forward_read, output_folder, update_pb, is_blastnr, is_blastnt, is_blastBoth, is_mode_ab1)
    else:
        blastnt_results_file, blastnr_results_file = process_sample_paired_middle_stage(sample_name, is_blastnr, is_blastnt, is_blastBoth, forward_read, reverse_read, output_folder, update_pb, is_mode_ab1)
        
    # refresh_gui(update_pb)
    write_log_process_pair_single_blast_results(is_blastnr, is_blastnt, is_blastBoth, blastnt_results_file, blastnr_results_file)
    

def process_sample_paired_no_middle_stage(
    is_blastnr: bool,
    is_blastnt: bool,
    is_blastBoth: bool,
    forward_read: str,
    reverse_read: str,
    output_folder: str,
    update_pb: Callable,
) -> Tuple[str, str]:
    """
    Process a paired-end sample without intermediate processing stages and run BLAST.

    Args:
        is_blastnr (bool): Flag for running BLAST with nr database.
        is_blastnt (bool): Flag for running BLAST with nt database.
        is_blastBoth (bool): Flag for running BLAST with both databases.
        forward_read (str): Path to the forward read file.
        reverse_read (str): Path to the reverse read file.
        output_folder (str): The output folder for sample processing.

    Returns:
        Tuple[str, str]: Paths to BLAST results files for nt and nr databases.
    """
    write_log("in process_sample_paired_no_middle_stage [1]")
    blastnt_results_file = ""
    blastnr_results_file = ""
    forward_file_input, _ = convert_ab1_to_fastq_paired(forward_read, reverse_read, output_folder)
    write_log("in process_sample_paired_no_middle_stage [2]", is_blastBoth, is_blastnr, is_blastnt)
    if is_blastBoth:
        blastnt_results_file = run_blast_pair(forward_file_input, "blastn", "nt", output_folder)
        refresh_gui(update_pb)
        blastnr_results_file = run_blast_pair(forward_file_input, "blastx", "nr", output_folder)
    elif is_blastnr:
        write_log("in process_sample_paired_no_middle_stage [3]")
        blastnr_results_file = run_blast_pair(forward_file_input, "blastx", "nr", output_folder)
        write_log("in process_sample_paired_no_middle_stage [4]")
    elif is_blastnt:
        blastnt_results_file = run_blast_pair(forward_file_input, "blastn", "nt", output_folder)
    write_log("in process_sample_paired_no_middle_stage [4]")
    refresh_gui(update_pb)
    return blastnt_results_file, blastnr_results_file

def process_sample_paired_middle_stage(
    sample_name: str,
    is_blastnr: bool,
    is_blastnt: bool,
    is_blastBoth: bool,
    forward_read: str,
    reverse_read: str,
    output_folder: str,
    update_pb: Callable,
    is_mode_ab1: bool
) -> Tuple[str, str]:
    """
    Process a paired-end sample with intermediate processing stages and run BLAST.

    Args:
        sample_name (str): The name of the sample.
        is_blastnr (bool): Flag for running BLAST with nr database.
        is_blastnt (bool): Flag for running BLAST with nt database.
        is_blastBoth (bool): Flag for running BLAST with both databases.
        forward_read (str): Path to the forward read file.
        reverse_read (str): Path to the reverse read file.
        output_folder (str): The output folder for sample processing.

    Returns:
        Tuple[str, str]: Paths to BLAST results files for nt and nr databases.
    """
    print("aka [6]")
    print("process_sample_paired_middle_stage")
    write_log("process_sample_paired_middle_stage")
    blastnt_results_file = ""
    blastnr_results_file = ""
    if is_mode_ab1:
        forward_file_input, reverse_file_input = convert_ab1_to_fastq_paired(forward_read, reverse_read, output_folder)
    else:
        print("forward_read", forward_read)
        forward_file_input = transform_file_path(forward_read)
        reverse_file_input = transform_file_path(reverse_read, "R")
        print("in fastq mode", forward_file_input, reverse_file_input)
    
    reverse_file_rc, forward_file_trimmed, reverse_file_trimmed, consensus_fasta_file = perform_middle_stage(forward_file_input, reverse_file_input, output_folder)
    print("aka [7]")
    if is_blastBoth:
        print("aka [8]")
        blastnt_results_file = run_blast_pair(consensus_fasta_file, "blastn", "nt", output_folder)
        print("aka [9]")
        refresh_gui(update_pb)
        blastnr_results_file = run_blast_pair(consensus_fasta_file, "blastx", "nr", output_folder)
    elif is_blastnr:
        blastnr_results_file = run_blast_pair(consensus_fasta_file, "blastx", "nr", output_folder)
    elif is_blastnt:
        blastnt_results_file = run_blast_pair(consensus_fasta_file, "blastn", "nt", output_folder)
    print("aka [10]")
    refresh_gui(update_pb)
    write_log_process_pair_no_skip_middle_stage(sample_name, forward_file_input, reverse_file_input, reverse_file_rc, forward_file_trimmed, reverse_file_trimmed, consensus_fasta_file)
    return blastnt_results_file, blastnr_results_file 

def perform_middle_stage(
    forward_file_input: str,
    reverse_file_input: str,
    output_folder: str
) -> Tuple[str, str, str, str]:
    """
    Perform intermediate processing stages for paired-end reads.

    This function performs the following stages:
    1. Reverse complement of the input reverse FASTQ file.
    2. Trimming of low-quality bases from the forward FASTQ file.
    3. Trimming of low-quality bases from the reverse complemented FASTQ file.
    4. Merging of the trimmed forward and reverse FASTQ files into a consensus FASTA file.

    Args:
        forward_file_input (str): Path to the input forward FASTQ file.
        reverse_file_input (str): Path to the input reverse FASTQ file.
        output_folder (str): The output folder for the processed files.

    Returns:
        Tuple[str, str, str, str]: Paths to the processed files in the following order:
            - Path to the reverse complemented FASTQ file.
            - Path to the trimmed forward FASTQ file.
            - Path to the trimmed reverse FASTQ file.
            - Path to the consensus FASTA file.

    Example:
        reverse_file_rc, forward_file_trimmed, reverse_file_trimmed, consensus_fasta_file = perform_middle_stage(
            "/path/to/forward.fastq",
            "/path/to/reverse.fastq",
            "/path/to/output_folder"
        )
    """
    reverse_file_rc = reverse_complement(reverse_file_input, output_folder)
    forward_file_trimmed = trim_fastq(forward_file_input, output_folder)
    reverse_file_trimmed = trim_fastq(reverse_file_rc, output_folder)
    consensus_fasta_file = run_merger(forward_file_trimmed, reverse_file_trimmed, output_folder)
    return reverse_file_rc, forward_file_trimmed, reverse_file_trimmed, consensus_fasta_file


def write_log_process_pair_no_skip_middle_stage(
    sample_name: str,
    forward_file_input: str,
    reverse_file_input: str,
    reverse_file_rc: str,
    forward_file_trimmed: str,
    reverse_file_trimmed: str,
    consensus_fasta_file: str
) -> None:
    """
    Write log information for paired-end sample processing without skipping middle stages.

    Args:
        sample_name (str): The name of the sample.
        forward_file_input (str): Path to the original forward FASTQ file.
        reverse_file_input (str): Path to the original reverse FASTQ file.
        reverse_file_rc (str): Path to the reverse complemented FASTQ file.
        forward_file_trimmed (str): Path to the trimmed forward FASTQ file.
        reverse_file_trimmed (str): Path to the trimmed reverse FASTQ file.
        consensus_fasta_file (str): Path to the consensus FASTA file.

    Returns:
        None

    Example:
        write_log_process_pair_no_skip_middle_stage(
            "Sample001",
            "/path/to/forward_original.fastq",
            "/path/to/reverse_original.fastq",
            "/path/to/reverse_complemented.fastq",
            "/path/to/forward_trimmed.fastq",
            "/path/to/reverse_trimmed.fastq",
            "/path/to/consensus.fasta"
        )
    """
    write_log("Sample:", sample_name)
    write_log("Forward Fastq:", forward_file_input)
    write_log("Reverse Fastq:", reverse_file_input)
    write_log("Reverse Complemented Fastq:", reverse_file_rc)
    write_log("Trimmed Forward Fastq:", forward_file_trimmed)
    write_log("Trimmed Reverse Fastq:", reverse_file_trimmed)
    write_log("Consensus FASTA File:", consensus_fasta_file)
    
def write_log_process_pair_single_blast_results(
    is_blastnr: bool,
    is_blastnt: bool,
    is_blastBoth: bool,
    blastnt_results_file: str,
    blastnr_results_file: str
) -> None:
    """
    Write log information for BLAST results of a paired-end sample.

    Args:
        is_blastnr (bool): Flag indicating whether BLASTnr was performed.
        is_blastnt (bool): Flag indicating whether BLASTnt was performed.
        is_blastBoth (bool): Flag indicating whether both BLASTnt and BLASTnr were performed.
        blastnt_results_file (str): Path to the BLASTnt results file.
        blastnr_results_file (str): Path to the BLASTnr results file.

    Returns:
        None

    Example:
        write_log_process_pair_single_blast_results(
            is_blastnr=True,
            is_blastnt=False,
            is_blastBoth=False,
            blastnt_results_file="/path/to/blastnt_results.xml",
            blastnr_results_file="/path/to/blastnr_results.xml"
        )
    """
    if is_blastBoth:
        write_log("BLASTnt Results File:", blastnt_results_file)
        write_log("BLASTnr Results File:", blastnr_results_file)
    elif is_blastnr:
        write_log("BLASTnr Results File:", blastnr_results_file)
    elif is_blastnt:
        write_log("BLASTnt Results File:", blastnt_results_file)

def process_samples_folder_paired(
    samples_folder: str,
    update_pb: Callable,
    skip_middle_stages: bool,
    is_blastnr: bool,
    is_blastnt: bool,
    is_blastBoth: bool,
    is_overwrite: bool,
    is_mode_ab1: bool,
) -> None:
    """
    Process a folder of paired-end samples.

    Args:
        samples_folder (str): Path to the folder containing paired-end samples.
        update_pb (Callable): Function to update the progress bar.
        skip_middle_stages (bool): Flag to skip intermediate processing stages.
        is_blastnr (bool): Flag indicating whether to perform BLASTn.
        is_blastnt (bool): Flag indicating whether to perform BLASTx.
        is_blastBoth (bool): Flag indicating whether to perform both BLASTn and BLASTx.
        is_overwrite (bool): Flag indicating whether to overwrite existing files.

    Returns:
        None

    Raises:
        ValueError: If any of the input arguments are not valid.
    """
    # Validate input arguments
    if not (os.path.exists(samples_folder) and os.path.isdir(samples_folder)):
        raise ValueError(f"The samples_folder path is not valid: {samples_folder}")

    if not callable(update_pb):
        raise ValueError("The 'update_pb' parameter must be a callable function.")
    
    if not ((is_blastBoth and not is_blastnt  and not is_blastnr) or 
            (is_blastnt and not is_blastBoth and not is_blastnr) or 
            (is_blastnr and not is_blastnt  and not is_blastBoth)):
        raise ValueError("The combinations for is_blastnr, is_blastnt, is_blast_both is not valid, only one must be True and all others must be False")
    print("process_samples_folder_paired", is_mode_ab1)
    if is_mode_ab1:
        return _process_samples_folder_paired(samples_folder, update_pb, skip_middle_stages, is_blastnr, is_blastnt, is_blastBoth, is_overwrite)
    else:
        return _process_samples_folder_paired_fastq(samples_folder, update_pb, skip_middle_stages, is_blastnr, is_blastnt, is_blastBoth, is_overwrite, is_mode_ab1)

def _process_samples_folder_paired(samples_folder, update_pb, skip_middle_stages, is_blastnr, is_blastnt, is_blastBoth, is_overwrite):
    """Process a folder of paired-end samples.

    Args:
        samples_folder (str): Path to the folder containing paired-end samples.
        update_pb (function): Function to update the progress bar.
        skip_middle_stages (bool): Flag to skip intermediate processing stages.

    Returns:
        None
    """
    write_log("process_samples_folder_paired")
    reads = find_matching_reads_paired_proc(samples_folder, is_blastnr, is_blastnt, is_blastBoth, is_overwrite)
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = []
        for sample_name, (forward_read, reverse_read) in reads.items():
            sample_output_folder = os.path.join(samples_folder, sample_name)
            os.makedirs(sample_output_folder, exist_ok=True)
            future = executor.submit(process_sample_paired, sample_name, forward_read, reverse_read, sample_output_folder, update_pb, skip_middle_stages, is_blastnr, is_blastnt, is_blastBoth)
            futures.append(future)
        concurrent.futures.wait(futures)
    write_log("Finished all paired files")
    
def _process_samples_folder_paired_fastq(samples_folder, update_pb, skip_middle_stages, is_blastnr, is_blastnt, is_blastBoth, is_overwrite, is_mode_ab1):
    """Process a folder of paired-end samples.

    Args:
        samples_folder (str): Path to the folder containing paired-end samples.
        update_pb (function): Function to update the progress bar.
        skip_middle_stages (bool): Flag to skip intermediate processing stages.

    Returns:
        None
    """
    write_log("process_samples_folder_single. Mode AB1? ", is_mode_ab1)
    print("aka [4]")
    reads = find_matching_reads_paired_proc(samples_folder, is_blastnr, is_blastnt, is_blastBoth, is_overwrite, is_mode_ab1)
    print("reads unique pair ", reads)
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = []
        for sample_name, (forward_read, reverse_read) in reads.items():
            sample_output_folder = os.path.join(samples_folder, sample_name)
            os.makedirs(sample_output_folder, exist_ok=True)
            future = executor.submit(process_sample_paired, sample_name, forward_read, reverse_read, sample_output_folder, update_pb, skip_middle_stages, is_blastnr, is_blastnt, is_blastBoth, is_mode_ab1)
            futures.append(future)
        concurrent.futures.wait(futures)
    write_log("Finished all paired files")

        
################################################################
################################################################
################################################################
################################ Single
################################################################
################################################################
################################################################    

def find_matching_reads_single_proc(
    reads_folder: str,
    is_blastnr: bool,
    is_blastnt: bool,
    is_blastBoth: bool,
    is_overwrite: bool,
    is_mode_ab1: bool
) -> Dict[str, str]:
    """
    Find matching single reads in the specified folder and perform BLAST analysis based on specified flags.

    This function validates the input arguments to ensure only one of the BLAST-related flags (is_blastnr, is_blastnt, is_blastBoth) is set to True. It raises a ValueError if the input combination is not valid.

    Args:
        reads_folder (str): The folder containing the read files.
        is_blastnr (bool): Flag indicating whether to perform BLASTn.
        is_blastnt (bool): Flag indicating whether to perform BLASTx.
        is_blastBoth (bool): Flag indicating whether to perform both BLASTn and BLASTx.
        is_overwrite (bool): Flag indicating whether to overwrite existing files.

    Returns:
        Dict[str, str]: A dictionary mapping sample names to single read files.

    Raises:
        ValueError: If more than one BLAST-related flag is set to True or all are set to False.
    """

    # Validate BLAST flags
    blast_flags = [is_blastnr, is_blastnt, is_blastBoth]
    if blast_flags.count(True) != 1:
        raise ValueError("Invalid combination of BLAST flags. Only one of 'is_blastnr', 'is_blastnt', or 'is_blastBoth' should be True.")
    if not os.path.isdir(reads_folder):
        raise ValueError(f"The provided 'reads_folder' is not a valid directory: {reads_folder}")
    print("is_mode_ab1", is_mode_ab1)
    if is_mode_ab1:
        return _find_matching_reads_single_proc(reads_folder, is_blastnr, is_blastnt, is_blastBoth, is_overwrite)
    else:
        return _find_matching_reads_single_proc_fastq(reads_folder, is_blastnr, is_blastnt, is_blastBoth, is_overwrite)

def _find_matching_reads_single_proc(
    reads_folder: str,
    is_blastnr: bool,
    is_blastnt: bool,
    is_blastBoth: bool,
    is_overwrite: bool,
) -> Dict[str, str]:
    """
    Internal function for finding matching single reads in the specified folder.

    Args:
        reads_folder (str): The folder containing the read files.
        is_blastnr (bool): Flag indicating whether to perform BLASTn.
        is_blastnt (bool): Flag indicating whether to perform BLASTx.
        is_blastBoth (bool): Flag indicating whether to perform both BLASTn and BLASTx.
        is_overwrite (bool): Flag indicating whether to overwrite existing files.

    Returns:
        Dict[str, str]: A dictionary mapping sample names to single read files.
    """
    forward_reads = {}
    reverse_reads = {}
    print("FFROM here",  is_blastnr, is_blastnt, is_blastBoth)
    gen_folders = find_gen_single_files(reads_folder, is_blastnr, is_blastnt, is_blastBoth, is_mode_ab1 = True)
    for file_name in os.listdir(reads_folder):
        print("New file_name", file_name)
        if file_name.endswith("_R.ab1"):
            sample_name = file_name[:-len("_R.ab1")]
            reverse_reads[sample_name] = os.path.join(reads_folder, file_name)
        elif file_name.endswith("_F.ab1"):
            sample_name = file_name[:-len("_F.ab1")]
            forward_reads[sample_name] = os.path.join(reads_folder, file_name)

    matches = {}
    write_log("gen_folders", gen_folders)
    for sample_name, forward_read in forward_reads.items():
        write_log(sample_name, "sample_name not in reverse_reads:", sample_name not in reverse_reads)
        if sample_name not in reverse_reads:
            write_log("is_overwrite", is_overwrite, "sample_name not in gen_folders", sample_name not in gen_folders, "(not is_overwrite and sample_name not in gen_folders)", (not is_overwrite and sample_name not in gen_folders) )
            if is_overwrite or (not is_overwrite and sample_name not in gen_folders):
                matches[sample_name] = forward_read
    write_log(f"in folder {reads_folder}")
    write_log("forward_reads", forward_reads)
    write_log("reverse_reads", reverse_reads)
    write_log("files that are single that are going to be processed: ", matches)
    return matches



def _find_matching_reads_single_proc_fastq(
    reads_folder: str,
    is_blastnr: bool,
    is_blastnt: bool,
    is_blastBoth: bool,
    is_overwrite: bool,
) -> Dict[str, str]:
    """
    Internal function for finding matching single reads in the specified folder.

    Args:
        reads_folder (str): The folder containing the read files.
        is_blastnr (bool): Flag indicating whether to perform BLASTn.
        is_blastnt (bool): Flag indicating whether to perform BLASTx.
        is_blastBoth (bool): Flag indicating whether to perform both BLASTn and BLASTx.
        is_overwrite (bool): Flag indicating whether to overwrite existing files.

    Returns:
        Dict[str, str]: A dictionary mapping sample names to single read files.
    """
    forward_reads = {}
    reverse_reads = {}
    print("FFROM here",  is_blastnr, is_blastnt, is_blastBoth)
    gen_folders = find_gen_single_files(reads_folder, is_blastnr, is_blastnt, is_blastBoth, is_mode_ab1 = False)
    print("in _find_matching_reads_single_proc_fastq", os.listdir(reads_folder))
    for file_name in os.listdir(reads_folder):
        print("New file_name", file_name)
        if file_name.endswith("R.fastq"):
            sample_name = file_name[:-len("R.fastq")]
            reverse_reads[sample_name] = os.path.join(reads_folder, file_name)
        elif file_name.endswith("F.fastq"):
            sample_name = file_name[:-len("F.fastq")]
            forward_reads[sample_name] = os.path.join(reads_folder, file_name)

    matches = {}
    write_log("gen_folders", gen_folders)
    for sample_name, forward_read in forward_reads.items():
        write_log(sample_name, "sample_name not in reverse_reads:", sample_name not in reverse_reads)
        if sample_name not in reverse_reads:
            write_log("is_overwrite", is_overwrite, "sample_name not in gen_folders", sample_name not in gen_folders, "(not is_overwrite and sample_name not in gen_folders)", (not is_overwrite and sample_name not in gen_folders) )
            if is_overwrite or (not is_overwrite and sample_name not in gen_folders):
                matches[sample_name] = forward_read
    write_log(f"in folder {reads_folder}")
    write_log("forward_reads", forward_reads)
    write_log("reverse_reads", reverse_reads)
    write_log("files that are single that are going to be processed: ", matches)
    return matches

def convert_ab1_to_fastq_single(forward_ab1: str, output_folder: str) -> Tuple[str, str]:
    """
    Wrapper function to convert sing AB1 files to FASTQ format.

    Args:
        forward_ab1 (str): Path to the forward AB1 file.
        output_folder (str): The output folder for the converted FASTQ files.

    Returns:
        Tuple[str, str]: Paths to the converted forward and reverse FASTQ files.

    Raises:
        ValueError: If the input file paths or output folder path are not valid.
    """
    if not (os.path.isfile(forward_ab1) and forward_ab1.endswith(".ab1")):
        raise ValueError(f"The forward AB1 file path is not valid: {forward_ab1}")
    if not (os.path.isdir(output_folder) and os.access(output_folder, os.W_OK)):
        raise ValueError(f"The output folder path is not valid or not writable: {output_folder}")
    return _convert_ab1_to_fastq_single(forward_ab1, output_folder)



def _convert_ab1_to_fastq_single(forward_ab1, output_folder):
    """
    Internal function to convert AB1 files to FASTQ format for paired-end reads.

    Args:
        forward_ab1 (str): Path to the forward AB1 file.
        reverse_ab1 (str): Path to the reverse AB1 file.
        output_folder (str): The output folder for the converted FASTQ files.

    Returns:
        Tuple[str, str]: Paths to the converted forward and reverse FASTQ files.
    """
    forward_fastq = os.path.join(output_folder, os.path.basename(forward_ab1[:-6] + "F.fastq"))
    SeqIO.convert(forward_ab1, "abi", forward_fastq, "fastq")
    return forward_fastq


def convert_fastq_to_fasta(input_file: str, output_folder: str) -> str:
    """
    Convert a FASTQ file to FASTA format.

    Args:
        input_file (str): Path to the input FASTQ file.
        output_folder (str): The output folder for the converted FASTA file.

    Returns:
        str: Path to the converted FASTA file.

    Raises:
        ValueError: If the input file path is not valid or the output folder is not writable.
    """
    # Validate input file
    if not os.path.isfile(input_file):
        raise ValueError(f"The input file does not exist: {input_file}")
    if not input_file.lower().endswith(".fastq"):
        raise ValueError(f"The input file is not a FASTQ file: {input_file}")

    # Validate output folder
    if not os.path.isdir(output_folder):
        raise ValueError(f"The output folder does not exist: {output_folder}")
    if not os.access(output_folder, os.W_OK):
        raise ValueError(f"The output folder is not writable: {output_folder}")

    return _convert_fastq_to_fasta(input_file, output_folder)


def _convert_fastq_to_fasta(input_file, output_folder):
    """
    Internal function to convert a FASTQ file to FASTA format.

    Args:
        input_file (str): Path to the input FASTQ file.
        output_folder (str): The output folder for the converted FASTA file.

    Returns:
        str: Path to the converted FASTA file.
    """
    output_file = os.path.join(output_folder, os.path.basename(input_file[:-6] + ".fasta"))
    SeqIO.convert(input_file, "fastq", output_file, "fasta")
    return output_file

def run_blast_single(
    input_file: str,
    program: str,
    database: str,
    output_folder: str
) -> str:
    """
    Process a single-end sample, including conversion, trimming, and BLAST.

    Args:
        input_file (str): Path to the input FASTA file.
        program (str): The BLAST program (e.g., "blastn" or "blastx").
        database (str): The BLAST database (e.g., "nt" or "nr").
        output_folder (str): The output folder for BLAST results.

    Returns:
        str: Path to the BLAST results file in XML format.

    Raises:
        ValueError: If any of the input arguments are not valid.
    """
    # Validate input arguments
    if not (os.path.isfile(input_file) and input_file.lower().endswith((".fasta", ".fa", ".fna"))):
        raise ValueError(f"The input file path is not a valid FASTA file: {input_file}")

    if program.lower() not in ["blastn", "blastx"]:
        raise ValueError(f"Invalid BLAST program: {program}. Supported programs are 'blastn' and 'blastx'.")

    if database.lower() not in ["nt", "nr"]:
        raise ValueError(f"Invalid BLAST database: {database}. Supported databases are 'nt' and 'nr'.")

    if not os.path.isdir(output_folder):
        raise ValueError(f"The output folder path is not valid: {output_folder}")

    return _run_blast_single(input_file, program, database, output_folder)

class TimeoutException(Exception):
    pass

def _run_blast_single(input_file: str, program: str, database: str, output_folder: str) -> str:
    """
    Internal function to perform BLAST for a single-end sample.

    Args:
        input_file (str): Path to the input FASTA file.
        program (str): The BLAST program (e.g., "blastn" or "blastx").
        database (str): The BLAST database (e.g., "nt" or "nr").
        output_folder (str): The output folder for BLAST results.

    Returns:
        str: Path to the BLAST results file in XML format.
    """
    global last_thread_creation_time
    result_file = os.path.join(output_folder, f"blast_results_{database}.xml")
    input_record = SeqIO.read(input_file, format="fasta")

    write_log(f"(single) File: {extract_filename(input_file)} is trying to get access to send blast reqest from single")
    if is_send_blast(): # Am I allowed to send new blast request today? Hint, I can't send more than the MAX_BLAST_REQUESTS_PER_DAY as not to get banned from NCBI itself.
        sleep_for_interval_bet_reqs_if_necessay(input_file,"single")  
        write_log(f"(single) File: {extract_filename(input_file)} will send qlblast reqest now")
        result_handle = NCBIWWW.qblast(program, database, input_record.format("fasta"))
        confirm_blast_sent()
        write_log(f"(single) File: {extract_filename(input_file)} got the results from qblast")
        with open(result_file, "w") as out_handle:
            out_handle.write(result_handle.read())
        result_handle.close()

        has_error, error_message = parse_blast_result(result_file)
        if has_error:
            store_error_details(input_file, program, database, output_folder, result_file, error_message, "single")
        return result_file
    else:
        return sleep_till_end_of_day_then_search_again_single(input_file, program, database, output_folder)


def parse_blast_result(file_path):
    """
    Parse the BLAST XML result file to check for errors.

    Args:
        file_path (str): Path to the BLAST result XML file.

    Returns:
        bool: True if an error is found, otherwise False.
        str: Error message if any.
    """
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()

        # Check for Iteration_message that indicates an error
        iteration_message = root.find(".//Iteration_message")
        if iteration_message is not None:
            return True, iteration_message.text
        else:
            return False, ""
    except ET.ParseError:
        print(f"Error parsing XML file: {file_path}")
        return True, "XML Parsing Error"


def store_error_details(input_file, program, database, output_folder, result_file, error_message, function_to_be_called):
    """
    Store error details for files that encountered an error during BLAST.

    Args:
        input_file (str): Path to the input FASTA file.
        result_file (str): Path to the BLAST result XML file.
        error_message (str): The error message.
        :param database:
    """
    # Folder name is the name of the file (based on your structure)
    folder_name = os.path.basename(os.path.dirname(input_file))
    ab1_file = os.path.join(os.path.dirname(input_file), f"{folder_name}.ab1")

    # Create a summary dictionary to store information
    error_details = {
        'input_file': input_file,
        'program': program,
        'database': database,
        'output_folder': output_folder,
        'result_file': result_file,
        'error_message': error_message,
        'num_trials': 1,
        'function_to_be_called': function_to_be_called
    }
    files_with_error.append(error_details)


def sleep_till_end_of_day_then_search_again_single(input_file: str, program: str, database: str, output_folder: str) -> str:
    """
    Sleep until the end of the day, reset BLAST request counter, and restart the BLAST search.

    This function is invoked when the daily limit of BLAST requests has been reached. It calculates the remaining time
    until the end of the day, sleeps for that duration, resets the BLAST request counter, and then restarts the BLAST search.

    Args:
        input_file (str): Path to the input FASTA file.
        program (str): The BLAST program (e.g., "blastn" or "blastx").
        database (str): The BLAST database (e.g., "nt" or "nr").
        output_folder (str): The output folder for BLAST results.

    Returns:
        str: Path to the BLAST results file in XML format, generated after the reset and restart.

    Note:
        This function assumes that the global variables `blast_req_sent`, `MAX_BLAST_REQUESTS_PER_DAY`, 
        `start_time_day`, and `last_thread_creation_time` are defined and accessible.

    Raises:
        None
    """
    elapsed_time = time.time() - start_time_day
    period_to_sleep_day = max(24 * 3600 - elapsed_time, 0)
    write_log(f"A {blast_req_sent} requests have been sent, and I can't send more than {MAX_BLAST_REQUESTS_PER_DAY} requests, \
                        So I will sleep for the rest of the day. I will sleep for {period_to_sleep_day} seconds.")
    time.sleep(period_to_sleep_day)
    write_log(f"I need to wake up now, I will call reset_blast_sent()")
    # wake up
    reset_blast_sent()
    return run_blast_single(input_file, program, database, output_folder)




def process_sample_single(
    sample_name: str,
    forward_read: str,
    output_folder: str,
    update_pb: Callable,
    is_blastnr: bool,
    is_blastnt: bool,
    is_blastBoth: bool,
    is_mode_ab1: bool,
) -> None:
    """
    Process a single-end sample, including conversion to FASTQ, trimming, and BLAST analysis.

    Args:
        sample_name (str): The name of the sample.
        forward_read (str): Path to the forward read AB1 file.
        output_folder (str): The output folder for sample processing.
        update_pb (Callable): Function to update the progress bar.
        is_blastnr (bool): Flag to indicate if BLASTx against 'nr' database should be performed.
        is_blastnt (bool): Flag to indicate if BLASTn against 'nt' database should be performed.
        is_blastBoth (bool): Flag to indicate if both BLASTx and BLASTn should be performed.

    Raises:
        ValueError: If any of the input arguments are not valid.
    """
    # Validate input arguments
    if not os.path.isfile(forward_read):
        raise ValueError(f"The forward read file path is not valid: {forward_read}")
    if not os.path.isdir(output_folder):
        raise ValueError(f"The output folder path is not valid: {output_folder}")
    if not isinstance(is_blastnr, bool) or not isinstance(is_blastnt, bool) or not isinstance(is_blastBoth, bool):
        raise ValueError("is_blastnr, is_blastnt, and is_blastBoth must be boolean values.")
    print("HEX [6]", is_mode_ab1)
    if is_mode_ab1:
        print("HEX [7]")
        return _process_sample_single(sample_name, forward_read, output_folder, update_pb, is_blastnr, is_blastnt, is_blastBoth)
    else:
        print("HEX [8]", sample_name, forward_read, output_folder)
        return _process_sample_single_fastq(sample_name, forward_read, output_folder, update_pb, is_blastnr, is_blastnt, is_blastBoth)


def _process_sample_single(
    sample_name: str,
    forward_read: str,
    output_folder: str,
    update_pb: Callable,
    is_blastnr: bool,
    is_blastnt: bool,
    is_blastBoth: bool
) -> None:
    """Process a single-end sample, including conversion, trimming, and BLAST.

    Args:
        sample_name (str): The name of the sample.
        forward_read (str): Path to the forward read file.
        output_folder (str): The output folder for sample processing.
        update_pb (function): Function to update the progress bar.

    Returns:
        None
    """
    print("HEX [9]")
    forward_file_input = convert_ab1_to_fastq_single(forward_read, output_folder)
    forward_file_trimmed = trim_fastq(forward_file_input, output_folder)
    forward_file_fasta = convert_fastq_to_fasta(forward_file_trimmed, output_folder)
    if is_blastBoth:
        blastnr_results_file = run_blast_single(forward_file_fasta, "blastx", "nr", output_folder)
        refresh_gui(update_pb)
        blastnt_results_file = run_blast_single(forward_file_fasta, "blastn", "nt", output_folder)
    elif is_blastnr:
        blastnr_results_file = run_blast_single(forward_file_fasta, "blastx", "nr", output_folder)
    else:
        blastnt_results_file = run_blast_single(forward_file_fasta, "blastn", "nt", output_folder)
        
    refresh_gui(update_pb)
    write_log("Sample:", sample_name)
    write_log("Forward Fastq:", forward_file_input)
    write_log("Trimmed Forward Fastq:", forward_file_trimmed)
    write_log("Forward FASTA:", forward_file_fasta)
    write_log_process_pair_single_blast_results(is_blastnr, is_blastnt, is_blastBoth, blastnt_results_file, blastnr_results_file)
        
 
 
def transform_file_path(forward_file_input: str, pre = "F") -> str:
    base_dir = os.path.dirname(forward_file_input)
    file_name = os.path.basename(forward_file_input)
    sample_name = file_name.split(f'{pre}.fastq')[0]
    new_dir = os.path.join(base_dir, sample_name)
    new_file_path = os.path.join(new_dir, file_name)
    return new_file_path


def _process_sample_single_fastq(
    sample_name: str,
    forward_file_input: str,
    output_folder: str,
    update_pb: Callable,
    is_blastnr: bool,
    is_blastnt: bool,
    is_blastBoth: bool
) -> None:
    """Process a single-end sample, including conversion, trimming, and BLAST.

    Args:
        sample_name (str): The name of the sample.
        forward_read (str): Path to the forward read file.
        output_folder (str): The output folder for sample processing.
        update_pb (function): Function to update the progress bar.
        forward_file_input: the fastq file
    Returns:
        None
    """
    print("HEX [9]")
    print("HEX [10]", forward_file_input, output_folder)
    forward_file_trimmed = trim_fastq(forward_file_input, output_folder)
    print("HEX [11]")
    forward_file_fasta = convert_fastq_to_fasta(forward_file_trimmed, output_folder)
    print("HEX [12]")
    if is_blastBoth:
        print("HEX [14]")
        blastnr_results_file = run_blast_single(forward_file_fasta, "blastx", "nr", output_folder)
        refresh_gui(update_pb)
        blastnt_results_file = run_blast_single(forward_file_fasta, "blastn", "nt", output_folder)
    elif is_blastnr:
        print("HEX [15]")
        blastnr_results_file = run_blast_single(forward_file_fasta, "blastx", "nr", output_folder)
    else:
        print("HEX [16]")
        blastnt_results_file = run_blast_single(forward_file_fasta, "blastn", "nt", output_folder)
        
    refresh_gui(update_pb)
    write_log("Sample:", sample_name)
    write_log("Forward Fastq:", forward_file_input)
    write_log("Trimmed Forward Fastq:", forward_file_trimmed)
    write_log("Forward FASTA:", forward_file_fasta)
    write_log_process_pair_single_blast_results(is_blastnr, is_blastnt, is_blastBoth, blastnt_results_file, blastnr_results_file)
        
 

def process_samples_folder_single(
    samples_folder: str,
    update_pb: Callable,
    is_blastnr: bool,
    is_blastnt: bool,
    is_blastBoth: bool,
    is_overwrite: bool,
    is_mode_ab1: bool
) -> None:
    """
    Process all single-end samples within a specified folder.

    This function scans a given directory for sample files and processes each sample
    using the `process_sample_single` function. It utilizes multithreading for efficient processing.

    Args:
        samples_folder (str): Directory path containing sample files.
        update_pb (Callable, optional): Function to update the progress bar.
        is_blastnr (bool, optional): Flag to perform BLASTx analysis.
        is_blastnt (bool, optional): Flag to perform BLASTn analysis.
        is_blastBoth (bool, optional): Flag to perform both BLASTx and BLASTn analysis.
        is_overwrite (bool, optional): Flag to indicate whether to overwrite existing results.

    Returns:
        None

    Raises:
        ValueError: If the samples folder path is not valid.
    """
    # Validate input arguments
    # Validate input arguments
    if not (os.path.exists(samples_folder) and os.path.isdir(samples_folder)):
        raise ValueError(f"The samples_folder path is not valid: {samples_folder}")

    if not callable(update_pb):
        raise ValueError("The 'update_pb' parameter must be a callable function.")
    
    if not ((is_blastBoth and not is_blastnt  and not is_blastnr) or 
            (is_blastnt and not is_blastBoth and not is_blastnr) or 
            (is_blastnr and not is_blastnt  and not is_blastBoth)):
        raise ValueError("The combinations for is_blastnr, is_blastnt, is_blast_both is not valid, only one must be True and all others must be False")
    
    print("HEX [2]")
    print("from _process_samples_folder_single: is_blastnr, is_blastnt, is_blastBoth", is_blastnr, is_blastnt, is_blastBoth)
    if is_mode_ab1:
        print("HEX [3]")
        return _process_samples_folder_single(samples_folder, update_pb, is_blastnr, is_blastnt, is_blastBoth, is_overwrite, is_mode_ab1)
    else:
        return _process_samples_folder_single_fastq(samples_folder, update_pb, is_blastnr, is_blastnt, is_blastBoth, is_overwrite, is_mode_ab1)

def _process_samples_folder_single(
    samples_folder: str,
    update_pb: [Callable] ,
    is_blastnr: bool,
    is_blastnt: bool,
    is_blastBoth: bool,
    is_overwrite: bool,
    is_mode_ab1: bool
) -> None:
    """
    Internal function to process all single-end samples in a specified folder.

    Args:
        samples_folder (str): Path to the folder containing sample files.
        update_pb (function, optional): Function to update the progress bar.
        is_blastnr (bool, optional): Flag indicating whether to perform BLASTx.
        is_blastnt (bool, optional): Flag indicating whether to perform BLASTn.
        is_blastBoth (bool, optional): Flag indicating whether to perform both BLASTx and BLASTn.
        is_overwrite (bool, optional): Flag indicating whether to overwrite existing files.
    """
    print("HEX [4]")
    write_log("process_samples_folder_single. Mode AB1? ", is_mode_ab1)
    reads = find_matching_reads_single_proc(samples_folder, is_blastnr, is_blastnt, is_blastBoth, is_overwrite, is_mode_ab1)
    print("reads unique find_matching_reads_single_proc", reads, is_mode_ab1)
    print("HEX [5]")
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = []
        for sample_name, forward_read in reads.items():
            sample_output_folder = os.path.join(samples_folder, sample_name)
            os.makedirs(sample_output_folder, exist_ok=True)
            future = executor.submit(process_sample_single, sample_name, forward_read, sample_output_folder, update_pb, is_blastnr, is_blastnt, is_blastBoth, is_mode_ab1 = True)
            futures.append(future)
        concurrent.futures.wait(futures)
    write_log("Finished all single files")


def _process_samples_folder_single_fastq(
    samples_folder: str,
    update_pb: [Callable] ,
    is_blastnr: bool,
    is_blastnt: bool,
    is_blastBoth: bool,
    is_overwrite: bool,
    is_mode_ab1: bool
) -> None:
    """
    Internal function to process all single-end samples in a specified folder.

    Args:
        samples_folder (str): Path to the folder containing sample files.
        update_pb (function, optional): Function to update the progress bar.
        is_blastnr (bool, optional): Flag indicating whether to perform BLASTx.
        is_blastnt (bool, optional): Flag indicating whether to perform BLASTn.
        is_blastBoth (bool, optional): Flag indicating whether to perform both BLASTx and BLASTn.
        is_overwrite (bool, optional): Flag indicating whether to overwrite existing files.
    """
    print("AKA [2]")
    write_log("process_samples_folder_single. Mode AB1? ", is_mode_ab1)
    reads = find_matching_reads_single_proc(samples_folder, is_blastnr, is_blastnt, is_blastBoth, is_overwrite, is_mode_ab1)
    print("reads unique find_matching_reads_single_proc", reads, is_mode_ab1)
    print("HEX [_process_samples_folder_single_fastq]")
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = []
        for sample_name, forward_read in reads.items():
            sample_output_folder = os.path.join(samples_folder, sample_name)
            print("HEX sample_name", sample_name, forward_read, sample_output_folder)
            os.makedirs(sample_output_folder, exist_ok=True)
            future = executor.submit(process_sample_single, sample_name, forward_read, sample_output_folder, update_pb, is_blastnr, is_blastnt, is_blastBoth, is_mode_ab1)
            futures.append(future)
        concurrent.futures.wait(futures)
    write_log("Finished all single files")

def find_num_samples(
    folder_path: str,
    is_single: bool,
    is_pair: bool,
    is_single_pair_both: bool,
    show_num_files_pb: Callable
) -> None:
    """
    Find the number of samples based on the sequencing option.

    Args:
        option (str): The sequencing option ("Single," "Paired," or "Both").
        folder_path (str): Path to the folder containing samples.
        show_num_files_pb (function): Function to update the progress bar.

    Raises:
        ValueError: If the provided option is not one of ["Single", "Paired", "Both"].
        ValueError: If the folder_path is not a valid directory.
    """
    global total_num_samples
    if is_single:
        total_num_samples = len(find_matching_reads_single(folder_path))
        # show_num_files_pb(option, total_num_samples,  0) 
    elif is_pair:
        total_num_samples = len(find_matching_reads_paired(folder_path))
        # show_num_files_pb(option, 0,  total_num_samples) 
    elif is_single_pair_both:
        num_single = len(find_matching_reads_single(folder_path))
        num_pair = len(find_matching_reads_paired(folder_path)(folder_path))
        total_num_samples  = num_single + num_pair
        # show_num_files_pb(option, num_single,  num_pair) 

def refresh_gui(update_pb):
    """Refresh the graphical user interface by updating the progress bar.

    Args:
        update_pb (function): Function to update the progress bar.

    Returns:
        None
    """
    write_log("in refresh_gui1")
    global thread_lock_num_finish
    global num_finish
    global total_num_samples
    with thread_lock_num_finish:
        global num_finish
        write_log("inside thread_lock_num_finish")
        num_finish += 1
        time.sleep(0.1)
    write_log("in refresh_gui2")
    write_log(num_finish)
    write_log(total_num_samples)
    write_log(num_finish*100/total_num_samples)
    write_log(update_pb)
    update_pb(num_finish*100/total_num_samples)


def confirm_blast_sent() -> None:
    """
    Confirms that a BLAST request has been sent by incrementing a global counter.

    This function is used to track the number of BLAST requests sent within a given time period. It 
    increments a global counter (`blast_req_sent`) each time a BLAST request is sent. The function 
    is thread-safe, using a global lock (`thread_lock_max_day`) to ensure that the counter is 
    incremented correctly when accessed by multiple threads.

    The function also includes a brief sleep to manage the timing and synchronization of thread 
    operations. It logs its activity for debugging and monitoring purposes.

    Side Effects:
        - Increments the global `blast_req_sent` counter.
        - Logs the function's activity.
        - Briefly sleeps to manage thread timing.

    Note:
        This function is designed to be used in a multi-threaded environment where tracking the 
        number of BLAST requests is necessary. The global lock and counter are critical for 
        maintaining accurate counts in such an environment.
    """
    write_log("in confirm_blast_sent")
    global thread_lock_max_day
    with thread_lock_max_day:
        global blast_req_sent
        write_log("inside confirm_blast_sent")
        blast_req_sent += 1
        time.sleep(0.1)
    write_log("in confirm_blast_sent2")


def is_send_blast() -> bool:
    """
    Determines if a BLAST request can be sent based on the daily limit.

    This function checks if the number of BLAST requests sent on the current day
    has reached the maximum allowed limit (MAX_BLAST_REQUESTS_PER_DAY). It uses
    a thread lock to ensure thread-safe access to the shared variable `blast_req_sent`.
    
    Global Variables:
        blast_req_sent (int): A counter tracking the number of BLAST requests sent.
        thread_lock_max_day (threading.Lock): A lock for thread-safe access to `blast_req_sent`.

    Returns:
        bool: True if the number of requests sent is less than the daily limit, False otherwise.
    """    
    global thread_lock_max_day
    with thread_lock_max_day:
        global blast_req_sent
        if blast_req_sent >= MAX_BLAST_REQUESTS_PER_DAY:
            return False
        return True


def reset_blast_sent()->None:
    """
    Reset the BLAST request counter and update the start time for a new day.

    This function resets the global counter `blast_req_sent` to zero and updates
    the start time `start_time_day` to the current time. It uses a thread lock
    (`thread_lock_max_day`) to ensure thread-safe access when multiple threads
    may attempt to reset the counter.

    Global Variables:
        blast_req_sent (int): A counter tracking the number of BLAST requests sent.
        thread_lock_max_day (threading.Lock): A lock for thread-safe access to `blast_req_sent`.
        start_time_day (float): The timestamp marking the start of the current day.

    Note:
        This function includes a check to inhibit multiple threads from resetting
        `blast_req_sent` in case it has already been reset by another thread.

    Raises:
        None
    """
    global thread_lock_max_day
    global start_time_day
    with thread_lock_max_day:
        global blast_req_sent
        if blast_req_sent == MAX_BLAST_REQUESTS_PER_DAY: # This is to inhibit multipel threads reseting blast_req_sent couple of times
            blast_req_sent = 0
            start_time_day = time.time()



class UpdateProgressBarSignal(QObject):
    update_signal = pyqtSignal(int)

# Modify your existing functions to use the signal
class SangerLogicWorker(QObject):
    update_progress_signal = pyqtSignal(int)

    def __init__(self, folder_path, skip_middle_stages, is_blastnr, is_blastnt, is_blastBoth,
                is_single, is_paired, is_singlePair_both, is_overwrite, num_blast_requests, is_mode_ab1):
        super().__init__()
        self.folder_path = folder_path
        self.skip_middle_stages = skip_middle_stages
        self.is_blastnr = is_blastnr
        self.is_blastnt = is_blastnt
        self.is_blastBoth = is_blastBoth
        self.is_single = is_single
        self.is_paired = is_paired
        self.is_singlePair_both = is_singlePair_both
        self.is_overwrite = is_overwrite
        self.num_blast_requests = num_blast_requests
        global total_num_samples
        total_num_samples = self.num_blast_requests
        self.is_mode_ab1 = is_mode_ab1
        self

    def start_sanger_logic(self):
        # global num_finish
        # global total_num_samples
        # num_finish = 2
        # total_num_samples = 4
        # refresh_gui(self._update_progress)
        # with concurrent.futures.ThreadPoolExecutor() as executor:
        #     future = executor.submit(self._update_progress, 50)
        #     result = future.result()
        #     print("Update progress result:", result)
        # self._update_progress(50)  # Initialize progress bar
        global is_model_ab1
        start_time = time.time()
        write_log("Start time of selected folder path", start_time)

        if self.is_single:
            write_log("start_sanger_single")
            print("HEX [1]")
            process_samples_folder_single(self.folder_path, self._update_progress,
                                        self.is_blastnr, self.is_blastnt, self.is_blastBoth, self.is_overwrite, self.is_mode_ab1)
        elif self.is_paired:
            write_log("start_sanger_pair")
            process_samples_folder_paired(self.folder_path, self._update_progress,
                                        self.skip_middle_stages, self.is_blastnr, self.is_blastnt, self.is_blastBoth,
                                        self.is_overwrite, self.is_mode_ab1)
        else:
            write_log("start_sanger_both")
            print("AKA [0]")
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future_single = executor.submit(process_samples_folder_single, self.folder_path, self._update_progress,
                                        self.is_blastnr, self.is_blastnt, self.is_blastBoth, self.is_overwrite, self.is_mode_ab1)
                future_paired = executor.submit(process_samples_folder_paired, self.folder_path, self._update_progress,
                                        self.skip_middle_stages, self.is_blastnr, self.is_blastnt, self.is_blastBoth,
                                        self.is_overwrite, self.is_mode_ab1)
            concurrent.futures.wait([future_single, future_paired])

        end_time_all = time.time()
        write_log("Time paired of selected folder path", str(end_time_all - start_time), " Seconds")
        if files_with_error:
            write_log("There are some failed files, I will sleep for 30 mins then i will retry them again")
            self.csv_file_path = os.path.join(self.folder_path, 'error_summary.csv')
            save_all_errors_to_csv(self.csv_file_path)
            retry_failed_files()
        else:
            write_log("Found to errors. It's Done")
        self._write_failed_files_log()
        
    def _update_progress(self, value):
        write_log("in _update_progress", value)
        # Emit the signal to update the progress bar
        self.update_progress_signal.emit(int(value))
        
    def _write_failed_files_log(self):
        if failed_files:
            with open("failed_files.log", "w") as log_file:
                log_file.write("The following files failed to process:\n")
                for file_name in failed_files:
                    log_file.write(f"{file_name}\n")
            write_log("Failed files log has been written.")
        else:
            write_log("No failed files to log.")

def save_all_errors_to_csv(csv_file_path):
    """
    Save all stored error details to a CSV file once all files have been processed.
    """
    if files_with_error:
        with open(csv_file_path, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['input_file', 'program', 'database', 'output_folder',
                             'result_file', 'error_message', 'num_trials', 'function_to_be_called'])
            for error in files_with_error:
                writer.writerow([
                    error['input_file'],
                    error['program'],
                    error['database'],
                    error['output_folder'],
                    error['result_file'],
                    error['error_message'],
                    error['num_trials'],
                    error['function_to_be_called']
                ])


def retry_failed_files():
    """
    Retry all the files with errors after a 30-minute interval.
    """
    print("There are some failed files, I will sleep for 30 minutes, then retry them.")
    time.sleep(30*60)


    # Retry the files using the function specified
    for error in files_with_error:
        write_log("Retrying the file: ", error['input_file'])
        if error['function_to_be_called'] == 'single':
            _run_blast_single(error['input_file'], error['program'], error['database'], error['output_folder'])
        elif error['function_to_be_called'] == 'pair':
            _run_blast_pair(error['input_file'], error['program'], error['database'], error['output_folder'])
