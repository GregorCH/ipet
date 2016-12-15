'''
The MIT License (MIT)

Copyright (c) 2016 Zuse Institute Berlin, www.zib.de

Permissions are granted as stated in the license file you have obtained
with this software. If you find the library useful for your purpose,
please refer to README.md for how to cite IPET.

@author: Gregor Hendel
'''
class Observable:
    '''
    observables represent the client in the Observer pattern. They have the possibility to nofify their
    observers and invoke an update every time they change their state
    '''
    observermap = {}  # : map which has observables as keys, and observers as values
    def addObserver(self, newobserver):
        '''
        add an observer to the list of observers
        '''
        theset = Observable.observermap.setdefault(self, set())

        theset.add(newobserver)

    def removeObserver(self, observer):
        '''
        removes an observer from the list of observers
        '''
        theset = Observable.observermap.get(self)
        if theset is not None:
            theset.remove(observer)

    def notify(self, *args):
        '''
        notify all observers about changes in the state
        '''
        theset = Observable.observermap.setdefault(self, set())
        for observer in theset:
            observer.update(*args)
