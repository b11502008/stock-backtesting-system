import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile
from PySide6.QtWidgets import QPushButton, QMessageBox

def on_button_click():
    QMessageBox.information(None, "messenge", "Hello!!!")

app = QApplication(sys.argv)

ui_path = os.path.join(os.path.dirname(__file__), "ui", "testButton.ui")
ui_file = QFile(ui_path)
loader = QUiLoader()
window = loader.load(ui_file)
ui_file.close()

button = window.findChild(QPushButton, "pushButton")
button.clicked.connect(on_button_click)

window.show()
app.exec()
