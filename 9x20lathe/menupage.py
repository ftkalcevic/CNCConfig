import LCD

class menupage:
    lcd = None
    header = [0,0,320,14]
    button1 = [0,222,77,17]
    button2 = [81,222,77,17]
    button3 = [162,222,77,17]
    button4 = [243,222,77,17]
    buttons = [ button1, button2, button3, button4 ]

    # constants
    NEXT_PAGE = 1
    LAST_PAGE = 2

    def __init__(self,xlcd):
        self.lcd = xlcd

    def __del__(self):
        return

    def update(self):
        return

    def setfocus(self):
        return

    def losefocus(self):
        return


    def drawbuttons( self, labels ):
	self.lcd.fg((255,255,255))
	self.lcd.bg((0,0,0))
        for b in self.buttons:
	    self.lcd.fill(b[0],b[1],b[2],b[3])

	self.lcd.fg((0,0,0))
	self.lcd.bg((255,255,255))
        for b, l in zip( self.buttons, labels):
	    self.lcd.centeredtextp( b, l )

    def drawtitle( self, title ):
        self.lcd.font(0)
	self.lcd.bg((255,255,0))
	self.lcd.fg((0,0,0))
	self.lcd.centeredtextp( self.header, title )

