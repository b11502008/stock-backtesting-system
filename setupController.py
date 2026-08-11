# strategySetupDialog.py
import os
from PySide6.QtWidgets import QDialog, QCheckBox, QLineEdit, QVBoxLayout, QDialogButtonBox, QWidget
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile
from PySide6.QtWidgets import QComboBox

class setupController(QDialog):
    def __init__(self, name, param, parent=None):
        super().__init__(parent)

        loader = QUiLoader()
        self.loader = loader
        ui_path = os.path.join(os.path.dirname(__file__), "ui", "setup.ui")
        ui_file = QFile(ui_path)
        ui_file.open(QFile.ReadOnly)
        self.ui = loader.load(ui_file)
        ui_file.close()

        self.setFixedSize(450, 300)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.ui)

        self.strategyName = self.ui.findChild(QLineEdit, "strategyName")
        self.strategyName.setText(name)

        self.setupSelector = self.ui.findChild(QComboBox, "setupSelector")
        self.setupSelector.currentTextChanged.connect(self.on_module_changed)
        
        self.setupArea = self.ui.findChild(QWidget, "setupArea")
        self.setupLayout = self.setupArea.layout()

        self.stopLoss = self.ui.findChild(QLineEdit, "stopLoss")
        self.takeProfit = self.ui.findChild(QLineEdit, "takeProfit")
        self.riskRatio = self.ui.findChild(QLineEdit, "riskRatio")

        # 預先建立一個 param dict 或外部傳入也可
        self.param = param
        self.currentWidget = None

        if "ma_short" in self.param:
            self.setupSelector.setCurrentText("MA")
        elif "kd_window" in self.param:
            self.setupSelector.setCurrentText("KD")
        elif "bool_window" in self.param:
            self.setupSelector.setCurrentText("Bool")
        if "stop_loss_pct" in self.param:
            self.stopLoss.setText(self.param["stop_loss_pct"])
        if "take_profit_pct" in self.param:
            self.takeProfit.setText(self.param["take_profit_pct"])
        if "position_pct" in self.param:
            self.riskRatio.setText(self.param["position_pct"])

        self.buttonBox = self.ui.findChild(QDialogButtonBox, "buttonBox")
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.on_module_changed(self.setupSelector.currentText())

    def loadSetup(self, filename):
        path = os.path.join(os.path.dirname(__file__), "ui", filename)
        file = QFile(path)
        if not file.open(QFile.ReadOnly):
            print(f"Failed to open {filename}")
            return QWidget()

        widget = self.loader.load(file)
        file.close()
        return widget
    
    def on_module_changed(self, module_name):
        # 清除舊的 widget
        if self.currentWidget:
            self.setupLayout.removeWidget(self.currentWidget)
            self.currentWidget.setParent(None)
            self.currentWidget = None

        # 載入新的模組
        filename = f"{module_name}Setup.ui"
        widget = self.loadSetup(filename)
        widget.setFixedSize(208,160)
        self.setupLayout.addWidget(widget)
        self.currentWidget = widget

        module_name_lower = module_name.lower()
        if module_name_lower == "ma":
            self.shortMA = widget.findChild(QLineEdit, "shortMA")
            self.longMA = widget.findChild(QLineEdit, "longMA")
            if "ma_short" in self.param:
                self.shortMA.setText(self.param["ma_short"])
                self.longMA.setText(self.param["ma_long"])
            else:
                self.shortMA.setText("5")
                self.longMA.setText("20")
        elif module_name_lower == "kd":
            self.KDWindow = widget.findChild(QLineEdit, "KDWindow")
            self.lowerBound = widget.findChild(QLineEdit, "lowerBound")
            self.upperBound = widget.findChild(QLineEdit, "upperBound")
            if "kd_window" in self.param:
                self.KDWindow.setText(self.param["kd_window"])
                self.lowerBound.setText(self.param["lower_bound"])
                self.upperBound.setText(self.param["upper_bound"])
            else:
                self.KDWindow.setText("9")
                self.lowerBound.setText("20")
                self.upperBound.setText("80")
        elif module_name_lower == "bool":
            self.BoolWindow = widget.findChild(QLineEdit, "BoolWindow")
            self.BoolRatio = widget.findChild(QLineEdit, "BoolRatio")
            if "bool_window" in self.param:
                self.BoolWindow.setText(self.param["bool_window"])
                self.BoolRatio.setText(self.param["std_multiplier"])
            else:
                self.BoolWindow.setText("20")
                self.BoolRatio.setText("2")
        # stop選項相關移除

    def setupParam(self):
        current = self.setupSelector.currentText().lower()
        self.param = {}
        if current == "ma":
            self.param["ma_short"] = self.shortMA.text()
            self.param["ma_long"] = self.longMA.text()
        elif current == "kd":
            self.param["kd_window"] = self.KDWindow.text()
            self.param["lower_bound"] = self.lowerBound.text()
            self.param["upper_bound"] = self.upperBound.text()
        elif current == "bool":
            self.param["bool_window"] = self.BoolWindow.text()
            self.param["std_multiplier"] = self.BoolRatio.text()
        # stop選項相關移除
        if self.stopLoss.text() == "":
            self.param["stop_loss_pct"] = None
        else:
            self.param["stop_loss_pct"] = self.stopLoss.text()
        if self.takeProfit.text() == "":
            self.param["take_profit_pct"] = None
        else:
            self.param["take_profit_pct"] = self.takeProfit.text()
        self.param["position_pct"] = self.riskRatio.text()
        return self.param


    def setupName(self):
        return self.strategyName.text()
