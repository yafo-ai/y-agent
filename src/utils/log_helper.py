import os
import logging
from logging.handlers import TimedRotatingFileHandler

def get_logger(logger_name, log_path, level=logging.DEBUG):
    if not os.path.exists(log_path):
        os.makedirs(log_path, exist_ok=True)

    log_file = f"{log_path}{logger_name}.txt"

    logger = logging.getLogger(logger_name)
    logger.setLevel(level)
    logger.propagate = False  # 防止日志信息在多个记录器间传播

    file_handler = TimedRotatingFileHandler(log_file, when='midnight', interval=1, backupCount=30)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger

# 
logger = get_logger("app_logger", "./src/logs/")
chat_logger = get_logger("chat_logger", "./src/logs/chatg_logs/", level=logging.DEBUG)

"""
loger实列

from src.utils.log_helper import logger
logger.info("信息")
logger.debug("调试")
logger.warn("警告")
logger.error("错误")

"""