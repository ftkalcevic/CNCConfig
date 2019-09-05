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

gtk.rc_parse('/home/frankt/linuxcnc/9x20lathe/touchy/theme/HighContrastFT/gtk-2.0/gtkrc')

class SpindleState:
    Stopped = 0
    Forward = 1
    Reverse = 2

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

        self.btnSpindleReverse = self.builder.get_object("btnSpindleReverse")
        self.btnSpindleForward = self.builder.get_object("btnSpindleForward")
        self.btnSpindleStop = self.builder.get_object("btnSpindleStop")
        self.vscaleSpindleSpeed = self.builder.get_object("vscaleSpindleSpeed")

 
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
                    ( "spinSFM", 100 ) )
        for widget_name,value in params:
            widget = self.builder.get_object(widget_name)
            widget.set_value( value )

    def DoTouchoff( self,  widget, axis, index ):
        status = linuxcnc.stat()
        status.poll()

        pos = status.position[index] - status.g5x_offset[index] - status.tool_offset[index]

        if index == 0:
            # radius/diameter
            if not 80 in status.gcodes:
                pos = pos*2

        dialog = CalculatorDialog()
        if dialog.run(widget.get_parent(), "Touch off " + axis, str(pos) ):
            new = float(dialog.get_value())
            cmd = "G10 L20 P0 %s%s" % (axis,new)
            ensure_mode(linuxcnc.MODE_MDI)
            linuxcnc.command().mdi(cmd)


    def on_btnTouchOffX_pressed(self,w):
        self.DoTouchoff( w, "X", 0 )

    def on_btnTouchOffZ_pressed(self,w):
        self.DoTouchoff( w, "Z", 2 )


    def on_btnRun_pressed(self,w):
        cmd = "O<face> call [%s] [%s] [%s] [%s] [%s]" % ( 
                    self.builder.get_object("spinXStart").get_value(),
                    self.builder.get_object("spinXEnd").get_value(),
                    self.builder.get_object("spinXFeed").get_value(),
                    self.builder.get_object("spinZStep").get_value(),
                    self.builder.get_object("spinSFM").get_value() )
        print cmd
        ensure_mode(linuxcnc.MODE_MDI)
        linuxcnc.command().mdi(cmd)

    def DoCalculator(self, spin, desc):
        dialog = CalculatorDialog()
        if dialog.run(spin.get_parent(), desc, str(spin.get_value()) ):
            spin.set_value( float(dialog.get_value()) )

    def on_spinXStart_button_press_event(self,w,d):
        self.DoCalculator(w, "X Start")

    def on_spinXFeed_button_press_event(self,w,d):
        self.DoCalculator(w, "X Feed")

    def on_spinSFM_button_press_event(self,w,d):
        self.DoCalculator(w, "SFM")

    def on_spinZStep_button_press_event(self,w,d):
        self.DoCalculator(w,"Z Step")

    def on_spinXEnd_button_press_event(self,w,d):
        self.DoCalculator(w,"X End")

    def on_btnSpindleStop_toggled(self,w):
        if self.btnSpindleStop.get_active():
            linuxcnc.command().spindle(linuxcnc.SPINDLE_OFF)
        else:
            self.on_vscaleSpindleSpeed_value_changed(w)

    def on_vscaleSpindleSpeed_value_changed(self,w):
        
        speed = float(self.vscaleSpindleSpeed.get_value())
        if speed < 1:
            speed = 1

        if self.btnSpindleStop.get_active():
            pass
        elif self.btnSpindleForward.get_active():
            linuxcnc.command().spindle(linuxcnc.SPINDLE_FORWARD,speed)
        elif self.btnSpindleReverse.get_active():
            linuxcnc.command().spindle(linuxcnc.SPINDLE_REVERSE,speed)

def get_handlers(halcomp,builder,useropts):
    return [HandlerClass(halcomp,builder,useropts)]

