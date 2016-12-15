'''
The MIT License (MIT)

Copyright (c) 2016 Zuse Institute Berlin, www.zib.de

Permissions are granted as stated in the license file you have obtained
with this software. If you find the library useful for your purpose,
please refer to README.md for how to cite IPET.

@author: Gregor Hendel
'''
from .Observer import Observable
from .IPETMessageStream import Message
class Manager(Observable):
    '''
    manages all manageables of a certain type of which many objects might exist and need to be listed / browsed frequently
    '''

    def __init__(self, listofmanageables=[], activate=False):
        '''
        constructs a new Manager
        
        constructs a new Manager by creating an empty dictionary. Fills the dictionary with a list
        of manageables, if non-empty. All elements can be optionally activated.
        '''
        self.stringrepresentations = {}
        self.activeset = set()
        for manageable in listofmanageables:
            self.addManageable(manageable)
            if activate:
                self.activate(manageable)

    def addManageable(self, manageable):
        '''
        add manageable to dictionary - ensures that only one manageable with that string representation is stored
        '''
        stringrepresentation = self.getStringRepresentation(manageable)
        self.stringrepresentations[stringrepresentation] = manageable

    def getStringRepresentation(self, manageable):
        '''
        return an manageable's string representation
        '''
        if type(manageable) is str:
            return manageable
        else:
            try:
                return manageable.getName()
            except AttributeError:
                return str(manageable)


    def getManageable(self, stringrepresentation):
        '''
        returns the manageable belonging to a string representation, or None, if no such manageable is available
        '''
        return self.stringrepresentations.get(stringrepresentation, None)

    def deleteManageable(self, manageable):
        '''
        delete an manageable from the manager
        '''
        for key, val in list(self.stringrepresentations.items()):
            if val == manageable:
                oldstringrepresentation = key
                break
        del self.stringrepresentations[oldstringrepresentation]
        self.deactivate([manageable])

    def reinsertManageable(self, manageable):
        '''
        reinserts a manageable after a possible name change that was not 
        
        reinserts a manageable after its name has changed
        '''
        active = self.isActive(manageable)
        self.deleteManageable(manageable)
        self.addManageable(manageable)
        if active:
            self.activate([manageable])


    def editObjectAttribute(self, manageable, attributename, newattribute):
        '''
        edit an objects attribute and ensure that a changed object representation is directly
        processed
        '''
        oldname = self.getStringRepresentation(manageable)
        manageable.editAttribute(attributename, newattribute)
        newname = self.getStringRepresentation(manageable)
        print(newname, newattribute)
        if oldname != newname:
            self.chgManageableName(manageable, oldname, newname)
        self.notify(Message("Changed attribute %s of %s to %s" % (attributename, newname, newattribute), Message.MESSAGETYPE_INFO))

    def chgManageableName(self, manageable, oldname, newname):
        '''
        changes a manageables name, if possible
        '''
        if newname != oldname:
            if self.getManageable(newname) is not None:
                raise KeyError("An element of name %s is already listed" % (newname))
            del self.stringrepresentations[oldname]
            self.stringrepresentations[newname] = manageable


    def getManageables(self, onlyactive=False):
        '''
        returns all (or only active) manageables
        '''
        if onlyactive:
            return list(self.activeset)
        else:
            return list(self.stringrepresentations.values())

    def getAllRepresentations(self, onlyactive=False):
        '''
        returns a list of all string representations
        '''
        if not onlyactive:
            return list(self.stringrepresentations.keys())
        else:
            return [self.getStringRepresentation(manageable) for manageable in self.activeset]

    def activate(self, manageables):
        '''
        adds a manageable to the active set
        '''
        for manageable in manageables:
            if self.getStringRepresentation(manageable) not in self.stringrepresentations:
                raise KeyError("%s is not managed by this manager - call addManageable() first" % (self.getStringRepresentation(manageable)))
            if not manageable in self.activeset:
                self.activeset.add(manageable)

        if manageables != []:
            self.notify(Message("Activated %s" % ", ".join(map(self.getStringRepresentation, manageables)), messagetype=Message.MESSAGETYPE_INFO))

    def addAndActivate(self, manageable):
        '''
        adds a manageable to the manager and activates it
        '''
        self.addManageable(manageable)
        self.activate([manageable])

    def getActiveSet(self):
        '''
        returns the set of active objects managed by the manager
        '''
        return self.activeset

    def deactivate(self, manageables):
        '''
        removes a list of manageables from the active set of managed objects - elements stays present and can be activated again
        '''
        for manageable in manageables:
            try:
                self.activeset.remove(manageable)
            except KeyError:
                pass
        self.notify(Message("Deactivated %s" % ", ".join(map(self.getStringRepresentation, manageables)), messagetype=Message.MESSAGETYPE_INFO))


    def countManageables(self, onlyactive):
        '''
        count the number of (optionally only the active) manageables
        '''
        if onlyactive:
            return len(self.activeset)
        else:
            return len(list(self.stringrepresentations.keys()))

    def isActive(self, manageable):
        '''
        is the manageable part of the active set of this manager
        '''
        return manageable in self.activeset
