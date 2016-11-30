'''
Created on 06.03.2013

@author: bzfhende
'''
from tkinter import Tk, Listbox, Menu
from ipet import Experiment
# from IpetScatterWidget import IpetScatterWidget
from tkinter.constants import BOTH, TOP, LEFT, RIGHT, VERTICAL, END, BOTTOM
# from IPETBoundHistoryWidget import IPETBoundHistoryWidget
from .IPETTableWidget import IpetTableWidget
from ipet import TestRun
import tkinter.ttk
from .IPETOutputWidget import IpetOutputWidget
import tkinter.filedialog
from .IPETManagerMenu import IPETManagerMenu
from tkinter.ttk import Frame, Label, Button, Scrollbar, Separator
import tkinter.constants
from .IPETBoundHistoryWidget import IPETBoundHistoryWidget
from .IpetMessageWidget import IpetMessageWidget
from .IPETScatterWidget import IpetScatterWidget
from .IPETProgressStatus import IpetProgressStatus
from .IPETImageButton import IpetImageButton

class IpetApplication(Tk):
    DEFAULT_BORDERWIDTH = 15

    selected_problem = ''
    selected_testrun = None
    _experiment = None

    listboxlistmap = {}
    listToActionDict = {}
    updatableWidgets = []

    TITLE = "IPET- Interactive Python Evaluation Tools"



    def __init__(self, _experiment = None, show = True):
        '''
        initializes a IpetApplication. Pass an existing _experiment or None to make the GUI create a new, empty
        _experiment instance
        '''
        Tk.__init__(self)
        self.wm_title(IpetApplication.TITLE)
        screenwidth = self.winfo_screenwidth()
        screenheight = self.winfo_screenheight()

#        self.selectionframe = Frame(self, width=screenwidth / 10, height=screenheight)
#        self.selectionframe.pack(side=LEFT, fill=Tkconstants.Y)
#
#        selectionstatusframe = Frame(self.selectionframe, width=screenwidth / 10)
#        Label(selectionstatusframe, text="Current Selection:").pack(side=TOP, fill=Tkconstants.X)
#        self.selectedProbLabel = Label(selectionstatusframe)
#        self.selectedTestrunLabel = Label(selectionstatusframe, justify=RIGHT)
#
#        self.selectedProbLabel.pack(side=TOP, fill=Tkconstants.X)
#        self.selectedTestrunLabel.pack(side=TOP, fill=Tkconstants.X)
#        selectionstatusframe.pack(side=TOP)
#
#        problemslabel = Label(self.selectionframe, text="Problem: ")
#        problemslabel.pack(side=TOP)
#
#        probnamesselectionframe, self.probnamesbox = self.listmakeBoxWithScrollbar(self.selectionframe,
#                                                                                   self.getProblemList(), self.setSelectedProblem,
#                                                                                   theheight=screenheight / 2)
#        testrunlistboxframe, self.testrunsbox = self.listmakeBoxWithScrollbar(self.selectionframe, self.getTestrunnames(),
#                                                                              self.setSelectedTestrun, theheight=screenheight / 3)
#        probnamesselectionframe.pack(side=TOP, fill=Tkconstants.X)
#
#        testrunlabel = Label(self.selectionframe, text="Testrun: ")
#        testrunlabel.pack(side=TOP)
#
#        testrunlistboxframe.pack(side=TOP, fill=Tkconstants.X)
#
#        recollectDataButton = Button(self.selectionframe, text="Collect data", command=self.reCollectData)
#        recollectDataButton.pack(side=TOP)

        # make the remaining window show a tabbed panel with the different widgets
        widgets = [IpetTableWidget, IpetOutputWidget, IpetMessageWidget, IpetScatterWidget, IPETBoundHistoryWidget]
        tabbedFrame = tkinter.ttk.Notebook(self, width=screenwidth * 9 / 10, height=self.winfo_screenheight())

        for widget in widgets:
            tabbedFrame.add(widget(tabbedFrame, self), text=widget.name)
        navbar = self.createNavBar()
        navbar.pack(side=TOP, fill=tkinter.constants.X)
        self.progressstatus = IpetProgressStatus(self, width=screenwidth * 9 / 10, height=self.winfo_screenheight() / 12)
        self.progressstatus.pack(side=BOTTOM, fill=tkinter.constants.X)
        tabbedFrame.pack(side=BOTTOM, fill=BOTH, expand=1)
        self.setExperiment(_experiment)

        self.setupMenu()

        self.geometry("%dx%d+0+0" % (screenwidth, screenheight))

        if show:
            self.mainloop()

    def createNavBar(self):
        navbar = Frame(self, width=self.winfo_screenwidth(), height=16)
        buttons = (
                   ("edit-new-document-icon", "Create new _experiment", self.resetExperiment),
                   ("Load-icon", "Load Experiment from .cmp file", self.loadExperiment),
                   ("disk-icon", "Save Experiment to .cmp format", self.saveExperiment),
                   None,
                   ("document-add-icon", "Add log file(s) to current _experiment", self.addLogFiles),
                   ("coin-add-icon", "Add solution file(s) to current _experiment", self.addSolufiles),
                   None,
                   ("reload-icon", "Collect data", self.reCollectData)
                   )
        for button in buttons:
            if button:
                imagefilename, tooltip, command = button
                IpetImageButton(navbar, imagefilename, tooltip, command).pack(side=LEFT)
            else:
                Separator(navbar, orient=tkinter.constants.VERTICAL).pack(side=LEFT, fill=tkinter.constants.Y, padx=5)
        return navbar

    def listmakeBoxWithScrollbar(self, master, alist, guiupdatefunction, theheight=5):
        frame = Frame(master, height=theheight)
        scrollbar = Scrollbar(frame, orient=VERTICAL)
        listbox = Listbox(frame, bg='white', yscrollcommand=scrollbar.set)
        scrollbar.config(command=listbox.yview)
        scrollbar.pack(side=RIGHT, fill=tkinter.constants.Y)
        listbox.guiupdatefunction = guiupdatefunction
        self.updatelistbox(listbox, alist)
        listbox.pack(side=LEFT, fill=BOTH, expand=1)
        listbox.bind("<Double-Button-1>", self.handleClickEventListbox)

        return frame, listbox

    def updatelistbox(self, listbox, alist):
        '''
        updates list box, needs to be invoked when list has changed
        '''
        if alist == []:
            self.listboxlistmap[listbox] = []
            listbox.delete(0, END)
            return
        newelems = [elem for elem in alist if not elem in self.listboxlistmap.get(listbox, [])]
        if newelems == []:
            return

        listbox.delete(0, END)
        self.listboxlistmap[listbox] = alist
        for item in self.listboxlistmap[listbox]:
            listbox.insert(END, item)

    def updateGui(self):
        '''
        refresh the IpetApplication when data has changed
        '''
        for widget in self.updatableWidgets:
            widget.update()

