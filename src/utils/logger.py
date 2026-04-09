import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logger():
    log_dir = os.path.expanduser("~/Library/Application Support/OmniScribe")
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, "omniscribe.log")
    logger = logging.getLogger("OmniScribe")
    logger.setLevel(logging.DEBUG) 
    file_handler = RotatingFileHandler(log_path, maxBytes=5*1024*1024, backupCount=3)
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] [%(module)s] - %(message)s')
    file_handler.setFormatter(formatter)
    if not logger.handlers: logger.addHandler(file_handler)
    return logger

logger = setup_logger()