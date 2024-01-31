# AtomicSystemSolver

Requires PyQt5 and QuTiP

Object-oriented approach to building and solving atomic systems using QuTiP.

Atomic Levels, Lasers, Decays, and Cavities are classes. The system Hamiltonian is created by the AtomicSystem class, which takes the objects above above as arguments. Changing a property of an object (e.g. laser rabi frequency) automatically updated the system Hamiltonian. The evolution of the system can be solved using AtomicSystem's solve method.

Systems can be saved to and loaded from json files.

There is a GUI that can load system jsons and display the results of the simulation, allowing changes to parameters to be easily visualised.
