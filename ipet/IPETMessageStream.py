'''
Created on 08.08.2014

@author: Customer
'''
import sys

class Message:
    '''
    class for representing state messages to the user
    
    a Message contains a string message and a type
    '''
    MESSAGETYPE_WARNING = 1
    MESSAGETYPE_ERROR = 2
    MESSAGETYPE_INFO = 3
    messagetypes = {MESSAGETYPE_WARNING, MESSAGETYPE_INFO, MESSAGETYPE_ERROR}

    def __init__(self, stringmessage, messagetype):
        '''
        '''
        self.stringmessage = stringmessage
        if messagetype not in Message.messagetypes:
            raise ValueError(Message("Error: wrong messagetype %s, must be in %s" % (repr(messagetype), str(Message.messagetypes)), Message.MESSAGETYPE_ERROR))
        self.messagetype = messagetype

    def __str__(self):
        return self.stringmessage
    def __unicode__(self):
        return unicode(self.stringmessage)
    def __repr__(self):
        return self.stringmessage

class ErrorMessage(Message):
    '''
    subclass of message to represent error messages
    '''
    def __init__(self, stringmessage):
        '''
        constructs an error message
        '''
        Message.__init__(self, stringmessage, Message.MESSAGETYPE_ERROR)

class InfoMessage(Message):
    '''
    subclass of message to represent info messages
    '''
    def __init__(self, stringmessage):
        '''
        constructs an info message
        '''
        Message.__init__(self, stringmessage, Message.MESSAGETYPE_INFO)

class WarningMessage(Message):
    '''
    subclass of message to represent warning messages
    
    '''
    def __init__(self, stringmessage):
        '''
        constructs a warning message
        '''
        Message.__init__(self, stringmessage, Message.MESSAGETYPE_WARNING)

streams = {Message.MESSAGETYPE_ERROR:sys.stderr,
           Message.MESSAGETYPE_INFO:sys.stdout,
           Message.MESSAGETYPE_WARNING:sys.stderr}

def processMessage(message):
    '''
    processes a message by passing it to the correct message handler for the messagetype of the message
    
    :param message:Message object
    '''
    stream = streams.get(message.messagetype, sys.stdout)
    stream.write(str(message))

def setStream(messagetype, stream):
    if not hasattr(stream, 'write') or not callable(getattr(stream, 'write')):
        raise ValueError(ErrorMessage("stream object has no 'write'-method"))
    streams[messagetype] = stream


if __name__ == '__main__':
    # create some messages and print them
    message1 = Message("Hello Info\n", Message.MESSAGETYPE_INFO)
    message2 = ErrorMessage("Hello Error\n")
    map(processMessage, [message1, message2])

    setStream(Message.MESSAGETYPE_ERROR, sys.stdout)
    setStream(Message.MESSAGETYPE_INFO, sys.stderr)

    map(processMessage, [message1, message2])

    print message2

