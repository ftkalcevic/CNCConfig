#!/usr/bin/python

import tempfile, time, os, Tkinter, sys
#from LCD_BUF import *
import LCD_BUF
from pendant_wizard import *
from menupage import *
import hal, emc

ProbeToolNC = "/home/frankt/emc2/nc_files/probe-tool.ngc"
ProbeToolZero = "/home/frankt/emc2/nc_files/probe-tool-zero.ngc"

t = Tkinter.Tk(); t.wm_withdraw()


def RunGCode( filename ):
    # get into correct mode to load gcode
    ensure_mode(emc.MODE_MDI)
    e.cmd.wait_complete()
    ensure_mode(emc.MODE_AUTO)
    e.cmd.wait_complete()

    # We get axis to load it for us otherwise it doesn't detect
    # the file change
    t.tk.call("send", "axis", "open_file_name", filename)

    # Now run it
    ensure_mode(emc.MODE_AUTO)
    e.cmd.wait_complete()
    e.cmd.auto(emc.AUTO_RUN, 0 )


def MakeLoadAndRunGCode( file_suffix, gcode ):
    # Create a tempory file
    print gcode
    fd, name = tempfile.mkstemp( suffix=file_suffix, text=True )
    os.write(fd,gcode)
    os.close(fd)

    RunGCode( name )


def MakeAndLoadGCode( file_suffix, gcode ):
    # Create a tempory file
    fd, name = tempfile.mkstemp( suffix=file_suffix, text=True )
    os.write(fd,gcode)
    os.close(fd)

    # get into correct mode to load gcode
    ensure_mode(emc.MODE_MDI)
    e.cmd.wait_complete()
    ensure_mode(emc.MODE_AUTO)
    e.cmd.wait_complete()

    # We get axis to load it for us otherwise it doesn't detect
    # the file change
    t.tk.call("send", "axis", "open_file_name", name)



def ChangeTool(tool_number):
    cmd = "M6T%02d G43" % tool_number
 
    ensure_mode(emc.MODE_MDI)
    #e.cmd.wait_complete()

    e.cmd.mdi( cmd )
    #e.cmd.wait_complete()

    #ensure_mode(emc.MODE_MANUAL)

    return

 
def GetSelectToolMenu():
    # For tool change, we just use a wizard and list all tools
    tools = []
    for number, name in e.tool_table.items():
	tools.append( [number, name] )
    tools.sort()

    # build the wizard
    def callback(n): return lambda lcd, e, s : ChangeTool(n)
    items = []
    for i, (number, name) in enumerate(tools):
	items.append( ActionItem(0,i+1, ("T%02d " %number) + name, callback(number) ) )
    return items
	
