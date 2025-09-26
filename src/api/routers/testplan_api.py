import asyncio
import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Path, Body, BackgroundTasks
from sqlalchemy.orm import Session

from src.api.customer_exception import ValidationException
from src.api.testcase_task import plan_case_execute_task
from src.database.enums import TestCaseResultType, get_enum_name, TestPlanState
from src.database.models import TestCase, TestPlan, TestReport, TestCaseLog, TestPlanCateMap, TestPlanCaseMap, PromptModel
from src.database.db_session import get_scoped_session
from src.utils.testplan_helper import TestPlanTasking, TestPlanContinueTasking

router = APIRouter(
    prefix="/api/testplan",
    tags=["测试计划"],
)


@router.post("/pagination", summary="计划列表")
def get_test_plan_page(page: int = Body(default=1, description="页码"),
                       pagesize: int = Body(default=10, description="每页数量"),
                       plan_name: str = Body(default=None, description="计划名称"),
                       plan_state: TestPlanState = Body(default=TestPlanState.默认, description="计划状态")):
    """获取测试用例列表"""
    filters = []
    if plan_state is not None and plan_state != TestPlanState.默认:
        filters.append(TestPlan.state == plan_state.value)
    if plan_name is not None and plan_name != '':
        filters.append(TestPlan.name.like(f'%{plan_name}%'))
    return TestPlan.get_pagination(page, pagesize, *filters)


@router.get("/{id}/relation_cate_case", summary="计划用例列表")
def get_test_plan_relation_cate_case(id: int = Path(description="计划ID")):
    return TestPlan.get(id).get_relation_cate_cases()


@router.get("/{id}/reports", summary="计划报告列表")
def get_plan_reports(id: int = Path(description="计划ID")):
    """获取计划id 获取测试计划报告记录"""
    return TestPlan.get(id).plan_reports()


@router.post("/add", summary="新增测试计划")
def plan_add(name: str = Body(default=None, description="计划名称"),
             caption: str = Body(default=None, description="计划介绍"),
             note: str = Body(default=None, description="备注"),
             workflow_id: int = Body(description="工作流id", default=None),
             evaluation_llm_id: int = Body(description="评估大模型id", default=None),
             evaluation_prompt_id: int = Body(description="评估提示词id", default=None),
             is_forced: bool = Body(description="是否强制使用指定的工作流执行", default=False)):
    """新增测试计划"""
    model = TestPlan.plan_add(name, caption, note, workflow_id, evaluation_llm_id, evaluation_prompt_id, is_forced, None, 'W')
    return {"id": model.id}


@router.post("/edit", summary="编辑测试计划")
def plan_edit(id: int = Body(default=None, description="计划ID"),
              name: str = Body(default=None, description="计划名称"),
              caption: str = Body(default=None, description="计划介绍"),
              note: str = Body(default=None, description="备注"),
              workflow_id: int = Body(description="工作流id", default=None),
              evaluation_llm_id: int = Body(description="评估大模型id", default=None),
              evaluation_prompt_id: int = Body(description="评估提示词id", default=None),
              is_forced: bool = Body(description="是否强制使用指定的工作流执行", default=False)):
    """编辑测试计划"""
    TestPlan.get(id).plan_edit(name, caption, note, workflow_id, evaluation_llm_id, evaluation_prompt_id, is_forced, None)
    return {"result": "success"}


@router.post("/delete/{id}", summary="删除测试计划")
def plan_delete(id: int = Path(description="计划ID")):
    """删除测试计划"""
    model = TestPlan.get(id)
    # if model.state == TestPlanState.测试中.value:
    #     raise NoneException(f"测试计划{id}正在执行中，无法删除")
    model.delete(True)
    return {"result": "success"}


@router.post("/relation_cate/{id}", summary="关联测试分类")
def plan_relation_cate(id: int = Path(description="计划ID"), cate_ids: list[int] = Body(default=None, description="测试分类IDS")):
    """关联测试分类"""
    TestPlan.get(id).plan_relation_cate_maps(cate_ids)
    return {"result": "success"}


@router.post("/relation_case/{id}", summary="关联测试用例")
def plan_relation_case(id: int = Path(description="计划ID"), case_ids: list[int] = Body(default=None, description="用例库IDS")):
    """关联测试用例"""
    TestPlan.get(id).plan_relation_case_maps(case_ids)
    return {"result": "success"}


@router.post("/cases/{id}", summary="计划用例列表")
def plan_cases(id: int = Path(description="计划ID"),
               session: Session = Depends(get_scoped_session)):
    """获取测试计划关联的用例"""
    model = TestPlan.get(id)
    cases = model.plan_cases()
    return {"rows": cases}


