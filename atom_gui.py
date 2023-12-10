import sys
import json
import numpy as np
import copy
from fractions import Fraction
import time
from datetime import datetime
import os

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QGridLayout
from PyQt5.QtWidgets import QLineEdit, QSpinBox, QDoubleSpinBox, QCheckBox
from PyQt5.QtWidgets import QFrame, QMainWindow, QComboBox, QPushButton
from PyQt5.QtWidgets import QApplication, QGroupBox, QScrollArea
from gui_elements import add_framed_widget

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt

import matplotlib.lines as lines

import qutip as qu
import qutipfuncs as quf

# from qobjects import Cavity, Level, Laser, Decay
from system_builder import build_system_from_dict
from systems import defaults_dict

L_dict = {"S": 0, "P": 1, "D": 2}
L_dict_inv = {0: "S", 1: "P", 2: "D"}

save_path = "results/"


class AtomGui(QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setWindowTitle("Atomic System Solver")

        self.mainWidget = QWidget(self)
        self.mainLayout = QHBoxLayout()

        self.scrollArea = QScrollArea()
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )  # Disable horizontal scrolling

        self.systemWidget = QWidget()
        self.systemLayout = QVBoxLayout()
        self.systemWidget.setLayout(self.systemLayout)
        self.scrollArea.setWidget(self.systemWidget)
        self.mainLayout.addWidget(self.scrollArea, stretch=1)
        self.initLayout = QHBoxLayout()

        self.AMHidden = True

        with open("systems.json", "r+") as systems:
            self.all_systems = json.load(systems)
        self.systemSelector = add_framed_widget(
            QComboBox, self.initLayout, label="System"
        )
        for system in self.all_systems.keys():
            self.systemSelector.addItem(system)

        self.system_dict = copy.deepcopy(
            self.all_systems[self.systemSelector.currentText()]
        )

        self.initButton = add_framed_widget(
            QPushButton, self.initLayout, label="", args=["Load System"]
        )
        self.initButton.clicked.connect(self.update_system)

        self.systemLayout.addLayout(self.initLayout)

        self.saveLayout = QHBoxLayout()
        self.sysName = QLineEdit()
        self.saveLayout.addWidget(self.sysName)
        self.saveButton = QPushButton("Save System")
        self.saveLayout.addWidget(self.saveButton)
        self.saveButton.clicked.connect(self.save_system)

        self.removeButton = QPushButton("Remove System")
        self.saveLayout.addWidget(self.removeButton)
        self.removeButton.clicked.connect(self.remove_system)

        self.systemLayout.addLayout(self.saveLayout)

        self.levels = LevelsSection(parent=self)
        self.systemLayout.addWidget(self.levels)
        self.lasers = LasersSection(parent=self)
        self.systemLayout.addWidget(self.lasers)
        self.cavities = CavitySection(parent=self)
        self.systemLayout.addWidget(self.cavities)
        self.decays = DecaysSection(parent=self)
        self.systemLayout.addWidget(self.decays)
        self.paramsWidget = ParamsSection(parent=self)
        self.systemLayout.addWidget(self.paramsWidget)
        self.solver = SolverWidget(parent=self)
        self.systemLayout.addWidget(self.solver)

        self.plotLayout = QVBoxLayout()
        self.plotter = PlotWidget(parent=self)
        self.plotLayout.addWidget(self.plotter)
        self.clearButton = QPushButton("Clear")
        self.clearButton.clicked.connect(self.plotter.clear)
        # self.plotLayout.addWidget(self.clearButton)
        self.levelDiagram = GrotrianDiagram(parent=self)
        self.plotLayout.addWidget(self.levelDiagram)

        self.mainLayout.addLayout(self.plotLayout, stretch=1)

        self.mainWidget.setLayout(self.mainLayout)
        self.setCentralWidget(self.mainWidget)

        self.systemSelector.currentIndexChanged.connect(self.update_system)
        self.init_system()

    def save_system(self):
        newName = self.sysName.text()
        self.all_systems[newName] = copy.deepcopy(self.system_dict)
        self.system_dict = self.all_systems[newName]
        with open("systems.json", "w") as systems:
            json.dump(self.all_systems, systems, indent=2)
        self.update_system_list()
        find_or_add(self.systemSelector, newName)

    def remove_system(self):
        key = self.sysName.text()
        self.all_systems.pop(key),
        with open("systems.json", "w") as systems:
            json.dump(self.all_systems, systems, indent=2)
        self.update_system_list()

    def update_system_list(self):
        self.systemSelector.blockSignals(True)
        self.systemSelector.clear()
        for system in self.all_systems.keys():
            self.systemSelector.addItem(system)
        self.systemSelector.blockSignals(False)

    def init_system(self):
        self.system_dict = copy.deepcopy(
            self.all_systems[self.systemSelector.currentText()]
        )
        self.sysName.setText(self.systemSelector.currentText())
        self.levels.init_section()
        self.lasers.init_section()
        self.cavities.init_section()
        self.decays.init_section()
        self.solver.init_section()
        self.plotter.init_section()
        for level in self.system_dict["levels"]:
            self.levels.add_level(level)
        for laser in self.system_dict["lasers"]:
            self.lasers.add_coupling()
        for decay in self.system_dict["decays"]:
            self.decays.add_coupling()
        for cavity in self.system_dict["cavities"]:
            self.cavities.add_coupling()
        self.update()

    def auto_update(self):
        if self.solver.autoSolveBox.isChecked():
            self.update()

    def update(self):
        self.solver.solve_system()
        t0 = time.time()
        self.update_diagram()
        t = time.time() - t0
        print("Time to update diagram: {}".format(round(t, 5)))
        self.update_plot()
        t0 = time.time()
        t = time.time() - t0
        print("Time to update plot: {}".format(round(t, 5)))

    def update_system(self):
        for idx in range(len(self.lasers.coupling_list[:])):
            self.lasers.remove_widget(idx)
        for idx in range(len(self.decays.coupling_list[:])):
            self.decays.remove_widget(idx)
        for idx in range(len(self.cavities.coupling_list[:])):
            self.cavities.remove_widget(idx)
        for level in list(self.levels.levels_dict.keys()):
            self.levels.remove_level(level)

        self.init_system()

    def update_diagram(self):
        self.levelDiagram.plot(self.system_dict)

    def update_plot(self):
        self.plotter.clear()
        self.solver.plot_expect()

    def toggle_am(self):
        if self.AMHidden:
            self.AMHidden = False
            for level in self.levels.levels_widget_dict.values():
                level.mainFrame.hide()
                level.AMFrame.show()
            for laser in self.lasers.widget_dict.values():
                laser.AMFrame.show()
                laser.mainFrame.hide()
            for cavity in self.cavities.widget_dict.values():
                cavity.AMFrame.show()
                cavity.mainFrame.hide()
        else:
            self.AMHidden = True
            for level in self.levels.levels_widget_dict.values():
                level.AMFrame.hide()
                level.mainFrame.show()
            for laser in self.lasers.widget_dict.values():
                laser.AMFrame.hide()
                laser.mainFrame.show()
            for cavity in self.cavities.widget_dict.values():
                cavity.AMFrame.hide()
                cavity.mainFrame.show()


