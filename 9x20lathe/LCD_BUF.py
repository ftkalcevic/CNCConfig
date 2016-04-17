# This is a light buffering implemetation for the LCD.
# There are 2 things that limit the display through put
#   1) The amount to be drawn
#   2) The maximum number of packets per second sent
# To limit 1, we only send changes, not complete lines.  To limit 2
# we use begin/end locks to only send changes at the end.
# The intelligence is limited.  Changing fore/back colours can confuse
# things.  Avoid putting colour changes in a begin/end block

import socket

class FontData:
    char_width = 0
    char_height = 0
    rows = 0
    columns = 0
    def __init__(self, _char_width, _char_height, _rows, _columns ):
        self.char_width = _char_width
	self.char_height = _char_height
	self.rows = _rows
	self.columns = _columns

font_data = [ FontData(7, 14, 17, 45), FontData(14, 26, 9, 22) ]

class LCD_Buffer:
    global font_data
    lcd_socket = None
    last_font = 1
    last_fg = (255,255,255)
    last_bg = (0,0,0)
    buffer = [ [ " "*font_data[0].columns for i in range(font_data[0].rows) ],
               [ " "*font_data[1].columns for i in range(font_data[1].rows) ] ]
    old_buffer = [ [], [] ]
    old_buffer[0].extend(buffer[0])
    old_buffer[1].extend(buffer[1])

    def __init__(self, lcd_socket):
        self.lcd_socket = lcd_socket

    def text(self,x,y,s):
	line = self.buffer[self.last_font][y]
	a = line[:x]
	b = line[x+len(s):]
	self.buffer[self.last_font][y] = a + s + b

    def textp(self,x,y,s):
    	self.flushbuffer()
	self.lcd_socket.send('textp ' + `x` + ',' + `y` + ', "' + s + '"\n')

    def font(self,f):
        self.flushbuffer()
	self.last_font = f
	self.lcd_socket.send('font ' + `f` + '\n')
	#self.buffer[self.last_font] = [ " "*font_data[self.last_font].columns for i in range(font_data[self.last_font].rows) ]
	#self.old_buffer[self.last_font] = []
	#self.old_buffer[self.last_font].extend(self.buffer[self.last_font])


    def fg(self,clr):
	if clr != self.last_fg:
	    self.flushbuffer()
	self.last_fg = clr
        r,g,b = clr
	self.lcd_socket.send('fg ' + `r` + ',' + `g` + ',' + `b` + '\n')

    def bg(self,clr):
	if clr != self.last_bg:
	    self.flushbuffer()
	self.last_bg = clr
        r,g,b = clr
	self.lcd_socket.send('bg ' + `r` + ',' + `g` + ',' + `b` + '\n')

    def backlight(self,intensity):
	self.lcd_socket.send('backlight ' + `intensity` + '\n')

    def cls(self):
        self.buffer[0] = [ " "*font_data[0].columns for i in range(font_data[0].rows) ]
        self.buffer[1] = [ " "*font_data[1].columns for i in range(font_data[1].rows) ]
	self.old_buffer[0] = []
	self.old_buffer[0].extend(self.buffer[0])
	self.old_buffer[1] = []
	self.old_buffer[1].extend(self.buffer[1])

    def begin(self):
	#self.cls()
        #self.old_buffer = []
	#self.old_buffer.extend(self.buffer)
	pass

    def end(self):
    	self.flushbuffer()

    def flushbuffer(self):
    	for y, s in enumerate(self.buffer[self.last_font]):
	    if self.old_buffer[self.last_font][y] != s:
		x = 0
		while self.buffer[self.last_font][y][x] == self.old_buffer[self.last_font][y][x]:
		    x += 1
		end = len(self.buffer[self.last_font][y])-1
		while self.buffer[self.last_font][y][end] == self.old_buffer[self.last_font][y][end]:
		    end -= 1
		self.lcd_socket.send( 'text ' + `x` + ',' + `y` + ', "' + s[x:end+1] + '"\n')
		#print "   old:" + self.old_buffer[self.last_font][y]
		#print "   new:" + s
		self.old_buffer[self.last_font][y] = s
		#print "newold:" + self.old_buffer[self.last_font][y]
	#self.old_buffer[self.last_font] = []
	#self.old_buffer[self.last_font].extend(self.buffer[self.last_font])

    def getFG():
    	return self.last_fg

    def getBG():
    	return self.last_bg

class LCD:
    global font_data
    buffering = 0
    current_font = 0
    buffer = None

    def __init__(self,host,port):
	self.lcd_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	self.lcd_socket.connect((host, port))
	self.lcd_socket.send('hello\n')
    	self.buffer = LCD_Buffer(self.lcd_socket)

    def __del__(self):
        self.lcd_socket.close()

    def cls(self):
        self.buffer.cls()
	self.lcd_socket.send('cls\n')

    def text(self,x,y,s):
        if x >= font_data[self.current_font].columns or y >= font_data[self.current_font].rows:
	    return

        self.buffer.text(x,y,s)
	if self.buffering == 0:
            self.lcd_socket.send('text ' + `x` + ',' + `y` + ', "' + s + '"\n')

    def textp(self,x,y,s):
        self.buffer.textp(x,y,s)
	if self.buffering == 0:
            self.lcd_socket.send('textp ' + `x` + ',' + `y` + ', "' + s + '"\n')

    def font(self,f):
        self.buffer.font(f)
        self.current_font = f
	if self.buffering == 0:
            self.lcd_socket.send('font ' + `f` + '\n')

    def fg(self,clr):
        self.buffer.fg(clr)
	self.last_fg = clr
	if self.buffering == 0:
	    r,g,b = clr
	    self.lcd_socket.send('fg ' + `r` + ',' + `g` + ',' + `b` + '\n')

    def bg(self,clr):
        self.buffer.bg(clr)
	self.last_bg = clr
	if self.buffering == 0:
	    r,g,b = clr
            self.lcd_socket.send('bg ' + `r` + ',' + `g` + ',' + `b` + '\n')

    def getFG(self):
        return self.last_fg

    def getBG(self):
        return self.last_bg

    def backlight(self,intensity):
        self.buffer.backlight(intensity)
	if self.buffering == 0:
            self.lcd_socket.send('backlight ' + `intensity` + '\n')

    def rect(self,x,y,w,h):
        self.lcd_socket.send('rect ' + `x` + ',' + `y` + ',' + `w` + ',' + `h` + '\n')

    def fill(self,x,y,w,h):
        self.lcd_socket.send('fill ' + `x` + ',' + `y` + ',' + `w` + ',' + `h` + '\n')

    def centeredtextp( self, rect, s ):
	self.textp( rect[0] + (rect[2] - len(s) * font_data[self.current_font].char_width)/2, rect[1] + (rect[3] - font_data[self.current_font].char_height)/2, s )

    def begin(self):
        if self.buffering == 0:
	    self.buffer.begin()
    	self.buffering += 1

    def end(self):
    	self.buffering -= 1
	if self.buffering == 0:
	    self.buffer.end()