############################################################################
#                      manual menu page
############################################################################
class manual_menupage(menupage):
    lastAxisSelect = -1
    old_values = ["","","",""]
    value_positions = ( (5,1), (4,2), (8,3), (7,4) )
    id_to_axis = ( 0,1,4,5)
    axis_to_id = ( 0,1,-1,-1,2,3)
    labels = ( "Dia:  ", "Z:  ", "Spindle:     rpm", "Feed:        mm/min" )
    old_task_state = -1

    def __init__(self,lcd):
        menupage.__init__(self,lcd)

    def __del__(self):
    	return

    def initial_update(self):
        self.lastAxisSelect = e.hal["axis-select"]
        self.old_values = ["","","",""]

    def update(self):
	highlight_changed = False
        text_changed = False

    	# We hightlight the selected axis.
	axisSelect = e.hal["axis-select"]
        if axisSelect != self.lastAxisSelect:
	    if self.axis_to_id[self.lastAxisSelect] >= 0:
		self.old_values[self.axis_to_id[self.lastAxisSelect]] = ""
		text_changed = True
	    if self.axis_to_id[axisSelect] >= 0:
		self.old_values[self.axis_to_id[axisSelect]] = ""
		highlight_changed = True
	    self.lastAxisSelect = axisSelect
	    #self.draw_labels()

        # read values to update
	current_values = [ '%7.3f' % x_position(),
	                   '%8.3f' % z_position(),
	                   '%4.0f' % e.hal["spindle-speed"],
	                   '%5.0f' % (e.stat.current_vel*60) ]	# convert to mm/min

	# First determine if anything has changed
	if not highlight_changed and not text_changed:
	    for  axis, old, current in zip( self.id_to_axis, self.old_values, current_values ):
		if old != current:
		    if axis == axisSelect:
			highlight_changed = True
		    else:
			text_changed = True


	# Paint
	if text_changed:
	    for  axis, old, current, pos in zip( self.id_to_axis, self.old_values, current_values, self.value_positions ):
		if old != current and axis != axisSelect:
		    x,y = pos
		    self.lcd.text( x, y, current )


	if highlight_changed:
	    x,y = self.value_positions[self.axis_to_id[axisSelect]]
	    current = current_values[self.axis_to_id[axisSelect]]
	    self.lcd.fg((0,0,0))
	    self.lcd.bg((255,255,255))
	    self.lcd.text( x, y, current )
	    self.lcd.bg((0,0,0))
	    self.lcd.fg((255,255,255))

	self.old_values = current_values

	if self.old_task_state != e.stat.task_state:
	    self.old_task_state = e.stat.task_state
	    if e.stat.task_state != emc.STATE_ON:
		self.lcd.bg((255,0,0))
		self.lcd.text( 4, 6, "  Machine Off  " )
		self.lcd.bg((0,0,0))
	    else:
		self.lcd.text( 4, 6, "               " )



	# check the menu buttons
	if e.hal.menu1 and e.event_change["menu1"]:	# Button 1 - next page
	    return self.NEXT_PAGE
	elif e.hal.menu2 and e.event_change["menu2"]:	# Button 2 - Spindle
	    # toggle spindle
	    if e.stat.spindle_enabled:
		e.cmd.spindle(emc.SPINDLE_OFF)
	    else:
		e.cmd.spindle(emc.SPINDLE_FORWARD)
	elif e.hal.menu3 and e.event_change["menu3"]:	# Button 3 - Zero
	    if e.hal.enable:
	        if axisSelect == 0:
		    zero_axis(0)
		elif axisSelect == 1:
		    zero_axis(2)
	elif e.hal.menu4 and e.event_change["menu4"]:	# Button 4 - Home
	    if e.hal.enable:
	        if axisSelect == 0:
    		    ensure_mode(emc.MODE_MANUAL)
		    e.cmd.home(0)
		elif axisSelect == 1:
    		    #ensure_mode(emc.MODE_MANUAL)
		    #e.cmd.home(2)
		    pass

    def draw_labels(self):
	axisSelect = e.hal["axis-select"]
        for y, (axis, label) in enumerate( zip(self.id_to_axis, self.labels) ):
	    #if axis == axisSelect:
		#self.lcd.fg((0,0,0))
		#self.lcd.bg((255,255,255))
		#self.lcd.text( 0, y+1, label )
		#self.lcd.bg((0,0,0))
		#self.lcd.fg((255,255,255))
	    #else:
		self.lcd.text( 0, y+1, label )

    def setfocus(self):
    	self.lcd.font(0)
	self.lcd.fg((255,0,0))
	self.lcd.bg((255,0,0))
	self.lcd.text(1,1,"1234567890")
	self.lcd.fg((0,255,0))
	self.lcd.bg((0,255,0))
	self.lcd.text(1,2,"1234567890")
	self.lcd.fg((0,0,255))
	self.lcd.bg((0,0,255))
	self.lcd.text(1,3,"1234567890")
	return
        # We have been switched to.  Redraw the screen 
	self.lcd.font(0)
	self.lcd.fg((255,255,255))
	self.lcd.bg((0,0,0))
	self.lcd.cls()
 	self.drawbuttons( ("Next Page", "Spindle", "Zero", "Home") )

	self.drawtitle( "  Manual  " )

	self.lcd.begin()
	self.lcd.font(1)
    	self.lcd.fg((255,255,255))
	self.lcd.bg((0,0,0))

    	self.draw_labels()
	self.initial_update()
	self.lcd.end()

    def losefocus(self):
    	return



