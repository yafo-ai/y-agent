import json
import os
import tempfile
from datetime import datetime
from pathlib import Path

from src.api.customer_exception import ValidationException
from src.utils.log_helper import logger


class TestPlanTasking:
    """测试计划任务"""
    testplan_file = Path('./src/configs/testplan_tasking.json')

    @classmethod
    def load_plan(cls):
        """加载测试计划的任务"""
        if not cls.testplan_file.exists():
            return []
        try:
            with cls.testplan_file.open('r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f'加载测试计划任务异常：{str(e)}')
            return []

    @classmethod
    def append_plan(cls, plan_id: int):
        """追加测试计划任务，如果任务已经存在，则不再追加"""
        job = [{"plan_id": plan_id, "datatime": datetime.now().isoformat()}]

        jobs = cls.load_plan()
        if any(j['plan_id'] == plan_id for j in jobs):
            return None
        jobs.extend(job)
        cls._save_plan(jobs)

    @classmethod
    def remove_plan(cls, test_plan_id: int):
        """删除测试计划的任务"""
        jobs = cls.load_plan()
        original_len = len(jobs)
        update_jobs = [j for j in jobs if j['plan_id'] != test_plan_id]
        if len(update_jobs) == original_len:
            logger.error(f'测试计划{test_plan_id}不存在')
            return
        cls._save_plan(update_jobs)

    @classmethod
    def _save_plan(cls, jobs: list[dict]):
        tmp_fd, tmp_path = tempfile.mkstemp(dir=cls.testplan_file.parent, prefix=cls.testplan_file.stem + '.tmp')
        try:
            with os.fdopen(tmp_fd, 'w', encoding='utf-8') as f:
                json.dump(jobs, f, ensure_ascii=False, indent=4)
            os.replace(tmp_path, cls.testplan_file)
        except Exception as e:
            logger.error(f'保存测试计划任务异常：{str(e)}')
            os.unlink(tmp_path)
            raise ValidationException(str(e))


class TestPlanContinueTasking(TestPlanTasking):
    """测试计划重启任务"""
    testplan_file = Path('./src/configs/testplan_continue_tasking.json')

    @classmethod
    def append_restart_plan(cls):
        """服务停止，追加重启任务"""
        jobs = TestPlanTasking.load_plan()
        if jobs is None or len(jobs) == 0:
            return
        for job in jobs:
            cls.append_plan(job['plan_id'])
        for job in jobs:
            TestPlanTasking.remove_plan(job['plan_id'])


if __name__ == '__main__':
    print(TestPlanTasking.load_plan())
    TestPlanTasking.append_plan(1)
    TestPlanTasking.append_plan(2)
    print(TestPlanTasking.load_plan())
    TestPlanTasking.append_plan(2)
    print(TestPlanTasking.load_plan())
    TestPlanTasking.remove_plan(1)
    print(TestPlanTasking.load_plan())

