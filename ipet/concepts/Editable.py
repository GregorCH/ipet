"""
Created on 26.12.2013

@author: bzfhende
"""
import collections
class Editable:
    """
    an editable object defines a set of attributes to be editable after construction
    """
    editabletypes = [float, str, int, bool]
    def getEditableAttributes(self):
        """
        return a list of attributes which may be edited
        """
        return [elem for elem in dir(self) if not elem.startswith('__') and not isinstance(getattr(self,elem), collections.Callable) \
                and type(getattr(self, elem)) in self.editabletypes]

    def editAttribute(self, attributename, newvalue):
        """
        overwrite the existing attribute value of given name with new value
        raises an AttributeError if no such attribute exists
        """
        if not hasattr(self, attributename):
            raise AttributeError("Editable has no attribute named %s" % (attributename))

        try:
            # call the set method if available
            setter_method = getattr(self, 'set_' + attributename)
            setter_method(newvalue)
        except AttributeError:
            setattr(self, attributename, newvalue)

    def checkAttributes(self):
        """
        check the current attributes for inconsistensies and raise an EditableAttributeError in this case
        """
        return True


    def attributesToDict(self):
        return {elem:getattr(self, elem) for elem in self.getEditableAttributes()}
    
    def attributesToStringDict(self):
        return {elem:str(getattr(self, elem)) for elem in self.getEditableAttributes()}
    
    def getRequiredOptionsByAttribute(self, attr):
        return None
    
    def getAttrDocumentation(self, attr):
        for line in self.__init__.__doc__.splitlines():
            if line.strip().startswith(attr):
                return line[line.index(":") + 1:]
        return None
    
    def equals(self, other):
        """
        returns True if other is of the same class and has the same attributes as self
        """
        if other is None:
            return False
        elif other.__class__ != self.__class__:
            return False
        
        return self.attributesToDict() == other.attributesToDict()
        
class EditableAttributeError(Exception):
    """
    class to represent an error if this editable were to be used now for an evaluation
    """
    DEFAULT_MESSAGE = "Attribute {0} is set incorrectly"
    def __init__(self, attr, message = None):
        """
        constructs an EditableAttributeError that should be thrown if checkAttributes() detects an inconsistency

        Parameters
        ----------
        attr : the name of the attribute that failed
        message : (optional) message to understand the reason of this error, otherwise, a template {0} is used
        """.format(EditableAttributeError.DEFAULT_MESSAGE)

        if type(attr) is not str:
            raise TypeError("Passed argument 'attr' must be of type 'str'")

        self.attr = attr
        
        if message is None:
            self.message = self.DEFAULT_MESSAGE.format(attr)
        else:
            self.message = message

    def getMessage(self):
        """
        returns the corresponding message of this error
        """
        return self.message

    def getAttribute(self):
        """
        returns the name of the attribute that caused this error
        """
        return self.attr