############################################################################
#                      Program Run Page
############################################################################
class programrunpage(menupage):
    old_values0 = None
    old_values1 = None
    lastAxisSelect = -1
    #                   file   line   x      z       rpm    so      feed   fro
    value_positions0 = ( (6,8), (6,9) )
    value_positions1 = (               (4,1), (14,1), (7,2), (17,2), (6,3), (17,3) )
    axis_select_id   = (                -1,    -1,     -1,    4,      -1,    5 )
    old_task_state = -1
    lines = None
    showGCode = False

    def __init__(self,lcd):
        menupage.__init__(self,lcd)

    def __del__(self):
    	pass

    def update(self):
        self.update1()
	self.update0()

	# check the menu buttons
	if e.hal.menu1 and e.event_change["menu1"]:
	    return self.NEXT_PAGE
	if e.hal.menu4 and e.event_change["menu4"]:
	    self.showGCode = not self.showGCode
	    self.old_values0 = None
	    x,y = self.value_positions0[1]
	    self.lcd.font(0)
	    if self.showGCode:
		self.lcd.text( 0, y, "%-45s" % " " )
	    else:
		self.lcd.text( 0, y, "%-45s" % "Line:" )
	    self.lcd.font(1)


    def MakeNiceFilename(self, filename, max_len ):
        if len(filename) <= max_len:
	    return filename
	# filename too long.  split the path/filename out
	path, file = os.path.split(filename)
        # blindly shrink the path to fit and stick ... in the middle
	path_len = max_len - len(file) - 1
	pre = (path_len-3)/2
	post = path_len - pre - 3
	return path[0:pre] + "..." + path[-post:] + "/" + file

    def load_file(self, file ):
        self.lines = open(file).readlines()

    def file_line(self, lineno ):
    	if self.lines == None:
	    str = ""
	elif lineno >= len(self.lines):
	    str = ""
	else:
	    str = self.lines[lineno].strip()
	return str

    # updates in font 0 (small font)	
    def update0(self):	
	if self.old_values0 is None:
	    self.old_values0 = [ "", -1 ]

        if e.stat.file != self.old_values0[0]:
	    if self.showGCode:
		self.load_file( e.stat.file )
	    self.old_values0[0] = e.stat.file 
	    self.old_values0[1] = -1
	    x,y = self.value_positions0[0]
	    self.lcd.font(0)
	    self.lcd.text( x, y, '%-39s' % self.MakeNiceFilename(e.stat.file, 39 ) )

	if e.stat.motion_line != self.old_values0[1]:
	    self.old_values0[1] = e.stat.motion_line
	    x,y = self.value_positions0[1]
	    self.lcd.font(0)
	    if self.showGCode:
		self.lcd.text( 0, y, "%5d:%-39s" % (e.stat.motion_line, self.file_line(e.stat.motion_line-1)[-39:] ) )
	    else:
		self.lcd.text( x, y, '%-8d'  % (e.stat.motion_line+1) )

	self.lcd.font(1)

    # updates in font 1 (large font)	
    def update1(self):	
	current_values = [ '%7.3f' % x_position(),
	                   '%8.3f' % z_position(),
	                   '%4.0f' % e.hal["spindle-speed"],
	                   '%3.0f' % (e.stat.spindlerate*100) + "%",
	                   '%5.0f' % (e.stat.current_vel*60),		# convert to mm/min
			   '%3.0f' % (e.stat.feedrate*100) + "%"  ]

	axisSelect = e.hal["axis-select"]
        if axisSelect != self.lastAxisSelect:
            self.old_values1 = None
	    self.lastAxisSelect = axisSelect

	if self.old_values1 is None:
	    self.old_values1 = [ "" for i in enumerate(current_values)]

        for  axis, old, current, pos in zip( self.axis_select_id, self.old_values1, current_values, self.value_positions1 ):
	    if old != current:
		x,y = pos
		if axis == axisSelect:
		    self.lcd.fg((0,0,0))
		    self.lcd.bg((255,255,255))
		    self.lcd.text( x, y, current )
		    self.lcd.bg((0,64,0))
		    self.lcd.fg((255,255,255))
		else:
		    self.lcd.text( x, y, current )

	self.old_values1 = current_values

	# check machine status
	if self.old_task_state != e.stat.task_state:
	    self.old_task_state = e.stat.task_state
	    if e.stat.task_state != emc.STATE_ON:
		self.lcd.bg((255,0,0))
		self.lcd.text( 4, 6, "  Machine Off  " )
		self.lcd.bg((0,64,0))
	    else:
		self.lcd.text( 4, 6, "               " )


    def setfocus(self):
        self.old_values0 = None
        self.old_values1 = None
    	self.old_task_state = -1

        # We have been switched to.  Redraw the screen 
	self.lcd.begin()
	self.lcd.font(0)
	self.lcd.bg((0,64,0))
	self.lcd.fg((0,0,0))
	self.lcd.cls()
 	self.drawbuttons( ("Next Page", "", "", "Show GCode") )
	self.lcd.end()

	self.drawtitle( "  Program Run  ")

	self.lcd.begin()
	self.lcd.font(1)
	self.lcd.bg((0,64,0))
	self.lcd.fg((255,255,255))
	self.lcd.text(0,1,"Dia:")
	self.lcd.text(12,1,"Z:")
	self.lcd.text(0,2,"RPM:")
	self.lcd.text(12,2,"SO:")
	self.lcd.text(0,3,"Feed:")
	self.lcd.text(12,3,"FRO:")
	self.lcd.end()
	self.update1()

	self.lcd.begin()
	self.lcd.font(0)
	self.lcd.text(0,8,"File:")
	self.lcd.text(0,9,"Line:")
	self.update0()
	self.lcd.end()


    def losefocus(self):
	e.hal["tool-changed"] = False		# Reset the toggle
	return


