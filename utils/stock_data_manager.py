import os
import time
import pandas as pd
import requests
from tqdm import tqdm
from datetime import datetime

class StockDataManager():
    def __init__(self, data_dir=None):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.data_dir = data_dir or os.path.join(base_dir, '..', 'data')
        os.makedirs(self.data_dir, exist_ok=True)
    
    def convert_minguo_to_ad(self, date_str):
        y, m, d = date_str.split('/')
        return f'{int(y) + 1911}-{m}-{d}'
    
    def parse_twse_response(self, data):
        df = pd.DataFrame(data['data'], columns=data['fields'])
        df['日期'] = df['日期'].apply(self.convert_minguo_to_ad)
        df['日期'] = pd.to_datetime(df['日期'], format='%Y-%m-%d', errors='coerce')
        df = df.rename(columns={
            '日期': 'Date',
            '成交股數': 'Volume',
            '開盤價': 'Open',
            '最高價': 'High',
            '最低價': 'Low',
            '收盤價': 'Close'
        })[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']]

        for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce')

        return df.dropna(subset=['Open', 'High', 'Low', 'Close'])
    
    def fetch_monthly_data(self, ticker, year, month):
        date_str = f'{year}{month:02d}01'
        url = f'https://www.twse.com.tw/exchangeReport/STOCK_DAY?response=json&date={date_str}&stockNo={ticker}'
        headers = {'User-Agent': 'Mozilla/5.0'}

        try:
            res = requests.get(url, headers=headers, timeout=10)
            data = res.json()
            if data['stat'] != 'OK':
                print(f"[無資料] {ticker} - {year}/{month:02d}")
                return None
            return self.parse_twse_response(data)
        
        except Exception as e:
            print(f'[錯誤] {ticker} - {year}/{month:02d} 擷取失敗：{e}')
            return None
    
    def fetch_all_history(self, ticker, start_year=2015):
        print(f'\n[下載中] {ticker} 歷史資料...')
        all_data = []
        today = pd.to_datetime(datetime.today().date())

        date_ranges = [
            (year, month)
            for year in range(start_year, today.year + 1)
            for month in range(1, 13)
            if not (year == today.year and month > today.month)
        ]

        for year, month in tqdm(date_ranges, desc=f"{ticker} 下載進度"):
            df = self.fetch_monthly_data(ticker, year, month)
            if df is not None:
                all_data.append(df)
                time.sleep(0.8)

        if all_data:
            df_all = pd.concat(all_data)
            df_all.sort_values('Date', inplace=True)
            df_all.to_csv(os.path.join(self.data_dir, f'{ticker}.csv'), index=False)
            print(f"[完成] 儲存 {ticker}，共 {len(df_all)} 筆資料")
        else:
            print(f"[失敗] {ticker} 沒有下載到任何資料")
    
    def update_existing_csv(self, ticker):
        file_path = os.path.join(self.data_dir, f'{ticker}.csv')
        try:
            existing_df = pd.read_csv(file_path, parse_dates=['Date'])
            existing_df['Date'] = pd.to_datetime(existing_df['Date'], errors='coerce')
            last_date = existing_df['Date'].max()
            today = pd.to_datetime(datetime.today().date())
            if last_date >= today:
                print(f'[快取] {ticker} 資料已為最新')
                return
        except Exception as e:
            print(f'[錯誤] 讀取 {ticker} 時發生錯誤：{e}')
            return
        
        date = datetime.today().strftime('%Y%m%d')
        url = f'https://www.twse.com.tw/exchangeReport/STOCK_DAY?response=json&date={date}&stockNo={ticker}'
        headers = {'User-Agent': 'Mozilla/5.0'}

        try:
            res = requests.get(url, headers=headers, timeout=10)
            data = res.json()
            if data['stat'] != 'OK':
                print(f'[失敗] 讀取 {ticker} 無資料更新：{data["stat"]}')
                return
            
            new_df = self.parse_twse_response(data)
            combined = pd.concat([existing_df, new_df])
            combined = combined.drop_duplicates(subset='Date').sort_values('Date')
            combined.to_csv(file_path, index=False)
            print(f'[更新] {ticker} 資料已更新')

        except Exception as e:
            print(f'[錯誤] {ticker} 更新失敗：{e}')

    def add_new_stocks(self, tickers, start_year=2015):
        for ticker in tqdm(tickers, desc="新增股票資料"):
            file_path = os.path.join(self.data_dir, f'{ticker}.csv')
            if os.path.exists(file_path):
                print(f'[略過] {ticker} 已存在資料檔案')
                continue
            self.fetch_all_history(ticker, start_year)

    def update_all(self):
        csv_files = [file for file in os.listdir(self.data_dir) if file.endswith('.csv')]
        for file in tqdm(csv_files, desc="更新全部股票資料"):
            ticker = file.replace('.csv', '')
            self.update_existing_csv(ticker)
            time.sleep(1)

if __name__ == '__main__':
    manager = StockDataManager()
    #manager.add_new_stocks(['2882'])
    manager.update_all()