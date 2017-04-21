
import xml.etree.ElementTree as ElementTree

class Solver():
    
    def __init__(self):
        # FARI Better: Use Dataframe from pandas and just keep adding?
        self.options = { 'solvertype_recognition': "default",
        'primalboundpatterns': "default",
        'primalboundindices': "default",
        'dualboundpatterns': "default",
        'dualboundindices': "default",
        'solvingtimereadkeys': "default",
        'solvingtimelineindex': "default"}

    def initializeSolverFromFile(self, filename):
        tree = ElementTree.parse(filename)
        root = tree.getroot()
