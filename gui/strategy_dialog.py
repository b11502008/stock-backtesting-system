from PyQt5.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QComboBox, QStackedWidget,
    QWidget, QSpinBox, QDoubleSpinBox, QHBoxLayout, QPushButton
)

class StrategyDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("策略參數設定")
        self.resize(300, 250)

        form = QFormLayout(self)
        # 策略名稱
        self.name_edit = QLineEdit()
        form.addRow("策略名稱：", self.name_edit)

        # 主策略類型
        self.type_combo = QComboBox()
        self.type_combo.addItems(["MA", "KD", "布林通道"])
        form.addRow("主策略：", self.type_combo)

        # 動態參數區 (StackedWidget)
        self.stack = QStackedWidget()
        # --- MA 參數 ---
        ma_w = QWidget(); ma_l = QFormLayout()
        self.short_ma = QSpinBox(); self.short_ma.setRange(1, 200)
        self.long_ma  = QSpinBox(); self.long_ma.setRange(1, 500)
        ma_l.addRow("短 MA (天)：", self.short_ma)
        ma_l.addRow("長 MA (天)：", self.long_ma)
        ma_w.setLayout(ma_l)
        # --- KD 參數 ---
        kd_w = QWidget(); kd_l = QFormLayout()
        self.k_period = QSpinBox(); self.k_period.setRange(1, 100)
        self.d_period = QSpinBox(); self.d_period.setRange(1, 100)
        kd_l.addRow("K 期：", self.k_period)
        kd_l.addRow("D 期：", self.d_period)
        kd_w.setLayout(kd_l)
        # --- 布林通道參數 ---
        boll_w = QWidget(); boll_l = QFormLayout()
        self.b_period  = QSpinBox(); self.b_period.setRange(1, 200)
        self.b_std_mul = QDoubleSpinBox(); self.b_std_mul.setRange(0.1, 10.0)
        boll_l.addRow("N 期：", self.b_period)
        boll_l.addRow("Std 倍數：", self.b_std_mul)
        boll_w.setLayout(boll_l)

        self.stack.addWidget(ma_w)
        self.stack.addWidget(kd_w)
        self.stack.addWidget(boll_w)
        form.addRow(self.stack)

        # 其他共通參數
        self.stop_loss   = QDoubleSpinBox(); self.stop_loss.setSuffix(" %")
        self.stop_profit = QDoubleSpinBox(); self.stop_profit.setSuffix(" %")
        self.allocation  = QDoubleSpinBox(); self.allocation.setSuffix(" %")
        form.addRow("停損：", self.stop_loss)
        form.addRow("停利：", self.stop_profit)
        form.addRow("投入比例：", self.allocation)

        # OK / Cancel
        btn_box = QHBoxLayout()
        ok_btn     = QPushButton("確定"); ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("取消"); cancel_btn.clicked.connect(self.reject)
        btn_box.addStretch()
        btn_box.addWidget(cancel_btn)
        btn_box.addWidget(ok_btn)
        form.addRow(btn_box)

        # 當主策略改變時，切換對應參數頁面
        self.type_combo.currentIndexChanged.connect(self.stack.setCurrentIndex)

    def get_params(self):
        params = {
            "name": self.name_edit.text(),
            "type": self.type_combo.currentText(),
            "stop_loss": self.stop_loss.value(),
            "stop_profit": self.stop_profit.value(),
            "allocation": self.allocation.value()
        }
        idx = self.stack.currentIndex()
        if idx == 0:  # MA
            params.update({
                "short_ma": self.short_ma.value(),
                "long_ma":  self.long_ma.value()
            })
        elif idx == 1:  # KD
            params.update({
                "k_period": self.k_period.value(),
                "d_period": self.d_period.value()
            })
        else:  # 布林通道
            params.update({
                "b_period":  self.b_period.value(),
                "b_std_mul": self.b_std_mul.value()
            })
        return params