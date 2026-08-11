import os
from PySide6.QtWidgets import QCheckBox, QVBoxLayout, QWidget, QPushButton, QLabel, QDialog
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, Qt
from PySide6.QtCore import Signal
from setupController import setupController

class strategyController(QWidget):
    requestDelete = Signal(QWidget)
    requestSyncName = Signal(QWidget)

    def __init__(self, number = 1):
        super().__init__()

        loader = QUiLoader()
        ui_path = os.path.join(os.path.dirname(__file__), "ui", "strategy.ui")
        ui_file = QFile(ui_path)
        ui_file.open(QFile.ReadOnly)
        self.ui = loader.load(ui_file, self)
        ui_file.close()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.ui)
        self.setLayout(layout)

        self.strategyName = self.ui.findChild(QLabel, "strategyName")
        self.setupButton = self.ui.findChild(QPushButton, "setupButton")
        self.deleteButton = self.ui.findChild(QPushButton, "deleteButton")
        
        self.strategyName.setText(f"策略 {number}")
        self.param = {"ma_short":"5",
                      "ma_long":"20",
                      "stop_loss_pct":None,
                      "take_profit_pct":None,
                      "position_pct":"10"}

        self.setupButton.clicked.connect(self.requestSetup)
        self.deleteButton.clicked.connect(self.emitRequestDelete)

    def requestSetup(self):
        dialog = setupController(self.strategyName.text(), self.param, self)
        if dialog.exec() == QDialog.Accepted:
            self.param = dialog.setupParam()
            self.strategyName.setText(dialog.setupName())
            self.requestSyncName.emit(self)

    def getParam(self):
        return self.param
    
    def getStrategyName(self):
        return self.strategyName.text()

    def emitRequestDelete(self):
        self.requestDelete.emit(self)