#!/usr/bin/python

import time, os
import LCD
from menupage import *
import hal, emc

global h, lcd, emc_stat, emc_cmd, event_change

############################################################################
#                      main menu page
############################################################################
class page(menupage):
    lastAxisSelect = -1
    old_values = ["","","",""]
    value_positions = ( (4,1), (4,2), (8,3), (7,4) )
    axis_select_id = ( 0,1,4,5)
    labels = ( "X:  ", "Z:  ", "Spindle:     rpm", "Feed:        mm/min" )

    def __init__(self,lcd):
        menupage.__init__(self,lcd)

    def __del__(self):
    	return

    def initial_update(self):
        self.lastAxisSelect = h["axis-select"]
        self.old_values = ["","","",""]

    def update(self):
    	# We hightlight the selected axis.
	axisSelect = h["axis-select"]
        if axisSelect != self.lastAxisSelect:
            self.old_values = ["","","",""]
	    self.lastAxisSelect = axisSelect
	    self.draw_labels()

        # read values to update
	current_values = [ '%8.3f' % x_position(),
	                   '%8.3f' % z_position(),
	                   '%4.0f' % h["spindle-speed"],
	                   '%5.0f' % (emc_stat.current_vel*60) ]	# convert to mm/min

        for  axis, old, current, pos in zip( self.axis_select_id, self.old_values, current_values, self.value_positions ):
	    if old != current:
		x,y = pos
		if axis == axisSelect:
		    self.lcd.fg(0,0,0)
		    self.lcd.bg(255,255,255)
		    self.lcd.text( x, y, current )
		    self.lcd.bg(0,0,0)
		    self.lcd.fg(255,255,255)
		else:
		    self.lcd.text( x, y, current )

	self.old_values = current_values

	# check the menu buttons
	global event_change
	if h.menu1 and event_change["menu1"]:	# Button 1 - next page
	    return self.NEXT_PAGE
	elif h.menu2 and event_change["menu2"]:	# Button 2 - Spindle
	    # toggle spindle
	    if emc_stat.spindle_enabled:
		emc_cmd.spindle(emc.SPINDLE_OFF)
	    else:
		emc_cmd.spindle(emc.SPINDLE_FORWARD)
	elif h.menu3 and event_change["menu3"]:	# Button 3 - Zero
	    if h.enable:
	        if axisSelect == 0:
		    zero_axis(0)
		elif axisSelect == 1:
		    zero_axis(2)
	elif h.menu4 and event_change["menu4"]:	# Button 4 - Home
	    if h.enable:
	        if axisSelect == 0:
		    emc_cmd.home(0)
		elif axisSelect == 1:
		    emc_cmd.home(2)

    def draw_labels(self):
	axisSelect = h["axis-select"]
        for y, (axis, label) in enumerate( zip(self.axis_select_id, self.labels) ):
	    if axis == axisSelect:
		self.lcd.fg(0,0,0)
		self.lcd.bg(255,255,255)
		self.lcd.text( 0, y+1, label )
		self.lcd.bg(0,0,0)
		self.lcd.fg(255,255,255)
	    else:
		self.lcd.text( 0, y+1, label )

    def setfocus(self):
        # We have been switched to.  Redraw the screen 
	self.lcd.font(0)
	self.lcd.fg(255,255,255);
	self.lcd.bg(0,0,0);
	self.lcd.cls()
 	self.drawbuttons( ("Next Page", "Spindle", "Zero", "Home") )

	self.lcd.bg(255,255,0);
	self.lcd.centeredtextp( self.header, "  Manual  " )

	self.lcd.font(1)
    	self.lcd.fg(255,255,255)
	self.lcd.bg(0,0,0)

    	self.draw_labels()
	self.initial_update()

    def losefocus(self):
    	return


