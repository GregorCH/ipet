'''
The MIT License (MIT)

Copyright (c) 2016 Zuse Institute Berlin, www.zib.de

Permissions are granted as stated in the license file you have obtained
with this software. If you find the library useful for your purpose,
please refer to README.md for how to cite IPET.

@author: Gregor Hendel
'''

class IpetNode:
    '''
    A Node is an interface to an XML-like ancestor-structure
    '''

    def addChild(self, child):
        '''
        append a child to this node's children
        '''
        pass
    
    def getChildren(self):
        '''
        return a list of all children of this node
        '''
        return None
    
    def acceptsAsChild(self, child):
        '''
        returns whether this node accepts node 'child' as child
        '''
        return False
    
    def removeChild(self, child):
        '''
        remove the child from this node's children.
        '''
        pass
    
    @staticmethod
    def getNodeTag():
        return "Node"
        