############################################################################
#                      Wizards
############################################################################

def MakeFaceGCode( lcd, e, colours ):
    items = wizard_page.face_items
    startdia = items[0].value
    enddia = items[1].value
    startz = items[2].value
    endz = items[3].value
    feed = items[4].value
    depthofcut = items[5].value
    sfm = items[6].value
    max_rpm = items[7].value
    clearance = items[8].value

    # Create GCode
    gcode = ""
    gcode += "o<facingoutside> CALL [%f] [%f] [%f] [%f] [%f] [%f] [%f] [%f] [%f] [%f] [%f] [%f]\n" % (startdia, enddia, startz, endz, feed, depthofcut, 0, 0, 0, sfm, max_rpm, clearance )
    gcode += "M2\n"
    MakeAndLoadGCode( 'face.ngc', gcode )


def MakeTurnGCode( lcd, e, colours ):
    items = wizard_page.turn_items
    startDia = items[0].value
    endDia = items[1].value
    startZ = items[2].value
    endZ = items[3].value
    feed = items[4].value
    depthofcut = items[5].value
    sfm = items[6].value
    max_rpm = items[7].value
    clearance = items[8].value

    # Create gcode
    gcode = ""
    gcode += "o<turn> CALL [%f] [%f] [%f] [%f] [%f] [%f] [%f] [%f] [%f] [%f] [%f] [%f]\n" % (startDia, endDia, startZ, endZ, feed, depthofcut, 0, 0, 0, sfm, max_rpm, clearance )
    gcode += "M2\n"
    MakeAndLoadGCode( 'turn.ngc', gcode )


def MakeBoreGCode( lcd, e, colours ):
    items = wizard_page.bore_items
    startDia = items[0].value
    endDia = items[1].value
    startZ = items[2].value
    endZ = items[3].value
    feed = items[4].value
    depthofcut = items[5].value
    clearance = items[6].value
    spindle = items[7].value
 
    # Create gcode
    gcode = ""
    gcode += "o<Bore> CALL [%f] [%f] [%f] [%f] [%f] [%f] [%f] [%f] [%f] [%f]\n" % (startDia, endDia, startZ, endZ, feed, depthofcut, 0, 0, clearance, spindle )
    gcode += "M2\n"
    MakeAndLoadGCode( 'bore.ngc', gcode )


def MakeTaperGCode( lcd, e, colours ):
    items = wizard_page.taper_items
    startdia = items[0].value
    enddia = items[1].value
    startz = items[2].value
    endz = items[3].value
    angle = items[4].value
    feed = items[5].value
    depthofcut = items[6].value
    sfm = items[7].value
    max_rpm = items[8].value
    clearance = items[9].value

    # Create GCode
    gcode = ""
    gcode += "o<taper> CALL [%f] [%f] [%f] [%f] [%f] [%f] [%f] [%f] [%f] [%f] [%f] [%f] [%f] [%f]\n" % (startdia, enddia, startz, endz, angle, 0, feed, depthofcut, 0, 0, 0, sfm, max_rpm, clearance )
    gcode += "M2\n"
    MakeAndLoadGCode( 'taper.ngc', gcode )


