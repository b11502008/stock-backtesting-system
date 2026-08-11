import sys
import os
import re
import pandas as pd
import warnings
from tqdm import tqdm 
from datetime import datetime
from strategies.ma_strategy import MAStrategy
from strategies.kd_strategy import KDStrategy
from strategies.bollinger_strategy import BollingerStrategy

# 輸出顯示設定
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)


def get_default_params(strategy_type):
    schema = get_strategy_param_schema()[strategy_type]
    return {key: value['default'] for key, value in schema.items()}

def get_strategy_param_schema():
    return {
        'ma': {
            'ma_short': {'default': 5, 'description': '短期均線期數'},
            'ma_long': {'default': 20, 'description': '長期均線期數'},
            'stop_loss_pct': {'default': None, 'description': '停損百分比（可選）'},
            'take_profit_pct': {'default': None, 'description': '停利百分比（可選）'},
            'position_pct': {'default': 10, 'description': '每次進場佔總資產比例（%）'}
        },
        'kd': {
            'kd_window': {'default': 9, 'description': 'KD計算視窗大小'},
            'lower_bound': {'default': 20, 'description': '超賣區閾值'},
            'upper_bound': {'default': 80, 'description': '超買區閾值'},
            'stop_loss_pct': {'default': None, 'description': '停損百分比（可選）'},
            'take_profit_pct': {'default': None, 'description': '停利百分比（可選）'},
            'position_pct': {'default': 10, 'description': '每次進場佔總資產比例（%）'}
        },
        'boll': {
            'bool_window': {'default': 20, 'description': '布林通道期數'},
            'std_multiplier': {'default': 2, 'description': '標準差乘數'},
            'stop_loss_pct': {'default': None, 'description': '停損百分比（可選）'},
            'take_profit_pct': {'default': None, 'description': '停利百分比（可選）'},
            'position_pct': {'default': 10, 'description': '每次進場佔總資產比例（%）'}
        }
    }

