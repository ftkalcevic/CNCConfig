#!/usr/bin/env python
# vim: sts=4 sw=4 et

import os,sys
from gladevcp.persistence import IniFile,widget_defaults,set_debug,select_widgets
import hal
import hal_glib
import gtk
import glib
import gobject
import linuxcnc
import math
from ImageEx import ImageEx
from Calc import CalculatorDialog
from touchy import preferences
import pango

gwiz_path = "/home/frankt/linuxcnc/9x20lathe/gwiz"
wizard_path = gwiz_path + "/wizards"
wizards = []
digits = 3
pxCalc = None
calcSize = 32
dialog = None

debug = False

settings = None


gtk.rc_parse('/home/frankt/.themes/HighContrast/gtk-2.0/gtkrc')


class Settings:
    def __init__(self):
        prefs = preferences.preferences()

        self.control_font_name = prefs.getpref('control_font', 'Sans 18', str)
        self.dro_font_name = prefs.getpref('dro_font', 'Courier 10 Pitch Bold 16', str)
        self.error_font_name = prefs.getpref('error_font', 'Sans Bold 10', str)
        self.listing_font_name = prefs.getpref('listing_font', 'Sans 10', str)
        self.theme_name = prefs.getpref('gtk_theme', 'Follow System Theme', str)

        self.control_font = pango.FontDescription(self.control_font_name)

class HandlerClass:
    '''
    class with gladevcp callback handlers
    '''
    
    def __init__(self, halcomp,builder,useropts):

        self.halcomp = halcomp
        self.builder = builder
        self.prelude = gwiz_path + os.sep + "prelude.ngc"
        #global pxCalc
        #pxCalc = gtk.gdk.pixbuf_new_from_file_at_size(gwiz_path+os.sep+"img/calc.png",calcSize,calcSize)

        self.load_preferences()

        self.load_wizards()
        self.build_screens()



    def load_wizards(self):
        # each wizard is in its own subdirectory
        try:
            dir = os.listdir( wizard_path )
            dir.sort()

            for d in dir[:]:
                full_path = wizard_path + os.sep + d
                if debug: print full_path
                if os.path.isdir(full_path):

                    wizard = Wizard.load_wizard( full_path )
                    if wizard:
                        wizards.append(wizard)
                        if debug: print wizard.desc_name

        except IOError:
            return

               
    def build_screens(self):
        # create the gtk screens
        # the first page of the notebook is a place holder - remove it
        nb = self.builder.get_object("notebook1")
        nb.remove_page(0)

        for w in wizards:

            # build the panel the attach it to the notebook

            # vbox with main panel then button bar
            vbox = gtk.VBox()

            hbox = gtk.HBox()
            vbox.pack_start(hbox)

            # image
            img = ImageEx()
            img.set_from_file( w.image_path )
            hbox.pack_start(img)

            # parameters
            vbox_params = gtk.VBox()
            hbox.pack_start(vbox_params)

            table = gtk.Table( rows = len(w.config), columns = 3 )

            row = 0
            for c in w.config:
                
                c.createConfig(table, row)
                row = row + 1

            vbox_params.pack_start(table)
            align = gtk.Alignment()
            vbox_params.pack_start(align)

            btnbar = gtk.HButtonBox()
            btnbar.modify_font(settings.control_font)
            btn1 = gtk.Button("Run")
            btn1.set_size_request(150, 100)
            btn1.modify_font(settings.control_font)
            btn1.connect("button-press-event",self.on_run, w)
            btnbar.pack_start(btn1)
            
            vbox.pack_start(btnbar,expand=True, fill=True)

            lbl = gtk.Label(w.desc_name)
            lbl.modify_font(settings.control_font)
            nb.append_page( vbox, lbl ) 

            mainwin = self.builder.get_object("window1")
            mainwin.show_all()


    def load_preferences(self):
        global settings
        settings = Settings()

        gtksettings = gtk.settings_get_default()
        gtksettings.set_string_property("gtk-theme-name", settings.theme_name, "")
 

    # run as program
    def on_run_program(self, btn, event, w):
        if debug: print "on_run"

        # prelude
        with open(self.prelude,'r') as f:
            cmd = f.read() + "\n"

        # include the subroutine
        with open(w.subroutine_path,'r') as f:
            cmd = cmd + f.read() + "\n"

        # build the subroutine call
        cmd = cmd + "\n" + w.desc_oword + " call "
        for c in w.config:
            cmd = cmd + " [%s]" % c.get_value()
        
        cmd = cmd + "\nM2\n"
        if debug: print cmd

        # save the file to /tmp then open it
        filename = os.sep+"tmp"+os.sep+w.desc_name+".ngc"
        open(filename,'w').write(cmd)

        linuxcnc.command().mode(linuxcnc.MODE_AUTO)
        linuxcnc.command().program_open(filename)

        ensure_mode(linuxcnc.MODE_AUTO)
        linuxcnc.command().auto(linuxcnc.AUTO_RUN, 0)


    # run as mdi
    def on_run(self, btn, event, w):
        if debug: print "on_run"

        # build the subroutine call
        cmd = w.desc_oword + " call "
        for c in w.config:
            cmd = cmd + " [%s]" % c.get_value()
        
        if debug: print cmd

        ensure_mode(linuxcnc.MODE_MDI)
        linuxcnc.command().mdi(cmd)