class LevelsSection(QGroupBox):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.parent = parent
        self.main_widget = parent
        self.init_section()

        # self.setFrameStyle(QFrame.Box)
        self.layout = QVBoxLayout()
        self.setTitle("Levels")

        self.buttonsLayout = QHBoxLayout()
        self.addLevelButton = QPushButton("Add level")
        self.addLevelButton.clicked.connect(lambda: self.add_level())
        # self.buttonsLayout.addWidget(self.addLevelButton)

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
        try:
            self.level_dict["pop"] = [float(i) for i in pop.split(",")]
        except Exception:
            self.level_dict["pop"] = 0
        self.level_dict["J"] = self.jBox.value()
        self.level_dict["L"] = self.lBox.value()
        self.level_dict["S"] = self.sBox.value()
        self.main_widget.auto_update()

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


class CouplingSection(QGroupBox):
    def __init__(self, title, dict_key, widget_type, parent=None):
        super().__init__(parent)
        self.main_widget = parent
        self.setTitle(title)
        self.dict_key = dict_key
        self.widget_type = widget_type
        self.init_section()
        self.layout = QVBoxLayout()

        self.couplingsLayout = QVBoxLayout()
        self.layout.addLayout(self.couplingsLayout)
        self.setLayout(self.layout)

        self.addButton = QPushButton("Add")
        self.layout.addWidget(self.addButton)
        self.addButton.clicked.connect(self.add_coupling)

    def init_section(self):
        self.system_dict = self.main_widget.system_dict
        self.coupling_list = self.system_dict[self.dict_key]
        self.widget_dict = {}
        self.num_couplings = 0

    def add_coupling(self):
        num = self.num_couplings
        if self.max_check():
            print("Maximum number of {} in use".format(self.dict_key))
            return
        if num > len(self.coupling_list) - 1:
            self.coupling_list.append(copy.deepcopy(defaults_dict[self.dict_key]))
        coupling = self.widget_type(num, self.dict_key, parent=self)
        self.widget_dict[num] = coupling
        self.couplingsLayout.addWidget(coupling)
        self.get_levels()
        coupling.get_pars()

        self.num_couplings += 1

    def get_levels(self):
        for laser in self.widget_dict.values():
            for key in self.main_widget.levels.levels_dict.keys():
                if laser.groundBox.findText(key) == -1:
                    laser.groundBox.addItem(key)
                if laser.excitedBox.findText(key) == -1:
                    laser.excitedBox.addItem(key)

    def remove_widget(self, idx):
        self.couplingsLayout.removeWidget(self.widget_dict[idx])
        self.widget_dict[idx].deleteLater()
        self.widget_dict.pop(idx)

    def max_check(self):
        return False


