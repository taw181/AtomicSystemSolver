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
from systems import sysdict, default_params

class AtomGui(QMainWindow):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)

        self.setWindowTitle("Atomic System Solver")
        self.mainWidget = QWidget(self)
        self.mainLayout = QHBoxLayout()
        self.settings = QSettings()

        self.systemLayout = QVBoxLayout()

        self.initLayout = QHBoxLayout()

        self.sysName = ComboBox('System')
        for system in sysdict.keys():
            self.sysName.box.addItem(system)
        self.initLayout.addWidget(self.sysName)
        
        self.initButton = PushButton('Load Settings')
        self.initButton.button.clicked.connect(self.initSystem)
        self.initLayout.addWidget(self.initButton)
        self.systemLayout.addLayout(self.initLayout)

        self.levels = levelsSection(parent=self)
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
        
        self.initSystem()

    def initSystem(self):
        sys = sysdict[self.sysName.box.currentText()]
        for level in sys.levels:
            self.levels.addLevel(self)


class levelsSection(QFrame):
    def __init__(self,parent=None):
        super().__init__(parent)
        self.levelsdict = {}
        self.levelsWidgetDict = {}
        self.num = 0
        self.AMHidden = True
        self.setFrameStyle(QFrame.box)
        self.layout = QVBoxLayout()
        self.layout.addWidget(QLabel('Levels'))

        self.buttonsLayout = QHBoxLayout()
        self.addLevelButton = QPushButton('Add level')
        self.addLevelButton.clicked.connect(lambda: self.addLevel(parent))
        self.buttonsLayout.addWidget(self.addLevelButton)

        self.showAMButton = QPushButton('Toggle AM Settings')
        self.showAMButton.clicked.connect(lambda: self.showAM(parent))
        self.buttonsLayout.addWidget(self.showAMButton)

        self.layout.addLayout(self.buttonsLayout)
        self.setLayout(self.layout)

    def addLevel(self,parent):
        level = levelWidget(num=self.num,parent=parent)
        self.levelsWidgetDict[str(self.num)] = level
        self.layout.addWidget(self.levelsWidgetDict[str(self.num)])
        level.setlevel(self.num,parent)
        self.num += 1

    def showAM(self,parent):
        if self.AMHidden:
            self.AMHidden = False
            for level in self.levelsWidgetDict.values():
                level.AMFrame.show()
            for laser in parent.lasers.laserWidgetDict.values():
                laser.AMFrame.show()
        else:
            self.AMHidden = True
            for level in self.levelsWidgetDict.values():
                level.AMFrame.hide()
            for laser in parent.lasers.laserWidgetDict.values():
                laser.AMFrame.hide()


