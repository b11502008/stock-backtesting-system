from abc import ABC, abstractmethod
import numpy as np
import pandas as pd

class BaseStrategy(ABC):
    def __init__(self, df, params:dict):
        self.df = df
        self.params = params
    
    @abstractmethod
    def generate_signals(self):
        pass

    def apply_stop_condition(self, entry_index, entry_price, exit_limit_index=None):
        stop_loss_pct = self.params.get('stop_loss_pct')
        take_profit_pct = self.params.get('take_profit_pct')
        if stop_loss_pct is None and take_profit_pct is None:
            return None
        
        if stop_loss_pct is not None:
            stop_loss_pct = int(stop_loss_pct)
        if take_profit_pct is not None:
            take_profit_pct = int(take_profit_pct)

        stop_loss_price = entry_price * (1 - stop_loss_pct / 100) if stop_loss_pct is not None else -np.inf
        take_profit_price = entry_price * (1 + take_profit_pct / 100) if take_profit_pct is not None else np.inf

        df_slice = self.df.iloc[entry_index + 1:exit_limit_index + 1 if exit_limit_index else None].copy()

        # Create boolean masks
        take_profit_hits = df_slice['High'] >= take_profit_price
        stop_loss_hits = df_slice['Low'] <= stop_loss_price

        # Find first take profit hit
        tp_index = np.argmax(take_profit_hits.to_numpy()) if take_profit_hits.any() else None
        sl_index = np.argmax(stop_loss_hits.to_numpy()) if stop_loss_hits.any() else None

        # Determine exit index
        if tp_index is not None and (sl_index is None or tp_index <= sl_index):
            row = df_slice.iloc[tp_index]
            return {
                'exit_index': entry_index + 1 + tp_index,
                'exit_date': row['Date'],
                'exit_price': take_profit_price,
                'reason': 'take_profit'
            }

        elif sl_index is not None:
            row = df_slice.iloc[sl_index]
            return {
                'exit_index': entry_index + 1 + sl_index,
                'exit_date': row['Date'],
                'exit_price': stop_loss_price,
                'reason': 'stop_loss'
            }

        return None
    
    def final_exit(self, entry_index):
        if entry_index < len(self.df) - 1:
            final_row = self.df.iloc[-1]
            return {
                'exit_index': len(self.df) - 1,
                'exit_date': final_row['Date'],
                'exit_price': final_row['Close'],
                'reason': 'final_close'
            }
        else:
            return None