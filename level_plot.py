import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt

class GrotrianDiagram(QWidget):
    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):
        # Create a Matplotlib figure and canvas
        self.fig, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.fig)

        # Set up the PyQt window
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.canvas)

        self.setLayout(self.layout)

        # Create the Grotrian diagram
        self.plotGrotrianDiagram()

    def plotGrotrianDiagram(self):
        # Customize this function based on your Grotrian diagram requirements
        # Here's a simple example with S, P, and D levels connected by lasers

        # Angular momentum or quantum numbers
        s_angular_momentum = 0
        p_angular_momentum = 1
        d_angular_momentum = 2

        # Energy levels
        s_energy = 2
        p_energy = 4
        d_energy = 3

        # Laser transitions
        s_to_p = [s_angular_momentum, p_angular_momentum]
        d_to_p = [d_angular_momentum, p_angular_momentum]

        # Plot energy levels as horizontal bars
        self.ax.hlines(y=s_energy, xmin=s_angular_momentum - 0.2, xmax=s_angular_momentum + 0.2, color='r', label='S Level')
        self.ax.hlines(y=p_energy, xmin=p_angular_momentum - 0.2, xmax=p_angular_momentum + 0.2, color='b', label='P Level')
        self.ax.hlines(y=d_energy, xmin=d_angular_momentum - 0.2, xmax=d_angular_momentum + 0.2, color='g', label='D Level')

        # Plot laser transitions
        self.ax.plot(s_to_p, [s_energy, p_energy], 'k-', label='S to P Laser')
        self.ax.plot(d_to_p, [d_energy, p_energy], 'k-', label='D to P Laser')

        # Set labels and legend
        self.ax.set_xlabel('Angular Momentum')
        self.ax.set_ylabel('Energy Level')
        self.ax.legend()

        # Show the plot
        self.canvas.draw()

def main():
    app = QApplication(sys.argv)
    mainWindow = QMainWindow()
    mainWindow.setGeometry(100, 100, 800, 600)

    centralWidget = GrotrianDiagram()
    mainWindow.setCentralWidget(centralWidget)

    mainWindow.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