class levelWidget(QFrame):
    def __init__(self,num = 0, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout()
        self.setFrameStyle(QFrame.box)

        self.levelMainLayout = QHBoxLayout()

        self.nameBox = TextBox('Name')
        self.nameBox.box.setText(str(num))
        self.nameBox.box.textChanged.connect(lambda: self.setlevel(num,parent))
        self.levelMainLayout.addWidget(self.nameBox)

        self.kindBox = ComboBox('Kind')
        self.kindBox.box.addItem('g')
        self.kindBox.box.addItem('e')
        self.kindBox.box.currentIndexChanged.connect(lambda: self.setlevel(num,parent))
        self.levelMainLayout.addWidget(self.kindBox)

        self.popBox = TextBox('pop')
        self.popBox.box.textChanged.connect(lambda: self.setlevel(num,parent))
        self.levelMainLayout.addWidget(self.popBox)

        self.layout.addLayout(self.levelMainLayout)

        self.AMFrame = QFrame()
        self.levelAMLayout = QHBoxLayout()
        
        self.sBox = SpinBox('S')
        self.sBox.box.valueChanged.connect(lambda: self.setlevel(num,parent))
        self.levelAMLayout.addWidget(self.sBox)
        
        self.lBox = SpinBox('L')
        self.lBox.box.valueChanged.connect(lambda: self.setlevel(num,parent))
        self.levelAMLayout.addWidget(self.lBox)
        
        self.jBox = SpinBox('J')
        self.jBox.box.valueChanged.connect(lambda: self.setlevel(num,parent))
        self.levelAMLayout.addWidget(self.jBox)

        self.AMFrame.setLayout(self.levelAMLayout)
        self.layout.addWidget(self.AMFrame)
        if parent.levels.AMHidden:
            self.AMFrame.hide()

        # self.removeButton = QPushButton('Remove Level')
        # self.removeButton.clicked.connect(lambda: self.removeLevel(num,parent))
        # self.layout.addWidget(self.removeButton)

        self.setLayout(self.layout)
        
    def get_level_pars(self, params):
        pass

    def setlevel(self,num,parent):
        levelpars = {}
        levelpars['name'] = self.nameBox.box.text()
        levelpars['kind'] = self.kindBox.box.currentText()
        pop = self.popBox.box.text()
        if pop == '':
            levelpars['pop'] = 0
        else:
            levelpars['pop'] = [float(i) for i in pop.split(',')]
        levelpars['J'] = self.jBox.box.value()
        levelpars['L'] = self.lBox.box.value()
        levelpars['S'] = self.sBox.box.value()
        parent.levels.levelsdict[str(num)] = levelpars


    def delete_level(self):
        """
        deleting widgets in pyqt is difficult and prone to errors. this function likely has some overkill.
        """
        self.groupItemList.remove(self)  # remove the item from the command list
        self.parent.layout.removeWidget(self)  # remove the item widget from the layout
        for i, item in enumerate(self.groupItemList):  # update labels
            item.idx = i
            item.update_idx_label()
        self.parent.children().remove(self)  # remove the item widget from the layout again, but different?
        self.deleteLater()  # remove the widget from memory, later ??
        self.update_loop_file()

class lasersSection(QFrame):
    def __init__(self,parent=None):
        super().__init__(parent)
        self.lasersdict = {}
        self.laserWidgetDict = {}
        self.num = 0
        self.layout = QVBoxLayout()
        self.setFrameStyle(QFrame.box)
        self.layout.addWidget(QLabel('Lasers'))

        self.buttonsLayout = QHBoxLayout()
        self.addLaserButton = QPushButton('Add laser')
        self.addLaserButton.clicked.connect(lambda: self.addLaser(parent))
        self.buttonsLayout.addWidget(self.addLaserButton)

        self.getLevelsButton = QPushButton('Get Levels')
        self.getLevelsButton.clicked.connect(lambda: self.getLevels(parent))
        self.buttonsLayout.addWidget(self.getLevelsButton)

        self.layout.addLayout(self.buttonsLayout)

        self.setLayout(self.layout)

    def addLaser(self,parent):
        num = self.num
        laser = laserWidget(num=self.num,parent=parent)
        self.laserWidgetDict[str(num)] = laser
        self.layout.addWidget(self.laserWidgetDict[str(num)])
        laser.setLaser(num,parent)
        self.num += 1

    def getLevels(self, parent):
        print('getting levels')
        for laser in self.laserWidgetDict.values():
            laser.groundBox.box.clear()
            laser.excitedBox.box.clear()
            for v in parent.levels.levelsdict.values():
                laser.groundBox.box.addItem(v['name'])
                laser.excitedBox.box.addItem(v['name'])



class laserWidget(QFrame):
    def __init__(self,num = 0,parent=None):
        super().__init__(parent)
        self.num = num
        self.setFrameStyle(QFrame.box)
        self.layout = QVBoxLayout()

        self.laserMainLayout = QHBoxLayout()
        self.groundBox = ComboBox('Lower State')
        self.groundBox.box.currentIndexChanged.connect(lambda: self.setLaser(num, parent))
        self.excitedBox = ComboBox('Upper State')
        self.excitedBox.box.currentIndexChanged.connect(lambda: self.setLaser(num, parent))
        self.laserMainLayout.addWidget(self.groundBox)
        self.laserMainLayout.addWidget(self.excitedBox)

        self.omegaBox = SpinBox('Omega',default=1)
        self.omegaBox.box.valueChanged.connect(lambda: self.setLaser(num, parent))
        self.laserMainLayout.addWidget(self.omegaBox)

        self.deltaBox = SpinBox('delta',default=1)
        self.deltaBox.box.valueChanged.connect(lambda: self.setLaser(num, parent))
        self.laserMainLayout.addWidget(self.deltaBox)

        self.layout.addLayout(self.laserMainLayout)

        self.AMFrame = QFrame()
        self.laserDirLayout = QHBoxLayout()
        self.kBox = SpinBox('k', maxval=360)
        self.kBox.box.valueChanged.connect(lambda: self.setLaser(num, parent))
        self.laserDirLayout.addWidget(self.kBox)

        self.s1Box = SpinBox('S')
        self.s2Box = SpinBox('')
        self.s3Box = SpinBox('')
        self.s1Box.box.valueChanged.connect(lambda: self.setLaser(num, parent))
        self.s2Box.box.valueChanged.connect(lambda: self.setLaser(num, parent))
        self.deltaBox.box.valueChanged.connect(lambda: self.setLaser(num, parent))
        self.laserDirLayout.addWidget(self.s1Box)
        self.laserDirLayout.addWidget(self.s2Box)
        self.laserDirLayout.addWidget(self.s3Box)

        self.AMFrame.setLayout(self.laserDirLayout)
        self.layout.addWidget(self.AMFrame)
        if parent.levels.AMHidden:
            self.AMFrame.hide()

        # self.setLaserButton = QPushButton('Set Laser')
        # self.setLaserButton.clicked.connect(lambda: self.setLaser(num, parent))
        # self.layout.addWidget(self.setLaserButton)

        self.setLayout(self.layout)

        #self.getLevels(parent)

    def setLaser(self, num, parent):
        laserpars = {}
        laserpars['L1'] = self.groundBox.box.currentText()
        laserpars['L2'] = self.excitedBox.box.currentText()
        laserpars['Omega'] = self.omegaBox.box.value()
        laserpars['Delta'] = self.deltaBox.box.value()
        laserpars['k'] = self.kBox.box.value()
        laserpars['S'] = [self.s1Box.box.value(), self.s2Box.box.value(), self.s3Box.box.value()]

        parent.lasers.lasersdict[str(num)] = laserpars
        #print('Laser {} set'.format(num))


class paramsSection(QFrame):
    def __init__(self,parent=None,):
        super().__init__(parent)
        self.params = default_params
        self.initGUI()
        self.setParams()

    def initGUI(self):
        self.setFrameStyle(QFrame.box)
        self.layout = QVBoxLayout()

        self.tlistGroup = QGroupBox('tlist')
        self.tlistLayout = QHBoxLayout()

        self.startBox = SpinBox('t_start',intval=True)
        self.tlistLayout.addWidget(self.startBox)
        self.endBox = SpinBox('t_stop',intval=True,default=10)
        self.tlistLayout.addWidget(self.endBox)
        self.stepsBox = SpinBox('t_steps',intval=True,default=1000)
        self.tlistLayout.addWidget(self.stepsBox)
        self.tlistGroup.setLayout(self.tlistLayout)
        self.layout.addWidget(self.tlistGroup)

        self.bFieldGroup = QGroupBox('B Field')
        self.bFieldLayout = QHBoxLayout()
        self.bBox = SpinBox('B')
        self.bFieldLayout.addWidget(self.bBox)
        self.bDirBox = SpinBox('Bdir',intval=True, maxval=360)
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
        start = self.startBox.box.value()
        stop = self.endBox.box.value()
        steps = self.stepsBox.box.value()
        self.params['tlist'] = np.linspace(start,stop,steps)

        self.params['B'] = self.bBox.box.value()
        self.params['Bdir'] = 0
        self.params['zeeman'] = self.zeemanBool.isChecked()
        self.params['mixed'] = self.mixedBool.isChecked()

class solverWidget(QFrame):
    def __init__(self,parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.box)
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
        self.box = QLineEdit()
        layout.addWidget(self.box)
        self.setLayout(layout)

class SpinBox(QFrame):
    def __init__(self,label,default=0, intval=False, minval=0, maxval = 1000000):
        super().__init__()
        layout = QVBoxLayout()
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(1)
        layout.addWidget(QLabel(label))
        if intval:
            self.box = QSpinBox()
        else:
            self.box = QDoubleSpinBox()
        self.box.setMinimum(minval)
        self.box.setMaximum(maxval)
        self.box.setValue(default)
        layout.addWidget(self.box)
        self.setLayout(layout)

class ComboBox(QFrame):
    def __init__(self,label):
        super().__init__()
        layout = QVBoxLayout()
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(1)
        layout.addWidget(QLabel(label))
        self.box = QComboBox()
        layout.addWidget(self.box)
        self.setLayout(layout)
        
class PushButton(QFrame):
    def __init__(self,label):
        super().__init__()
        layout = QVBoxLayout()
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(1)
        layout.addWidget(QLabel())
        self.button = QPushButton(label)
        layout.addWidget(self.button)
        self.setLayout(layout)


if __name__ == '__main__':
    app = QApplication(sys.argv)

    window = AtomGui()
    window.show()

    app.exec_()
