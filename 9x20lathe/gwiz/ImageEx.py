#!/usr/bin/env python
# vim: sts=4 sw=4 et

import os,sys
from gladevcp.persistence import IniFile,widget_defaults,set_debug,select_widgets
import gtk
import glib
import gobject
import math


# ImageEx - based on https://stackoverflow.com/questions/5067310/pygtk-how-do-i-make-an-image-automatically-scale-to-fit-its-parent-widget

class ImageEx(gtk.Image):
    pixbuf = None
    __gtype_name__ = 'ImageEx'

    def __init__(self, *args, **kwargs):
        super(ImageEx, self).__init__(*args, **kwargs)
        self.connect("size-allocate", self.on_size_allocate)
        self.lastWidth = -1
        self.lastHeight = -1

    def set_from_file(self, path):
        self.path = path
        pixbuf = gtk.gdk.pixbuf_new_from_file(self.path)
        self.set_from_pixbuf(pixbuf)

    def on_size_allocate(self, obj, rect):
        # skip if no pixbuf set
        if self.path is None:
            return

        pixbuf = self.get_pixbuf()

        # calculate proportions for image widget and for image
        k_pixbuf = float(pixbuf.props.height) / pixbuf.props.width
        k_rect = float(rect.height-2) / (rect.width-2)

        # recalculate new height and width
        if k_pixbuf < k_rect:
            newWidth = rect.width-2
            newHeight = int(newWidth * k_pixbuf)
        else:
            newHeight = rect.height - 2
            newWidth = int(newHeight / k_pixbuf)


        if newWidth == 0 or newHeight == 0:
            return

        if newWidth == pixbuf.props.width and newHeight == pixbuf.props.height:
            return
        
        if rect.width == self.lastWidth and rect.height == self.lastHeight:
            return

        self.lastWidth = rect.width
        self.lastHeight = rect.height

        # get internal image pixbuf and check that it not yet have new sizes
        # that's allow us to avoid endless size_allocate cycle
        pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(self.path,newWidth,newHeight)
        self.set_from_pixbuf(pixbuf)