class CouplingWidget(QFrame):
    def __init__(self, num, key, parent=None):
        super().__init__(parent)
        self.num = num
        self.setFrameStyle(QFrame.Box)
        self.layout = QVBoxLayout()
        self.parent = parent
        self.main_widget = parent.main_widget
        self.system_dict = parent.system_dict
        self.coupling_dict = self.system_dict[key][num]
        self.main_boxes = []
        self.AM_boxes = []

        self.mainLayout = QHBoxLayout()
        self.mainFrame = QFrame()
        self.mainFrame.setLayout(self.mainLayout)
        self.layout.addWidget(self.mainFrame)
        self.init_main_boxes()

        self.AMFrame = QFrame()
        self.AMLayout = QHBoxLayout()
        self.AMFrame.setLayout(self.AMLayout)
        self.layout.addWidget(self.AMFrame)
        self.init_AM_boxes()

        self.init_cavity_boxes()

        self.setLayout(self.layout)

        if not self.system_dict["params"]["zeeman"]:
            self.AMFrame.hide()

        self.get_pars()
        self.init_connections()

    def init_main_boxes(self):
        pass

    def init_cavity_boxes(self):
        pass

    def init_AM_boxes(self):
        pass

    def init_connections(self):
        for box in self.main_boxes + self.AM_boxes:
            box.valueChanged.connect(lambda val: self.set_values())

    def set_values(self, key, val):
        coupling_dict = self.coupling_dict
        if key in ("N", "n"):
            maxval = self.NBox.value() - 1
            self.nBox.setMaximum(maxval)
            if self.nBox.value() > maxval:
                self.nBox.setValue(maxval)
        if key in ("s1", "s2", "s3"):
            coupling_dict["S"] = [
                self.s1Box.value(),
                self.s2Box.value(),
                self.s3Box.value(),
            ]
        elif key in ("p1", "p2", "p3"):
            coupling_dict["pol"] = [
                self.polBox.value(),
                self.polBox.value(),
                self.polBox.value(),
            ]
        elif key in ("L1", "L2"):
            level_names = self.main_widget.system_dict["levels"].keys()
            if (self.groundBox.currentText() not in level_names) or (
                self.excitedBox.currentText() not in level_names
            ):
                print("bad level name")
                return
            else:
                coupling_dict["L1"] = self.groundBox.currentText()
                coupling_dict["L2"] = self.excitedBox.currentText()
            print(self.main_widget.system_dict["levels"].keys())
            # coupling_dict["L1"] = self.groundBox.currentText()
            # coupling_dict["L2"] = self.excitedBox.currentText()
        else:
            coupling_dict[key] = val
        print(self.main_widget.system_dict)
        self.main_widget.auto_update()

    def get_pars(self):
        pass

    def set_level_boxes(self):
        level_names = list(self.main_widget.system_dict["levels"].keys())
        print(level_names)
        if self.coupling_dict["L1"] in level_names:
            print("lower level {} found".format(self.coupling_dict["L1"]))
            find_or_add(self.groundBox, self.coupling_dict["L1"])
        else:
            find_or_add(self.groundBox, level_names[0])
            self.coupling_dict["L1"] = level_names[0]
        if self.coupling_dict["L2"] in level_names:
            find_or_add(self.excitedBox, self.coupling_dict["L2"])
            print("upper level {} found".format(self.coupling_dict["L2"]))
        else:
            print("upper level {} not found".format(self.coupling_dict["L2"]))
            find_or_add(self.excitedBox, level_names[1])
            self.coupling_dict["L2"] = level_names[1]


