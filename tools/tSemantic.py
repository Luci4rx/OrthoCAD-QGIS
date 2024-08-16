from qgis.PyQt.QtWidgets import QAction, QLineEdit, QVBoxLayout, QDialog, QPushButton

class SemanticEditor(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Редактор атрибутів")
        
        # Створення текстового поля
        self.text_input = QLineEdit(self)
        
        # Додавання кнопки
        self.button = QPushButton("OK", self)
        self.button.clicked.connect(self.accept)
        
        # Додавання текстового поля і кнопки до макету
        layout = QVBoxLayout()
        layout.addWidget(self.text_input)
        layout.addWidget(self.button)
        self.setLayout(layout)


    def get_text(self):
        return self.text_input.text()
