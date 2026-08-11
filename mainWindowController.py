import os
from PySide6.QtWidgets import QMainWindow, QVBoxLayout, QWidget, QPushButton, QScrollArea, QLineEdit, QCheckBox, QLabel, QComboBox
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, Qt
from strategyController import strategyController
from run_backtester import run_backtest_from_gui
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

matplotlib.rcParams['font.sans-serif'] = ['Microsoft JhengHei']
matplotlib.rcParams['axes.unicode_minus'] = False

def safe_int(val):
    try:
        return int(val)
    except (TypeError, ValueError):
        return None

class MainWindowController(QMainWindow):
    def __init__(self):
        super().__init__()

        self.strategyNumber = 1
        self.strategyNameMap = {}

        loader = QUiLoader()
        self.loader = loader
        ui_path = os.path.join(os.path.dirname(__file__), "ui", "mainWindow.ui")
        ui_file = QFile(ui_path)
        ui_file.open(QFile.ReadOnly)
        self.ui = loader.load(ui_file, None)
        ui_file.close()
        self.setCentralWidget(self.ui)
        self.resize(1000, 550)

        self.plotWidget = self.ui.findChild(QWidget, "plotWidget")
        self.plotWidget.setLayout(QVBoxLayout())

        self.startTime = self.ui.findChild(QLineEdit, "startTime")
        self.endTime = self.ui.findChild(QLineEdit, "endTime")
        self.initialCash = self.ui.findChild(QLineEdit, "initialCash")
        self.brokerFee = self.ui.findChild(QLineEdit, "brokerFee")
        self.startButton = self.ui.findChild(QPushButton, "startButton")
        self.addButton = self.ui.findChild(QPushButton, "addButton")
        self.strategyArea = self.ui.findChild(QScrollArea, "strategyArea")
        self.selectArea = self.ui.findChild(QScrollArea, "selectArea")
        self.winRate = self.ui.findChild(QLabel, "winRate")
        self.totalPnl = self.ui.findChild(QLabel, "totalPnl")
        self.IRR = self.ui.findChild(QLabel, "IRR")
        self.maxDrawdown = self.ui.findChild(QLabel, "maxDrawdown")
        self.chooseStrategy = self.ui.findChild(QComboBox, "chooseStrategy")
        self.standardTrend = self.ui.findChild(QCheckBox, "standardTrend")

        self.strategyContent = self.strategyArea.widget()
        self.strategyLayout = self.strategyContent.layout()
        self.strategyLayout.setAlignment(Qt.AlignTop)
        self.selectContent = self.ui.findChild(QWidget, "scrollAreaWidgetContents_2")
        self.selectLayout = self.selectContent.layout()
        self.selectLayout.setAlignment(Qt.AlignTop)

        self.startButton.clicked.connect(self.startBacktesting)
        self.addButton.clicked.connect(self.addStrategy)
        self.standardTrend.stateChanged.connect(self.plot)
        self.chooseStrategy.currentTextChanged.connect(self.updatePerformanceSummary)

    def startBacktesting(self):
        self.summary = {}  # 先定義空的 summary
        allParam = {}
        self.chooseStrategy.clear()

        for widget in self.strategyNameMap.keys():
            strategy_name = widget.getStrategyName()
            strategy_param = widget.getParam()

            strategy_param['stop_loss_pct'] = safe_int(strategy_param.get('stop_loss_pct'))
            strategy_param['take_profit_pct'] = safe_int(strategy_param.get('take_profit_pct'))

            allParam[strategy_name] = strategy_param

            if "ma_short" in strategy_param:
                allParam[strategy_name]["strategy_name"] = "ma"
            elif "kd_window" in strategy_param:
                allParam[strategy_name]["strategy_name"] = "kd"
            else:
                allParam[strategy_name]["strategy_name"] = "boll"

            self.chooseStrategy.addItem(strategy_name)

        allParam["start_time"] = self.startTime.text()
        allParam["end_time"] = self.endTime.text()
        allParam["initial_cash"] = self.initialCash.text()
        allParam["broker_fee"] = str(float(self.brokerFee.text()) / 100)
        allParam["tax_sell_only"] = "0.003"

        self.link, result, self.summary = run_backtest_from_gui(allParam)
        self.results = result

        self.updatePerformanceSummary()
        self.plot()

    def updatePerformanceSummary(self):
        selected_strategy = self.chooseStrategy.currentText()
        if selected_strategy in self.summary:
            res = self.summary[selected_strategy]
            self.winRate.setText(f"{res['win_rate']:.2f}%")
            self.totalPnl.setText(f"{res['total_pnl']:.2f}")
            self.IRR.setText(f"{res['annualized_return']:.2f}%")
            self.maxDrawdown.setText(f"{res['max_drawdown']:.2f}%")
        else:
            self.winRate.setText("")
            self.totalPnl.setText("")
            self.IRR.setText("")
            self.maxDrawdown.setText("")

    def plot(self, _=None):
        if not hasattr(self, 'results') or self.results is None:
            return
        self.plot_selected_strategies(self.results)

    def plot_selected_strategies(self, results):
        dates = results['dates']
        strategies = results['strategies']
        strategy_names = [
            widget.getStrategyName()
            for widget, meta in self.strategyNameMap.items()
            if meta["checkBox"].isChecked()
        ]

        layout = self.plotWidget.layout()
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()

        fig = Figure(figsize=(12, 6))
        ax = fig.add_subplot(111)

        if self.standardTrend.isChecked():
            try:
                benchmark_df = pd.read_csv(os.path.join(os.path.dirname(__file__), "asset_csv", "benchmark_asset.csv"))
                benchmark_df['Date'] = pd.to_datetime(benchmark_df['Date'])
                benchmark_df = benchmark_df.dropna()
                if not benchmark_df.empty:
                    benchmark_dates = benchmark_df['Date'].dt.strftime("%Y-%m-%d").tolist()
                    benchmark_values = benchmark_df['Asset']
                    first_val = benchmark_values.iloc[0]
                    benchmark_returns = (benchmark_values / first_val - 1) * 100
                    ax.plot(benchmark_dates, benchmark_returns, label='0050 (大盤)', linestyle='--', linewidth=2)
            except Exception as e:
                print(f"⚠️ 無法載入 benchmark_asset.csv: {e}")

        for name in strategy_names:
            linkage = self.link[name]
            ax.plot(dates, strategies[linkage], label=name)

        ax.set_title('多策略報酬比較')
        ax.set_xlabel('日期')
        ax.set_ylabel('報酬率 (%)')
        ax.legend()
        ax.grid(True)
        max_ticks = 10
        total_dates = len(dates)
        interval = max(1, total_dates // max_ticks)
        selected_indices = range(0, total_dates, interval)
        selected_dates = [dates[i] for i in selected_indices]  
        ax.set_xticks(selected_dates)
        ax.set_xticklabels(selected_dates, rotation=45)
        fig.tight_layout()

        canvas = FigureCanvas(fig)
        layout.addWidget(canvas)

    def addStrategy(self):
        subWidget = strategyController(number=self.strategyNumber)
        subWidget.setFixedHeight(50)
        self.strategyLayout.addWidget(subWidget)
        strategyName = subWidget.getStrategyName()
        checkBox = QCheckBox(strategyName)
        checkBox.setFixedHeight(20)
        self.selectLayout.addWidget(checkBox)
        index = self.chooseStrategy.count()
        self.strategyNameMap[subWidget] = {"checkBox": checkBox, "comboIndex": index}
        subWidget.requestSyncName.connect(self.updateStrategyName)
        subWidget.requestDelete.connect(self.deleteStrategy)
        self.strategyNumber += 1
        subWidget.requestSetup()
        checkBox.stateChanged.connect(self.plot)

    def updateStrategyName(self, widget):
        strategyName = widget.getStrategyName()
        checkBox = self.strategyNameMap.get(widget)["checkBox"]
        index = self.strategyNameMap.get(widget)["comboIndex"]
        self.chooseStrategy.setItemText(index, strategyName)
        checkBox.setText(strategyName)

    def deleteStrategy(self, widget):
        self.strategyLayout.removeWidget(widget)
        widget.setParent(None)
        widget.deleteLater()

        checkBox = self.strategyNameMap[widget]["checkBox"]
        self.selectLayout.removeWidget(checkBox)
        checkBox.setParent(None)
        checkBox.deleteLater()

        index = self.strategyNameMap[widget]["comboIndex"]
        self.chooseStrategy.removeItem(index)

        del self.strategyNameMap[widget]