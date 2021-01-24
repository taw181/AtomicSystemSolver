import sys
import time
import numpy as np

from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, pyqtSlot, pyqtSignal, QThread, QThreadPool, QRunnable, QObject, QSettings
from pyqtgraph import PlotWidget, plot
import pyqtgraph as pg

import qutip as qu
import numpy as np
import qutipfuncs as quf
import matplotlib.pyplot as plt
from qobjects import *
from system_builder import *

class AtomGui(QMainWindow):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)

        self.setWindowTitle("Atomic System Solver")
        self.mainWidget = QWidget(self)
        self.mainLayout = QHBoxLayout()
        self.settings = QSettings()

        self.systemLayout = QVBoxLayout()

        self.levels = levelsSection()
        self.systemLayout.addWidget(self.levels)
        self.lasers = lasersSection(parent=self)
        self.systemLayout.addWidget(self.lasers)
        self.paramswidget = paramsSection(parent=self)
        self.systemLayout.addWidget(self.paramswidget)
        self.solver = solverWidget(parent=self)
        self.systemLayout.addWidget(self.solver)
        self.mainLayout.addLayout(self.systemLayout)

        self.plotLayout = QVBoxLayout()
        self.plotter = pg.PlotWidget()
        self.plotLayout.addWidget(self.plotter)
        self.clearButton = QPushButton('Clear')
        self.clearButton.clicked.connect(self.plotter.clear)
        self.plotLayout.addWidget(self.clearButton)
        self.mainLayout.addLayout(self.plotLayout)

        self.mainWidget.setLayout(self.mainLayout)
        self.setCentralWidget(self.mainWidget)


class levelsSection(QFrame):
    def __init__(self,parent=None):
        super().__init__(parent)
        self.levelsdict = {}
        self.num = 0
        self.layout = QVBoxLayout()
        self.setFrameStyle(QFrame.Box)
        self.layout.addWidget(QLabel('Levels'))
        self.addLevelButton = QPushButton('Add level')
        self.addLevelButton.clicked.connect(self.addLevel)
        self.layout.addWidget(self.addLevelButton)
        self.setLayout(self.layout)

    def addLevel(self):
        self.layout.addWidget(levelWidget(num=self.num,parent=self))
        self.num+=1


class levelWidget(QFrame):
    def __init__(self,num = 0, parent=None):
        super().__init__(parent)
        self.layout = QHBoxLayout()
        self.setFrameStyle(QFrame.Box)

        self.nameBox = TextBox('Name')
        self.nameBox.Box.setText(str(num))
        self.nameBox.Box.textChanged.connect(lambda: self.setlevel(num,parent))
        self.layout.addWidget(self.nameBox)

        self.kindBox = ComboBox('Kind')
        self.kindBox.Box.addItem('g')
        self.kindBox.Box.addItem('e')
        self.kindBox.Box.currentIndexChanged.connect(lambda: self.setlevel(num,parent))
        self.layout.addWidget(self.kindBox)

        self.popBox = TextBox('pop')
        self.popBox.Box.textChanged.connect(lambda: self.setlevel(num,parent))
        self.layout.addWidget(self.popBox)

        self.jBox = SpinBox('J')
        self.jBox.Box.valueChanged.connect(lambda: self.setlevel(num,parent))
        self.layout.addWidget(self.jBox)

        self.lBox = SpinBox('L')
        self.lBox.Box.valueChanged.connect(lambda: self.setlevel(num,parent))
        self.layout.addWidget(self.lBox)

        # self.removeButton = QPushButton('Remove Level')
        # self.removeButton.clicked.connect(lambda: self.removeLevel(num,parent))
        # self.layout.addWidget(self.removeButton)

        self.setLayout(self.layout)

    def setlevel(self,num,parent):
        levelpars = {}
        levelpars['name'] = self.nameBox.Box.text()
        levelpars['kind'] = self.kindBox.Box.currentText()
        levelpars['pop'] = [float(i) for i in self.popBox.Box.text().split(',')]
        levelpars['J'] = self.jBox.Box.value()
        levelpars['L'] = self.lBox.Box.value()
        parent.levelsdict[str(num)] = levelpars

        print(levelpars['pop'])

