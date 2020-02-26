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
        params = (  ( "angle-start", 0 ),
                    ( "f-mult", 6 ),
                    ( "r-fract", 0 ),
                    ( "ecc-offset", 0 ),
                    ( "f-num", 4 ) )
        for widget_name,value in params:
            widget = self.builder.get_object(widget_name)
            if isinstance(widget,gtk.ComboBox):
                widget.set_active( value )
            else:
                widget.set_value( value )

    def DoCalculator(self, spin, desc):
        dialog = CalculatorDialog()
        if dialog.run(spin.get_parent(), desc, str(spin.get_value()) ):
            spin.set_value( float(dialog.get_value()) )

    def on_anglestart_button_press_event(self,w,d):
        self.DoCalculator(w, "Start Angle")

    def on_fmult_button_press_event(self,w,d):
        self.DoCalculator(w, "f-mult")

    def on_rfract_button_press_event(self,w,d):
        self.DoCalculator(w, "r-fract")

    def on_eccoffset_button_press_event(self,w,d):
        self.DoCalculator(w,"Eccentric Offset")

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

