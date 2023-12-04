import sys
import numpy as np
import copy
from fractions import Fraction

# import markdown2

from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QGridLayout
from PyQt5.QtWidgets import QLineEdit, QSpinBox, QDoubleSpinBox, QCheckBox
from PyQt5.QtWidgets import QFrame, QMainWindow, QComboBox, QPushButton
from PyQt5.QtWidgets import QApplication, QGroupBox, QLabel
from gui_elements import add_framed_widget

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt

import qutip as qu
import qutipfuncs as quf
from qobjects import Level, Laser
from system_builder import AtomSystem
from systems import sysdict

L_dict = {"S": 0, "P": 1, "D": 2}

L_dict_inv = {0: "S", 1: "P", 2: "D"}


class AtomGui(QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setWindowTitle("Atomic System Solver")
        self.mainWidget = QWidget(self)
        self.mainLayout = QHBoxLayout()

        self.systemLayout = QVBoxLayout()

        self.initLayout = QHBoxLayout()

        self.AMHidden = True

        self.sysName = add_framed_widget(QComboBox, self.initLayout, label="System")
        for system in sysdict.keys():
            self.sysName.addItem(system)
        self.system_dict = copy.deepcopy(sysdict[self.sysName.currentText()])

        self.initButton = add_framed_widget(
            QPushButton, self.initLayout, label="", args=["Load Settings"]
        )
        self.initButton.clicked.connect(self.update_system)

        self.systemLayout.addLayout(self.initLayout)

        self.levels = LevelsSection(parent=self)
        self.systemLayout.addWidget(self.levels)
        self.lasers = LasersSection(parent=self)
        self.systemLayout.addWidget(self.lasers)
        self.paramsWidget = ParamsSection(parent=self)
        self.systemLayout.addWidget(self.paramsWidget)
        self.solver = SolverWidget(parent=self)
        self.systemLayout.addWidget(self.solver)
        self.mainLayout.addLayout(self.systemLayout)

        self.plotLayout = QVBoxLayout()
        self.plotter = PlotWidget()
        self.plotLayout.addWidget(self.plotter)
        self.clearButton = QPushButton("Clear")
        self.clearButton.clicked.connect(self.plotter.clear)
        self.plotLayout.addWidget(self.clearButton)
        self.levelDiagram = GrotrianDiagram(parent=self)
        self.plotLayout.addWidget(self.levelDiagram)

        self.mainLayout.addLayout(self.plotLayout)

        self.mainWidget.setLayout(self.mainLayout)
        self.setCentralWidget(self.mainWidget)

        self.sysName.currentIndexChanged.connect(self.update_system)
        self.init_system()

    def init_system(self):
        self.system_dict = copy.deepcopy(sysdict[self.sysName.currentText()])
        self.levels.init_section()
        self.lasers.init_section()
        self.solver.init_section()
        for level in self.system_dict["levels"]:
            self.levels.add_level(level)
        for laser in self.system_dict["lasers"]:
            self.lasers.add_laser()
        self.update_diagram()
        self.update_plot()

    def update_system(self):
        for idx in range(len(self.lasers.lasers_list[:])):
            self.lasers.remove_laser(idx)
        for level in list(self.levels.levels_dict.keys()):
            self.levels.remove_level(level)
        self.init_system()

    def update_diagram(self):
        self.levelDiagram.plot(
            self.system_dict["levels"],
            self.system_dict["lasers"],
            self.system_dict["params"],
        )

    def update_plot(self):
        self.solver.solve_system()
        self.plotter.clear()
        self.solver.plot_expect()

    def toggle_am(self):
        if self.AMHidden:
            self.AMHidden = False
            for level in self.levels.levels_widget_dict.values():
                level.mainFrame.hide()
                level.AMFrame.show()
            for laser in self.lasers.laser_widget_dict.values():
                laser.AMFrame.show()
                laser.mainFrame.hide()
        else:
            self.AMHidden = True
            for level in self.levels.levels_widget_dict.values():
                level.AMFrame.hide()
                level.mainFrame.show()
            for laser in self.lasers.laser_widget_dict.values():
                laser.AMFrame.hide()
                laser.mainFrame.show()


class LevelsSection(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.parent = parent
        self.main_widget = parent
        self.init_section()

        self.setFrameStyle(QFrame.Box)
        self.layout = QVBoxLayout()
        self.layout.addWidget(QLabel("Levels"))

        self.buttonsLayout = QHBoxLayout()
        self.addLevelButton = QPushButton("Add level")
        self.addLevelButton.clicked.connect(lambda: self.addLevel())
        self.buttonsLayout.addWidget(self.addLevelButton)

        self.showAMButton = QPushButton("Toggle AM Settings")
        self.showAMButton.clicked.connect(parent.toggle_am)
        self.buttonsLayout.addWidget(self.showAMButton)

        self.layout.addLayout(self.buttonsLayout)
        self.setLayout(self.layout)

    def init_section(self):
        self.system_dict = self.parent.system_dict
        self.levels_dict = self.system_dict["levels"]
        self.levels_widget_dict = {}

    def add_level(self, name):
        level = LevelWidget(name, parent=self)
        self.levels_widget_dict[name] = level
        self.layout.addWidget(level)
        level.get_level_pars()

    def remove_level(self, name):
        self.layout.removeWidget(self.levels_widget_dict[name])
        self.levels_widget_dict[name].deleteLater()
        self.levels_widget_dict.pop(name)
        self.levels_dict.pop(name)


class LevelWidget(QFrame):
    def __init__(self, name, parent=None):
        super().__init__(parent)

        self.name = name
        self.system_dict = parent.system_dict
        self.level_dict = parent.levels_dict[name]
        self.main_widget = parent.main_widget

        self.layout = QVBoxLayout()
        self.setFrameStyle(QFrame.Box)

        self.mainFrame = QFrame()
        self.levelMainLayout = QHBoxLayout()

        self.nameBox = add_framed_widget(
            QLineEdit, self.levelMainLayout, label="Name", args=[name]
        )

        self.popBox = add_framed_widget(
            QLineEdit, self.levelMainLayout, label="Population"
        )

        self.mainFrame.setLayout(self.levelMainLayout)

        self.layout.addWidget(self.mainFrame)

        self.AMFrame = QFrame()
        self.levelAMLayout = QHBoxLayout()

        self.sBox = add_framed_widget(QDoubleSpinBox, self.levelAMLayout, label="S")
        self.sBox.setSingleStep(0.5)

        self.lBox = add_framed_widget(QSpinBox, self.levelAMLayout, label="L")

        self.jBox = add_framed_widget(QDoubleSpinBox, self.levelAMLayout, label="J")
        self.jBox.setSingleStep(0.5)

        self.AMFrame.setLayout(self.levelAMLayout)
        self.layout.addWidget(self.AMFrame)
        if not self.system_dict["params"]["zeeman"]:
            self.AMFrame.hide()

        self.get_level_pars()
        self.nameBox.textChanged.connect(self.set_level)
        self.popBox.textChanged.connect(self.set_level)
        self.sBox.valueChanged.connect(self.set_level)
        self.lBox.valueChanged.connect(self.set_level)
        self.jBox.valueChanged.connect(self.set_level)

        # self.removeButton = QPushButton('Remove Level')
        # self.removeButton.clicked.connect(lambda: self.removeLevel(num,parent))
        # self.layout.addWidget(self.removeButton)

        self.setLayout(self.layout)

    def get_level_pars(self):
        self.popBox.setText(", ".join(map(str, self.level_dict["pop"])))
        self.sBox.setValue(self.level_dict["S"])
        self.lBox.setValue(self.level_dict["L"])
        self.jBox.setValue(self.level_dict["J"])

    def set_level(self):
        old_name = self.name
        new_name = self.nameBox.text()
        edit_key_in_place(self.system_dict, old_name, new_name)
        self.name = new_name
        pop = self.popBox.text()
        if pop == "":
            self.level_dict["pop"] = 0
        else:
            self.level_dict["pop"] = [float(i) for i in pop.split(",")]
        self.level_dict["J"] = self.jBox.value()
        self.level_dict["L"] = self.lBox.value()
        self.level_dict["S"] = self.sBox.value()
        self.main_widget.update_diagram()
        self.main_widget.update_plot()

    def delete_level(self):
        """
        deleting widgets in pyqt is difficult and prone to errors. this function likely has some overkill.
        """
        self.parent.levels_widget_dict.remove(
            self
        )  # remove the item from the command list
        self.parent.layout.removeWidget(self)  # remove the item widget from the layout
        self.parent.children().remove(
            self
        )  # remove the item widget from the layout again, but different?
        self.deleteLater()  # remove the widget from memory, later ??


class LasersSection(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.parent = parent
        self.main_widget = parent
        self.init_section()

        self.layout = QVBoxLayout()
        self.setFrameStyle(QFrame.Box)
        self.layout.addWidget(QLabel("Lasers"))

        self.buttonsLayout = QHBoxLayout()
        self.getLevelsButton = QPushButton("Get Levels")
        self.getLevelsButton.clicked.connect(self.get_levels)
        # self.buttonsLayout.addWidget(self.getLevelsButton)

        self.layout.addLayout(self.buttonsLayout)

        self.setLayout(self.layout)

    def init_section(self):
        self.system_dict = self.parent.system_dict
        self.lasers_list = self.system_dict["lasers"]
        self.laser_widget_dict = {}
        self.num_lasers = 0

    def add_laser(self):
        num = self.num_lasers
        laser = LaserWidget(num=num, parent=self)
        self.laser_widget_dict[num] = laser
        self.layout.addWidget(laser)
        # self.get_levels()
        laser.get_laser_pars()
        self.num_lasers += 1

    def get_levels(self):
        for laser in self.laser_widget_dict.values():
            laser.groundBox.clear()
            laser.excitedBox.clear()
            for key in self.parent.levels.levels_dict.keys():
                laser.groundBox.addItem(key)
                laser.excitedBox.addItem(key)

    def remove_laser(self, idx):
        self.layout.removeWidget(self.laser_widget_dict[idx])
        self.laser_widget_dict[idx].deleteLater()
        self.laser_widget_dict.pop(idx)
        # self.lasers_list.pop(idx)


class LaserWidget(QFrame):
    def __init__(self, num=0, parent=None):
        super().__init__(parent)
        self.num = num
        self.setFrameStyle(QFrame.Box)
        self.layout = QVBoxLayout()
        self.parent = parent
        self.main_widget = parent.main_widget
        self.system_dict = parent.system_dict
        self.laser_dict = self.system_dict["lasers"][num]
        self.num = num

        self.laserMainLayout = QHBoxLayout()
        self.mainFrame = QFrame()
        self.mainFrame.setLayout(self.laserMainLayout)

        self.groundBox = add_framed_widget(
            QComboBox, self.laserMainLayout, label="Lower State"
        )

        self.excitedBox = add_framed_widget(
            QComboBox, self.laserMainLayout, label="Upper State"
        )

        self.omegaBox = add_framed_widget(
            QDoubleSpinBox, self.laserMainLayout, label="Omega"
        )
        self.omegaBox.setSingleStep(0.1)
        self.omegaBox.setMaximum(100)
        self.deltaBox = add_framed_widget(
            QDoubleSpinBox, self.laserMainLayout, label="Delta"
        )
        self.deltaBox.setSingleStep(0.1)
        self.deltaBox.setMaximum(100)
        self.deltaBox.setMinimum(-100)

        self.layout.addWidget(self.mainFrame)

        self.AMFrame = QFrame()
        self.laserDirLayout = QHBoxLayout()

        self.kBox = add_framed_widget(QSpinBox, self.laserDirLayout, label="k")
        self.kBox.setMaximum(360)

        self.s1Box = add_framed_widget(QSpinBox, self.laserDirLayout, label="S")
        self.s2Box = add_framed_widget(QSpinBox, self.laserDirLayout)
        self.s3Box = add_framed_widget(QSpinBox, self.laserDirLayout)

        self.get_laser_pars()

        self.groundBox.currentIndexChanged.connect(lambda: self.set_laser(num))
        self.excitedBox.currentIndexChanged.connect(lambda: self.set_laser(num))
        self.omegaBox.valueChanged.connect(lambda: self.set_laser(num))
        self.deltaBox.valueChanged.connect(lambda: self.set_laser(num))
        self.kBox.valueChanged.connect(lambda: self.set_laser(num))

        self.s1Box.valueChanged.connect(lambda: self.set_laser(num))
        self.s2Box.valueChanged.connect(lambda: self.set_laser(num))
        self.s3Box.valueChanged.connect(lambda: self.set_laser(num))

        self.AMFrame.setLayout(self.laserDirLayout)
        self.layout.addWidget(self.AMFrame)
        if not self.system_dict["params"]["zeeman"]:
            self.AMFrame.hide()

        # self.set_laserButton = QPushButton('Set Laser')
        # self.set_laserButton.clicked.connect(lambda: self.set_laser(num, parent))
        # self.layout.addWidget(self.set_laserButton)

        self.setLayout(self.layout)

    def set_laser(self, num):
        laserpars = {}
        laserpars["L1"] = self.groundBox.currentText()
        laserpars["L2"] = self.excitedBox.currentText()
        laserpars["Omega"] = self.omegaBox.value()
        laserpars["Delta"] = self.deltaBox.value()
        laserpars["k"] = self.kBox.value()
        laserpars["S"] = [self.s1Box.value(), self.s2Box.value(), self.s3Box.value()]

        self.parent.lasers_list[num].update(laserpars)
        self.main_widget.update_diagram()
        self.main_widget.update_plot()

    def get_laser_pars(self):
        find_or_add(self.groundBox, self.laser_dict["L1"])
        find_or_add(self.excitedBox, self.laser_dict["L2"])
        self.omegaBox.setValue(self.laser_dict["Omega"])
        self.deltaBox.setValue(self.laser_dict["Delta"])
        self.s1Box.setValue(self.laser_dict["S"][0])
        self.s2Box.setValue(self.laser_dict["S"][1])
        self.s3Box.setValue(self.laser_dict["S"][2])


class CavityWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.Box)
        self.layout = QVBoxLayout()
        self.parent = parent
        self.main_widget = parent.main_widget
        self.system_dict = parent.system_dict
        self.cavity_dict = self.system_dict["cavity"]

        self.laserMainLayout = QHBoxLayout()

        self.groundBox = add_framed_widget(
            QComboBox, self.laserMainLayout, label="Lower State"
        )

        self.excitedBox = add_framed_widget(
            QComboBox, self.laserMainLayout, label="Upper State"
        )

        self.gBox = add_framed_widget(
            QDoubleSpinBox, self.laserMainLayout, label="Omega"
        )
        self.gBox.setSingleStep(0.1)
        self.gBox.setMaximum(100)
        self.deltaBox = add_framed_widget(
            QDoubleSpinBox, self.laserMainLayout, label="Delta"
        )
        self.deltaBox.setSingleStep(0.1)
        self.deltaBox.setMaximum(100)
        self.deltaBox.setMinimum(-100)
        self.layout.addLayout(self.laserMainLayout)

        self.AMFrame = QFrame()
        self.laserDirLayout = QHBoxLayout()

        self.kBox = add_framed_widget(QSpinBox, self.laserDirLayout, label="k")
        self.kBox.setMaximum(360)

        self.s1Box = add_framed_widget(QSpinBox, self.laserDirLayout, label="pol")
        self.s2Box = add_framed_widget(QSpinBox, self.laserDirLayout)
        self.s3Box = add_framed_widget(QSpinBox, self.laserDirLayout)

        self.get_laser_pars()

        self.groundBox.currentIndexChanged.connect(lambda: self.set_laser)
        self.excitedBox.currentIndexChanged.connect(lambda: self.set_laser)
        self.omegaBox.valueChanged.connect(lambda: self.set_laser)
        self.deltaBox.valueChanged.connect(lambda: self.set_laser)
        self.kBox.valueChanged.connect(lambda: self.set_laser)

        self.s1Box.valueChanged.connect(lambda: self.set_laser)
        self.s2Box.valueChanged.connect(lambda: self.set_laser)
        self.s3Box.valueChanged.connect(lambda: self.set_laser)

        self.AMFrame.setLayout(self.laserDirLayout)
        self.layout.addWidget(self.AMFrame)
        if not self.system_dict["params"]["zeeman"]:
            self.AMFrame.hide()

        # self.set_laserButton = QPushButton('Set Laser')
        # self.set_laserButton.clicked.connect(lambda: self.set_laser(num, parent))
        # self.layout.addWidget(self.set_laserButton)

        self.setLayout(self.layout)

    def set_laser(self):
        laserpars = {}
        laserpars["L1"] = self.groundBox.currentText()
        laserpars["L2"] = self.excitedBox.currentText()
        laserpars["g"] = self.omegaBox.value()
        laserpars["Delta"] = self.deltaBox.value()
        laserpars["k"] = self.kBox.value()
        laserpars["pol"] = [self.s1Box.value(), self.s2Box.value(), self.s3Box.value()]

        self.main_widget.system_dict["cavity"].update(laserpars)
        self.main_widget.update_diagram()
        self.main_widget.update_plot()

    def get_laser_pars(self):
        find_or_add(self.groundBox, self.laser_dict["L1"])
        find_or_add(self.excitedBox, self.laser_dict["L2"])
        self.omegaBox.setValue(self.laser_dict["g"])
        self.deltaBox.setValue(self.laser_dict["Delta"])
        self.kBox.setValue(self.laser_dict["k"])
        self.s1Box.setValue(self.laser_dict["pol"][0])
        self.s2Box.setValue(self.laser_dict["pol"][1])
        self.s3Box.setValue(self.laser_dict["pol"][2])


class ParamsSection(QFrame):
    def __init__(
        self,
        parent=None,
    ):
        super().__init__(parent)
        self.main_widget = parent
        self.params = self.main_widget.system_dict["params"]
        self.initGUI()
        # self.set_params()

    def initGUI(self):
        self.setFrameStyle(QFrame.Box)
        self.layout = QVBoxLayout()

        self.tlistGroup = QGroupBox("tlist")
        self.tlistLayout = QHBoxLayout()

        self.startBox = add_framed_widget(
            QDoubleSpinBox, self.tlistLayout, label="t_start"
        )
        self.startBox.setMaximum(9999999)
        self.startBox.setValue(self.params["t_start"])
        self.endBox = add_framed_widget(QDoubleSpinBox, self.tlistLayout, label="t_max")
        self.endBox.setMaximum(9999999)
        self.endBox.setValue(self.params["t_max"])
        self.stepsBox = add_framed_widget(QSpinBox, self.tlistLayout, label="n_step")
        self.stepsBox.setMaximum(9999999)
        self.stepsBox.setValue(self.params["n_step"])

        self.tlistGroup.setLayout(self.tlistLayout)
        self.layout.addWidget(self.tlistGroup)

        self.bFieldGroup = QGroupBox("B Field")
        self.bFieldLayout = QHBoxLayout()
        self.bBox = add_framed_widget(QDoubleSpinBox, self.bFieldLayout, label="B")
        # self.bDirBox = add_framed_widget(QSpinBox, self.bFieldLayout, label='Bdir')

        self.zeemanBool = QCheckBox()
        self.zeemanBool.setText("Zeeman?")
        self.bFieldLayout.addWidget(self.zeemanBool)
        self.bFieldGroup.setLayout(self.bFieldLayout)
        self.layout.addWidget(self.bFieldGroup)

        self.othersLayout = QHBoxLayout()
        self.mixedBool = QCheckBox()
        self.mixedBool.setText("Mixed states?")
        self.othersLayout.addWidget(self.mixedBool)
        self.bFieldLayout.addLayout(self.othersLayout)

        self.setParamsButton = QPushButton("Set Params")
        self.setParamsButton.clicked.connect(self.set_params)
        self.layout.addWidget(self.setParamsButton)

        self.startBox.valueChanged.connect(self.set_params)
        self.endBox.valueChanged.connect(self.set_params)
        self.stepsBox.valueChanged.connect(self.set_params)
        self.bBox.valueChanged.connect(self.set_params)
        self.zeemanBool.stateChanged.connect(self.set_params)
        self.mixedBool.stateChanged.connect(self.set_params)

        self.setLayout(self.layout)

    def set_params(self):
        self.params = self.main_widget.system_dict["params"]
        t_start = self.startBox.value()
        t_max = self.endBox.value()
        n_step = self.stepsBox.value()
        self.params["tlist"] = np.linspace(t_start, t_max, n_step)

        self.params["B"] = self.bBox.value()
        self.params["Bdir"] = 0
        self.params["zeeman"] = self.zeemanBool.isChecked()
        self.params["mixed"] = self.mixedBool.isChecked()
        self.main_widget.update_diagram()
        self.main_widget.update_plot()


class SolverWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.Box)
        self.parent = parent
        self.main_widget = parent
        self.system_dict = parent.system_dict
        self.levels_dict = parent.levels.levels_dict
        self.lasers_list = parent.lasers.lasers_list
        self.params = parent.paramsWidget.params
        self.ops_dict = {}
        self.checked_dict = {}
        self.layout = QVBoxLayout()
        self.layout.addWidget(QLabel("Solver"))

        self.buttonsLayout = QHBoxLayout()
        self.printButton = QPushButton("Print")
        self.printButton.clicked.connect(self.print_system)
        self.buttonsLayout.addWidget(self.printButton)
        self.solveButton = QPushButton("Solve System")
        self.solveButton.clicked.connect(self.solve_system)
        self.buttonsLayout.addWidget(self.solveButton)
        self.plotButton = QPushButton("Plot")
        self.plotButton.clicked.connect(lambda: self.plot_expect(parent))
        self.buttonsLayout.addWidget(self.plotButton)
        self.layout.addLayout(self.buttonsLayout)

        self.ops_grid = QGridLayout()
        self.layout.addLayout(self.ops_grid)

        self.setLayout(self.layout)

    def print_system(self):
        print(self.parent.system_dict)
        self.system_dict = self.parent.system_dict
        system = self.build_system(self.system_dict)
        print(system.levels)
        print(" ")
        print(system.lasers)
        print(" ")
        print(system.params)

    def build_system(self, system_dict):
        levels = []
        for v in system_dict["levels"].values():
            levels.append(Level(**v))
        lasers = []
        for v in system_dict["lasers"]:
            lasers.append(Laser(**v))
        system = AtomSystem(levels, lasers, system_dict["params"])
        return system

    def solve_system(self):
        self.system_dict = self.parent.system_dict
        system = self.build_system(self.system_dict)
        self.result, self.e_ops = system.solve()
        for key, widget in (self.ops_dict.copy()).items():
            self.ops_grid.removeWidget(widget)
            self.ops_dict.pop(key)
            # self.checked_dict.pop(key)
        for key, op in self.e_ops.items():
            row, col = divmod(self.ops_grid.count(), 4)
            # key_html = markdown2.markdown(key)
            widget = QCheckBox(key)
            self.ops_dict[key] = widget
            if key in self.checked_dict.keys():
                widget.setChecked(self.checked_dict[key])
            else:
                self.checked_dict[key] = True
                widget.setChecked(True)
            widget.stateChanged.connect(self.update_checked_dict)
            self.ops_grid.addWidget(widget, row, col)

    def update_checked_dict(self):
        for key in self.ops_dict.keys():
            self.checked_dict[key] = (self.ops_dict[key]).isChecked()

    def plot_expect(self):
        for key, op in self.e_ops.items():
            if self.ops_dict[key].isChecked():
                exp = qu.expect(op, self.result.states)
                self.parent.plotter.plot(
                    self.system_dict["params"]["tlist"], exp, label=key
                )

    def init_section(self):
        for key, widget in (self.ops_dict.copy()).items():
            self.ops_grid.removeWidget(widget)
            self.ops_dict.pop(key)
            self.checked_dict.pop(key)


class PlotWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.figure, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.figure)
        self.ax.set_xlabel("Time")
        self.ax.set_ylabel("Expectation Value")

        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        self.setLayout(layout)

    def plot(self, *args, **kwargs):
        self.ax.plot(*args, **kwargs)
        self.ax.legend()
        self.canvas.draw()

    def clear(self):
        self.ax.clear()
        self.canvas.draw()