def find_widget(w,child_name):

    for c in w.get_children():
        if c.get_name() == child_name:
            return c
        else:
            op = getattr(c, "get_children", None)
            if callable(op):
                return find_widget(c,child_name)
    return None

 

def running(s, do_poll=True):
    if do_poll: s.poll()
    return s.task_mode == linuxcnc.MODE_AUTO and s.interp_state != linuxcnc.INTERP_IDLE


def ensure_mode(*modes):
    stat = linuxcnc.stat()
    stat.poll()
    if not modes: return False
    if stat.task_mode in modes: return True
    if running(stat, do_poll=False): return False
    linuxcnc.command().mode(modes[0])
    linuxcnc.command().wait_complete()
    return True


def get_handlers(halcomp,builder,useropts):
    return [HandlerClass(halcomp,builder,useropts)]

class FloatConfig:
    def __init__(self, type, axis, name, description, defaultValue):
        self.type = type
        self.axis = axis
        self.name = name
        self.description = description
        self.defaultValue = float(defaultValue)

    def createConfig(self, table, row):

        lbl = gtk.Label(self.name)
        lbl.set_alignment(1,0.5)
        lbl.modify_font(settings.control_font)
        table.attach( lbl, 1, 2, row, row+1)

        hbox = gtk.HBox()
        self.spin = gtk.SpinButton(digits=digits)
        self.spin.set_range(-100000, 100000)
        self.spin.set_value( float(self.defaultValue) )
        self.spin.set_increments(0.1, 10)
        self.spin.modify_font(settings.control_font)
        self.spin.connect("button-press-event",self.on_calc_click,self.name,self.spin)

        hbox.pack_start(self.spin)

        if self.axis != '':
            btn = gtk.Button(self.axis + " =>" )
            btn.connect("button-press-event", self.on_press_copy_axis, 
                        self.axis, self.spin)
            btn.get_child().modify_font(settings.control_font)
            table.attach( btn, 0, 1, row, row+1)

        #btn = gtk.Button()
        #imgCalc = gtk.Image()
        #global pxCalc
        #imgCalc.set_from_pixbuf(pxCalc)
        #btn.set_image(imgCalc)
        #btn.connect("button-press-event",self.on_calc_click,self.name,self.spin)
        #hbox.pack_start(btn, expand=False, fill=False)
        table.attach( hbox, 2, 3, row, row+1)

    def on_press_copy_axis(self, btn, event, axis, spinbox):

        status = linuxcnc.stat()
        status.poll()
        pos = status.position

        n = 0
        a = axis.lower()
        if a == 'x':
            n = pos[0]
        if a == 'y':
            n = pos[1]
        if a == 'z':
            n = pos[2]

        spinbox.set_value(n)


    def on_calc_click(self,btn,ev,axis,spin):
        dialog = CalculatorDialog()
        if dialog.run(btn.get_parent(), axis, str(spin.get_value()) ):
            spin.set_value( float(dialog.get_value()) )

    def get_value(self):
        return self.spin.get_value()