class lasersSection(QFrame):
    def __init__(self,parent=None):
        super().__init__(parent)
        self.lasersdict = {}
        self.num = 0
        self.layout = QVBoxLayout()
        self.setFrameStyle(QFrame.Box)
        self.layout.addWidget(QLabel('Lasers'))
        self.addLaserButton = QPushButton('Add laser')
        self.addLaserButton.clicked.connect(lambda: self.addLaser(parent))
        self.layout.addWidget(self.addLaserButton)

        self.setLayout(self.layout)

    def addLaser(self,parent):
        self.layout.addWidget(laserWidget(num=self.num,parent=parent))
        self.num += 1

class laserWidget(QFrame):
    def __init__(self,num = 0,parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.Box)
        self.layout = QHBoxLayout()
        self.groundBox = ComboBox('Lower State')
        self.groundBox.Box.currentIndexChanged.connect(lambda: self.setLaser(num, parent))
        self.excitedBox = ComboBox('Upper State')
        self.excitedBox.Box.currentIndexChanged.connect(lambda: self.setLaser(num, parent))
        self.layout.addWidget(self.groundBox)
        self.layout.addWidget(self.excitedBox)

        self.omegaBox = SpinBox('Omega',default=1)
        self.omegaBox.Box.valueChanged.connect(lambda: self.setLaser(num, parent))
        self.layout.addWidget(self.omegaBox)

        # self.setLaserButton = QPushButton('Set Laser')
        # self.setLaserButton.clicked.connect(lambda: self.setLaser(num, parent))
        # self.layout.addWidget(self.setLaserButton)

        self.getLevelsButton = QPushButton('Get Levels')
        self.getLevelsButton.clicked.connect(lambda: self.getLevels(parent))
        self.layout.addWidget(self.getLevelsButton)

        self.setLayout(self.layout)

        self.getLevels(parent)

    def setLaser(self, num, parent):
        laserpars = {}
        laserpars['L1'] = self.groundBox.Box.currentText()
        laserpars['L2'] = self.excitedBox.Box.currentText()
        laserpars['Omega'] = self.omegaBox.Box.value()

        parent.lasers.lasersdict[str(num)] = laserpars
        #print('Laser {} set'.format(num))

    def getLevels(self, parent):
        print('getting levels')
        self.groundBox.Box.clear()
        self.excitedBox.Box.clear()
        for v in parent.levels.levelsdict.values():
            self.groundBox.Box.addItem(v['name'])
            self.excitedBox.Box.addItem(v['name'])