class GrotrianDiagram(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.initUI()
        self.main_widget = parent

    def initUI(self):
        # Create a Matplotlib figure and canvas
        self.fig, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.fig)

        # Set up the PyQt window
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.canvas)

        self.setLayout(self.layout)

    def plot(self, levels, lasers, params):
        self.ax.clear()
        zeeman = params["zeeman"]
        for key in levels.keys():
            level = levels[key]
            S = level["S"]
            L = level["L"]
            J = level["J"]
            if L == 1:
                energy = 2
            elif L == 2:
                energy = 1
            else:
                energy = 0
            am_min = L - 0.2
            am_max = L + 0.2
            if J != 0:
                J_dec = str(J)
                J_frac = Fraction(J_dec)
                J_frac = "{}/{}".format(J_frac.numerator, J_frac.denominator)
            else:
                J_frac = J
            label = "$^{{{}}}{}_{{{}}}$".format(int(2 * S + 1), L_dict_inv[L], J_frac)
            if not zeeman:
                self.ax.hlines(y=energy, xmin=am_min, xmax=am_max)
            self.ax.text(am_max, energy, label)

            if zeeman and J != 0:
                w = quf.zeemanFS(J, S, L, 1e-4, 1)
                N = int(2 * J + 1)
                M = np.arange(-J, J + 1)
                B = params["B"]
                full_length = 0.4
                m_length = full_length / N
                for i, m in enumerate(M):
                    shift = w * B * m * 1e-9
                    start = am_min + i * m_length
                    stop = am_min + (i + 1) * m_length
                    self.ax.hlines(y=energy + shift, xmin=start, xmax=stop)

        for laser in lasers:
            Omega = laser["Omega"]
            Delta = laser["Delta"]

            x1 = levels[laser["L1"]]["L"]
            x2 = levels[laser["L2"]]["L"]
            dx = x2 - x1

            L = levels[laser["L1"]]["L"]
            if L == 1:
                energy = 2
            elif L == 2:
                energy = 1
            else:
                energy = 0
            y1 = energy
            L = levels[laser["L2"]]["L"]
            if L == 1:
                energy = 2
            elif L == 2:
                energy = 1
            else:
                energy = 0
            y2 = energy - Delta / 10
            dy = y2 - y1

            label = "$\Omega={}$,\n$\Delta={}$".format(round(Omega, 3), round(Delta, 3))
            alpha = min([Omega, 1])
            self.ax.arrow(
                x1, y1, dx, dy, width=0.01, length_includes_head=True, alpha=alpha
            )
            self.ax.text(0.1 + x1 + dx / 2, y1 + dy / 2, label)

            if Delta != 0:
                self.ax.hlines(y=y2, xmin=x2 - 0.2, xmax=x2 + 0.2, linestyle="dashed")

        # Set labels and legend
        self.ax.set_xlabel("L")
        self.ax.set_xticks([0, 1, 2])
        self.ax.set_ylabel("Energy (arb scale)")
        self.ax.set_yticks([])
        # self.ax.legend()

        # Show the plot
        self.canvas.draw()


def edit_key_in_place(d, oldKey, newKey):
    """
    Changes the key of a dictionary in place (does not create a new dictionary) while preserving order
    :param d: dict
    :param oldKey: key to be replaced
    :param newKey: new key
    :return:
    """
    replacement = {oldKey: newKey}
    for k, v in list(d.items()):
        d[replacement.get(k, k)] = d.pop(k)


def find_or_add(box, text):
    """if it's in the box, set it, if not, add and set it"""
    idx = box.findText(text)
    if idx < 0:
        box.addItem(text)
        idx = box.findText(text)
    box.setCurrentIndex(idx)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = AtomGui()
    window.show()

    app.exec_()
