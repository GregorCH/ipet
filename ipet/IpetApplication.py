'''
Created on 06.03.2013

@author: bzfhende
'''
from Tkinter import Tk, Listbox, Menu
from Comparator import Comparator
# from SCIPguiScatterWidget import SCIPguiScatterWidget
from Tkconstants import BOTH, TOP, LEFT, RIGHT, VERTICAL, END
# from SCIPguiPbHistoryWidget import SCIPguiPbHistoryWidget
from SCIPguiTableWidget import SCIPguiTableWidget
from TestRun import TestRun
import ttk
from SCIPguiOutputWidget import SCIPguiOutputWidget
import tkFileDialog
from IPETManagerMenu import IPETManagerMenu
from ttk import Frame, Label, Button, Scrollbar
import Tkconstants
from SCIPguiPbHistoryWidget import SCIPguiPbHistoryWidget
from SCIPguiScatterWidget import SCIPguiScatterWidget

class IpetApplication(Tk):
    DEFAULT_BORDERWIDTH = 15

    selected_problem = ''
    selected_testrun = None
    comparator = None

    listboxlistmap = {}
    listToActionDict = {}
    updatableWidgets = []

    TITLE = "IPET- Interactive Python Evaluation Tools"



    def __init__(self, comparator=None, show=True):
        '''
        initializes a IpetApplication. Pass an existing comparator or None to make the GUI create a new, empty
        comparator instance
        '''
        Tk.__init__(self)
        self.wm_title(IpetApplication.TITLE)
        screenwidth = self.winfo_screenwidth()
        screenheight = self.winfo_screenheight()

        self.selectionframe = Frame(self, width=screenwidth / 10, height=screenheight)
        self.selectionframe.pack(side=LEFT, fill=Tkconstants.Y)

        selectionstatusframe = Frame(self.selectionframe, width=screenwidth / 10)
        Label(selectionstatusframe, text="Current Selection:").pack(side=TOP, fill=Tkconstants.X)
        self.selectedProbLabel = Label(selectionstatusframe)
        self.selectedTestrunLabel = Label(selectionstatusframe, justify=RIGHT)

        self.selectedProbLabel.pack(side=TOP, fill=Tkconstants.X)
        self.selectedTestrunLabel.pack(side=TOP, fill=Tkconstants.X)
        selectionstatusframe.pack(side=TOP)

        problemslabel = Label(self.selectionframe, text="Problem: ")
        problemslabel.pack(side=TOP)

        probnamesselectionframe, self.probnamesbox = self.listmakeBoxWithScrollbar(self.selectionframe,
                                                                                   self.getProblemList(), self.setSelectedProblem,
                                                                                   theheight=screenheight / 2)
        testrunlistboxframe, self.testrunsbox = self.listmakeBoxWithScrollbar(self.selectionframe, self.getTestrunnames(),
                                                                              self.setSelectedTestrun, theheight=screenheight / 3)
        probnamesselectionframe.pack(side=TOP, fill=Tkconstants.X)

        testrunlabel = Label(self.selectionframe, text="Testrun: ")
        testrunlabel.pack(side=TOP)

        testrunlistboxframe.pack(side=TOP, fill=Tkconstants.X)

        recollectDataButton = Button(self.selectionframe, text="Collect data", command=self.reCollectData)
        recollectDataButton.pack(side=TOP)

        # make the remaining window show a tabbed panel with the different widgets
        widgets = [SCIPguiTableWidget, SCIPguiOutputWidget, SCIPguiScatterWidget]
        tabbedFrame = ttk.Notebook(self, width=screenwidth * 9 / 10, height=self.winfo_screenheight())

        for widget in widgets:
            tabbedFrame.add(widget(tabbedFrame, self), text=widget.name)

        tabbedFrame.pack(side=LEFT, fill=BOTH, expand=1)

        self.setComparator(comparator)

        self.setupMenu()

        self.geometry("%dx%d+0+0" % (screenwidth, screenheight))

        if show:
            self.mainloop()

    def listmakeBoxWithScrollbar(self, master, alist, guiupdatefunction, theheight=5):
        frame = Frame(master, height=theheight)
        scrollbar = Scrollbar(frame, orient=VERTICAL)
        listbox = Listbox(frame, bg='white', yscrollcommand=scrollbar.set)
        scrollbar.config(command=listbox.yview)
        scrollbar.pack(side=RIGHT, fill=Tkconstants.Y)
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

        self.updatelistbox(self.probnamesbox, self.getProblemList())
        self.updatelistbox(self.testrunsbox, self.getTestrunnames())
        if not self.selected_problem is None:
            self.selectedProbLabel.config(text=self.selected_problem)
        else:
            self.selectedProbLabel.config(text="No Problem selected")
        if not self.selected_testrun is None:
            self.selectedTestrunLabel.config(text=self.selected_testrun.getIdentification())
        else:
            self.selectedTestrunLabel.config(text="No Testrun selected")


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
            print "Error : No such testrun exists: ", identification
            return None

    def requestUpdate(self, widget):
        '''
        requests Application to add this widget to the list of updatable widgets
        '''
        if not widget in self.updatableWidgets:
            self.updatableWidgets.append(widget)

    def getAllDatakeys(self):
        '''
        get all data keys (i.e., column names) of the data of this comparator
        '''
        try:
            return self.comparator.getDatakeys()
        except:
            return []

    def getTestrunnames(self):
        return map(TestRun.getIdentification, self.getTestrunList())

    def getProblemList(self, onlyfiltered=False):
        '''
        all optionally filtered problem instances as a list

        returns the list of problem instances which may have been filtered first through the list of active
        comparator filters
        
        :param onlyfiltered: set to :code:`True` for filtering problems through the set of active filters of the comparator instance
        
        :return: all optionally filtered problem instances as a list
        '''
        try:
            probnamelist = self.comparator.probnamelist
            if onlyfiltered:
                filters = self.comparator.getManager('filter').getManageables(onlyactive=True)
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
        of the comparator object decides if testruns are active
        '''
        try:
            return self.comparator.getManager('testrun').getManageables(onlyactive)
        except AttributeError:
            return []

    def addReader(self, reader):
        '''
        adds a reader to the comparator object
        
        :param reader: an instance of :ipet:`StatisticReader`
        '''
        self.comparator.addReader(reader)

    def reCollectData(self):
        '''
        invokes data recollection and an update of the GUI
        '''
        self.comparator.collectData()
        self.updateGui()

    def handleClickEventListbox(self, event):

        idx = int(event.widget.curselection()[0])
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
        self.menu.add_cascade(menu=compMenu, label="Comparator")
        compMenu.add_command(label="New", command=self.resetComparator)
        compMenu.add_command(label="Save", command=self.saveComparator)
        compMenu.add_command(label="Load", command=self.loadComparator)
        compMenu.add_separator()
        compMenu.add_command(label=" Add Log Files", command=self.addLogFiles)
        compMenu.add_command(label=" Add Solu Files", command=self.addSolufiles)
        compMenu.add_separator()
        compMenu.add_command(label=" Recollect Data", command=self.reCollectData)

        if self.comparator is not None:
            for managername, manager in self.comparator.getManagers().iteritems():
                managermenu = IPETManagerMenu(self.menu, manager)
                self.menu.add_cascade(menu=managermenu, label=managername.capitalize())

        self.file_opt = options = {}
        options['defaultextension'] = '.*'
        options['filetypes'] = [('all files', '.*'), ('out-files', '.out'), ('Comparator files', '.cmp'), ('Solu Files', '.solu')]

    def loadComparator(self):
        '''
        load method to ask for comparator instance to be loaded
        '''
        self.file_opt['defaultextension'] = '.cmp'
        filename = tkFileDialog.askopenfilename(**self.file_opt)
        if filename:
            compy = self.comparator.loadFromFile(filename)
            if not compy is None:
                self.setComparator(compy)

    def saveComparator(self):
        '''
        saves the comparator instance to a file
        '''
        self.file_opt['defaultextension'] = '.cmp'
        filename = tkFileDialog.asksaveasfilename(**self.file_opt)
        if filename:
            self.comparator.saveToFile(filename)

    def resetComparator(self):
        '''
        replaces the current comparator instance by an empty comparator.
        '''
        self.setComparator(None)

    def setComparator(self, comparator):
        '''
        replaces the current comparator instance by :code:`comparator`

        :param comparator: new comparator instance to replace current comparator
        '''
        if comparator is not None:
            self.comparator = comparator
        else:
            self.comparator = Comparator()
        try:
            self.selected_testrun = self.comparator.testruns[0]
            self.selected_problem = self.comparator.probnamelist[0]
        except:
            self.selected_testrun = None
            self.selected_problem = None
        print "Problem list", self.getProblemList()
        print "Testruns;", self.getTestrunnames()
        if hasattr(self, 'menu'):
            del self.menu
        self.setupMenu()
        self.updateGui()

    def addLogFiles(self):
        '''
        opens a file dialog and adds log files by creating new test runs to the current comparator 
        '''
        self.file_opt['defaultextension'] = '.out'
        filenames = tkFileDialog.askopenfilenames(**self.file_opt)
        print filenames
        for filename in filenames:
            if filename:
                self.comparator.addLogFile(filename)

        self.updatelistbox(self.testrunsbox, self.getTestrunnames())

    def addSolufiles(self):
        '''
        adds a solu file for reading in (in-)feasibility status and optimal or best known solution values
        '''
        self.file_opt['defaultextension'] = '.solu'
        filenames = tkFileDialog.askopenfilenames(**self.file_opt)
        print filenames
        for filename in filenames:
            if filename:
                self.comparator.addSoluFile(filename)
