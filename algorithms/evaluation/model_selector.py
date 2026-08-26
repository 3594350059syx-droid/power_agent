import os
from datetime import datetime, timedelta
from backend.database.connection import get_db
from backend.database.models import Device, SensorPoint, TimeseriesData
from backend.services.data_service import get_device_by_code_or_name, resolve_param_name
from algorithms.prediction import TimeSeriesPredictor, fetch_history_data, prepare_training_data
from algorithms.prediction.model_utils import split_train_test
from .metrics import evaluate_predictions, compare_models


MODEL_DIR = 'models/prediction'

HIGH_LOAD_THRESHOLD = 280.0


class ModelSelector:
    """
    模型自适应选择器

    根据当前工况（高负荷/低负荷）自动选择并切换预测模型。
    - 高负荷: power > 280MW
    - 低负荷: power <= 280MW
    """

    def __init__(self, model_dir: str = MODEL_DIR):
        self.model_dir = model_dir

    def detect_condition(self, device_id: str) -> str:
        """
        识别当前工况

        参数:
            device_id: str - 设备编码

        返回:
            str - 工况 ('high' 或 'low')
        """
        db = next(get_db())
        try:
            device = get_device_by_code_or_name(db, device_id)
            if not device:
                return 'low'

            sensor = db.query(SensorPoint).filter(
                SensorPoint.device_id == device.id,
                SensorPoint.point_name == 'power'
            ).first()

            if not sensor:
                return 'low'

            recent = db.query(TimeseriesData.value).filter(
                TimeseriesData.device_id == device.id,
                TimeseriesData.sensor_id == sensor.id,
                TimeseriesData.recorded_at >= datetime.now() - timedelta(minutes=30)
            ).order_by(TimeseriesData.recorded_at.desc()).limit(30).all()

            if not recent:
                return 'low'

            avg_power = sum(r[0] for r in recent) / len(recent)
            return 'high' if avg_power > HIGH_LOAD_THRESHOLD else 'low'

        finally:
            db.close()

    def train_condition_models(self, device_id: str, parameter: str,
                               history_hours: int = 168) -> dict:
        """
        分别训练高负荷和低负荷两个模型

        参数:
            device_id: str - 设备编码
            parameter: str - 测点参数名
            history_hours: int - 训练数据时长

        返回:
            dict - 训练结果
        """
        db = next(get_db())
        try:
            device = get_device_by_code_or_name(db, device_id)
            if not device:
                return {'error': f"Device '{device_id}' not found"}

            resolved_name = resolve_param_name(parameter)

            raw_df = fetch_history_data(device_id, parameter, hours=history_hours)
            if raw_df.empty:
                return {'error': 'No historical data available'}

            power_df = fetch_history_data(device_id, 'power', hours=history_hours)

            if not power_df.empty:
                merged = raw_df.merge(power_df[['ds', 'y']], on='ds', suffixes=('', '_power'))
                high_load_df = merged[merged['y_power'] > HIGH_LOAD_THRESHOLD][['ds', 'y']]
                low_load_df = merged[merged['y_power'] <= HIGH_LOAD_THRESHOLD][['ds', 'y']]
            else:
                high_load_df = raw_df.iloc[:len(raw_df) // 2]
                low_load_df = raw_df.iloc[len(raw_df) // 2:]

            results = {}

            for condition, condition_df in [('high', high_load_df), ('low', low_load_df)]:
                if len(condition_df) < 30:
                    results[condition] = {'error': f'Insufficient data for {condition} load: {len(condition_df)} samples'}
                    continue

                df = prepare_training_data(condition_df, resample_freq='1min')
                train_df, test_df = split_train_test(df, test_ratio=0.2)

                predictor = TimeSeriesPredictor(model_type='auto')
                predictor.fit(train_df)

                metrics = predictor.evaluate(test_df) if not test_df.empty else {}

                model_name = f"{device.device_code}_{resolved_name}_{condition}"
                filepath = os.path.join(self.model_dir, f"{model_name}.pkl")
                os.makedirs(self.model_dir, exist_ok=True)
                predictor.save(filepath)

                results[condition] = {
                    'model_name': model_name,
                    'model_path': filepath,
                    'model_type': predictor.model_type,
                    'train_samples': len(train_df),
                    'test_samples': len(test_df),
                    'metrics': metrics
                }

            return results

        finally:
            db.close()

    def select_model_by_condition(self, device_id: str, parameter: str) -> dict:
        """
        根据当前工况自动选择模型

        参数:
            device_id: str - 设备编码
            parameter: str - 测点参数名

        返回:
            dict - 模型选择结果
        """
        db = next(get_db())
        try:
            device = get_device_by_code_or_name(db, device_id)
            if not device:
                return {'error': f"Device '{device_id}' not found"}

            resolved_name = resolve_param_name(parameter)
            condition = self.detect_condition(device_id)

            model_name = f"{device.device_code}_{resolved_name}_{condition}"
            model_path = os.path.join(self.model_dir, f"{model_name}.pkl")

            if os.path.exists(model_path):
                predictor = TimeSeriesPredictor.load(model_path)
                model_source = 'cached'
            else:
                train_result = self.train_condition_models(device_id, parameter)
                if condition in train_result and 'model_path' in train_result[condition]:
                    predictor = TimeSeriesPredictor.load(train_result[condition]['model_path'])
                    model_source = 'newly_trained'
                else:
                    raw_df = fetch_history_data(device_id, parameter, hours=168)
                    df = prepare_training_data(raw_df, resample_freq='1min')
                    predictor = TimeSeriesPredictor(model_type='auto')
                    predictor.fit(df)
                    model_source = 'fallback_full'

            return {
                'device_id': device.device_code,
                'parameter': resolved_name,
                'condition': condition,
                'condition_desc': '高负荷(>280MW)' if condition == 'high' else '低负荷(≤280MW)',
                'model_name': model_name,
                'model_type': predictor.model_type,
                'model_source': model_source
            }

        finally:
            db.close()

    def compare_condition_models(self, device_id: str, parameter: str) -> dict:
        """
        对比高负荷/低负荷模型的预测效果

        参数:
            device_id: str - 设备编码
            parameter: str - 测点参数名

        返回:
            dict - 模型对比结果
        """
        train_results = self.train_condition_models(device_id, parameter)

        if 'error' in train_results:
            return train_results

        eval_results = {}
        for condition, result in train_results.items():
            if 'metrics' in result:
                eval_results[f"model_{condition}"] = result['metrics']

        comparison = compare_models(eval_results)

        condition = self.detect_condition(device_id)

        return {
            'device_id': device_id,
            'parameter': resolve_param_name(parameter),
            'current_condition': condition,
            'current_condition_desc': '高负荷(>280MW)' if condition == 'high' else '低负荷(≤280MW)',
            'models': train_results,
            'comparison': comparison,
            'recommended_model': f"model_{condition}"
        }


def select_model_by_condition(device_id: str, parameter: str = 'stator_temp') -> dict:
    """
    便捷函数：根据工况选择模型

    参数:
        device_id: str - 设备编码
        parameter: str - 测点参数名

    返回:
        dict - 模型选择结果
    """
    selector = ModelSelector()
    return selector.select_model_by_condition(device_id, parameter)