import json
import time
from typing import Optional

from sqlalchemy import or_

from src.api.customer_exception import ValidationException
from src.agent.model_types import EvaluationResponse
from src.database.enums import TestCaseStateType, TestPlanState
from src.database.models import ModelConfig, PromptModel, TestCase, TestPlan
from src.llm.llm_helper import llm_content_pydantic_object_parser, llm_generate_text
from src.utils.json_helper import _customer_serializer
from src.utils.log_helper import logger
from src.database.models import WorkFlow

from src.database.db_session import on_request_end, set_current_request_id


def plan_case_execute_task(plan_id, report_id, execute_workflow_id, unit_llm_id, evaluation_llm_id, evaluation_prompt_id, is_continue):
    set_current_request_id()
    plan = TestPlan.get(plan_id)
    try:
        last_report_case_ids = plan.get_last_report_case_ids()
        case_list = plan.plan_cases()
        for case in case_list:
            if is_continue:
                if case.id in last_report_case_ids:
                    continue
            print(f"执行测试用例: {case.id}")
            case.test_state = TestCaseStateType.测试中.value
            case.update(True)
            if plan.tag == 'W':
                testcase_execute(case.id, plan.id, report_id, execute_workflow_id, evaluation_llm_id, evaluation_prompt_id, True if execute_workflow_id is not None else plan.is_forced)
            elif plan.tag == 'S':
                testcase_unit_execute(case.id, plan.id, report_id, unit_llm_id, evaluation_llm_id, evaluation_prompt_id)
        if all(case.test_state == TestCaseStateType.测试完成.value for case in case_list) and plan.state != TestPlanState.测试完成.value:
            plan.state = TestPlanState.测试完成.value
            plan.update(True)
    except Exception as e:
        logger.error(f"测试计划【{plan_id}_{plan.name}】执行异常: {str(e)}")
        plan.state = TestPlanState.测试完成.value
        plan.error_msg = str(e)
        plan.update(True)
    finally:
        on_request_end()


def case_execute_task(case_ids, workflow_id, unit_llm_id, evaluation_llm_id, evaluation_prompt_id, is_forced: bool = False, tag='W'):
    set_current_request_id()
    try:
        case_list = TestCase.query.filter(TestCase.id.in_(case_ids)).all()
        for case in case_list:
            print(f"执行测试用例: {case.id}")
            case.test_state = TestCaseStateType.测试中.value
            case.update(True)
            if tag == 'W':
                testcase_execute(case.id, None, None, workflow_id, evaluation_llm_id, evaluation_prompt_id, is_forced)
            elif tag == 'S':
                testcase_unit_execute(case.id, None, None, unit_llm_id, evaluation_llm_id, evaluation_prompt_id)
    except Exception as e:
        logger.error(f'测试用例执行异常: {str(e)}')
    finally:
        on_request_end()


def testcase_execute(case_id: int, test_plan_id: Optional[int], test_report_id: Optional[int],
                     execution_workflow_id: Optional[int], evaluation_llm_id: Optional[int], evaluation_prompt_id: Optional[int],
                     is_forced: bool = False):
    """
    Args:
        case_id: 测试用例ID
        test_plan_id: 测试计划ID
        test_report_id: 测试报告ID
        execution_workflow_id: 流程ID
        evaluation_llm_id: 评测大模型ID
        evaluation_prompt_id: 评测提示词ID
          is_forced: 是否强制使用指定流程
            True: 优先使用 execution_workflow_id，其次用例默认流程
            False: 优先使用用例默认流程，其次 execution_workflow_id
    """
    response = None
    elapsed_time = None
    current_workflow_log_id = None
    execute_workflow_name = None
    response_answer_str = None
    error_msg = None
    test_case = None
    try:
        test_case = TestCase.get(case_id)
        case_workflow_id = test_case.workflow_id
        user_input = {"user_input": test_case.question}
        if is_forced:
            workflow_id = execution_workflow_id if execution_workflow_id is not None else case_workflow_id
        else:
            workflow_id = case_workflow_id if case_workflow_id is not None else execution_workflow_id
            if case_workflow_id is not None:
                user_input = json.loads(test_case.workflow_log_inputs)

        wf_model = WorkFlow.get(workflow_id)
        execute_workflow_name = wf_model.name
        start_time = time.time()

        # 校验测试用例是否可以执行
        TestCase.check_case_execute(test_case, workflow_id, is_forced)

        from src.agent.working.working_manager import load_graph, run_graph
        graph = load_graph(wf_model.id, wf_model.data_json,workflow_source_name='流程测试')
        response = run_graph(wf_model.id, wf_model.name, graph, user_input)
        error_msg = response.get("error_msg")

        current_workflow_log_id = response.get("log_id")

        end_time = time.time()
        elapsed_time = round(end_time - start_time, 2)

        answer_str = json.dumps(response.get("output"), ensure_ascii=False)
        response_answer_str = answer_str
        accuracy, score = _evaluate_with_llm(evaluation_llm_id, evaluation_prompt_id, test_case.right_answer, response_answer_str, user_input,
                                             test_case.test_standard)

        test_case.execute_completed(response_answer_str, accuracy, score,
                                    json.dumps(response, ensure_ascii=False, default=_customer_serializer), elapsed_time, test_plan_id,
                                    test_report_id, evaluation_llm_id, evaluation_prompt_id, current_workflow_log_id,
                                    None, None, None, execute_workflow_name, error_msg)
    except Exception as e:
        error_msg = str(e) if error_msg is None else f'{error_msg}_{str(e)}'
        test_case.execute_completed(response_answer_str, False, str(0), json.dumps(response, ensure_ascii=False, default=_customer_serializer),
                                    elapsed_time, test_plan_id, test_report_id, evaluation_llm_id, evaluation_prompt_id, current_workflow_log_id,
                                    None, None, None, execute_workflow_name, error_msg)
        logger.error(f"testcase_execute Error: {str(e)}")


