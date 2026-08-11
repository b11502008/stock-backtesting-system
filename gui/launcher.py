import sys
from PyQt5.QtWidgets import QApplication
# 用絕對導入，不動其他路徑
from gui.main_window import MainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w   = MainWindow()
    w.show()
    sys.exit(app.exec_())