class LasersSection(CouplingSection):
    def __init__(self, parent=None):
        super().__init__("Lasers", "lasers", LaserWidget, parent=parent)

    def max_check(self):
        if self.num_couplings > len(self.system_dict["levels"]) - 2:
            return True
        else:
            return False


class LaserWidget(CouplingWidget):
    def __init__(self, num, key, parent=None):
        super().__init__(num, key, parent=parent)

    def init_main_boxes(self):
        self.groundBox = add_framed_widget(
            QComboBox, self.mainLayout, label="Lower State"
        )

        self.excitedBox = add_framed_widget(
            QComboBox, self.mainLayout, label="Upper State"
        )

        self.omegaBox = add_framed_widget(
            QDoubleSpinBox, self.mainLayout, label="Omega"
        )
        self.omegaBox.setSingleStep(0.1)
        self.omegaBox.setMaximum(100)
        self.deltaBox = add_framed_widget(
            QDoubleSpinBox, self.mainLayout, label="Delta"
        )
        self.deltaBox.setSingleStep(0.1)
        self.deltaBox.setMaximum(100)
        self.deltaBox.setMinimum(-100)

    def init_AM_boxes(self):
        self.kBox = add_framed_widget(QSpinBox, self.AMLayout, label="k")
        self.kBox.setMaximum(360)

        self.s1Box = add_framed_widget(QDoubleSpinBox, self.AMLayout, label="S1")
        self.s2Box = add_framed_widget(QDoubleSpinBox, self.AMLayout, label="S2")
        self.s3Box = add_framed_widget(QDoubleSpinBox, self.AMLayout, label="S3")

        for box in [self.s1Box, self.s2Box, self.s3Box]:
            box.setMinimum(-1.0)
            box.setMaximum(1.0)
            box.setSingleStep(0.1)

    def init_connections(self):
        self.groundBox.currentTextChanged.connect(
            lambda val: self.set_values("L1", val)
        )
        self.excitedBox.currentTextChanged.connect(
            lambda val: self.set_values("L2", val)
        )
        self.omegaBox.valueChanged.connect(lambda val: self.set_values("Omega", val))
        self.deltaBox.valueChanged.connect(lambda val: self.set_values("Delta", val))

        self.kBox.valueChanged.connect(lambda val: self.set_values("k", val))
        self.s1Box.valueChanged.connect(lambda val: self.set_values("s1", val))
        self.s2Box.valueChanged.connect(lambda val: self.set_values("s2", val))
        self.s3Box.valueChanged.connect(lambda val: self.set_values("s3", val))

    def get_pars(self):
        self.set_level_boxes()
        self.omegaBox.setValue(self.coupling_dict["Omega"])
        self.deltaBox.setValue(self.coupling_dict["Delta"])
        self.kBox.setValue(self.coupling_dict["k"])
        self.s1Box.setValue(self.coupling_dict["S"][0])
        self.s2Box.setValue(self.coupling_dict["S"][1])
        self.s3Box.setValue(self.coupling_dict["S"][2])


class CavitySection(CouplingSection):
    def __init__(self, parent=None):
        super().__init__("Cavities", "cavities", CavityWidget, parent=parent)

    def max_check(self):
        if len(self.widget_dict) > 0:
            return True
        else:
            return False


