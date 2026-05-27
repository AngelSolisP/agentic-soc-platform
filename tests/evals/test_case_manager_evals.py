"""Case Manager Agent — ADK Evaluation Tests (Tier 2)."""
import json
import os

import pytest
from google.adk.evaluation.eval_set import EvalSet
from google.adk.evaluation.eval_config import EvalConfig


CASE_MGR_EVAL_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "evals", "case_manager")


@pytest.mark.mock
def test_case_manager_eval_agent_exposes_root_agent():
    from evals.case_manager.agent import root_agent
    assert root_agent is not None
    assert root_agent.name == "case_manager_agent"


@pytest.mark.mock
def test_case_manager_eval_set_parses():
    path = os.path.join(CASE_MGR_EVAL_DIR, "case_manager.test.json")
    with open(path) as f:
        content = f.read()
    eval_set = EvalSet.model_validate_json(content)
    assert eval_set.eval_set_id == "case_manager_evals"
    assert len(eval_set.eval_cases) == 10


@pytest.mark.mock
def test_case_manager_eval_config_parses():
    path = os.path.join(CASE_MGR_EVAL_DIR, "test_config.json")
    with open(path) as f:
        data = json.load(f)
    config = EvalConfig.model_validate(data)
    assert "tool_trajectory_avg_score" in config.criteria


@pytest.mark.eval
@pytest.mark.asyncio
async def test_case_manager_agent_eval_tool_trajectory():
    """Tier 2: Run case manager agent against Gemini and validate tool trajectory."""
    from google.adk.evaluation import AgentEvaluator

    await AgentEvaluator.evaluate(
        agent_module="evals.case_manager.agent",
        eval_dataset_file_path_or_dir="evals/case_manager/",
        num_runs=1,
    )
