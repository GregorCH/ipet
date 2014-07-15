'''
Created on 29.12.2013

@author: bzfhende
'''
class Observable:
   '''
   observables represent the client in the Observer pattern. They have the possibility to nofify their
   observers and invoke an update every time they change their state
   '''

   def addObserver(self, newobserver):
      '''
      add an observer to the list of observers
      '''
      try:
         getattr(self, 'setofobservers')
      except AttributeError:
         setattr(self, 'setofobservers', set())

      self.setofobservers.add(newobserver)

   def removeObserver(self, observer):
      '''
      removes an observer from the list of observers
      '''
      self.setofobservers.remove(observer)

   def notify(self):
      '''
      notify all observers about changes in the state
      '''
      try:
         for observer in self.setofobservers:
            observer.update(self)
      except AttributeError:
         setattr(self, 'setofobservers', set())
