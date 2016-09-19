'''
Created on 26.03.2015

@author: bzfhende
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
        