class wizardpage(menupage):
    colours = Colours( { 'fill':( (255,255,255),(64,0,64)), 
                         'text':( (255,255,255),(64,0,64)),
                         'button':( (255,255,255),(64,64,0)),
		         'high':( (0,0,0),(255,255,255)) } )

    face_items = [ EditItem(0,1,"Start Dia:         mm", 11,1, 10.0, "%7.3f", 1.0),
		   EditItem(0,2,"End Dia:           mm", 11,2, -1.0, "%7.3f", 1.0),
		   EditItem(0,3,"Start Z:           mm", 11,3, 1.0, "%7.3f", 1.0),
		   EditItem(0,4,"End Z:             mm", 11,4, 0.0, "%7.3f", 1.0),
		   EditItem(0,5,"Feed:              mm/rev", 13,5, 0.25, "%5.3f", 1.0),
		   EditItem(0,6,"Depth/Cut:         mm", 13,6, .25, "%5.3f", 1.0),
		   EditItem(0,7,"SFM:               ", 14,7, 100, "%4.0f", 10.0),
		   EditItem(0,8,"Max RPM:           rpm", 14,8, 1500, "%4.0f", 10.0),
		   EditItem(0,9,"Clearance:  99.999 mm", 12,9, 2.0, "%6.3f", 1.0),
	           ActionItem(10,11,"  Make GCode  ", MakeFaceGCode)  ]
    turn_items = [ EditItem(0,1,"Start Dia: 123.123 mm", 11,1, 15.0, "%7.3f", 1.0),
                   EditItem(0,2,"End Dia:   123.123 mm", 11,2, 10.0, "%7.3f", 1.0),
		   EditItem(0,3,"Start Z:  -112.123 mm", 10,3, 0.0, "%8.3f", 1.0),
		   EditItem(0,4,"End Z:    -112.123 mm", 10,4, -10.0, "%8.3f", 1.0),
		   EditItem(0,5,"Feed:        0.123 mm/rev", 13,5, 100, "%5.3f", 1.0),
		   EditItem(0,6,"Depth/Cut:   1.123 mm", 13,6, .25, "%5.3f", 1.0),
		   EditItem(0,7,"SFM:          9999", 14,7, 100, "%4.0f", 10.0),
		   EditItem(0,8,"Max RPM:      1200 rpm", 14,8, 1500, "%4.0f", 10.0),
		   EditItem(0,9,"Clearance:  99.999 mm", 12,9, 2.0, "%6.3f", 1.0),
	           ActionItem(10,11,"  Make GCode  ", MakeTurnGCode)  ]
    bore_items = [ EditItem(0,1,"Start Dia: 123.123 mm", 11,1, 10.0, "%7.3f", 1.0),
                   EditItem(0,2,"End Dia:   123.123 mm", 11,2, 15.0, "%7.3f", 1.0),
		   EditItem(0,3,"Start Z:  -112.123 mm", 10,3, 0.0, "%8.3f", 1.0),
		   EditItem(0,4,"End Z:    -112.123 mm", 10,4, -10.0, "%8.3f", 1.0),
		   EditItem(0,5,"Feed:        0.000 mm/rev", 13,5, .15, "%5.3f", 1.0),
		   EditItem(0,6,"Depth/Cut:   1.123 mm", 13,6, .25, "%5.3f", 1.0),
		   EditItem(0,7,"Clearance:  99.999 mm", 12,7, 2.0, "%6.3f", 1.0),
		   EditItem(0,8,"Spindle:      1234 rpm", 14,8, 500, "%4.0f", 10.0),
	           ActionItem(10,10,"  Make GCode  ", MakeBoreGCode)  ]
    taper_items = [ EditItem(0,1,"Start Dia:         mm", 11,1, 10.0, "%7.3f", 1.0),
		   EditItem(0,2,"End Dia:           mm", 11,2, -1.0, "%7.3f", 1.0),
		   EditItem(0,3,"Start Z:           mm", 11,3, 1.0, "%7.3f", 1.0),
		   EditItem(0,4,"End Z:             mm", 11,4, 0.0, "%7.3f", 1.0),
		   EditItem(0,5,"Angle:             deg", 11,5, 30.0, "%7.3f", 1.0),
		   EditItem(0,6,"Feed:              mm/rev", 13,6, 0.25, "%5.3f", 1.0),
		   EditItem(0,7,"Depth/Cut:         mm", 13,7, .25, "%5.3f", 1.0),
		   EditItem(0,8,"SFM:               ", 14,8, 100, "%4.0f", 10.0),
		   EditItem(0,9,"Max RPM:           rpm", 14,9, 1500, "%4.0f", 10.0),
		   EditItem(0,10,"Clearance:  99.999 mm", 12,10, 2.0, "%6.3f", 1.0),
	           ActionItem(10,12,"  Make GCode  ", MakeTaperGCode)  ]
    items = [ SubmenuItem(0,1," Face ",face_items),
    	      SubmenuItem(0,2," Turn ", turn_items ),
    	      SubmenuItem(0,3," Bore ", bore_items ),
	      SubmenuItem(0,4," Taper ", taper_items ),
	      SubmenuItem(0,5," Threading ", None ) ]

    wiz = None

    def __init__(self,lcd):
        menupage.__init__(self,lcd)
	self.wiz = wizard(lcd)

    def __del__(self):
    	pass

    def update(self):
        return self.wiz.update(self.lcd, e )

    def setfocus(self):
	#self.drawtitle( "  Wizards  ")
	self.wiz.init(self.lcd,e,"  Wizards  ",self.items,self.colours)

    def losefocus(self):
    	return

    def CleanLabel(self,l):
        l = l.strip()
	if l.find(':') != -1:
	    return l.split(':')[0].strip()
	return l

    def load(self):
        try:
	    ini = emc.ini("pendant-wizards.ini")
	    for item in self.items:
		if isinstance(item,SubmenuItem) and item.submenu != None:
		    section = self.CleanLabel(item.label)
		    for entry in item.submenu:
			if isinstance(entry,EditItem):
			    field = self.CleanLabel(entry.label)
			    value = ini.find( section, field )
			    if value != None:
				entry.value = float(value)
	except:
    	    pass
	return

    def save(self):
	fd = open("pendant-wizards.ini","w")
	for item in self.items:
	    if isinstance(item,SubmenuItem) and item.submenu != None:
		fd.write( "[" + self.CleanLabel(item.label) + ']\n');
		for entry in item.submenu:
		    if isinstance(entry,EditItem):
			fd.write( self.CleanLabel(entry.label) + "=" + `entry.value` + "\n" )
	fd.close()
        return


