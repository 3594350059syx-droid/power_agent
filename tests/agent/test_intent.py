"""
P0-3 意图识别测试脚本

验证 10 条测试用例的意图识别和参数抽取正确率。
验收标准: 10 条中至少 8 条正确（80%通过率）。

运行方式:
    python tests/agent/test_intent.py

当 DEEPSEEK_API_KEY 未配置时，自动降级为规则匹配测试。
当 API Key 已配置时，测试 LLM 意图识别准确率。
"""
import json
import sys
import os

# 确保项目根目录在 sys.path 中
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from agent.prompts.system_prompt import parse_intent_and_params
from agent.prompts.llm_client import is_llm_available


# ---------- 加载测试用例 ----------

test_cases_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "intent_test_cases.json")
with open(test_cases_path, "r", encoding="utf-8") as f:
    TEST_CASES = json.load(f)


# ---------- 测试逻辑 ----------

def run_tests():
    passed = 0
    failed = 0
    details = []

    llm_mode = is_llm_available()
    print("=" * 70)
    print(f"P0-3 意图识别测试 ({'LLM 模式' if llm_mode else '规则匹配模式（降级）'})")
    print("=" * 70)

    for tc in TEST_CASES:
        tc_id = tc["id"]
        message = tc["message"]
        expected_intent = tc["expected_intent"]
        expected_params = tc["expected_params"]

        # 调用意图识别
        intent, params = parse_intent_and_params(message)

        # 意图匹配
        intent_ok = intent == expected_intent

        # 参数匹配（expected_params 中的每个字段都必须匹配）
        params_ok = True
        param_errors = []
        for key, expected_val in expected_params.items():
            actual_val = params.get(key)
            if actual_val != expected_val:
                params_ok = False
                param_errors.append(f"{key}: expected={expected_val}, got={actual_val}")

        # 判定
        test_ok = intent_ok and params_ok
        if test_ok:
            passed += 1
            status = "[PASS]"
        else:
            failed += 1
            status = "[FAIL]"

        # 输出
        print(f"\n  {status} Case {tc_id}: {message[:40]}")
        print(f"    意图: expected={expected_intent}, got={intent} {'OK' if intent_ok else 'MISMATCH'}")
        if param_errors:
            print(f"    参数错误:")
            for err in param_errors:
                print(f"      - {err}")
        else:
            print(f"    参数: OK")
        print(f"    备注: {tc.get('note', '')}")

        details.append({
            "id": tc_id,
            "message": message,
            "expected_intent": expected_intent,
            "actual_intent": intent,
            "intent_ok": intent_ok,
            "params_ok": params_ok,
            "passed": test_ok,
        })

    # ---------- 汇总 ----------
    total = len(TEST_CASES)
    pass_rate = passed / total * 100

    print("\n" + "=" * 70)
    print(f"结果: {passed}/{total} 通过 ({pass_rate:.0f}%)")
    print(f"验收标准: >= 80% ({'PASS' if pass_rate >= 80 else 'FAIL'})")

    if pass_rate >= 80:
        print("ALL CHECKS PASSED")
    else:
        print(f"{failed} case(s) FAILED. 请检查上述 [FAIL] 项。")

    # ---------- 输出详细结果 JSON ----------
    result = {
        "mode": "llm" if llm_mode else "rule_fallback",
        "total": total,
        "passed": passed,
        "failed": failed,
        "pass_rate": f"{pass_rate:.0f}%",
        "acceptance": "PASS" if pass_rate >= 80 else "FAIL",
        "details": details,
    }

    result_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_results.json")
    with open(result_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n详细结果已保存: {result_path}")

    if pass_rate < 80:
        sys.exit(1)


if __name__ == "__main__":
    run_tests()
