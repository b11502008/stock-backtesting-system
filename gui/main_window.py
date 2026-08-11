import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QDateEdit, QLineEdit, QPushButton, QScrollArea, QDialog,
    QToolButton, QFrame
)
from PyQt5.QtCore import QDate
from .strategy_dialog import StrategyDialog
# TODO: 載入你的後端回測函式
# from backtester.run_backtester import backtest

class StrategyItem(QFrame):
    def __init__(self, params, parent=None):
        super().__init__(parent)
        self.params = params
        self.setObjectName("strategyItem")
        self.setStyleSheet("""
        QFrame#strategyItem {
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 4px;
            background: #fafafa;
        }
        QLabel {
            font-weight: bold;
        }
        QToolButton {
            border: none;
        }
        """)
        # Layout
        lay = QHBoxLayout(self)
        self.name_label = QLabel(params["name"])
        lay.addWidget(self.name_label)
        lay.addStretch()

        # edit button
        self.edit_btn = QToolButton()
        self.edit_btn.setIcon(QIcon.fromTheme("preferences-system"))  # 或自己放 gear.svg
        self.edit_btn.clicked.connect(self.on_edit)
        lay.addWidget(self.edit_btn)

        # delete button
        self.del_btn = QToolButton()
        self.del_btn.setIcon(QIcon.fromTheme("edit-delete"))
        self.del_btn.clicked.connect(self.on_delete)
        lay.addWidget(self.del_btn)

    def on_edit(self):
        dlg = StrategyDialog(self)
        # 預先填入原本參數
        dlg.name_edit.setText(self.params["name"])
        dlg.type_combo.setCurrentText(self.params["type"])
        # ... 其他欄位自己填 ...
        if dlg.exec_() == QDialog.Accepted:
            newp = dlg.get_params()
            self.params = newp
            self.name_label.setText(newp["name"])

    def on_delete(self):
        # 從 parent layout 裡移除自己
        self.setParent(None)
        self.deleteLater()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("回測系統")

        # --- 上方工具列 ---
        top_bar = QWidget()
        tlay = QHBoxLayout()
        self.date_start = QDateEdit(QDate(2015, 1, 1))
        self.date_end   = QDateEdit(QDate.currentDate())
        self.capital    = QLineEdit("1000000")
        self.fee_rate   = QLineEdit("0.1425")
        self.run_btn    = QPushButton("開始回測")
        self.run_btn.clicked.connect(self.run_backtest)

        tlay.addWidget(QLabel("回測區間：")); tlay.addWidget(self.date_start)
        tlay.addWidget(QLabel("~"));        tlay.addWidget(self.date_end)
        tlay.addSpacing(20)
        tlay.addWidget(QLabel("初始金額：")); tlay.addWidget(self.capital)
        tlay.addSpacing(20)
        tlay.addWidget(QLabel("手續費率(%):")); tlay.addWidget(self.fee_rate)
        tlay.addStretch()
        tlay.addWidget(self.run_btn)
        top_bar.setLayout(tlay)

        # --- 左側：策略列表 + 新增按鈕 ---
        side = QScrollArea()
        side.setWidgetResizable(True)
        container = QWidget()
        self.strat_layout = QVBoxLayout()
        # + 新增策略按鈕
        self.add_btn = QPushButton("+ 新增策略")
        self.add_btn.clicked.connect(self.add_strategy)
        self.strat_layout.addWidget(self.add_btn)
        self.strat_layout.addStretch()
        container.setLayout(self.strat_layout)
        side.setWidget(container)

        # --- 中央 & 右側 & 底部（留空或自行擴充） ---
        center = QLabel("資產曲線 (Matplotlib Canvas)")
        right  = QLabel("右側圖例勾選區")
        bottom = QLabel("績效指標區")

        # --- 主版面 ---
        body = QHBoxLayout()
        body.addWidget(side, 1)
        body.addWidget(center, 3)
        body.addWidget(right, 1)

        main_layout = QVBoxLayout()
        main_layout.addWidget(top_bar)
        main_layout.addLayout(body)
        main_layout.addWidget(bottom)

        central = QWidget()
        central.setLayout(main_layout)
        self.setCentralWidget(central)

    def add_strategy(self):
        dlg = StrategyDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            params = dlg.get_params()
            # 建一個 item 並插到 + 按鈕後面
            item = StrategyItem(params)
            # 插入到倒數第二個（最後一個是 stretch()）
            self.strat_layout.insertWidget(self.strat_layout.count()-1, item)

    def run_backtest(self):
        # 1) 收集主畫面參數
        start = self.date_start.date().toPyDate()
        end   = self.date_end.date().toPyDate()
        capital = float(self.capital.text())
        fee     = float(self.fee_rate.text())
        # 2) 收集所有策略參數
        #    (可以在 add_strategy 時把每個策略參數存在一個 list 裡)
        # 3) 呼叫核心回測
        #    result = backtest(start, end, capital, fee, strat_list)
        # 4) 更新圖表 & 績效區
        pass

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())