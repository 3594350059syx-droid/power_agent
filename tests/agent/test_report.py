"""诊断报告生成与 Agent/API 集成回归测试。"""

import os
import sys
import unittest
from unittest.mock import patch


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from agent.graph.workflow import tool_executor
from agent.prompts.system_prompt import extract_params
from agent.tools.report_tool import build_diagnosis, report_tool
from backend.api.report import latest_report
from backend.services.report_service import get_latest_report


class TestReportTool(unittest.TestCase):
    """报告内容必须覆盖既有报告契约和新增诊断信息。"""

    def test_report_contains_structured_diagnosis_sections(self):
        diagnosis = {
            "device_id": "boiler_002",
            "device_name": "2号锅炉",
            "diagnosis_time": "2026-08-30T10:00:00",
            "analysis_window_hours": 24,
            "risk_score": 0.85,
            "risk_level": "high",
            "alarms": [
                {
                    "parameter": "steam_temp",
                    "severity": "high",
                    "message": "主蒸汽温度超过阈值",
                }
            ],
            "causes": ["减温水流量不足"],
            "suggestions": ["检查减温水系统"],
            "trend_info": {"trend": "rising", "confidence": 0.92},
            "knowledge_refs": [
                {
                    "source": "锅炉运行规程 §3.2",
                    "content": "检查减温水阀门开度",
                    "similarity": 0.94,
                }
            ],
            "data_summary": {"min": 535, "max": 568, "avg": 548, "count": 24},
        }

        report = report_tool(diagnosis)

        self.assertTrue(report.startswith("# 设备诊断报告\n"))
        for section in ("## 设备信息", "## 风险评估", "## 异常摘要", "## 趋势分析", "## 异常原因", "## 处置建议"):
            self.assertIn(section, report)
        self.assertIn("2号锅炉", report)
        self.assertIn("0.85", report)
        self.assertIn("减温水流量不足", report)
        self.assertIn("检查减温水系统", report)
        self.assertTrue(report.endswith("\n"))

    def test_build_diagnosis_merges_partial_tool_results(self):
        diagnosis = build_diagnosis(
            {
                "data_tool": {
                    "device_id": "turbine_003",
                    "device_name": "3号汽轮机",
                    "stats": {"count": 12},
                },
                "alarm_tool": {
                    "device_id": "turbine_003",
                    "risk_score": 0.4,
                    "risk_level": "medium",
                    "alarms": [],
                    "recommendations": ["持续监控"],
                },
                "rag_tool": [{"source": "manual", "content": "检查振动", "similarity": 0.8}],
            },
            {"device_id": "turbine_003", "time_range_hours": 12},
        )

        self.assertEqual(diagnosis["device_id"], "turbine_003")
        self.assertEqual(diagnosis["analysis_window_hours"], 12)
        self.assertEqual(diagnosis["risk_score"], 0.4)
        self.assertEqual(diagnosis["suggestions"], ["持续监控"])
        self.assertEqual(diagnosis["knowledge_refs"][0]["source"], "manual")


class TestReportWorkflowIntegration(unittest.TestCase):
    def test_diagnosis_executes_prediction_tool(self):
        tool_results = {
            "data_tool": {"device_id": "boiler_002", "data": [], "stats": {}},
            "alarm_tool": {"device_id": "boiler_002", "risk_score": 0.72, "alarms": []},
            "predict_tool": {"trend": "rising", "confidence": 0.9, "predictions": []},
            "rag_tool": [],
        }
        statuses = {
            name: {"tool": name, "status": "success"}
            for name in ("data_tool", "alarm_tool", "predict_tool", "rag_tool")
        }
        state = {
            "intent": "diagnosis",
            "params": {"device_id": "boiler_002", "time_range_hours": 24},
            "tool_calls": [],
            "tool_results": {},
            "report": "",
        }

        with patch("agent.graph.workflow._execute_independent_tools", return_value=(tool_results, statuses)), \
                patch("agent.graph.workflow.call_tool", return_value="# 设备诊断报告\n"):
            result = tool_executor(state)

        self.assertEqual(
            [call["tool"] for call in result["tool_calls"]],
            ["data_tool", "alarm_tool", "predict_tool", "rag_tool"],
        )

    def test_report_is_generated_without_changing_legacy_tool_call_count(self):
        tool_results = {
            "data_tool": {"device_id": "boiler_002", "data": [], "stats": {}},
            "alarm_tool": {
                "device_id": "boiler_002",
                "risk_score": 0.72,
                "alarms": [],
            },
        }
        statuses = {
            "data_tool": {"tool": "data_tool", "status": "success"},
            "alarm_tool": {"tool": "alarm_tool", "status": "success"},
        }
        state = {
            "intent": "anomaly_detection",
            "params": {"device_id": "boiler_002", "time_range_hours": 24},
            "tool_calls": [],
            "tool_results": {},
            "report": "",
        }

        with patch("agent.graph.workflow._execute_independent_tools", return_value=(tool_results, statuses)), patch(
            "agent.graph.workflow.call_tool", return_value="# 设备诊断报告\n"
        ) as mock_call_tool:
            result = tool_executor(state)

        self.assertEqual(len(result["tool_calls"]), 2)
        self.assertEqual(result["tool_calls"][0]["tool"], "data_tool")
        self.assertEqual(result["tool_calls"][1]["tool"], "alarm_tool")
        self.assertEqual(result["report"], "# 设备诊断报告\n")
        self.assertEqual(result["tool_results"]["report_tool"], "# 设备诊断报告\n")
        mock_call_tool.assert_called_once()
        self.assertEqual(mock_call_tool.call_args.args[0], "report_tool")


class TestReportServiceAndApi(unittest.TestCase):
    @patch("backend.services.report_service.run_agent")
    def test_service_normalizes_device_id_and_returns_report(self, mock_run_agent):
        mock_run_agent.return_value = {
            "report": "# 设备诊断报告\n",
            "diagnosis": {"device_id": "turbine_003"},
        }

        result = get_latest_report("  turbine_003 ", hours=12)

        self.assertEqual(result["device_id"], "turbine_003")
        self.assertEqual(result["report"], "# 设备诊断报告\n")
        self.assertEqual(mock_run_agent.call_args.kwargs["mode"], "diagnose")
        self.assertIn("turbine_003", mock_run_agent.call_args.args[0])
        self.assertIn("12", mock_run_agent.call_args.args[0])

    def test_api_success_envelope(self):
        with patch("backend.api.report.get_latest_report", return_value={"report": "# 报告"}):
            response = latest_report("boiler_002", hours=24)

        self.assertTrue(response["success"])
        self.assertEqual(response["data"]["report"], "# 报告")

    def test_api_converts_service_error_to_http_error(self):
        with patch(
            "backend.api.report.get_latest_report",
            side_effect=RuntimeError("backend unavailable"),
        ):
            response = latest_report("boiler_002", hours=24)

        self.assertEqual(response.status_code, 503)
        self.assertIn("诊断报告暂时不可用", response.body.decode("utf-8"))


class TestReportInputCompatibility(unittest.TestCase):
    def test_canonical_device_ids_are_extracted(self):
        params = extract_params("分析 turbine_003 过去12小时异常")
        self.assertEqual(params["device_id"], "turbine_003")
        self.assertEqual(params["time_range_hours"], 12)


if __name__ == "__main__":
    unittest.main()