class UintConfig:
    def __init__(self, type, name, description, defaultValue):
        self.type = type
        self.name = name
        self.description = description
        self.defaultValue = int(defaultValue)

    def createConfig(self, table, row):

        lbl = gtk.Label(self.name)
        lbl.set_alignment(1,0.5)
        lbl.modify_font(settings.control_font)
        table.attach( lbl, 1, 2, row, row+1)

        hbox = gtk.HBox()
        self.spin = gtk.SpinButton(digits=0)
        self.spin.set_range(0, 100000)
        self.spin.set_increments(1, 10)
        self.spin.set_value( float(self.defaultValue) )
        self.spin.modify_font(settings.control_font)
        hbox.pack_start(self.spin)

        #btn = gtk.Button()
        #imgCalc = gtk.Image()
        #global pxCalc
        #imgCalc.set_from_pixbuf(pxCalc)
        #btn.set_image(imgCalc)
        #btn.connect("button-press-event",self.on_calc_click,self.name,self.spin)
        #hbox.pack_start(btn, expand=False, fill=False)
        table.attach( hbox, 2, 3, row, row+1)

    def on_calc_click(self,btn,ev,axis,spin):
        dialog = CalculatorDialog()
        if dialog.run(btn.get_parent(), axis, str(spin.get_value()) ):
            spin.set_value( int(dialog.get_value()) )

    def get_value(self):
        return int(self.spin.get_value())


class ListConfig:
    def __init__(self, type, name, description, *listData):
        self.type = type
        self.name = name
        self.description = description
        if debug: print listData
        if len(listData) % 2 == 1:
            self.defaultItem = listData[-1]
            listData = listData[:-1]
            if debug: print "using last item as default - %s" % self.defaultItem
        else:
            self.defaultItem = listData[0]
        self.data = [listData[i:i + 2] for i in xrange(0, len(listData), 2)]
       
        if debug: print self.data

    def createConfig(self, table, row):

        lbl = gtk.Label(self.name)
        lbl.set_alignment(1,0.5)
        lbl.modify_font(settings.control_font)
        table.attach( lbl, 1, 2, row, row+1)

        list = gtk.ListStore(gobject.TYPE_STRING,gobject.TYPE_STRING)
        for d in self.data:
            list.append(d)
        self.combo = gtk.ComboBox(list)
        self.combo.modify_font(settings.control_font)
        cell = gtk.CellRendererText()
        self.combo.pack_start(cell, True)
        self.combo.add_attribute(cell, 'text', 1)
        iter = list.get_iter_first()
        while ( iter != None ):
            if list.get_value(iter,0) == self.defaultItem:
                self.combo.set_active_iter( iter )
                break
            iter = list.iter_next(iter)
        
        table.attach( self.combo, 2, 3, row, row+1)

    def get_value(self):
        return self.combo.get_model().get_value(self.combo.get_active_iter(),0)

class Wizard:
    '''
    '''
    
    def __init__(self,path, config, desc, image, subroutine_path):
        self.path = path
        self.image_path = image
        self.config = Wizard.MakeConfig(config)
        desc_items = desc[0].split("|")
        self.desc_oword = desc_items[0]
        self.desc_name = desc_items[1]
        self.subroutine_path = subroutine_path

    @staticmethod
    def MakeConfig(config_list):
        config = []
        for c in config_list:
            entries = c.split("|")
            if entries[0] == 'S':
                config.append( FloatConfig( *entries ) )
            elif entries[0] == 'U':
                config.append( UintConfig( *entries ) )
            elif entries[0] == 'L':
                config.append( ListConfig( *entries ) )
            else:
                print "Unknown parameter type %s" % entries[0]
            
        return config

    @staticmethod
    def read_file( path ):
        with open(path,'r') as f:
            lines = f.readlines()
        contents = []
        for l in lines:
            line = l.strip()
            if len(line) > 0:
                contents.append(line)
        return contents

    @staticmethod
    def load_wizard(path):
        if debug: print path
        if not os.path.isfile(path+os.sep+"config"):
            if debug: print "Missing %s/config" % path
            return None
        if not os.path.isfile(path+os.sep+"desc"):
            if debug: print "Missing %s/desc" % path
            return None
        #if not os.path.isfile(path+os.sep+"subroutine.ngc"):
            #if debug: print "Missing %s/subroutine.ngc" % path
            #return None
        if ( not os.path.isfile(path+os.sep+"screen.png") and
             not os.path.isfile(path+os.sep+"screen.svg")):
            if debug: print "Missing %s/screen.[png|svg]" % path
            return None

        config = Wizard.read_file(path+os.sep+"config")
        desc = Wizard.read_file(path+os.sep+"desc")
        subroutine = None #path+os.sep+"subroutine.ngc"
        if os.path.isfile(path+os.sep+"screen.png"):
            image = path+os.sep+"screen.png"
        elif os.path.isfile(path+os.sep+"screen.svg"):
            image = path+os.sep+"screen.svg"
        else:
            image = None

        # config, desc, screen.png, ngc, version
        return Wizard(path, config, desc, image, subroutine)


