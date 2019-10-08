env = Environment()
kinbody = env.ReadRobotXMLFile('moveolike2.xml')
env.Add(kinbody)
solver = ikfast.IKFastSolver(kinbody=kinbody)
#chaintree = solver.generateIkSolver(baselink=0,eelink=7,freeindices=[2],solvefn=ikfast.IKFastSolver.solveFullIK_6D)
chaintree = solver.generateIkSolver(baselink=0,eelink=4,freeindices=[2],solvefn=ikfast.IKFastSolver.solveFullIK_TranslationAxisAngle4D)
code = solver.writeIkSolver(chaintree)
open('ik.cpp','w').write(code)