class Backtester:
    def __init__(self, strategy_name, start_date, end_date, initial_cash=1_000_000, broker_fee=0.001425, tax_sell_only=0.003, strategy_alias=None, custom_params=None):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.data_dir = os.path.join(base_dir, '..', 'data')
        self.asset_csv_dir = os.path.abspath(os.path.join(base_dir, '..', 'asset_csv'))
        os.makedirs(self.asset_csv_dir, exist_ok=True)

        self.strategy_name = strategy_name
        self.start_date = pd.to_datetime(start_date)
        self.end_date = pd.to_datetime(end_date)
        self.initial_cash = initial_cash
        self.broker_fee = broker_fee
        self.tax_sell_only = tax_sell_only
        self.strategy_alias = strategy_alias or strategy_name
        self.safe_alias = re.sub(r'[\\/*?:"<>|]', "_", self.strategy_alias)
        self.custom_params = custom_params or {}

        self.strategy_class = self._get_strategy_class(strategy_name)
        self.trades = []
        self.trade_by_date = {}
        self.asset_timeline = []
        self.logs = []

    def _log(self, msg):
        print(msg)
        self.logs.append(msg)

    def run(self):
        self._generate_all_trades()
        if not self.trades:
            self._log("⚠️ 無交易紀錄產生。可能因資料問題或策略條件未觸發。")
            return {
                "total_trades": 0,
                "average_pnl": 0,
                "total_pnl": 0,
                "win_rate": 0,
                "max_drawdown": 0,
                "annualized_return": 0
            }
        self._simulate_trading()
        summary = self.get_summary()
        self._save_asset_csv()
        self._save_benchmark_csv()
        return summary

    def _get_strategy_class(self, name):  
        if name == 'ma':
            return MAStrategy
        elif name == 'kd':
            return KDStrategy
        elif name == 'boll':
            return BollingerStrategy
        else:
            raise ValueError(f"Unsupported strategy: {name}")

    def _generate_all_trades(self):
        self._log("\n📥 載入股票資料並產生交易...")
        files = [f for f in os.listdir(self.data_dir) if f.endswith('.csv') and f != '0050.csv']
        for file in tqdm(files, desc=f"回測中：{self.strategy_alias}"):
            ticker = file.replace('.csv', '')
            df = pd.read_csv(os.path.join(self.data_dir, file))
            if 'Date' not in df or 'Close' not in df:
                self._log(f'⚠️ {file} 缺欄位，跳過')
                continue
            df['Date'] = pd.to_datetime(df['Date'])
            df = df[(df['Date'] >= self.start_date) & (df['Date'] <= self.end_date)].sort_values('Date')
            if df.empty:
                continue
            strategy = self.strategy_class(df.reset_index(drop=True), self.custom_params)
            stock_trades = strategy.generate_signals()
            for trade in stock_trades:
                trade['ticker'] = ticker
                self.trades.append(trade)
                self.trade_by_date.setdefault(trade['entry_date'], []).append(('buy', trade))
                self.trade_by_date.setdefault(trade['exit_date'], []).append(('sell', trade))

    def _simulate_trading(self): 
        self._log("\n🔁 模擬資產變化中...")
        cash = self.initial_cash
        position_pct = float(self.custom_params.get('position_pct', 10))
        holdings = {}
        price_cache = {}

        def get_total_asset(date):
            stock_value = 0
            for tkr, pos_list in holdings.items():
                if tkr not in price_cache:
                    df = pd.read_csv(os.path.join(self.data_dir, f"{tkr}.csv"))
                    df['Date'] = pd.to_datetime(df['Date'])
                    price_cache[tkr] = df.set_index('Date')['Close']
                series = price_cache[tkr]
                price = series.get(date)
                if price is None:
                    valid = series[series.index <= date]
                    price = valid.iloc[-1] if not valid.empty else None
                if price:
                    stock_value += sum([s * price for s, _ in pos_list])
            return cash + stock_value

        bench_df = pd.read_csv(os.path.join(self.data_dir, '0050.csv'))
        bench_df['Date'] = pd.to_datetime(bench_df['Date'])
        bench_df = bench_df[(bench_df['Date'] >= self.start_date) & (bench_df['Date'] <= self.end_date)]
        benchmark_dates = sorted(bench_df['Date'].unique())

        for current_date in benchmark_dates:
            # 處理當天的交易
            actions_today = self.trade_by_date.get(current_date, [])
            for action, trade in sorted(actions_today, key=lambda x: 0 if x[0] == 'sell' else 1):
                ticker = trade['ticker']
                entry_price = trade['entry_price']
                exit_price = trade['exit_price']

                if action == 'buy':
                    if pd.isna(entry_price) or entry_price <= 0:
                        continue
                    total_asset = get_total_asset(current_date)
                    budget = min(cash, total_asset * (position_pct / 100))
                    # 預估實際成本（含手續費）
                    shares = int(budget // (entry_price * (1 + self.broker_fee)))
                    if shares > 0:
                        cost = entry_price * shares * (1 + self.broker_fee)
                        if cost <= cash:
                            cash -= cost
                            holdings.setdefault(ticker, []).append((shares, entry_price))
                
                elif action == 'sell':
                    if pd.isna(exit_price) or exit_price <= 0:
                        continue
                    if ticker in holdings:
                        while holdings[ticker]:
                            shares_held, buy_price = holdings[ticker].pop(0)
                            cash += exit_price * shares_held * (1 - self.broker_fee - self.tax_sell_only)
                            pnl = (exit_price - buy_price) * shares_held
                            trade.update({'pnl': pnl, 'win': pnl > 0})

            # 記錄當日資產
            total_value = get_total_asset(current_date)
            ret_pct = (total_value / self.initial_cash - 1) * 100
            self.asset_timeline.append({'Date': current_date, 'Value': total_value, 'Return(%)': ret_pct})


    def _calculate_max_drawdown(self, equity_series):
        peak = equity_series.cummax()
        drawdown = (equity_series - peak) / peak
        return drawdown.min()

    def _calculate_annualized_return(self, equity_df):
        if equity_df.empty:
            return 0
        start_date = equity_df['Date'].iloc[0]
        end_date = equity_df['Date'].iloc[-1]
        days = (end_date - start_date).days
        final_value = equity_df['Value'].iloc[-1]
        total_return = final_value / self.initial_cash - 1
        return (1 + total_return) ** (365 / days) - 1 if days > 0 else 0

    def get_summary(self):
        df = pd.DataFrame(self.trades)
        df_equity = pd.DataFrame(self.asset_timeline).dropna()
        summary = {
            "total_trades": len(df),
            "average_pnl": df['pnl'].mean() if not df.empty else 0,
            "total_pnl": df['pnl'].sum() if not df.empty else 0,
            "win_rate": df['win'].mean() * 100 if not df.empty else 0,
            "max_drawdown": self._calculate_max_drawdown(df_equity['Value']) if not df_equity.empty else 0,
            'annualized_return': self._calculate_annualized_return(df_equity) * 100 if not df_equity.empty else 0
        }
        
        self._log("\n📊 回測統計摘要")
        for k, v in summary.items():
            if isinstance(v, float):
                self._log(f"{k}: {v:.2f}")
            else:
                self._log(f"{k}: {v}")
        
        return summary


    def _save_asset_csv(self):
        df_strategy = pd.DataFrame(self.asset_timeline).dropna()
        if df_strategy.empty:
            self._log("⚠️ 無資產資料產生")
            return

        df_strategy['Date'] = pd.to_datetime(df_strategy['Date'])
        csv_save_path = os.path.join(self.asset_csv_dir, f'{self.safe_alias}_資產紀錄.csv')
        df_strategy.to_csv(csv_save_path, index=False)
        self._log(f"📄 資產紀錄 CSV 儲存於：{csv_save_path}")
   
    def _save_benchmark_csv(self):
        file_path = os.path.join(self.data_dir, "0050.csv")
        df = pd.read_csv(file_path)
        df['Date'] = pd.to_datetime(df['Date'])
        df = df[(df['Date'] >= self.start_date) & (df['Date'] <= self.end_date)].copy()

        if df.empty:
            self._log("⚠️ 無有效 0050 資料，無法產出 benchmark 資產紀錄")
            return

        first_close = df.iloc[0]['Close']
        shares = int(self.initial_cash // first_close)
        remaining_cash = self.initial_cash - (shares * first_close)
        df['Asset'] = df['Close'] * shares + remaining_cash

        output_path = os.path.join(self.asset_csv_dir, "benchmark_asset.csv")
        df[['Date', 'Asset']].to_csv(output_path, index=False)
        self._log(f"✅ Benchmark 資產紀錄已儲存：{output_path}")

    def get_all_timeline(self):
        return self.asset_timeline

    def get_all_trades(self):
        return self.trades

    def get_logs(self):
        return self.logs
    
    def get_strategy_key(self):
        return self.safe_alias  # 或 return self.strategy_alias 也行


