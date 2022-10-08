import pandas as pd
from . import settings
import os
import logging

logger = logging.getLogger('log')


class core_algorithm:
    def __init__(self, core_prarm):
        logger.info("start_core_algorithm:"+core_prarm)

    def file_deal(self, path, work_id):
        try:
            with open(os.path.join(settings.PROCESS_URL, 'process_' + work_id), 'a+') as f:
                print("[" + work_id + "]" + " 开始任务：", file=f)
            self.work_id = work_id
            suffix = str(path).split(".")[-1]
            warn_data = None
            logger.info('local_path'+str(path))

            with open(os.path.join(settings.PROCESS_URL, 'process_' + self.work_id), 'a+') as f:
                print("[" + self.work_id + "]" + "  当前进度：100%", file=f)
        except Exception as e:
            logging.error("[" + work_id + "]:核心算法处理出错" + str(e))
