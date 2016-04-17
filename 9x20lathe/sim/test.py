import socket


lcd = None
host='localhost'
port=29090
for i in range(10):
    try:
	lcd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	lcd.connect((host, port))
	break
    except:
	pass
        
    time.sleep(1)
    
if lcd == None:
    print "Failed to connect to LCD socket - host:" + host + ", port:" + `port`
    exit()


def cls():
    lcd.send('cls\n')

def text(x,y,s):
    lcd.send('text ' + `x` + ',' + `y` + ', "' + s + '"\n')


cls()
text(0,0,"Test string")


