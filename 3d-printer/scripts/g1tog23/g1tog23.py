#!/usr/bin/python
import fileinput
import sys
import re
import os
from author import douglas

plane=17
tolerance=0.05


class gcode(object):
    def __init__(self):
        self.regMatch = {}
        self.layerList = []
        self.extrusionAmount = 0
        self.totalMoveTimeMinute = 0
        self.progressCallback = None
        self._abort = False


    def load(self, filename):
        if os.path.isfile(filename):
            self._fileSize = os.stat(filename).st_size
            gcodeFile = open(filename, 'r')
            self._load(gcodeFile)
            gcodeFile.close()


    def loadList(self, l):
        self._load(l)


    def abort(self):
        self._abort = True


    def _load(self, gcodeFile):

        st = []
        lastx = 0
        lasty = 0
        lastz = 0
        lasta = 0

        for line in gcodeFile:
            if self._abort:
                raise AnalysisAborted()

            line = line.rstrip()
            original_line = line
            if type(line) is tuple:
                line = line[0]

            if ';' in line or '(' in line:
                sem_pos = line.find(';')
                par_pos = line.find('(')
                pos = sem_pos
                if pos is None:
                    pos = par_pos
                elif par_pos is not None:
                    if par_pos > sem_pos:
                        pos = par_pos
                comment = line[pos+1:].strip()
                line = line[0:pos]

            G = self.getCodeInt(line, 'G')
            if G == 1:    #Move
                x = self.getCodeFloat(line, 'X')
                y = self.getCodeFloat(line, 'Y')
                z = self.getCodeFloat(line, 'Z')
                a = self.getCodeFloat(line, 'A')
                f = self.getCodeFloat(line, 'F')

                if x is None: 
                    x = lastx
                if y is None: 
                    y = lasty
                if z is None: 
                    z = lastz
                if a is None: 
                    a = lasta

                st.append( [x,y,z,a,f] )

                lastx = x
                lasty = y
                lastz = z
                lasta = a
            else:
                if G == 0:    #Rapid - remember position
                    x = self.getCodeFloat(line, 'X')
                    y = self.getCodeFloat(line, 'Y')
                    z = self.getCodeFloat(line, 'Z')
                    a = self.getCodeFloat(line, 'A')

                    if x is not None: 
                        lastx = x
                    if y is not None: 
                        lasty = y
                    if z is not None: 
                        lastz = z 
                    if a is not None: 
                        lasta = a

                if len(line) > 0 and len(st) > 0:
                    self.simplifyPath(st)
                    st = []
                print original_line

        if len(st) != 0:
            self.simplifyPath(st)


    def getCodeInt(self, line, code):
        if code not in self.regMatch:
            self.regMatch[code] = re.compile(code + '([^\s]+)', flags=re.IGNORECASE)
        m = self.regMatch[code].search(line)
        if m == None:
            return None
        try:
            return int(m.group(1))
        except:
            return None


    def getCodeFloat(self, line, code):
        if code not in self.regMatch:
            self.regMatch[code] = re.compile(code + '([^\s]+)', flags=re.IGNORECASE)
        m = self.regMatch[code].search(line)
        if m == None:
            return None
        try:
            return float(m.group(1))
        except:
            return None

    def simplifyPath(self, st):
        #print "st=",len(st)
        l = douglas(st, plane=plane, tolerance=tolerance)
        for i, (g, p, c) in enumerate(l):
            #print "i, g,p,c=", i, g,p,c
            s = g + " "
            if p[0] is not None:
                s = s + "X{0:f}".format(p[0]) + " "
            if p[1] is not None:
                s = s + "Y{0:f}".format(p[1]) + " "
            if p[2] is not None:
                s = s + "Z{0:f}".format(p[2]) + " "
            if p[3] is not None:
                s = s + "A{0:f}".format(p[3]) + " "
            if p[4] is not None:
                s = s + "F{0:f}".format(p[4]) + " "
            if c is not None:
                s = s + c
            s = s.rstrip()
            print s

gcode().loadList(fileinput.input())

