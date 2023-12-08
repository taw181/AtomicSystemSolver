from PyQt5.QtWidgets import QCheckBox, QFrame, QHBoxLayout, QVBoxLayout, QWidget
from PyQt5.QtWidgets import QLabel


def add_framed_widget(widget_type, parent_layout, label="", args=None, kwargs=None):
    if not args:
        args = []
    if not kwargs:
        kwargs = {}
    frame = QFrame()
    layout = QVBoxLayout()
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(1)
    layout.addWidget(QLabel(label))
    widget = widget_type(*args, **kwargs)
    layout.addWidget(widget)
    frame.setLayout(layout)
    parent_layout.addWidget(frame)
    return widget


class htmlCheckBox(QWidget):
    def __init__(self, label_text="", parent=None):
        super().__init__(parent=parent)
        self.checkBox = QCheckBox()
        self.label = QLabel(label_text)

        self.stateChanged = self.checkBox.stateChanged

        self.layout = QHBoxLayout()
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.checkBox)
        self.setLayout(self.layout)

    def isChecked(self):
        return self.checkBox.isChecked()

    def setChecked(self, state):
        self.checkBox.setChecked(state)


# def generate_framed_widget(inner_widget_class):
#     class FramedWidget(QFrame, inner_widget_class):
#         def __init__(self, label_text="", parent=None):
#             super(FramedWidget, self).__init__(parent)

#             # Set up frame properties
#             self.setFrameShape(QFrame.StyledPanel)
#             self.setFrameShadow(QFrame.Raised)

#             # Set up layout
#             layout = QVBoxLayout(self)
#             layout.setContentsMargins(0, 0, 0, 0)

#             # Add label
#             if label_text:
#                 label = QLabel(label_text)
#                 layout.addWidget(label)

#             # Add the inner widget to the layout
#             inner_widget = inner_widget_class(self)
#             layout.addWidget(inner_widget)

#             self.setLayout(layout)

#     return FramedWidget

# TextBox = generate_framed_widget(QLineEdit)
# SpinBox = generate_framed_widget(QSpinBox)
# ComboBox = generate_framed_widget(QComboBox)
# PushButton = generate_framed_widget(QPushButton)

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

# class SpinBox(QFrame):
#     def __init__(self,label,default=0, intval=False, minval=0, maxval = 1000000, parent=None):
#         super().__init__(parent=parent)
#         layout = QVBoxLayout()
#         layout.setContentsMargins(0,0,0,0)
#         layout.setSpacing(1)
#         layout.addWidget(QLabel(label))
#         if intval:
#             self.box = QSpinBox()
#         else:
#             self.box = QDoubleSpinBox()
#         self.box.setMinimum(minval)
#         self.box.setMaximum(maxval)
#         self.box.setValue(default)
#         layout.addWidget(self.box)
#         self.setLayout(layout)

# class AMBox(SpinBox):
#     def __init__(self, label, default=0, intval=False, parent=None):
#         super().__init__(label, default=0, intval=False, minval=0, maxval=5, parent=parent)

# class ComboBox(QFrame):
#     def __init__(self,label):
#         super().__init__()
#         layout = QVBoxLayout()
#         layout.setContentsMargins(0,0,0,0)
#         layout.setSpacing(1)
#         layout.addWidget(QLabel(label))
#         self.box = QComboBox()
#         layout.addWidget(self.box)
#         self.setLayout(layout)

# class PushButton(QFrame):
#     def __init__(self,label):
#         super().__init__()
#         layout = QVBoxLayout()
#         layout.setContentsMargins(0,0,0,0)
#         layout.setSpacing(1)
#         layout.addWidget(QLabel())
#         self.button = QPushButton(label)
#         layout.addWidget(self.button)
#         self.setLayout(layout)
