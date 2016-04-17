from menupage import *


class Colours():
    colours = None
    def __init__(self,colours):
    	self.colours = colours

    def fg(self,name):
    	return self.colours[name][0]

    def bg(self,name):
    	return self.colours[name][1]

class MenuItem():
    def __init__(self):
    	pass

    def Draw(self,lcd,highlight,colours):
    	pass

    def Select(self,lcd,e,colours):
    	pass

    def Update(self,lcd,e):
    	pass


class SubmenuItem(MenuItem):
    label = None
    x = None
    y = None
    submenu = None

    def __init__(self,x,y,label,submenu) :
        MenuItem.__init__(self)
	self.label = label
	self.x = x
	self.y = y
	self.submenu = submenu

    def Draw(self,lcd,highlighted,colours):
        if highlighted:
	    lcd.fg(colours.fg('high'))
	    lcd.bg(colours.bg('high'))
	    lcd.text( self.x, self.y, self.label )
	    lcd.fg(colours.fg('text'))
	    lcd.bg(colours.bg('text'))
	else:
	    lcd.text( self.x, self.y, self.label )

    def Select(self,lcd,e,colours):
    	return self.submenu

    def Update(self,lcd,e):
    	pass

class ActionItem(SubmenuItem):
    action = None

    def __init__(self,x,y,label,action) :
        SubmenuItem.__init__(self,x,y,label,None)
	self.action = action

    def Draw(self,lcd,highlighted,colours):
        if highlighted:
	    lcd.fg(colours.fg('high'))
	    lcd.bg(colours.bg('high'))
	    lcd.text( self.x, self.y, self.label )
	    lcd.fg(colours.fg('text'))
	    lcd.bg(colours.bg('text'))
	else:
	    lcd.fg(colours.fg('button'))
	    lcd.bg(colours.bg('button'))
	    lcd.text( self.x, self.y, self.label )
	    lcd.fg(colours.fg('text'))
	    lcd.bg(colours.bg('text'))

    def Select(self,lcd,e,colours):
    	self.action( lcd, e, colours )

    def Update(self,lcd,e):
    	pass



class EditItem(MenuItem):
    label = None
    value = None
    x = None
    y = None
    xv = None
    yv = None
    format = None
    selected = False
    scale = 1.0

    def __init__(self,x,y,label,xv,yv,value,format,scale) :
        MenuItem.__init__(self)
	self.label = label
	self.value = value
	self.x = x
	self.y = y
	self.xv = xv
	self.yv = yv
	self.format = format
	self.selected = False
	self.scale = scale

    def Draw(self,lcd,highlighted,colours):
        if highlighted:
	    lcd.fg(colours.fg('high'))
	    lcd.bg(colours.bg('high'))
	    lcd.text( self.x, self.y, self.label )
	    lcd.text( self.xv, self.yv, self.format % self.value )
	    lcd.fg(colours.fg('text'))
	    lcd.bg(colours.bg('text'))
	else:
	    lcd.text( self.x, self.y, self.label )
	    lcd.text( self.xv, self.yv, self.format % self.value )
    	self.selected = False

    def Select(self,lcd,e,colours):
    	if self.selected:
	    self.selected = False
	    lcd.fg(colours.fg('high'))
	    lcd.bg(colours.bg('high'))
	    lcd.text( self.xv, self.yv, self.format % self.value )
	    lcd.fg(colours.fg('text'))
	    lcd.bg(colours.bg('text'))
	else:
	    self.selected = True
	    lcd.text( self.xv, self.yv, self.format % self.value )

    def Update(self,lcd,e):
        if self.selected:
	    if e.wheel_change != 0:
		delta = 0.25 * (10 ** (e.hal["multiplier-select"] - 3)) * e.wheel_change
		self.value += delta * self.scale
		lcd.text( self.xv, self.yv, self.format % self.value )


class wizard(menupage):
    colours = None
    submenus = []
    CurrentItem = None
    submenu = None

    def __init__(self,lcd):
        menupage.__init__(self,lcd)
    	self.CurrentItem = 0
    	pass

    def update(self,lcd,e):
	# Up menu or next menu
	if e.hal.menu1 and e.event_change["menu1"]:
	    if len(self.submenus) == 1:
	        return self.NEXT_PAGE
	    else:
		self.PopMenu(lcd)
		return

    	# Scroll Up
    	if e.hal.menu2 and e.event_change["menu2"]:
	    self.submenu[self.CurrentItem].Draw( lcd, False, self.colours )
	    self.CurrentItem -= 1
	    if self.CurrentItem < 0:
		self.CurrentItem = len(self.submenu) - 1
	    self.submenu[self.CurrentItem].Draw( lcd, True, self.colours )

	# Scroll Down
    	if e.hal.menu3 and e.event_change["menu3"]:
	    self.submenu[self.CurrentItem].Draw( lcd, False, self.colours )
	    self.CurrentItem += 1
	    if self.CurrentItem >= len(self.submenu):
		self.CurrentItem = 0
	    self.submenu[self.CurrentItem].Draw( lcd, True, self.colours)

	# Select
    	if e.hal.menu4 and e.event_change["menu4"]:
	    ret = self.submenu[self.CurrentItem].Select( lcd, e, self.colours)
	    if ret != None:
		self.DoSubmenu( lcd, self.submenu[self.CurrentItem].label, ret )
		return

	self.submenu[self.CurrentItem].Update( lcd, e)

    def init(self,lcd, e, title, items, colours):
    	self.colours = colours
	self.submenus = []
	self.DoSubmenu( lcd, title, items )

    def DoSubmenu( self, lcd, title, submenu ):
	self.submenus.append( (title, self.CurrentItem, submenu ) )
	self.CurrentItem = 0
	self.submenu = submenu

	self.DrawMenu( lcd, title )


    def PopMenu( self, lcd ):
        self.CurrentItem = self.submenus[len(self.submenus)-1][1]
        self.submenus = self.submenus[:len(self.submenus)-1]
        title = self.submenus[len(self.submenus)-1][0]
        self.submenu = self.submenus[len(self.submenus)-1][2]

        self.DrawMenu( lcd, title )

    def DrawMenu( self, lcd, title ):
 	lcd.font(0)
	lcd.bg(self.colours.bg('fill'))
	lcd.fg(self.colours.fg('fill'))
	lcd.cls()
	if len(self.submenus) > 1:
	    button1 = "Back"
	else:
	    button1 = "Next Page"

 	self.drawbuttons( (button1, "Up", "Down", "Select") )

	lcd.bg((255,255,0))
	lcd.centeredtextp( self.header, title )

	lcd.bg(self.colours.bg('text'))
	lcd.fg(self.colours.fg('text'))
	lcd.font(0)
       
    	for i, item in enumerate(self.submenu):
	    item.Draw( lcd, self.CurrentItem == i, self.colours)