class CavityWidget(CouplingWidget):
    def __init__(self, num, key, parent=None):
        super().__init__(num, key, parent=parent)

    def init_main_boxes(self):
        self.groundBox = add_framed_widget(
            QComboBox, self.mainLayout, label="Lower State"
        )

        self.excitedBox = add_framed_widget(
            QComboBox, self.mainLayout, label="Upper State"
        )

        self.gBox = add_framed_widget(QDoubleSpinBox, self.mainLayout, label="g")
        self.gBox.setSingleStep(0.1)
        self.gBox.setMaximum(100)
        self.deltaBox = add_framed_widget(
            QDoubleSpinBox, self.mainLayout, label="Delta"
        )
        self.deltaBox.setSingleStep(0.1)
        self.deltaBox.setMaximum(100)
        self.deltaBox.setMinimum(-100)

    def init_cavity_boxes(self):
        self.cavityNLayout = QHBoxLayout()
        self.NBox = add_framed_widget(QSpinBox, self.mainLayout, label="Photon cutoff")

        self.nBox = add_framed_widget(QSpinBox, self.mainLayout, label="Initial n")
        self.kappaBox = add_framed_widget(
            QDoubleSpinBox, self.mainLayout, label="kappa"
        )
        self.layout.addLayout(self.mainLayout)

    def init_AM_boxes(self):
        self.kBox = add_framed_widget(QSpinBox, self.AMLayout, label="k")
        self.kBox.setMaximum(360)

        self.p1Box = add_framed_widget(QSpinBox, self.AMLayout, label="pol")
        self.p2Box = add_framed_widget(QSpinBox, self.AMLayout)
        self.p3Box = add_framed_widget(QSpinBox, self.AMLayout)

    def init_connections(self):
        self.groundBox.currentTextChanged.connect(
            lambda val: self.set_values("L1", val)
        )
        self.excitedBox.currentTextChanged.connect(
            lambda val: self.set_values("L2", val)
        )
        self.gBox.valueChanged.connect(lambda val: self.set_values("g", val))
        self.deltaBox.valueChanged.connect(lambda val: self.set_values("Delta", val))
        self.kappaBox.valueChanged.connect(lambda val: self.set_values("kappa", val))
        self.NBox.valueChanged.connect(lambda val: self.set_values("N", val))
        self.nBox.valueChanged.connect(lambda val: self.set_values("n", val))

        self.kBox.valueChanged.connect(lambda val: self.set_values("k", val))
        self.p1Box.valueChanged.connect(lambda val: self.set_values("p1", val))
        self.p2Box.valueChanged.connect(lambda val: self.set_values("p2", val))
        self.p3Box.valueChanged.connect(lambda val: self.set_values("p3", val))

    def get_pars(self):
        self.set_level_boxes()
        self.gBox.setValue(self.coupling_dict["g"])
        self.deltaBox.setValue(self.coupling_dict["Delta"])
        self.kappaBox.setValue(self.coupling_dict["kappa"])
        self.NBox.setValue(self.coupling_dict["N"])
        self.nBox.setValue(self.coupling_dict["n"])
        self.kBox.setValue(self.coupling_dict["k"])
        self.p1Box.setValue(self.coupling_dict["pol"][0])
        self.p2Box.setValue(self.coupling_dict["pol"][1])
        self.p3Box.setValue(self.coupling_dict["pol"][2])


class DecaysSection(CouplingSection):
    def __init__(self, parent=None):
        super().__init__("Decays", "decays", DecayWidget, parent=parent)

    def max_check(self):
        return False


class DecayWidget(CouplingWidget):
    def __init__(self, num, key, parent=None):
        super().__init__(num, key, parent=parent)

    def init_main_boxes(self):
        self.groundBox = add_framed_widget(
            QComboBox, self.mainLayout, label="Lower State"
        )

        self.excitedBox = add_framed_widget(
            QComboBox, self.mainLayout, label="Upper State"
        )

        self.gammaBox = add_framed_widget(
            QDoubleSpinBox, self.mainLayout, label="gamma"
        )
        self.gammaBox.setSingleStep(0.1)
        self.gammaBox.setMaximum(100)

    def init_connections(self):
        self.groundBox.currentTextChanged.connect(
            lambda val: self.set_values("L1", val)
        )
        self.excitedBox.currentTextChanged.connect(
            lambda val: self.set_values("L2", val)
        )
        self.gammaBox.valueChanged.connect(lambda val: self.set_values("gamma", val))

    def get_pars(self):
        self.set_level_boxes()
        self.gammaBox.setValue(self.coupling_dict["gamma"])


class ParamsSection(QGroupBox):
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
        # self.setFrameStyle(QFrame.Box)
        self.setTitle("Parameters")
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
        # self.layout.addWidget(self.setParamsButton)

        self.startBox.valueChanged.connect(self.set_params)
        self.endBox.valueChanged.connect(self.set_params)
        self.stepsBox.valueChanged.connect(self.set_params)
        self.bBox.valueChanged.connect(self.set_params)
        self.zeemanBool.stateChanged.connect(self.set_params)
        self.mixedBool.stateChanged.connect(self.set_params)

        self.setLayout(self.layout)

    def set_params(self):
        self.params = self.main_widget.system_dict["params"]
        self.params["t_start"] = self.startBox.value()
        self.params["t_max"] = self.endBox.value()
        self.params["n_step"] = self.stepsBox.value()

        self.params["B"] = self.bBox.value()
        self.params["Bdir"] = 0
        self.params["zeeman"] = self.zeemanBool.isChecked()
        self.params["mixed"] = self.mixedBool.isChecked()
        self.main_widget.auto_update()


