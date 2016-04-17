import socket

class FontData:
    char_width = 0
    char_height = 0
    def __init__(self, _char_width, _char_height ):
        self.char_width = _char_width
	self.char_height = _char_height

class LCD_Buffer:
    lcd_socket = None
    def __init__(self, lcd_socket):
        self.lcd_socket = lcd_socket

    def text(self,x,y,s):
	self.lcd_socket.send('text ' + `x` + ',' + `y` + ', "' + s + '"\n')

    def textp(self,x,y,s):
	self.lcd_socket.send('textp ' + `x` + ',' + `y` + ', "' + s + '"\n')

    def font(self,f):
	self.lcd_socket.send('font ' + `f` + '\n')

    def fg(self,r,g,b):
	self.lcd_socket.send('fg ' + `r` + ',' + `g` + ',' + `b` + '\n')

    def bg(self,r,g,b):
	self.lcd_socket.send('bg ' + `r` + ',' + `g` + ',' + `b` + '\n')

    def backlight(self,intensity):
	self.lcd_socket.send('backlight ' + `intensity` + '\n')


class LCD:
    buffering = 0
    current_font = 0
    font_data = [ FontData(7, 14), FontData(14,26) ]
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
        self.buffer.text(x,y,s)
	if buffering == 0:
            self.lcd_socket.send('text ' + `x` + ',' + `y` + ', "' + s + '"\n')

    def textp(self,x,y,s):
        self.buffer.textp(x,y,s)
	if buffering == 0:
            self.lcd_socket.send('textp ' + `x` + ',' + `y` + ', "' + s + '"\n')

    def font(self,f):
        self.buffer.font(f)
        current_font = f
	if buffering == 0:
            self.lcd_socket.send('font ' + `f` + '\n')

    def fg(self,r,g,b):
        self.buffer.fg(r,g,b)
	if buffering == 0:
	    self.lcd_socket.send('fg ' + `r` + ',' + `g` + ',' + `b` + '\n')

    def bg(self,r,g,b):
        self.buffer.bg(r,g,b)
	if buffering == 0:
            self.lcd_socket.send('bg ' + `r` + ',' + `g` + ',' + `b` + '\n')

    def backlight(self,intensity):
        self.buffer.backlight(intensity)
	if buffering == 0:
            self.lcd_socket.send('backlight ' + `intensity` + '\n')

    def rect(self,x,y,w,h):
        self.lcd_socket.send('rect ' + `x` + ',' + `y` + ',' + `w` + ',' + `h` + '\n')

    def fill(self,x,y,w,h):
        self.lcd_socket.send('fill ' + `x` + ',' + `y` + ',' + `w` + ',' + `h` + '\n')

    def centeredtextp( self, rect, s ):
	self.textp( rect[0] + (rect[2] - len(s) * self.font_data[self.current_font].char_width)/2, rect[1] + (rect[3] - self.font_data[self.current_font].char_height)/2, s )

    def begin(self):
    	self.buffering += 1

    def end(self):
    	self.buffering -= 1
	if self.buffering == 0:
	    pass