############################################################################
#                      tool offset page
############################################################################



def InitialiseToolOne( lcd, e, colours ):
    MaxProbeDistance = tooloffset_page.items[3].value
    SearchSpeed = tooloffset_page.items[4].value
    LatchSpeed = tooloffset_page.items[5].value
    MakeLoadAndRunGCode( 'probe.ngc', "o<probe-tool-one> call [%d] [%d] [%d]\nM2\n" % (MaxProbeDistance, SearchSpeed, LatchSpeed))

def StoreToolZ( lcd, e, colours ):
    # Locate the current tool & store the tool offset
    MaxProbeDistance = tooloffset_page.items[3].value
    SearchSpeed = tooloffset_page.items[4].value
    LatchSpeed = tooloffset_page.items[5].value
    MakeLoadAndRunGCode( 'probe.ngc', "o<probe-tool-offset> call [%d] [%d] [%d] [%d]\nM2\n" % ( MaxProbeDistance, SearchSpeed, LatchSpeed, e.stat.tool_in_spindle))


class tooloffsetpage(menupage):
    colours = Colours( { 'fill':( (255,255,255),(64,0,64)), 
			 'text':( (255,255,255),(64,0,64)),
			 'button':( (255,255,255),(64,64,0)),
			 'high':( (0,0,0),(255,255,255)) } )

    items = [ ActionItem(0,1,"  Initialise Tool #1  ", InitialiseToolOne ),
	      0,
	      ActionItem(0,3,"  Store Tool Z Offset  ", StoreToolZ),
	      EditItem(  0,4,"Max Probe Travel: 100 mm", 18,4,  5.0, "%3.0f", 1.0),
	      EditItem(  0,5,"Search Speed: 100 mm/min", 14,5, 25.0, "%3.0f", 1.0),
	      EditItem(  0,6,"Latch Speed:    1 mm/min", 14,6,  1.0, "%3.0f", 1.0) ]
    wiz = None

    def __init__(self,lcd):
        menupage.__init__(self,lcd)
	self.wiz = wizard(lcd)

    def __del__(self):
    	pass

    def update(self):
        return self.wiz.update(self.lcd, e )

    def setfocus(self):
        if self.items[1] == 0:
            self.items[1] = SubmenuItem(0,2,"  Select Tool...  ", GetSelectToolMenu())
	self.wiz.init(self.lcd,e,"  Tool Probing  ",self.items,self.colours)

    def losefocus(self):
    	return



############################################################################
#                      Select tool
############################################################################
       	
class selecttoolpage(menupage):

    def __init__(self,lcd):
        menupage.__init__(self,lcd)
	self.wiz = wizard(lcd)

    def __del__(self):
    	pass

    def update(self):
        return self.wiz.update(self.lcd, e )

    def setfocus(self):
        # For tool change, we just use a wizard and list all tools
	colours = Colours( { 'fill':( (255,255,255),(192,192,0)), 
			     'text':( (0,0,0),(192,192,0)),
			     'button':( (0,0,0),(192,192,0)),
			     'high':( (0,0,0),(0,192,0)) } )
 
	self.wiz.init(self.lcd, e, "  Select Tool  ", GetSelectToolMenu(), colours)
	
    def losefocus(self):
    	return



