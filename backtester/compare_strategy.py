import os
import pandas as pd

def load_strategy_result(strategy_key, alias, data_dir):
    # 組出完整檔案路徑（包含 asset_csv 資料夾與副檔名）
    base_dir = os.path.dirname(data_dir)  # 回到上層
    csv_path = os.path.join(base_dir, "asset_csv", f"{strategy_key}_資產紀錄.csv")
    df = pd.read_csv(csv_path)
    df['Date'] = pd.to_datetime(df['Date'])
    df = df[['Date', 'Return(%)']].copy()
    df.rename(columns={'Return(%)': alias}, inplace=True)
    return df

def compare_strategies(link, aliases, data_dir, start_date, end_date):
    result_df = None
    for alias in aliases:
        strategy_key = link[alias]  # 通常是 '策略 1_資產紀錄'
        df = load_strategy_result(strategy_key, alias, data_dir)
        if result_df is None:
            result_df = df
        else:
            result_df = pd.merge(result_df, df, on='Date', how='outer')

    result_df = result_df.sort_values('Date')
    result_df = result_df.fillna(method='ffill').fillna(0)
    dates = result_df['Date'].dt.strftime('%Y-%m-%d').tolist()
    strategies = {col: result_df[col].tolist() for col in result_df.columns if col != 'Date'}

    return {
        'dates': dates,
        'strategies': strategies
    }