#        self.updatelistbox(self.probnamesbox, self.getProblemList())
#        self.updatelistbox(self.testrunsbox, self.getTestrunnames())
#        if not self.selected_problem is None:
#            self.selectedProbLabel.config(text=self.selected_problem)
#        else:
#            self.selectedProbLabel.config(text="No Problem selected")
#        if not self.selected_testrun is None:
#            self.selectedTestrunLabel.config(text=self.selected_testrun.getIdentification())
#        else:
#            self.selectedTestrunLabel.config(text="No Testrun selected")


    def setSelectedProblem(self, idx):
        '''
        select a particular problem as active problem
        '''
        self.selected_problem = self.getProblemList()[idx]

    def setSelectedTestrun(self, idx):
        '''
        select testrun at specified index
        '''
        self.selected_testrun = self.getTestrunList()[idx]

    def getTestrun(self, identification):
        try:
            return [e for e in self.getTestrunList() if TestRun.getIdentification(e) == identification][0]
        except IndexError:
            print("Error : No such testrun exists: ", identification)
            return None

    def requestUpdate(self, widget):
        '''
        requests Application to add this widget to the list of updatable widgets
        '''
        if not widget in self.updatableWidgets:
            self.updatableWidgets.append(widget)

    def getAllDatakeys(self):
        '''
        get all data keys (i.e., column names) of the data of this _experiment
        '''
        try:
            return self.experiment.getDatakeys()
        except:
            return []

    def getTestrunnames(self):
        return list(map(TestRun.getIdentification, self.getTestrunList()))

    def getProblemList(self, onlyfiltered=False):
        '''
        all optionally filtered problem instances as a list

        returns the list of problem instances which may have been filtered first through the list of active
        _experiment filters

        :param onlyfiltered: set to :code:`True` for filtering problems through the set of active filters of the _experiment instance

        :return: all optionally filtered problem instances as a list
        '''
        try:
            probnamelist = self.experiment.probnamelist
            if onlyfiltered:
                filters = self.experiment.getManager('filter').getManageables(onlyactive = True)
                testruns = self.getTestrunList(onlyactive=True)
                for filterelem in filters:
                    probnamelist = filterelem.getFilteredList(probnamelist, testruns)
            return sorted(probnamelist)
        except AttributeError:
            return []

    def getTestrunList(self, onlyactive=True):
        '''
        returns the list of testruns instances as list

        :param onlyactive: set to :code:`False` to get all instead of only the currently active test runs. The testrun manager
        of the _experiment object decides if testruns are active
        '''
        try:
            return self.experiment.getManager('testrun').getManageables(onlyactive)
        except AttributeError:
            return []

    def addReader(self, reader):
        '''
        adds a reader to the _experiment object

        :param reader: an instance of :ipet:`StatisticReader`
        '''
        self.experiment.addReader(reader)

    def reCollectData(self):
        '''
        invokes data recollection and an update of the GUI
        '''
