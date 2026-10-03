import sys
from PySide6.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QGraphicsDropShadowEffect
from PySide6.QtCore import Qt


class GradientButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(70)
        self.setMinimumWidth(400)

        # Estilo: gradiente + bordas arredondadas
        self.setStyleSheet("""
            QPushButton {
                border-radius: 35px;
                border: none;
                color: white;
                font-size: 20px;
                font-weight: bold;
                padding: 10px 30px;
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1c6b63,
                    stop:0.5 #0f5952,
                    stop:1 #0a3d38
                );
            }
            QPushButton:hover {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 #218077,
                    stop:0.5 #126a61,
                    stop:1 #0d443e
                );
            }
            QPushButton:pressed {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 #0a3d38,
                    stop:1 #062824
                );
            }
        """)

        # Efeito de sombra para dar sensação de profundidade (3D)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(25)
        shadow.setXOffset(0)
        shadow.setYOffset(8)
        shadow.setColor(QColor(0, 0, 0, 160))
        self.setGraphicsEffect(shadow)


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Botão com gradiente e sombra")
        self.setStyleSheet("background-color: #0a2f2b;")
        self.resize(600, 300)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        botao = GradientButton("AULAS 100% ONLINE")
        layout.addWidget(botao)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())