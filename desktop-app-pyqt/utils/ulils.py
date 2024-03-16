import socket
import os
from loguru import logger
from datetime import datetime
import platform

def check_internet_connection():
    remote_server = "www.google.com"
    port = 80
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)
    try:
        sock.connect((remote_server, port))
        return True
    except socket.error:
        return False
    finally:
        sock.close()


def trigger_logger(base_path_for_log):
    print("trigger", log_file_path)
    # Remove any existing sinks (handlers)
    logger.remove()
    formatted_datetime = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    log_file_path = os.path.join(base_path_for_log, f"log_{formatted_datetime}.log")

    logger.add(log_file_path, backtrace=True, diagnose=True)
    print("log: ", log_file_path)

    # Add a sink to print logs to the terminal
    logger.add(lambda msg: print(msg, end=''), level="INFO")
    with open(log_file_path, "w") as x:
        pass

def write_log(*args):
    # Use the join() method to concatenate the strings with spaces between them
    msg = ' '.join(map(str, args))
    
    # Use the logger to output the aggregated message
    logger.info(msg)

def extract_filename(path):
    return os.path.basename(path)
