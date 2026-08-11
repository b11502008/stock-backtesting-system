from PySide6.QtWidgets import QApplication
from controller import MainWindowController
import sys

app = QApplication(sys.argv)
window = MainWindowController()
window.show()
sys.exit(app.exec())