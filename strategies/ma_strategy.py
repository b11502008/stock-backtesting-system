import numpy as np
import pandas as pd
from strategies.base import BaseStrategy

class MAStrategy(BaseStrategy):    
    def generate_signals(self):
        short_window = int(self.params.get('ma_short', 5))
        long_window = int(self.params.get('ma_long', 20))

        self.df["MA_short"] = self.df['Close'].rolling(window=short_window).mean()
        self.df["MA_long"] = self.df['Close'].rolling(window=long_window).mean()
        self.df['signal'] = np.where(self.df['MA_short'] > self.df['MA_long'], 1, 0)

        trades = []
        holding = False
        entry_index = None
        entry_price = None

        for i in range(1, len(self.df)):
            prev_signal = self.df.iloc[i - 1]['signal']
            curr_signal = self.df.iloc[i]['signal']

            # MA 金叉進場
            if not holding and prev_signal == 0 and curr_signal == 1:
                entry_index = i
                entry_price = self.df.iloc[i]['Close']
                holding = True
                continue

            elif holding:
                # 停利停損優先
                stop_result = self.apply_stop_condition(entry_index, entry_price, i)
                if stop_result is not None:
                    trades.append({
                        'entry_index': entry_index,
                        'entry_date': self.df.iloc[entry_index]['Date'],
                        'entry_price': entry_price,
                        **stop_result
                    })
                    holding = False
                    entry_index = None
                    entry_price = None
                    continue

                # MA 死叉出場
                if prev_signal == 1 and curr_signal == 0:
                    exit_row = self.df.iloc[i]
                    trades.append({
                        'entry_index': entry_index,
                        'entry_date': self.df.iloc[entry_index]['Date'],
                        'entry_price': entry_price,
                        'exit_index': i,
                        'exit_date': exit_row['Date'],
                        'exit_price': exit_row['Close'],
                        'reason': 'ma_cross'
                    })
                    holding = False
                    entry_index = None
                    entry_price = None

        if holding:
            final_exit = self.final_exit(entry_index)
            if final_exit is not None:
                trades.append({
                    'entry_index': entry_index,
                    'entry_date': self.df.iloc[entry_index]['Date'],
                    'entry_price': entry_price,
                    **final_exit
                })
        
        return trades