class SolverWidget(QGroupBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        # self.setFrameStyle(QFrame.Box)
        self.setTitle("Solve and Plot")
        self.parent = parent
        self.main_widget = parent
        self.system_dict = parent.system_dict
        self.levels_dict = parent.levels.levels_dict
        self.coupling_list = parent.lasers.coupling_list
        self.params = parent.paramsWidget.params
        self.layout = QHBoxLayout()
        self.exp_dict = {}

        self.topLayout = QHBoxLayout()
        # self.topLayout.addWidget(QLabel("Solver"))

        self.autoSolveBox = QCheckBox("Auto solve")
        self.autoSolveBox.setChecked(True)
        self.layout.addWidget(self.autoSolveBox)

        self.saveNameBox = QLineEdit()
        self.layout.addWidget(self.saveNameBox)

        self.buttonsLayout = QHBoxLayout()
        self.saveButton = QPushButton("Save")
        self.saveButton.clicked.connect(self.save_result)
        self.buttonsLayout.addWidget(self.saveButton)
        self.solveButton = QPushButton("Solve System")
        self.solveButton.clicked.connect(self.main_widget.update)
        self.buttonsLayout.addWidget(self.solveButton)

        self.layout.addLayout(self.buttonsLayout)

        self.setLayout(self.layout)

    def save_result(self):
        """
        creates a json file of the current loop. if auto, this goes to the looplist.
        if not, a file is created based on the current date and time.
        """
        date_dir = datetime.today().strftime("%Y_%m_%d")
        time_path = datetime.today().strftime("%Hh%M")
        full_dir = save_path + date_dir + "/"
        path_pre = full_dir + time_path + "_" + self.saveNameBox.text()
        if not os.path.exists(full_dir):
            os.makedirs(full_dir)

        result_path = path_pre + "_result"
        system_path = path_pre + "_system.json"

        qu.qsave(self.result, result_path)
        with open(system_path, "w") as outfile:
            json.dump(self.system_dict, outfile)

    def solve_system(self):
        try:
            self.system_dict = self.parent.system_dict
            system = build_system_from_dict(self.system_dict)
            self.result, self.e_ops = system.solve()
            self.main_widget.plotter.set_e_ops(self.e_ops)
        except Exception as e:
            print("Failed to solve system")
            print(e)

    def plot_expect(self):
        self.main_widget.plotter.set_e_ops(self.e_ops)
        params = self.main_widget.system_dict["params"]
        for key, op in self.e_ops.items():
            if self.main_widget.plotter.ops_dict[key].isChecked():
                exp = qu.expect(op, self.result.states)
                self.exp_dict[key] = exp
                tlist = np.linspace(
                    params["t_start"], params["t_max"], params["n_step"]
                )
                self.parent.plotter.plot(tlist, exp, label=key)
        self.tlist = tlist

    def init_section(self):
        pass


class PlotWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ops_dict = {}
        self.checked_dict = {}
        self.tlist = []
        self.main_widget = parent
        self.figure, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.figure)
        self.ax.set_xlabel("Time")
        self.ax.set_ylabel("Expectation Value")

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.canvas)

        self.ops_grid = QGridLayout()
        self.layout.addLayout(self.ops_grid)

        self.animationButton = QPushButton("Animation")
        self.animationButton.clicked.connect(self.run_animation)
        self.layout.addWidget(self.animationButton)

        self.setLayout(self.layout)

    def plot(self, *args, **kwargs):
        self.ax.plot(*args, **kwargs)
        self.ax.legend()
        self.canvas.draw()

    def clear(self):
        self.ax.clear()
        self.canvas.draw()

    def set_e_ops(self, e_ops):
        for key, widget in (self.ops_dict.copy()).items():
            self.ops_grid.removeWidget(widget)
            self.ops_dict.pop(key)
        for key, op in e_ops.items():
            row, col = divmod(self.ops_grid.count(), 4)
            # key_html = markdown2.markdown(key)
            widget = QCheckBox(key)
            # widget = htmlCheckBox(key)
            self.ops_dict[key] = widget
            if key in self.checked_dict.keys():
                widget.setChecked(self.checked_dict[key])
            else:
                self.checked_dict[key] = True
                widget.setChecked(True)
            widget.stateChanged.connect(self.update_checked_dict)
            self.ops_grid.addWidget(widget, row, col)

    def init_section(self):
        for key, widget in (self.ops_dict.copy()).items():
            self.ops_grid.removeWidget(widget)
            self.ops_dict.pop(key)
            self.checked_dict.pop(key)

    def update_checked_dict(self):
        for key in self.ops_dict.keys():
            self.checked_dict[key] = (self.ops_dict[key]).isChecked()

    def run_animation(self):
        diagram = self.main_widget.levelDiagram
        params = self.main_widget.system_dict["params"]
        tlist = np.linspace(0, params["t_max"], params["n_step"])
        for i, t in enumerate(tlist):
            vline = self.ax.vlines(t, 0, 1)
            self.canvas.draw()
            for key, point in diagram.level_points.items():
                point[0].set_alpha(self.main_widget.solver.exp_dict[key][i])
            if diagram.cavity_mode:
                n_list = self.main_widget.solver.exp_dict["n"]
                n_norm = n_list / max(n_list)
                diagram.cavity_mode.set_alpha(min((n_norm[i], 1)))
            diagram.canvas.draw()
            QApplication.processEvents()
            time.sleep(2.5 / len(tlist))
            vline.remove()
        self.canvas.draw()
        for point in diagram.level_points.values():
            point[0].set_alpha(0)
        if diagram.cavity_mode:
            diagram.cavity_mode.set_alpha(0)
        diagram.canvas.draw()


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

    def plot(self, system_dict):
        levels = system_dict["levels"]
        lasers = system_dict["lasers"]
        decays = system_dict["decays"]
        params = system_dict["params"]
        cavities = system_dict["cavities"]

        self.level_points = {}
        self.cavity_mode = None

        self.ax.clear()
        zeeman = params["zeeman"]
        for key in levels.keys():
            level = levels[key]
            S = level["S"]
            L = level["L"]
            J = level["J"]
            energy = level["energy"]

            if len(levels.keys()) == 2:
                level_centre = 1
            else:
                level_centre = L

            level_width = 0.6
            am_min = level_centre - level_width / 2
            am_max = level_centre + level_width / 2
            if J != 0:
                J_dec = str(J)
                J_frac = Fraction(J_dec)
                J_frac = "{}/{}".format(J_frac.numerator, J_frac.denominator)
            else:
                J_frac = J
            if zeeman:
                label = "$^{{{}}}{}_{{{}}}$".format(
                    int(2 * S + 1), L_dict_inv[L], J_frac
                )
            else:
                label = level["name"]
            if not zeeman or J == 0:
                self.ax.hlines(y=energy, xmin=am_min, xmax=am_max)
                point = self.ax.plot(
                    level_centre,
                    energy,
                    marker="o",
                    markersize=10,
                    color="red",
                    alpha=0,
                )
                self.level_points[key] = point
            self.ax.text(am_max, energy, label)

            if zeeman and J != 0:
                w = quf.zeemanFS(J, S, L, 1e-4, params["freq_scaling"])
                N = int(2 * J + 1)
                M = np.arange(-J, J + 1)
                B = params["B"]
                m_length = level_width / N
                for i, m in enumerate(M):
                    shift = w * B * m
                    start = am_min + i * m_length
                    stop = am_min + (i + 1) * m_length
                    y = energy + shift
                    self.ax.hlines(y=y, xmin=start, xmax=stop)
                    M_dec = str(m)
                    M_frac = Fraction(M_dec)
                    M_frac = "{}/{}".format(M_frac.numerator, M_frac.denominator)
                    new_key = key + " $m_J=$" + M_frac
                    point = self.ax.plot(
                        (start + stop) / 2,
                        y,
                        marker="o",
                        markersize=5,
                        color="red",
                        alpha=0,
                    )
                    self.level_points[new_key] = point

        for laser in lasers:
            Omega = laser["Omega"]
            if Omega == 0:
                continue
            Delta = laser["Delta"]

            if len(levels.keys()) == 2:
                x1 = 1
                x2 = 1
            else:
                x1 = levels[laser["L1"]]["L"]
                x2 = levels[laser["L2"]]["L"]

            dx = x2 - x1

            y1 = levels[laser["L1"]]["energy"]
            energy_2 = levels[laser["L2"]]["energy"]
            y2 = energy_2 - Delta / 10
            dy = y2 - y1

            x_offset = -np.sign(dx) * 0.1
            label = "$\Omega={}$,\n$\Delta={}$".format(round(Omega, 3), round(Delta, 3))
            alpha = min([Omega, 1])
            self.ax.arrow(
                x1 + x_offset,
                y1,
                dx / 1.2,
                dy,
                width=0.02,
                length_includes_head=True,
                alpha=alpha,
            )

            label_offset = 0
            if np.sign(dx) == -1:
                label_offset -= 0.4
            self.ax.text(x1 + label_offset, y1 + dy / 1.5, label)

            if Delta != 0:
                self.ax.hlines(
                    y=y2,
                    xmin=x2 - level_width / 2,
                    xmax=x2 + level_width / 2,
                    linestyle="dashed",
                )

        for decay in decays:
            Gamma = decay["gamma"]
            if len(levels.keys()) == 2:
                x1 = 1
                x2 = 1
            else:
                x1 = levels[decay["L1"]]["L"]
                x2 = levels[decay["L2"]]["L"]
            dx = x2 - x1

            y1 = levels[decay["L1"]]["energy"]
            energy_2 = levels[decay["L2"]]["energy"]
            y2 = energy_2
            dy = y2 - y1

            x_offset = -np.sign(dx) * 0.1
            label = "$\Gamma={}$".format(round(Gamma, 3))
            alpha = min([Gamma, 1])
            self.ax.arrow(
                x2 + x_offset,
                y2,
                -dx / 1.2,
                -dy,
                width=0.02,
                length_includes_head=True,
                alpha=alpha,
                linestyle="--",
            )
            label_offset = dx / 4 + 0.1
            if np.sign(dx) == -1:
                label_offset -= 0.6
            self.ax.text(x1 + label_offset, y1 + dy / 4, label)

        for cavity in cavities:
            g = cavity["g"]
            if g == 0:
                continue
            Delta = cavity["Delta"]

            if len(levels.keys()) == 2:
                x1 = 1
                x2 = 1
            else:
                x1 = levels[cavity["L1"]]["L"]
                x2 = levels[cavity["L2"]]["L"]
            dx = x2 - x1

            y1 = levels[cavity["L1"]]["energy"]
            energy_2 = levels[cavity["L2"]]["energy"]
            y2 = energy_2
            dy = y2 - y1

            self.add_cavity_mirrors(min([x1, x2]), dx, y1, dy, cavity)

            # self.ax.text(x1 + dx/2 - 0.4, y1 + dy / 2, label)

        # Set labels and legend
        self.ax.set_xlabel("L")
        self.ax.set_xticks([0, 1, 2])
        self.ax.set_ylabel("Energy (arb scale)")
        self.ax.set_yticks([])
        # self.ax.legend()

        # Show the plot
        self.canvas.draw()

    def add_mirror(self, x, dx, y, dy, side, cavity):
        g = cavity["g"]
        Delta = cavity["Delta"]
        kappa = cavity["kappa"]
        angle1 = -np.pi / 5
        angle2 = np.pi / 5
        dx = abs(dx)
        offset = 0.3
        x_circle = x + dx / 2 + offset
        if side == "L":
            angle1 += np.pi
            angle2 += np.pi
            x_circle -= 2 * offset
        y_circle = y + dy / 2
        radius = 0.3
        theta = np.linspace(angle1, angle2, 100)
        x_s1 = x_circle + radius * np.cos(theta)
        y_s1 = y_circle + radius * np.sin(theta)

        mirror = lines.Line2D(x_s1, y_s1)
        self.ax.add_line(mirror)

        if side == "L":
            label = "$g={}$,\n$\Delta_c={}$".format(round(g, 3), round(Delta, 3))
            self.ax.text(x_circle - radius - offset, y_circle - 0.4, label)

        if side == "R":
            if kappa:
                alpha = min([kappa, 1])
                self.ax.arrow(
                    x_circle + radius,
                    y_circle,
                    0.2,
                    0,
                    width=0.01,
                    length_includes_head=True,
                    alpha=alpha,
                    linestyle="--",
                )
                self.ax.text(
                    x_circle + radius, y_circle + 0.1, "$\kappa={}$".format(kappa)
                )
        mode_x = np.linspace(
            x + dx / 2 - offset - radius, x + dx / 2 + offset + radius, 100
        )
        x_list = np.linspace(0, 5 * np.pi, 100)
        mode_y_p = 0.1 * np.sin(x_list) + y_circle
        mode_y_m = -0.1 * np.sin(x_list) + y_circle
        # mode_p = plt.plot(mode_x, mode_y_p)
        # mode_m = plt.plot(mode_x, mode_y_m)
        self.cavity_mode = plt.fill_between(mode_x, mode_y_p, mode_y_m, alpha=0)

    def add_cavity_mirrors(self, x, dx, y, dy, cavity):
        self.add_mirror(x, dx, y, dy, "L", cavity)
        self.add_mirror(x, dx, y, dy, "R", cavity)


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
