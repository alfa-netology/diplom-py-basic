import logging
import datetime


def set_logger(name):
    """ задает параметры логгера"""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter('%(asctime)-25s %(levelname)-7s %(filename)-15s %(funcName)-18s line:%(lineno)-4s %(message)s')

    now = datetime.datetime.now().strftime("%Y-%m-%d-%H%M")
    file = logging.FileHandler(f'logs/{now}.log', encoding='utf-8')
    file.setLevel(logging.INFO)
    file.setFormatter(formatter)

    logger.addHandler(file)

    return logger


