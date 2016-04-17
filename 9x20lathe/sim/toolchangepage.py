import LCD
from menupage import *

class mainpage(menupage):

    def __init__(self,lcd):
        menupage.__init__(self,lcd)

    def __del__(self):
    	return

    def update(self):
	self.lcd.text(4,1, '%8.3f' % 0 )
	self.lcd.text(4,2, '%8.3f' % -123.23 )
	self.lcd.text(7,3, '%5.0f' % 550 )
	self.lcd.text(8,4, '%4.0f' % 900)

    def setfocus(self):
        # We have been switched to.  Redraw the screen 
	self.lcd.font(0)
	self.lcd.fg(255,255,255);
	self.lcd.bg(0,0,0);
	self.lcd.cls()
 	self.drawbuttons( ("Next Page", "b2", "button3", "Four") )

	#self.lcd.fg(255,255,255);
	#self.lcd.bg(0,0,0);
	self.lcd.bg(255,255,0);
	self.lcd.text(16,0," Program Run ")

	self.lcd.font(1)
    	self.lcd.fg(255,255,255)
	self.lcd.bg(0,0,0)

	self.lcd.text(0,1, "X:" )
	self.lcd.text(0,2, "Z:" )
	self.lcd.text(0,3, "Feed:" )
	self.lcd.text(13,3, "mm/min" )
	self.lcd.text(0,4, "Spindle:" )
	self.lcd.text(13,4, "rpm" )

	self.update()

    def losefocus(self):
    	return