class paramsSection(QFrame):
    def __init__(self,parent=None,):
        super().__init__(parent)
        self.params = {}
        self.initGUI()
        self.setParams()

    def initGUI(self):
        self.setFrameStyle(QFrame.Box)
        self.layout = QVBoxLayout()

        self.tlistGroup = QGroupBox('tlist')
        self.tlistLayout = QHBoxLayout()

        self.startBox = SpinBox('t_start',int=True)
        self.tlistLayout.addWidget(self.startBox)
        self.endBox = SpinBox('t_stop',int=True,default=10)
        self.tlistLayout.addWidget(self.endBox)
        self.stepsBox = SpinBox('t_steps',int=True,default=1000)
        self.tlistLayout.addWidget(self.stepsBox)
        self.tlistGroup.setLayout(self.tlistLayout)
        self.layout.addWidget(self.tlistGroup)

        self.bFieldGroup = QGroupBox('B Field')
        self.bFieldLayout = QHBoxLayout()
        self.bBox = SpinBox('B')
        self.bFieldLayout.addWidget(self.bBox)
        self.bDirBox = TextBox('Bdir')
        self.bFieldLayout.addWidget(self.bDirBox)
        self.zeemanBool = QCheckBox()
        self.zeemanBool.setText('Zeeman?')
        self.bFieldLayout.addWidget(self.zeemanBool)
        self.bFieldGroup.setLayout(self.bFieldLayout)
        self.layout.addWidget(self.bFieldGroup)

        self.othersLayout = QHBoxLayout()
        self.mixedBool = QCheckBox()
        self.mixedBool.setText('Mixed states?')
        self.othersLayout.addWidget(self.mixedBool)
        self.bFieldLayout.addLayout(self.othersLayout)

        self.setParamsButton = QPushButton('Set Params')
        self.setParamsButton.clicked.connect(self.setParams)
        self.layout.addWidget(self.setParamsButton)

        self.setLayout(self.layout)

    def setParams(self):
        start = self.startBox.Box.value()
        stop = self.endBox.Box.value()
        steps = self.stepsBox.Box.value()
        self.params['tlist'] = np.linspace(start,stop,steps)

        self.params['B'] = self.bBox.Box.value()
        self.params['Bdir'] = [0,0,1]
        self.params['zeeman'] = self.zeemanBool.isChecked()
        self.params['mixed'] = self.mixedBool.isChecked()

class solverWidget(QFrame):
    def __init__(self,parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.Box)
        self.levelsdict = parent.levels.levelsdict
        self.lasersdict = parent.lasers.lasersdict
        self.params = parent.paramswidget.params
        self.layout = QHBoxLayout()
        self.layout.addWidget(QLabel('Solver'))
        self.printButton = QPushButton('Print')
        self.printButton.clicked.connect(self.printSystem)
        self.layout.addWidget(self.printButton)
        self.solveButton = QPushButton('Solve System')
        self.solveButton.clicked.connect(self.solveSystem)
        self.layout.addWidget(self.solveButton)
        self.plotButton = QPushButton('Plot')
        self.plotButton.clicked.connect(lambda: self.plotExpect(parent))
        self.layout.addWidget(self.plotButton)
        self.setLayout(self.layout)

    def printSystem(self):
        levels = []
        for v in self.levelsdict.values():
            levels.append(Level(**v))
        lasers = []
        for v in self.lasersdict.values():
            lasers.append(Laser(**v))
        print(levels)
        print(' ')
        print(lasers)
        print(' ')
        print(self.params)

    def solveSystem(self):
        levels = []
        for v in self.levelsdict.values():
            levels.append(Level(**v))
        lasers = []
        for v in self.lasersdict.values():
            lasers.append(Laser(**v))
        system = AtomSystem(levels,lasers,self.params)
        self.result = system.solve()

    def plotExpect(self,parent):
        P = self.result.expect
        for i,pop in enumerate(P):
            parent.plotter.plot(self.params['tlist'],pop)


class TextBox(QFrame):
    def __init__(self,label):
        super().__init__()
        layout = QVBoxLayout()
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(1)
        layout.addWidget(QLabel(label))
        self.Box = QLineEdit()
        layout.addWidget(self.Box)
        self.setLayout(layout)

class SpinBox(QFrame):
    def __init__(self,label,default=0,int=False):
        super().__init__()
        layout = QVBoxLayout()
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(1)
        layout.addWidget(QLabel(label))
        if int:
            self.Box = QSpinBox()
        else:
            self.Box = QDoubleSpinBox()
        self.Box.setMaximum(1000000)
        self.Box.setValue(default)
        layout.addWidget(self.Box)
        self.setLayout(layout)

class ComboBox(QFrame):
    def __init__(self,label):
        super().__init__()
        layout = QVBoxLayout()
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(1)
        layout.addWidget(QLabel(label))
        self.Box = QComboBox()
        layout.addWidget(self.Box)
        self.setLayout(layout)

if __name__ == '__main__':
    app = QApplication(sys.argv)

    window = AtomGui()
    window.show()

    app.exec_()
