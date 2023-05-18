import logging


# Setup logger
logger = logging.getLogger("me 2.0")
stream_handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(levelname)-4s - [%(name)s::%(filename)-4s::%(funcName)s::%(lineno)d] - %(message)s")
stream_handler.setFormatter(formatter)

logger.addHandler(stream_handler)
logger.setLevel(logging.DEBUG)


# Persists log messages on the filesystem
def add_file_handler(file_path):
    file_handler = logging.FileHandler(file_path)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
