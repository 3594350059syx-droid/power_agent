"""高/低负荷模型自适应选择与评估。"""
from __future__ import annotations

import os
from datetime import datetime, timedelta
from pathlib import Path

from backend.database.connection import get_db
from backend.database.models import SensorPoint, TimeseriesData
from backend.services.data_service import get_device_by_code_or_name, resolve_param_name
from algorithms.prediction import TimeSeriesPredictor, fetch_history_data, prepare_training_data
from algorithms.prediction.model_utils import split_train_test
from .metrics import compare_models


PROJECT_ROOT = Path(__file__).resolve().parents[2]
MODEL_DIR = str(PROJECT_ROOT / "models" / "prediction")
HIGH_LOAD_THRESHOLD = 280.0
MIN_CONDITION_SAMPLES = 30
MODEL_CACHE_TTL_SECONDS = 6 * 3600


def _condition_description(condition: str) -> str:
    return "高负荷(>280MW)" if condition == "high" else "低负荷(≤280MW)"


class ModelSelector:
    """根据最近功率工况选择预测模型，并管理工况模型缓存。"""

    def __init__(self, model_dir: str = MODEL_DIR, min_condition_samples: int = MIN_CONDITION_SAMPLES):
        self.model_dir = model_dir
        self.min_condition_samples = min_condition_samples

    def _model_path(self, device_code: str, parameter: str, condition: str) -> str:
        return os.path.join(self.model_dir, f"{device_code}_{parameter}_{condition}.pkl")

    @staticmethod
    def _load_cached_model(model_path: str):
        """加载缓存；不存在、损坏或运行环境不兼容时统一视为 miss。"""
        if not os.path.exists(model_path):
            return None
        try:
            age = datetime.now().timestamp() - os.path.getmtime(model_path)
            if age >= MODEL_CACHE_TTL_SECONDS:
                return None
        except OSError:
            return None
        try:
            predictor = TimeSeriesPredictor.load(model_path)
            return predictor if predictor.model is not None else None
        except Exception:
            return None

    def detect_condition(self, device_id: str) -> str:
        """识别当前工况：最近 30 分钟功率均值严格大于 280MW 为 high。"""
        db = next(get_db())
        try:
            device = get_device_by_code_or_name(db, device_id)
            if not device:
                return "low"

            sensor = db.query(SensorPoint).filter(
                SensorPoint.device_id == device.id,
                SensorPoint.point_name == "power",
            ).first()
            if not sensor:
                return "low"

            recent = db.query(TimeseriesData.value).filter(
                TimeseriesData.device_id == device.id,
                TimeseriesData.sensor_id == sensor.id,
                TimeseriesData.recorded_at >= datetime.now() - timedelta(minutes=30),
            ).order_by(TimeseriesData.recorded_at.desc()).limit(30).all()
            if not recent:
                return "low"

            avg_power = sum(row[0] for row in recent) / len(recent)
            return "high" if avg_power > HIGH_LOAD_THRESHOLD else "low"
        finally:
            db.close()

    def _split_by_condition(self, raw_df, power_df):
        if not power_df.empty:
            merged = raw_df.merge(
                power_df[["ds", "y"]], on="ds", suffixes=("", "_power")
            )
            return (
                merged[merged["y_power"] > HIGH_LOAD_THRESHOLD][["ds", "y"]],
                merged[merged["y_power"] <= HIGH_LOAD_THRESHOLD][["ds", "y"]],
            )
        # 没有功率历史时不伪造工况标签；由调用方使用全量 fallback。
        return raw_df.iloc[0:0], raw_df.iloc[0:0]

    def _train_one_condition(self, condition_df, device_id: str, parameter: str, condition: str):
        sample_count = len(condition_df)
        result = {
            "condition": condition,
            "condition_desc": _condition_description(condition),
            "sample_count": sample_count,
            "model_name": None,
            "model_path": None,
            "model_type": None,
            "model_source": None,
            "metrics": {},
            "error": None,
        }
        if sample_count < self.min_condition_samples:
            result["error"] = (
                f"Insufficient data for {condition} load: {sample_count} samples "
                f"(minimum {self.min_condition_samples})"
            )
            return result

        df = prepare_training_data(condition_df, resample_freq="1min")
        result["sample_count"] = len(df)
        if len(df) < self.min_condition_samples:
            result["error"] = (
                f"Insufficient data for {condition} load after preprocessing: "
                f"{len(df)} samples (minimum {self.min_condition_samples})"
            )
            return result

        train_df, test_df = split_train_test(df, test_ratio=0.2)
        predictor = TimeSeriesPredictor(model_type="auto")
        predictor.fit(train_df)
        metrics = predictor.evaluate(test_df) if not test_df.empty else {}
        model_name = f"{device_id}_{parameter}_{condition}"
        model_path = self._model_path(device_id, parameter, condition)
        predictor.save(model_path)
        result.update({
            "model_name": model_name,
            "model_path": model_path,
            "model_type": predictor.model_type,
            "model_source": "newly_trained",
            "train_samples": len(train_df),
            "test_samples": len(test_df),
            "metrics": metrics,
        })
        return result

    def _train_full_fallback(self, raw_df, device_code: str, parameter: str):
        """训练并持久化不带工况标签的全量 fallback。"""
        full_df = prepare_training_data(raw_df, resample_freq="1min")
        if len(full_df) < self.min_condition_samples:
            return None
        train_df, test_df = split_train_test(full_df, test_ratio=0.2)
        predictor = TimeSeriesPredictor(model_type="auto")
        predictor.fit(train_df)
        metrics = predictor.evaluate(test_df) if not test_df.empty else {}
        model_name = f"{device_code}_{parameter}_fallback"
        model_path = os.path.join(self.model_dir, f"{model_name}.pkl")
        predictor.save(model_path)
        return {
            "model_name": model_name,
            "model_path": model_path,
            "model_type": predictor.model_type,
            "model_source": "fallback_full",
            "sample_count": len(full_df),
            "train_samples": len(train_df),
            "test_samples": len(test_df),
            "metrics": metrics,
            "fallback_reason": "condition samples insufficient",
        }

    def train_condition_models(self, device_id: str, parameter: str, history_hours: int = 168) -> dict:
        """训练高、低负荷模型，并返回稳定的每工况结果结构。"""
        db = next(get_db())
        try:
            device = get_device_by_code_or_name(db, device_id)
            if not device:
                return {"error": f"Device '{device_id}' not found"}

            resolved_name = resolve_param_name(parameter)
            raw_df = fetch_history_data(device_id, parameter, hours=history_hours)
            if raw_df.empty:
                return {"error": "No historical data available"}
            power_df = fetch_history_data(device_id, "power", hours=history_hours)
            high_df, low_df = self._split_by_condition(raw_df, power_df)
            results = {
                "high": self._train_one_condition(high_df, device.device_code, resolved_name, "high"),
                "low": self._train_one_condition(low_df, device.device_code, resolved_name, "low"),
            }
            if not power_df.empty:
                # 某一工况样本不足时，仍为该工况持久化一个明确标记的全量模型，
                # 让选择接口和评估接口共享同一 fallback 结果。
                missing_conditions = [
                    condition for condition, result in results.items()
                    if not result.get("model_path")
                ]
                if missing_conditions:
                    fallback = self._train_full_fallback(raw_df, device.device_code, resolved_name)
                    if fallback:
                        for condition in missing_conditions:
                            results[condition].update(fallback, error=None)
                return results
            fallback = self._train_full_fallback(raw_df, device.device_code, resolved_name)
            if not fallback:
                full_df = prepare_training_data(raw_df, resample_freq="1min")
                return {
                    condition: {
                        "condition": condition,
                        "condition_desc": _condition_description(condition),
                        "sample_count": len(full_df),
                        "model_name": None,
                        "model_path": None,
                        "model_type": None,
                        "model_source": "fallback_full",
                        "metrics": {},
                        "error": f"Insufficient training data: only {len(full_df)} samples",
                    }
                    for condition in ("high", "low")
                }
            for condition in ("high", "low"):
                results[condition].update({
                    **fallback,
                    "error": None,
                    "fallback_reason": "power history unavailable",
                })
            return results
        finally:
            db.close()

    def select_model_by_condition(self, device_id: str, parameter: str) -> dict:
        """加载当前工况缓存，缓存失效或不可用时训练并返回选择契约。"""
        db = next(get_db())
        try:
            device = get_device_by_code_or_name(db, device_id)
            if not device:
                return {"error": f"Device '{device_id}' not found"}
            resolved_name = resolve_param_name(parameter)
            condition = self.detect_condition(device_id)
            model_name = f"{device.device_code}_{resolved_name}_{condition}"
            model_path = self._model_path(device.device_code, resolved_name, condition)
            predictor = self._load_cached_model(model_path)
            model_source = "cached"
            fallback_reason = None
            train_result = None

            if predictor is None:
                model_source = "newly_trained"
                train_result = self.train_condition_models(device_id, parameter)
                condition_result = train_result.get(condition, {})
                if condition_result.get("model_path"):
                    model_path = condition_result["model_path"]
                    model_name = condition_result.get("model_name") or model_name
                    predictor = self._load_cached_model(model_path)
                    model_source = condition_result.get("model_source", model_source)
                    fallback_reason = condition_result.get("fallback_reason")

            if predictor is None:
                # 条件样本不足时使用全量数据 fallback，并持久化到独立文件。
                raw_df = fetch_history_data(device_id, parameter, hours=168)
                df = prepare_training_data(raw_df, resample_freq="1min")
                if len(df) < self.min_condition_samples:
                    return {
                        "error": f"Insufficient training data: only {len(df)} samples",
                        "device_id": device.device_code,
                        "parameter": resolved_name,
                        "condition": condition,
                        "model_name": model_name,
                        "model_source": "unavailable",
                    }
                predictor = TimeSeriesPredictor(model_type="auto")
                predictor.fit(df)
                model_name = f"{device.device_code}_{resolved_name}_fallback"
                model_path = os.path.join(self.model_dir, f"{model_name}.pkl")
                predictor.save(model_path)
                model_source = "fallback_full"
                fallback_reason = "condition model unavailable"

            metrics = {}
            sample_counts = {}
            if train_result:
                selected_result = train_result.get(condition, {})
                metrics = selected_result.get("metrics", {})
                sample_counts = {
                    key: value.get("sample_count", 0)
                    for key, value in train_result.items()
                    if key in ("high", "low") and isinstance(value, dict)
                }
            return {
                "device_id": device.device_code,
                "parameter": resolved_name,
                "condition": condition,
                "condition_desc": _condition_description(condition),
                "model_name": model_name,
                "model_path": model_path,
                "model_type": predictor.model_type,
                "model_source": model_source,
                "metrics": metrics,
                "sample_counts": sample_counts,
                "fallback_reason": fallback_reason,
            }
        finally:
            db.close()

    def compare_condition_models(self, device_id: str, parameter: str) -> dict:
        """返回高/低负荷 RMSE、MAE 对比及当前工况推荐模型。"""
        train_results = self.train_condition_models(device_id, parameter)
        if "error" in train_results:
            return train_results

        model_metrics = {
            f"model_{condition}": result.get("metrics", {})
            for condition, result in train_results.items()
            if isinstance(result, dict) and result.get("metrics")
        }
        comparison = compare_models(model_metrics)
        condition = self.detect_condition(device_id)
        selected = train_results.get(condition, {})
        return {
            "device_id": device_id,
            "parameter": resolve_param_name(parameter),
            "current_condition": condition,
            "current_condition_desc": _condition_description(condition),
            "models": train_results,
            "comparison": comparison,
            "recommended_model": f"model_{condition}" if selected.get("metrics") else None,
        }


def select_model_by_condition(device_id: str, parameter: str = "stator_temp") -> dict:
    """便捷函数：根据当前工况选择模型。"""
    return ModelSelector().select_model_by_condition(device_id, parameter)