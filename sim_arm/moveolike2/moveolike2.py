"""Loads up an environment, attaches a viewer, loads a scene, and requests information about the robot.
"""
from openravepy import *
import sys,time
from types import ModuleType
from numpy import *

env = Environment() # create openrave environment
viewer = env.SetViewer('qtcoin') # attach viewer (optional)
#env.Load('env.xml') # load a simple scene
#env.Load('simple.robot.xml') # load a simple scene
env.Load('moveolike2.xml') # load a simple scene
robot = env.GetRobots()[0] # get the first robot
env.Add(robot,True)


with env: # lock the environment since robot will be used
    raveLogInfo("Robot "+robot.GetName()+" has "+repr(robot.GetDOF())+" joints with values:\n"+repr(robot.GetDOFValues()))
    robot.SetDOFValues([0, 0, 0, 0],[0, 1, 2, 3]) # set joint 0 to value 0.5
    T = robot.GetLinks()[1].GetTransform() # get the transform of link 1
    raveLogInfo("The transformation of link 1 is:\n"+repr(T))

while True:
    cmd = raw_input("> ")
    if cmd == 'a':
        robot.GetLinks()[1].SetTransform