@router.post("/batch_execute", summary="执行测试计划")
def plan_execute(background_tasks: BackgroundTasks,
                 id: int | None = Body(description="计划id", default=None),
                 plan_name: str | None = Body(description="计划名称", default=None),
                 workflow_id: int | None = Body(description="执行工作流id", default=None),
                 unit_llm_id: int | None = Body(description="单元测试执行大模型id", default=None),
                 evaluation_llm_id: int | None = Body(description="评估大模型id", default=None),
                 evaluation_prompt_id: int | None = Body(description="评估提示词id", default=None),
                 is_continue: bool = Body(description="是否继续执行", default=False)):
    """执行测试计划"""
    plan = TestPlan.get(id)
    plan.error_msg = None
    plan.update(True)
    tmp_cases = plan.plan_cases()
    if tmp_cases is None or len(tmp_cases) == 0:
        raise ValidationException(f"测试计划{plan.id}没有关联的用例")
    if plan_name is None or plan_name == "":
        plan_name = f'【{plan.name}（{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}）测试报告】'
    if plan.tag == "W":
        if workflow_id is None or workflow_id <= 0:
            raise ValidationException(f"测试计划{plan.id}没有指定执行工作流")
        for case in tmp_cases:
            TestCase.check_case_execute(case, plan.workflow_id, plan.is_forced)
    if plan.tag == "S":
        if unit_llm_id is None or unit_llm_id <= 0:
            raise ValidationException(f'测试计划{plan.id}没有指定单元测试执行大模型')
    if evaluation_llm_id is None or evaluation_llm_id <= 0:
        raise ValidationException(f"测试计划{plan.id}没有关联的评估大模型")
    if evaluation_prompt_id is None or evaluation_prompt_id <= 0:
        raise ValidationException(f"测试计划{plan.id}没有关联的评估提示词")

    plan.state = TestPlanState.测试中.value
    report = plan.plan_add_report(plan_name)
    if is_continue:
        TestPlanContinueTasking.remove_plan(id)
    else:
        TestPlanTasking.append_plan(id)
    background_tasks.add_task(asyncio.to_thread, plan_case_execute_task, id, report.id, workflow_id, unit_llm_id, evaluation_llm_id, evaluation_prompt_id, is_continue)
    return {"result": "success"}


@router.post("/report", summary="报告列表")
def plan_reports_page(page: int = Body(default=1, description="页码"),
                      pagesize: int = Body(default=10, description="每页数量"),
                      plan_id: int = Body(default=None, description="计划ID")):
    """获取测试计划报告列表"""
    return TestReport.get_pagination(page, pagesize, plan_id)


@router.get("/report/{id}", summary="报告详情")
def plan_report(id: int = Path(description="报告ID")):
    """获取测试计划报告"""
    report = TestReport.get(id)
    report_dict = {
        "id": report.id,
        "plan_name": report.test_plan.name,
        "case_count": report.case_count,
        "create_at": report.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        "test_pass_count": report.test_pass_count,
        "test_fail_count": report.test_fail_count
    }
    return report_dict


@router.post("/report/{id}/delete", summary="报告删除")
def plan_report_delete(id: int = Path(description="报告ID")):
    """删除测试计划报告"""
    TestReport.get(id).delete(True)
    return {"result": "success"}


@router.post("/report/{id}/pagination", summary="报告计划列表")
def plan_report_page(id: int = Path(description="报告ID"),
                     page: int = Body(default=1, description="页码"),
                     pagesize: int = Body(default=10, description="每页数量"),
                     test_result: TestCaseResultType = Body(default=TestCaseResultType.默认, description="测试结果状态，成功 = 2001,失败 = 3001")):
    """获取测试计划报告列表"""
    if id is None or id == 0:
        raise ValidationException("请选择报告")
    return TestCaseLog.get_pagination(page, pagesize, test_result, (TestCaseLog.test_report_id == id))
    # 或者 return TestCaseLog.get_pagination(page, pagesize, test_result, test_report_id=id)


@router.post('/unit/add', summary="新增测试计划单元")
def plan_unit_add(name: str = Body(default=None, description="计划名称"),
                  caption: str = Body(default=None, description="计划介绍"),
                  note: str = Body(default=None, description="备注"),
                  unit_llm_id: Optional[int] = Body(description="单元测试大模型Id", default=None),
                  evaluation_llm_id: Optional[int] = Body(description="评估大模型id", default=None),
                  evaluation_prompt_id: Optional[int] = Body(description="评估提示词id", default=None)):
    """
    新增测试计划单元
    """
    model = TestPlan.plan_add(name, caption, note, None, evaluation_llm_id, evaluation_prompt_id, False, unit_llm_id, 'S')
    return {"id": model.id}


@router.post('/unit/edit', summary="编辑测试计划单元")
def plan_unit_edit(id: int = Body(description="计划ID"),
                   name: str = Body(default=None, description="计划名称"),
                   caption: str = Body(default=None, description="计划介绍"),
                   note: str = Body(default=None, description="备注"),
                   unit_llm_id: Optional[int] = Body(description="单元测试大模型Id", default=None),
                   evaluation_llm_id: Optional[int] = Body(description="评估大模型id", default=None),
                   evaluation_prompt_id: Optional[int] = Body(description="评估提示词id", default=None)):
    """
    编辑测试计划单元
    """
    TestPlan.get(id).plan_edit(name, caption, note, None, evaluation_llm_id, evaluation_prompt_id, False, unit_llm_id)
    return {"result": "success"}


@router.post('/batch_execute/continue', summary="继续执行测试计划")
def continue_batch_execute(background_tasks: BackgroundTasks,
                           id: int | None = Body(description="计划id", default=None),
                           plan_name: str | None = Body(description="计划名称", default=None),
                           workflow_id: int | None = Body(description="执行工作流id", default=None),
                           unit_llm_id: int | None = Body(description="单元测试执行大模型id", default=None),
                           evaluation_llm_id: int | None = Body(description="评估大模型id", default=None),
                           evaluation_prompt_id: int | None = Body(description="评估提示词id", default=None)):
    return plan_execute(background_tasks, id, plan_name, workflow_id, unit_llm_id, evaluation_llm_id, evaluation_prompt_id, True)
