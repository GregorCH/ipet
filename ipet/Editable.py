'''
Created on 26.12.2013

@author: bzfhende
'''
class Editable:
    '''
    an editable object defines a set of attributes to be editable after construction
    '''
    editabletypes = [float, str, int, bool]
    def getEditableAttributes(self):
        '''
        return a list of attributes which may be edited
        '''
        return [elem for elem in dir(self) if not elem.startswith('__') and not callable(getattr(self,elem)) \
                and type(getattr(self, elem)) in self.editabletypes]

    def editAttribute(self, attributename, newvalue):
        '''
        overwrite the existing attribute value of given name with new value
        raises an AttributeError if no such attribute exists
        '''
        if not hasattr(self, attributename):
            raise AttributeError("Editable has no attribute named %s" % (attributename))

        try:
            # call the set method if available
            setter_method = getattr(self, 'set_' + attributename)
            setter_method(newvalue)
        except AttributeError:
            setattr(self, attributename, newvalue)
