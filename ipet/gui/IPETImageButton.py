'''
Created on 14.08.2014

@author: Customer
'''
from ttk import Button
try:
    from ImageTk import PhotoImage
except:
    import PIL
    from PIL.ImageTk import PhotoImage
from IPETToolTip import createToolTip
import os

class IpetImageButton(Button):


    def __init__(self, master, imagenoextension, tooltip, command, **kw):
        if not hasattr(self, 'iconlib'):
            IpetImageButton.createImageLib()

        im = self.iconlib.get(imagenoextension)
        Button.__init__(self, master, image=im, command=command, **kw)
        self.im = im
        createToolTip(self, tooltip)

    @staticmethod
    def createImageLib():
        iconpath = os.path.join(os.path.dirname(__file__), os.path.pardir, os.path.pardir, "images")
        IpetImageButton.iconlib = il = {}
        print iconpath
        for image in os.listdir(iconpath):
            im = PhotoImage(file=iconpath + os.sep + image)
            il[os.path.splitext(image)[0]] = im