############################################################################
#                      tool change page
############################################################################
class toolchangepage(menupage):
    tool_table = None

    def __init__(self,lcd):
        menupage.__init__(self,lcd)

    def __del__(self):
    	pass

    def update(self):
	# check the menu buttons
	#if e.hal.menu1 and e.event_change["menu1"]:
	    #return self.NEXT_PAGE
	if e.hal.menu4 and e.event_change["menu4"]:
	    e.hal["tool-changed"] = True
	    return self.LAST_PAGE

    def setfocus(self):
        # We have been switched to.  Redraw the screen 
	self.lcd.font(0)
	self.lcd.bg((128,128,0))
	self.lcd.fg((0,0,0))
	self.lcd.cls()
 	self.drawbuttons( ("", "", "", "Changed") )

	self.drawtitle( "  Tool Change  ")

	self.lcd.font(1)

	self.lcd.centeredtextp((0,70,320,25), "Insert tool T%d" % e.hal["tool-prep-number"] )

	str = self.getToolDescription( e.hal["tool-prep-number"] )
	if len(str) > 0:
	    self.lcd.centeredtextp((0,100,320,25), str )

    def losefocus(self):
        ensure_mode(emc.MODE_MANUAL)
    	return

    def getToolDescription( self, tool_number ):
	if tool_number in e.tool_table:
	    return e.tool_table[tool_number]
	else:
	    return ""
	        	


############################################################################
#                      ESTOP Page
############################################################################
class estoppage(menupage):

    def __init__(self,lcd):
        menupage.__init__(self,lcd)

    def __del__(self):
    	pass

    def update(self):
	if e.stat.task_state != emc.STATE_ESTOP:
	    return self.LAST_PAGE

    def setfocus(self):
        # We have been switched to.  Redraw the screen 
	self.lcd.font(1)
	self.lcd.bg((0,0,0))
	self.lcd.fg((0,0,0))
	self.lcd.cls()

	self.lcd.fg((255,0,0))
	self.lcd.fill( 20, 20, 280, 180 )

	self.lcd.bg((255,0,0))
	self.lcd.fg((255,255,255))
	self.lcd.centeredtextp([0,90,320,2], "Emergency Stop" )
	self.lcd.centeredtextp([0,130,320,2], "Active" )

    def losefocus(self):
    	pass



############################################################################
#                      EMC Interface
############################################################################

class emcInterface():
    hal = None
    names = ( 'menu1', 'menu2', 'menu3', 'menu4', 'tool-change' )
    last_events = None
    event_change = None
    stat = None
    cmd = None
    wheel_change = 0
    last_wheel = 0
    tool_table = None

    def __init__(self):
        self.hal = hal.component("pendant-menu")
        self.hal.newpin("axis-select", hal.HAL_S32, hal.HAL_IN)
        self.hal.newpin("multiplier-select", hal.HAL_S32, hal.HAL_IN)
        self.hal.newpin("menu1", hal.HAL_BIT, hal.HAL_IN)
        self.hal.newpin("menu2", hal.HAL_BIT, hal.HAL_IN)
        self.hal.newpin("menu3", hal.HAL_BIT, hal.HAL_IN)
        self.hal.newpin("menu4", hal.HAL_BIT, hal.HAL_IN)
        self.hal.newpin("enable", hal.HAL_BIT, hal.HAL_IN)
        self.hal.newpin("spindle-speed", hal.HAL_FLOAT, hal.HAL_IN)
        self.hal.newpin("page", hal.HAL_U32, hal.HAL_OUT)
        self.hal.newpin("tool-change", hal.HAL_BIT, hal.HAL_IN)
        self.hal.newpin("tool-changed",hal.HAL_BIT, hal.HAL_OUT)
        self.hal.newpin("tool-prep-number", hal.HAL_S32, hal.HAL_IN)
        self.hal.newpin("jog-wheel", hal.HAL_S32, hal.HAL_IN)
        self.hal.ready()
	self.stat = emc.stat()
	self.cmd = emc.command()
	self.loadToolTable()


    def loadToolTable( self ):
	self.tool_table = {}
	try:
	    inifile = emc.ini(sys.argv[2])
	    tool_file = inifile.find("EMCIO", "TOOL_TABLE")
	    file = open( tool_file, 'r' )
	    for line in file:
		fields = line.split()
		if len(fields) > 0:
		    if fields[0].isdigit():
			number = int(fields[0])
			name = ""
			for c in fields[8:]:
			    name = name + " " + c
			name = name.strip()
			self.tool_table[number] = name
	    file.close()
	except IOError, strerror:
	    print "Failed to load tool table: "
	    print strerror
	except:
	    print "failed to load tool table"
	    pass
	#print "tool table"
	#for number,name in self.tool_table.items():
	    #print `number` + " " + name
	return
	        	


    def check_events(self):
	events = ( self.hal.menu1, self.hal.menu2, self.hal.menu3, self.hal.menu4, self.hal["tool-change"] )
	if self.last_events is not None:
	    self.event_change = dict(zip(self.names,[ new != old for new, old in zip(events, self.last_events) ]))
	else:
	    self.event_change = dict(zip(self.names,[False for name in self.names]))
        self.last_events = events

	wheel_value = self.hal["jog-wheel"]
	self.wheel_change = wheel_value - self.last_wheel
	self.last_wheel = wheel_value
	
