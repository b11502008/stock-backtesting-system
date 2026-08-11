import sys
from PySide6.QtWidgets import QApplication
from mainWindowController import MainWindowController

app = QApplication(sys.argv)
window = MainWindowController()
window.show()
sys.exit(app.exec())