def testcase_unit_execute(test_case_id: Optional[int], test_plan_id: Optional[int], report_id: Optional[int], unit_llm_id: Optional[int],
                          evaluation_llm_id: Optional[int], evaluation_prompt_id: Optional[int]):
    """
    Args:
        test_case_id: 测试用例ID
        test_plan_id: 测试计划ID
        unit_llm_id: 执行工作流的模型ID
        report_id: 测试报告ID
        evaluation_llm_id: 评测模型ID
        evaluation_prompt_id: 评测提示词ID
    """
    response = None
    elapsed_time: Optional[str] = None
    test_report_id: Optional[int] = report_id
    execute_llm_name = None
    response_content = None
    test_case = None
    try:
        test_case = TestCase.get(test_case_id)
        start_time = time.time()

        model = ModelConfig.get(unit_llm_id)
        execute_llm_name = model.name
        response_content = llm_generate_text(unit_llm_id, test_case.question,{},test_case.vision_file_str)

        end_time = time.time()
        elapsed_time = str(round(end_time - start_time, 2))

        accuracy, score = _evaluate_with_llm(evaluation_llm_id, evaluation_prompt_id, test_case.right_answer, response_content, test_case.question,
                                             test_case.test_standard)

        test_case.execute_completed(response_content, accuracy, score,
                                    json.dumps(response, ensure_ascii=False, default=_customer_serializer) if response is not None else None,
                                    elapsed_time, test_plan_id, test_report_id, evaluation_llm_id,
                                    evaluation_prompt_id,
                                    None, test_case.workflow_node_log_id, unit_llm_id, execute_llm_name, None, None)
    except Exception as e:
        error_msg = f"测试计划：【ID：{test_plan_id}】，用例：【{test_case_id}】，{str(e)}"
        test_case.execute_completed(response_content, False, '0',
                                    json.dumps(response, ensure_ascii=False, default=_customer_serializer) if response is not None else None,
                                    elapsed_time, test_plan_id, test_report_id, evaluation_llm_id, evaluation_prompt_id,
                                    None, test_case.workflow_node_log_id, unit_llm_id, execute_llm_name, None, error_msg)
        logger.error(error_msg)


def _evaluate_with_llm(llm_id: int, prompt_id: int, right_answer: str, answer: any, input: any, test_standard: any):
    """评测结果"""
    prompt_content = PromptModel.get(prompt_id).content
    context={"sys":{"test":{"right_answer":right_answer,"answer":answer,"input":input,"test_standard":test_standard}}}

    ai_text = llm_generate_text(llm_id, prompt_content,context)

    rst_model = llm_content_pydantic_object_parser(EvaluationResponse, ai_text)
    return rst_model.accuracy, str(rst_model.score)


def testcase_export(cate_id: Optional[int] = None, tag: Optional[str] = 'W'):
    """导出测试用例"""
    cases = TestCase.query.filter(TestCase.tag == tag)
    # 未分类
    if cate_id is not None and cate_id == 0:
        cases = cases.filter(or_(TestCase.test_cate_id == 0, TestCase.test_cate_id == None))
    # 指定分类
    elif cate_id is not None and cate_id > 0:
        cases = cases.filter(TestCase.test_cate_id == cate_id)
    cases = cases.all()
    if not cases or len(cases) == 0:
        raise ValidationException("没有找到测试用例")
    rows = [
        {
            "ID": case.id,
            "问题": case.question,
            "参考答案": case.right_answer,
            "测试标准": case.test_standard,
            "备注": case.note,
            "分类名称": case.test_cate.name if case.test_cate is not None else "未分类",
            "分类ID": case.test_cate_id,
            "是否审核": '是' if case.is_marked is True else '否',
            "是否更正": '是' if case.is_modified is True else '否',
            "创建时间": case.created_at.strftime("%Y-%m-%d %H:%M:%S")
        } for case in cases
    ]
    return rows
