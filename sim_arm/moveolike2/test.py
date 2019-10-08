"""Shows how to get all 6D IK solutions.
"""
from openravepy import *
import numpy, time, math

numpy.set_printoptions(precision=6,suppress=True)

env = Environment() # create the environment
env.SetViewer('qtcoin') # start the viewer
env.Load('simple.robot.env.xml') # load a scene
robot = env.GetRobots()[0] # get the first robot

joints=robot.GetJoints()
for j in joints:
    print("Joint type -%s-" % j.GetType())
    print(j.GetType());
    print(j.GetType().value);
    print(j.GetInfo()._type);
    if j.GetType() == KinBody.JointType.Revolute:
        print( "is Revolute")


manip = robot.SetActiveManipulator('arm') # set the manipulator to leftarm
ikmodel = databases.inversekinematics.InverseKinematicsModel(robot,iktype=IkParameterization.Type.Transform6D)
if not ikmodel.load():
    ikmodel.autogenerate()


# ikfastkins::kinematicsForward(joints: 0.000000 34.999978 89.999978 0.000000 0.000000 0.000000 
# eerot: 
#   1.000000 0.000000 0.000000 
#   0.000000 -0.819152 0.573576 
#   0.000000 -0.573576 -0.819152 
# eetrans: 0.000000 -0.622000 0.244487 
# world: 0.000000 -621.999540 244.487025 -145.000045 -0.000000 0.000000 )


with env: # lock environment
    #Tgoal = numpy.array([[0,-1,0,-0.21],[-1,0,0,0.04],[0,0,-1,0.92],[0,0,0,1]])
    Tgoal = numpy.array([[1,0,0,0],[0,-0.819152,0.573576,-0.622],[0,-0.573576,-0.819152,0.24487],[0,0,0,1]])
    sol = manip.FindIKSolution(Tgoal, IkFilterOptions.CheckEnvCollisions) # get collision-free solution
    with robot: # save robot state

        print( "sol" )
        print( sol )
        robot.SetDOFValues(sol,manip.GetArmIndices()) # set the current solution

        for i in range(len(sol)):
            sol[i] = sol[i] * 180 / math.pi
        print( sol )

        Tee = manip.GetEndEffectorTransform()
        print( "Tgoal" )
        print( Tgoal )
        print( "Tee" )
        print( Tee )
        env.UpdatePublishedBodies() # allow viewer to update new robot
        time.sleep(10)
    
    raveLogInfo('Tee is: '+repr(Tee))


    Tgoal = numpy.array([[1,0,0,0.01],[0,-0.819152,0.573576,-0.622],[0,-0.573576,-0.819152,0.24487],[0,0,0,1]])
    sol = manip.FindIKSolution(Tgoal, IkFilterOptions.CheckEnvCollisions) # get collision-free solution
    with robot: # save robot state

        print( "sol" )
        print( sol )
        robot.SetDOFValues(sol,manip.GetArmIndices()) # set the current solution

        for i in range(len(sol)):
            sol[i] = sol[i] * 180 / math.pi
        print( sol )

        Tee = manip.GetEndEffectorTransform()
        print( "Tgoal" )
        print( Tgoal )
        print( "Tee" )
        print( Tee )
        env.UpdatePublishedBodies() # allow viewer to update new robot
        time.sleep(10)
    
    raveLogInfo('Tee is: '+repr(Tee))


