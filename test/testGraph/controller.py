import os
from PySide6.QtWidgets import QMainWindow, QVBoxLayout, QWidget
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile
from graph import plot_graph

class MainWindowController(QMainWindow):
    def __init__(self):
        super().__init__()

        loader = QUiLoader()
        ui_path = os.path.join(os.path.dirname(__file__), "ui", "mainWindow.ui")
        ui_file = QFile(ui_path)
        ui_file.open(QFile.ReadOnly)
        self.ui = loader.load(ui_file, None)
        ui_file.close()
        self.setCentralWidget(self.ui)

        self.plotWidget = self.ui.findChild(QWidget, "plotWidget")
        self.plotWidget.setLayout(QVBoxLayout())

        self.comboBox = self.ui.findChild(QWidget, "comboBox")
        self.lineEdit_xStart = self.ui.findChild(QWidget, "lineEdit_xStart")
        self.lineEdit_xEnd = self.ui.findChild(QWidget, "lineEdit_xEnd")
        self.pushButton = self.ui.findChild(QWidget, "pushButton")
        self.setup_events()

    def setup_events(self):
        self.pushButton.clicked.connect(self.handle_button_click)

    def handle_button_click(self):
        try:
            x_start = float(self.lineEdit_xStart.text())
            x_end = float(self.lineEdit_xEnd.text())
            if x_start >= x_end:
                raise ValueError("x 起點必須小於終點")
        except ValueError as e:
            print(f"輸入錯誤: {e}")
            return
        selected = self.comboBox.currentText()
        plot_graph(self.plotWidget, selected, x_start, x_end)
