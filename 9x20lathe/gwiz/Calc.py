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

#gwiz_path = "/home/frankt/linuxcnc/9x20lathe/gwiz"



class CalculatorDialog(gtk.Dialog):

    def __init__(self, *args, **kwargs):
        super(CalculatorDialog, self).__init__(*args, **kwargs)

        self.builder = gtk.Builder()
        self.builder.add_from_file(os.path.join(os.path.dirname(__file__),"calc.ui"))
        self.dialog = self.builder.get_object("dialogCalc")
        self.dialog.set_modal(True)
        self.value = ""

        self.builder.get_object("buttonCalcHalX").connect("button-press-event", self.on_button_press,'[x]')
        self.builder.get_object("buttonCalcHalZ").connect("button-press-event", self.on_button_press,'[z]')
        self.builder.get_object("buttonCalcReciprical").connect("button-press-event", self.on_button_press,'recip')
        self.builder.get_object("buttonCalcDivide").connect("button-press-event", self.on_button_press,'/')
        self.builder.get_object("buttonCalc7").connect("button-press-event", self.on_button_press,'7')
        self.builder.get_object("buttonCalc8").connect("button-press-event", self.on_button_press,'8')
        self.builder.get_object("buttonCalc9").connect("button-press-event", self.on_button_press,'9')
        self.builder.get_object("buttonCalcMultiply").connect("button-press-event", self.on_button_press,'*')
        self.builder.get_object("buttonCalc4").connect("button-press-event", self.on_button_press,'4')
        self.builder.get_object("buttonCalc5").connect("button-press-event", self.on_button_press,'5')
        self.builder.get_object("buttonCalc6").connect("button-press-event", self.on_button_press,'6')
        self.builder.get_object("buttonCalcMinus").connect("button-press-event", self.on_button_press,'-')
        self.builder.get_object("buttonCalc1").connect("button-press-event", self.on_button_press,'1')
        self.builder.get_object("buttonCalc2").connect("button-press-event", self.on_button_press,'2')
        self.builder.get_object("buttonCalc3").connect("button-press-event", self.on_button_press,'3')
        self.builder.get_object("buttonCalcPlus").connect("button-press-event", self.on_button_press,'+')
        self.builder.get_object("buttonCalcPlusMinus").connect("button-press-event", self.on_button_press,'-')
        self.builder.get_object("buttonCalc0").connect("button-press-event", self.on_button_press,'0')
        self.builder.get_object("buttonCalcDP").connect("button-press-event", self.on_button_press,'.')
        self.builder.get_object("buttonCalcEquals").connect("button-press-event", self.on_button_press,'=')
        self.builder.get_object("buttonCalcOpenParenthesis").connect("button-press-event", self.on_button_press,'(')
        self.builder.get_object("buttonCalcCloseParenthesis").connect("button-press-event", self.on_button_press,')')
        self.builder.get_object("buttonCalcPi").connect("button-press-event", self.on_button_press,'math.pi')
        self.builder.get_object("buttonCalcClear").connect("button-press-event", self.on_button_press,'C')

    def on_button_press(self, widget, event, key):

        entry = self.builder.get_object( "calcDisplay" )
        text = entry.get_text()
    
        if key == "C":
            text = ""
        elif key in ( "[x]", "[z]" ):

            status = linuxcnc.stat()
            status.poll()
            p = status.position


            i  = 0
            if key == "[x]":
                i = 0
            elif key == "[z]":
                i = 2
 
            pos = p[i] - status.g5x_offset[i] - status.tool_offset[i]
            text = text + str(pos)

        elif key in ( "recip", "/", "*", "-", "+", "-", ".", "-", "(", ")", "math.pi", "C"):
            if key in ( "/", "*", "-", "+", "-", ".", "-", "(", ")", "math.pi"):
                text = text + key
        elif key == "=":
            text = eval(text)
        else:
            text = text + key
    
        entry.set_text( str(text) )

    def run(self,parent,axis,value):

        lbl = self.builder.get_object("labelCalcTitle")
        lbl.set_label( "Set coordinate for %s" % axis)
        entry = self.builder.get_object("calcDisplay")
        entry.set_text( value )
        ret = False
        #self.dialog.set_transient_for(spin)
        if self.dialog.run() == 1:
            self.value = entry.get_text()
            ret = True
        self.dialog.hide()
        return ret

    def get_value(self):
        return self.value


