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
from gwiz.ImageEx import ImageEx
from gwiz.Calc import CalculatorDialog
from touchy import preferences


debug = False


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


class HandlerClass:
    '''
    class with gladevcp callback handlers
    '''
    
    def __init__(self, halcomp,builder,useropts):

        self.halcomp = halcomp
        self.builder = builder

        img = ImageEx()
        img.set_from_file( "latheFace.svg" )
        vbox = builder.get_object("vboxImage")
        vbox.pack_start(img)
        vbox.reorder_child(img,0)
        vbox.show_all()

        self.load_defaults()
        self.load_settings()

    def load_settings(self):
        prefs = preferences.preferences()
        self.control_font_name = prefs.getpref('control_font', 'Sans 18', str)
        self.dro_font_name = prefs.getpref('dro_font', 'Courier 10 Pitch Bold 16', str)
        self.error_font_name = prefs.getpref('error_font', 'Sans Bold 10', str)
        self.listing_font_name = prefs.getpref('listing_font', 'Sans 10', str)
        self.theme_name = prefs.getpref('gtk_theme', 'Follow System Theme', str)
 
        settings = gtk.settings_get_default()
        settings.set_string_property("gtk-theme-name", self.theme_name, "")
        

    def load_defaults(self):
        params = (  ( "spinXStart", 15 ),
                    ( "spinXEnd", -1 ),
                    ( "spinXFeed", 0.1 ),
                    ( "spinZStep", 0.25 ),
                    ( "spinSFM", 300 ) )
        for widget_name,value in params:
            widget = self.builder.get_object(widget_name)
            widget.set_value( value )


    def on_btnTouchOffZ_clicked(self,w):
        status = linuxcnc.stat()
        status.poll()
        pos = status.position

        dialog = CalculatorDialog()
        if dialog.run(w.get_parent(), "Touch off Z", str(pos[2]) ):
            new_z = float(dialog.get_value())
            cmd = "G10 L20 P0 Z%s" % new_z
            ensure_mode(linuxcnc.MODE_MDI)
            linuxcnc.command().mdi(cmd)


    def on_btnRun_clicked(self,w):
        cmd = "O<face> call [%s] [%s] [%s] [%s] [%s]" % ( 
                    self.builder.get_object("spinXStart").get_value(),
                    self.builder.get_object("spinXEnd").get_value(),
                    self.builder.get_object("spinXFeed").get_value(),
                    self.builder.get_object("spinZStep").get_value(),
                    self.builder.get_object("spinSFM").get_value() )
        print cmd
        ensure_mode(linuxcnc.MODE_MDI)
        linuxcnc.command().mdi(cmd)

    def DoCalculator(self, spin):
        dialog = CalculatorDialog()
        if dialog.run(spin.get_parent(), "", str(spin.get_value()) ):
            spin.set_value( float(dialog.get_value()) )

    def on_spinXStart_button_press_event(self,w,d):
        self.DoCalculator(w)

    def on_spinXFeed_button_press_event(self,w,d):
        self.DoCalculator(w)

    def on_spinSFM_button_press_event(self,w,d):
        self.DoCalculator(w)

    def on_spinZStep_button_press_event(self,w,d):
        self.DoCalculator(w)

    def on_spinXEnd_button_press_event(self,w,d):
        self.DoCalculator(w)




def get_handlers(halcomp,builder,useropts):
    return [HandlerClass(halcomp,builder,useropts)]