#        progress.setUpdateStep(1 / float(len(self.getTestrunList(False))))
        rm = self.experiment.getManager('reader')
        rm.addObserver(self.progressstatus)
        self.progressstatus.start()
        self.progressstatus.update("Collecting Data")
        self.experiment.collectData()
        rm.removeObserver(self.progressstatus)
        self.progressstatus.update("Finished Data Collection")
        self.progressstatus.stop()
        self.progressstatus.after(5000, self.progressstatus.update, "I am idle")
        self.updateGui()

    def showStatusMessage(self, message):
        self.progressstatus.update(message)
        self.progressstatus.after(5000, self.progressstatus.update, "I am idle")

    def handleClickEventListbox(self, event):
        try:
            idx = int(event.widget.curselection()[0])
        except IndexError:
            return
        action = event.widget.guiupdatefunction
        action(idx)
        self.updateGui()

    def setupMenu(self):
        '''
        setup menu bar entries of the IpetApplication
        '''
        self.menu = Menu(self)
        self.config(menu=self.menu)
        compMenu = Menu(self.menu)
        self.menu.add_cascade(menu = compMenu, label = "Experiment")
        compMenu.add_command(label = "New", command = self.resetExperiment)
        compMenu.add_command(label = "Save", command = self.saveExperiment)
        compMenu.add_command(label = "Load", command = self.loadExperiment)
        compMenu.add_separator()
        compMenu.add_command(label=" Add Log Files", command=self.addLogFiles)
        compMenu.add_command(label=" Add Solu Files", command=self.addSolufiles)
        compMenu.add_separator()
        compMenu.add_command(label=" Recollect Data", command=self.reCollectData)

        if self.experiment is not None:
            for managername, manager in self.experiment.getManagers().items():
                managermenu = IPETManagerMenu(self.menu, manager)
                self.menu.add_cascade(menu=managermenu, label=managername.capitalize())

        self.file_opt = options = {}
        options['defaultextension'] = '.*'
        options['filetypes'] = [('all files', '.*'), ('out-files', r'.out'), ('Experiment files', r'.cmp'), ('Solu Files', r'.solu')]

    def loadExperiment(self):
        '''
        load method to ask for _experiment instance to be loaded
        '''
        self.file_opt['defaultextension'] = r'.cmp'
        filename = tkinter.filedialog.askopenfilename(**self.file_opt)
        if filename:
            compy = self.experiment.loadFromFile(filename)
            if not compy is None:
                self.setExperiment(compy)

    def saveExperiment(self):
        '''
        saves the _experiment instance to a file
        '''
        self.file_opt['defaultextension'] = r'.cmp'
        filename = tkinter.filedialog.asksaveasfilename(**self.file_opt)
        if filename:
            self.experiment.saveToFile(filename)

    def resetExperiment(self):
        '''
        replaces the current _experiment instance by an empty _experiment.
        '''
        self.setExperiment(None)

    def setExperiment(self, _experiment):
        '''
        replaces the current _experiment instance by :code:`_experiment`

        :param _experiment: new _experiment instance to replace current _experiment
        '''
        if _experiment is not None:
            self.experiment = _experiment
        else:
            self.experiment = Experiment()
        try:
            self.selected_testrun = self.experiment.testruns[0]
            self.selected_problem = self.experiment.probnamelist[0]
        except:
            self.selected_testrun = None
            self.selected_problem = None
        print("Problem list", self.getProblemList())
        print("Testruns;", self.getTestrunnames())
        if hasattr(self, 'menu'):
            del self.menu
        self.setupMenu()
        self.updateGui()

    def addLogFiles(self):
        '''
        opens a file dialog and adds log files by creating new test runs to the current _experiment
        '''
        self.file_opt['defaultextension'] = r".out"
        filenames = tkinter.filedialog.askopenfilenames(**self.file_opt)
        print(filenames)
        if type(filenames) not in [list, tuple]:
            filenames = [filenames]
        for filename in filenames:
            if filename:
                self.experiment.addOutputFile(filename)

#        self.updatelistbox(self.testrunsbox, self.getTestrunnames())

    def addSolufiles(self):
        '''
        adds a solu file for reading in (in-)feasibility status and optimal or best known solution values
        '''
        self.file_opt['defaultextension'] = r".solu"
        filenames = tkinter.filedialog.askopenfilenames(**self.file_opt)
        print(filenames)
        if type(filenames) not in [list, tuple]:
            filenames = [filenames]
        for filename in filenames:
            if filename:
                self.experiment.addSoluFile(filename)
