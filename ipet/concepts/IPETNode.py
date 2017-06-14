"""
The MIT License (MIT)

Copyright (c) 2016 Zuse Institute Berlin, www.zib.de

Permissions are granted as stated in the license file you have obtained
with this software. If you find the library useful for your purpose,
please refer to README.md for how to cite IPET.

@author: Gregor Hendel
"""
from ipet.concepts.Editable import Editable, EditableAttributeError
import logging
class IpetNode(Editable):
    """
    A Node is an interface to an XML-like ancestor-structure
    """
    active = True
    _attributes2options = {"active":[True, False]}
    deprecatedattrdir = {}
    
    def __init__(self, active = True, **kw):
        """
        constructs a new IpetNode

        Parameters
        ----------
        active : True or "True" if this element should be active, False otherwise
        """
        self.set_active(active)

        for d, message in self.deprecatedattrdir.items():
            if d in kw:
                logging.warn("Warning : The attribute '{0}' is deprecated and will be ignored; {1}. ".format(d, message))

    def addChild(self, child):
        """
        append a child to this node's children
        """
        pass
    
    def getChildren(self):
        """
        return a list of all children of this node
        """
        return None
    
    def acceptsAsChild(self, child):
        """
        returns whether this node accepts node 'child' as child
        """
        return False
    
    def removeChild(self, child):
        """
        remove the child from this node's children.
        """
        pass
    
    def isActive(self):
        """
        returns True if this node is currently active, False otherwise
        """
        return self.active
    
    def set_active(self, active):
        self.active = True if active in [True, "True"] else False

    def getEditableAttributes(self):
        """
        returns all editable attributes
        """
        return ["active"]

    def getRequiredOptionsByAttribute(self, attr):
        return self._attributes2options.get(attr)

    @staticmethod
    def getNodeTag():
        return "Node"

class IpetNodeAttributeError(EditableAttributeError):
    """
    subclass to allow for richer EditableAttributeErrors
    """

    def __init__(self, *args):
        """
        constructs an IpetNodeAttributeError
        """
        super(IpetNodeAttributeError, self).__init__(*args)


        
