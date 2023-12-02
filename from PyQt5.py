from PyQt5.QtWidgets import QApplication, QSpinBox, QFrame, QVBoxLayout, QWidget, QMainWindow, QFrame, QVBoxLayout, QWidget, QSpinBox, QComboBox, QLabel, QLineEdit, QPushButton

def generate_framed_widget(inner_widget_class):
    class FramedWidget(QFrame, inner_widget_class):
        def __init__(self, label_text="", parent=None):
            super(FramedWidget, self).__init__(parent)
            
            # Set up frame properties
            self.setFrameShape(QFrame.StyledPanel)
            self.setFrameShadow(QFrame.Raised)

            # Set up layout
            layout = QVBoxLayout(self)
            layout.setContentsMargins(0, 0, 0, 0)

            # Add label
            if label_text:
                label = QLabel(label_text)
                layout.addWidget(label)

            # Add the inner widget to the layout
            inner_widget = inner_widget_class(self)
            layout.addWidget(inner_widget)

            self.setLayout(layout)

    return FramedWidget

TextBox = generate_framed_widget(QLineEdit)
SpinBox = generate_framed_widget(QSpinBox)
ComboBox = generate_framed_widget(QComboBox)
PushButton = generate_framed_widget(QPushButton)

def add_framed_widget(widget_type, parent_layout, label=""):
    frame = QFrame()
    layout = QVBoxLayout()
    layout.setContentsMargins(0,0,0,0)
    layout.setSpacing(1)
    layout.addWidget(QLabel(label))
    widget = widget_type()
    layout.addWidget(widget)
    frame.setLayout(layout)
    parent_layout.addWidget(frame)
    return widget
    
    
# class TextBox(QFrame):
#     def __init__(self,label):
#         super().__init__()
#         layout = QVBoxLayout()
#         layout.setContentsMargins(0,0,0,0)
#         layout.setSpacing(1)
#         layout.addWidget(QLabel(label))
#         self.box = QLineEdit()
#         layout.addWidget(self.box)
#         self.setLayout(layout)

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        
        # Create a central widget and set the layout
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        # Set up the layout for the central widget
        central_layout = QVBoxLayout(central_widget)
        spin_widget = add_framed_widget(QSpinBox, central_layout, label="test")
        spin_widget.setValue(5)

if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())