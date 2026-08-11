import pandas as pd
from strategies.base import BaseStrategy

class BollingerStrategy(BaseStrategy):
    def __init__(self, df, params):
        super().__init__(df, params)
        self.compute_bollinger()
    
    def compute_bollinger(self):
        bool_window = int(self.params.get('bool_window', 20))
        std_multiplier = int(self.params.get('std_multiplier', 2))

        self.df['SMA'] = self.df['Close'].rolling(window=bool_window).mean()
        self.df['STD'] = self.df['Close'].rolling(window=bool_window).std()
        self.df['Upper'] = self.df['SMA'] + self.df['STD'] * std_multiplier
        self.df['Lower'] = self.df['SMA'] - self.df['STD'] * std_multiplier
    
    def generate_signals(self):
        trades = []
        position = None
        touched_upper = False
        window = int(self.params.get('bool_window', 20))

        for i in range(window, len(self.df)):
            prev_row = self.df.iloc[i - 1]
            curr_row = self.df.iloc[i]

            # 出場邏輯
            if position:
                # 檢查停損停利
                exit_signal = self.apply_stop_condition(position['entry_index'], position['entry_price'], i)
                if exit_signal is not None:
                    trades.append({**position, **exit_signal})
                    position = None
                    touched_upper = False
                    continue
            
                # 再次跌破下軌
                if curr_row['Close'] < curr_row['Lower']:
                    trades.append({
                        **position,
                        'exit_index': i,
                        'exit_date': curr_row['Date'],
                        'exit_price': curr_row['Close'],
                        'reason': 'break_lower_again'
                    })
                    position = None
                    touched_upper = False
                    continue
                
                # 是否突破上軌
                if curr_row['Close'] > curr_row['Upper']:
                    touched_upper = True
                    continue

                # 突破上軌後回落 0.995 上軌值以下
                if touched_upper and curr_row["Close"] < 0.995 * curr_row['Upper']:
                    trades.append({
                        **position,
                        'exit_index': i,
                        'exit_date': curr_row['Date'],
                        'exit_price': curr_row['Close'],
                        'reason': 'fall_from_upper'
                    })
                    position = None
                    touched_upper = False
                    continue
            # 進場邏輯
            else:
                # 等待從下軌跌破 → 回到 1.005 倍下軌再進場
                if prev_row['Close'] < prev_row['Lower'] and curr_row['Close'] >= 1.005 * curr_row['Lower']:
                    position = {
                        'entry_index': i,
                        'entry_date': curr_row['Date'],
                        'entry_price': curr_row['Close']
                    }
        
        if position:
            exit_signal = self.final_exit(position['entry_index'])
            if exit_signal is not None:
                trades.append({**position, **exit_signal}) 

        return trades