############################################################################
#                      Functions
############################################################################

class dummyLCD:
    def __init__(self,host,port):
	pass
    def __del__(self):
        pass
    def cls(self):
	pass
    def text(self,x,y,s):
        pass
    def textp(self,x,y,s):
        pass
    def font(self,f):
        pass
    def fg(self,b):
	pass
    def bg(self,b):
        pass
    def backlight(self,intensity):
        pass
    def rect(self,x,y,w,h):
    	pass
    def fill(self,x,y,w,h):
        pass
    def centeredtextp( self, rect, s ):
	pass
    def begin(self):
    	pass
    def end(self):
        pass

def InitialiseLCD():
    #return dummyLCD(0,0)
    # it may take time to for the LCD component to come up.  Retry a few times
    global lcd
    lcd = None
    host='localhost'
    port=29090
    for i in range(10):
        try:
            lcd = LCD_BUF.LCD(host,port)
	    break
        except:
    	    pass
        
        time.sleep(1)
    
    if lcd == None:
        print "Failed to connect to LCD socket - host:" + host + ", port:" + `port`
        exit()

    return lcd



def dro_position(index):
    return e.stat.actual_position[index] - e.stat.tool_offset[index] - e.stat.origin[index]

def x_position():
    return dro_position(0)*2.0	# Use diameter

def z_position():
    return dro_position(2)

def running():
    return e.stat.task_mode == emc.MODE_AUTO and e.stat.interp_state != emc.INTERP_IDLE


def ensure_mode(m, *p):
    e.stat.poll()
    if e.stat.task_mode == m or e.stat.task_mode in p: return True
    if running(): return False
    e.cmd.mode(m)
    e.cmd.wait_complete()
    return True


def zero_axis(axis):
    if not ensure_mode(emc.MODE_MDI): return
    cmd = "G10 L2 P1 %c%.12f" % ("xyzabc"[axis], (e.stat.actual_position[axis] - e.stat.tool_offset[axis]))
    e.cmd.mdi( cmd )
    e.cmd.wait_complete()
    ensure_mode(emc.MODE_MANUAL)

def ChangePage( index ):
    global page_index, h, activePage
    page_index = index
    e.hal.page = page_index
    activePage.losefocus()
    activePage = pages[page_index]
    activePage.setfocus()

############################################################################
#                      Main
############################################################################


#h = InitialiseHal()
e = emcInterface()
lcd = InitialiseLCD()
#emc_stat = emc.stat()
#emc_cmd = emc.command()

print "Starting menu"
lcd.backlight(1)

# List of the pages
pages = [ manual_menupage(lcd), selecttoolpage(lcd), programrunpage(lcd), tooloffsetpage(lcd), wizardpage(lcd), toolchangepage(lcd), estoppage(lcd)]
tooloffset_page = pages[3]
wizard_page = pages[4]
wizard_page.load()
scroll_pages_count = 5

TOOL_CHANGE_PAGE = 5
ESTOP_PAGE = 6
page_index = 0
page_index = 0
last_page_index = 0
e.hal.page = page_index
activePage = pages[page_index]
activePage.setfocus()
try:    
    while 1:        
	time.sleep(0.1)
	e.stat.poll()
	e.check_events()
	e.hal["tool-changed"] = False		# Reset the toggle
        #special for e-stop
	if e.stat.task_state == emc.STATE_ESTOP and page_index != ESTOP_PAGE:
	    last_page_index = page_index
	    ChangePage( ESTOP_PAGE )
        # special for tool change
	elif e.event_change["tool-change"]:
	    if e.hal["tool-change"]:
		last_page_index = page_index
		ChangePage( TOOL_CHANGE_PAGE )
	else:
	    ret = activePage.update()
	    if ret == menupage.NEXT_PAGE:
		page_index += 1
		if page_index >= scroll_pages_count:
		    page_index = 0
		ChangePage( page_index )
	    elif ret == menupage.LAST_PAGE:
		ChangePage( last_page_index )

except KeyboardInterrupt:
    pass
finally:    
    lcd.backlight(0)
    lcd.cls()
    wizard_page.save()
    print "menu exiting"

