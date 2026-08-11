import os
from backtester.backtester import Backtester, get_default_params
from backtester.compare_strategy import compare_strategies

def safe_int(val):
    try:
        return int(val)
    except (TypeError, ValueError):
        return None

def run_backtest_from_gui(param_dict):
    """
    param_dict 是由前端傳入的 dict，格式如下：
    {
        "start_time": "2023-06-26",
        "end_time": "2025-05-14",
        "initial_cash": "1000000",
        "broker_fee": "0.001425",
        "tax_sell_only": "0.003",
        "策略 1": {
            "strategy_name": "kd",
            "kd_window": 9,
            "lower_bound": 20,
            "upper_bound": 80,
            ...
        }
    }
    """
    start_date = param_dict["start_time"]
    end_date = param_dict["end_time"]
    initial_cash = float(param_dict["initial_cash"])
    broker_fee = float(param_dict["broker_fee"])
    tax_sell_only = float(param_dict.get("tax_sell_only", 0.003))

    summary = {}
    link = {}

    # 清除之前的資產記錄 CSV
    asset_csv_dir = os.path.join(os.path.dirname(__file__), 'asset_csv')
    if os.path.exists(asset_csv_dir):
        files = os.listdir(asset_csv_dir)
        for f in files:
            if f.endswith(".csv"):
                os.remove(os.path.join(asset_csv_dir, f))

    for strategy_alias, strategy_param in param_dict.items():
        if strategy_alias in ["start_time", "end_time", "initial_cash", "broker_fee", "tax_sell_only"]:
            continue

        strategy_name = strategy_param.get("strategy_name")
        strategy_param['stop_loss_pct'] = safe_int(strategy_param.get('stop_loss_pct'))
        strategy_param['take_profit_pct'] = safe_int(strategy_param.get('take_profit_pct'))

        bt = Backtester(
            strategy_name=strategy_name,
            strategy_alias=strategy_alias,
            start_date=start_date,
            end_date=end_date,
            initial_cash=initial_cash,
            broker_fee=broker_fee,
            tax_sell_only=tax_sell_only,
            custom_params=strategy_param,
        )
        summary[strategy_alias] = bt.run()
        link[strategy_alias] = bt.get_strategy_key()

    base_dir = os.path.dirname(__file__)
    data_dir = os.path.join(base_dir, "data")
    aliases = list(link.keys())

    results = compare_strategies(link, aliases, data_dir, start_date, end_date)
    return link, results, summary

    
