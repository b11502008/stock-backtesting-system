import numpy as np
import pandas as pd
from strategies.base import BaseStrategy

class KDStrategy(BaseStrategy):
    def __init__(self, df, params):
        super().__init__(df, params)
        self.compute_kd()

    def compute_kd(self):
        kd_window = int(self.params.get('kd_window', 9))
        low_min = self.df['Low'].rolling(window=kd_window).min()
        high_max = self.df['High'].rolling(window=kd_window).max()
        rsv = (self.df['Close'] - low_min) / (high_max - low_min) * 100

        K_list = []
        D_list = []
        k = 50
        d = 50
        for val in rsv:
            if pd.isna(val):
                K_list.append(np.nan)
                D_list.append(np.nan)
                continue
            k = k * 2 / 3 + val * 1 / 3
            d = d * 2 / 3 + k * 1 / 3
            K_list.append(k)
            D_list.append(d)

        self.df['K'] = K_list
        self.df['D'] = D_list

    def generate_signals(self):
        signals = []
        lower_bound = int(self.params.get('lower_bound', 50))
        upper_bound = int(self.params.get('upper_bound', 50))

        position = None  # 字典
        for i in range(1, len(self.df)):
            prev_row = self.df.iloc[i - 1]
            curr_row = self.df.iloc[i]
            
            # 檢查停損停利
            if position:
                exit_signal = self.apply_stop_condition(position['entry_index'], position['entry_price'], i)
                if exit_signal is not None:
                    signals.append({**position, **exit_signal})
                    position = None
                    continue
            
            # KD 低檔金叉進場
            if (
                position is None and
                prev_row['K'] < prev_row['D'] and
                curr_row['K'] > curr_row['D'] and
                curr_row['K'] < lower_bound and
                curr_row['D'] < lower_bound
            ):
                position = {
                    'entry_index': i,
                    'entry_date': curr_row['Date'],
                    'entry_price': curr_row['Close']
                }
                continue

            # KD 高檔死叉出場
            if (
                position and
                prev_row['K'] > prev_row['D'] and
                curr_row['K'] < curr_row['D'] and
                curr_row['K'] > upper_bound and
                curr_row['D'] > upper_bound
            ):
                exit_signal = {
                    'exit_index': i,
                    'exit_date': curr_row['Date'],
                    'exit_price': curr_row['Close'],
                    'reason': 'kd_death_cross_exit'
                }
                signals.append({**position, **exit_signal})
                position = None
        if position:
            exit_signal = self.final_exit(position['entry_index'])    
            if exit_signal is not None:
                signals.append({**position, **exit_signal})

        return signals