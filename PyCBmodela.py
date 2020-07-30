"""
    WIP interface between .brd and terminal (or server, at a later point). This file is intended to produce a string of RML 
    commands that can be used to control the Modela MDX-15. Current functionality is:
        -Producing a list of RML commands that mill out the board routes... except they're not scaled and I can't confirm it's 
         correct

    Suggested improvement: mill all wires with adjacent points together at the same time to improve milling speed

    29 July 2020
"""

import sys
import brdParse

MAX_X_COORDINATE = 8388607                                          # Range is -8388608.0 to 8388607.0
MAX_Y_COORDINATE = 8388607                                          # Range is -8388608.0 to 8388607.0
MAX_COORDINATE_VALUE = {
    'x' : MAX_X_COORDINATE,
    'y' : MAX_Y_COORDINATE
}

class ModelaTool:
    def __init__(self):
        self.x = 0
        self.y = 0
        # height : None                                               # Unsure whether or not to include height

    def updateCoordinateAbsolute(self, axis, value):                # Update tool coordinate to absolute position
        if(axis == 'x'):                                            # Should be reducible to simpler code, return to this later
            if abs(value) < MAX_COORDINATE_VALUE[axis]:
                self.x = value
            else:
                raise ValueError('updateCoordinateRelative pushed tool beyond x boundary')
        elif(axis == 'y'):
            if abs(value) < MAX_COORDINATE_VALUE[axis]:
                self.y = value
            else:
                raise ValueError('updateCoordinateRelative pushed tool beyond y boundary')
        else:
            raise ValueError('updateCoordinateRelative received bad axis')



"""
    initialize; tool velocity 5mm/s; tool z-axis velocity 5mm/s; set tool down/up positions to 0, 300; pen up; 
        pen up and move to (0,0); pen down
"""
def initializeTool():
    jobText = 'IN; VS5; !VZ5; PZ0,300; PU; PU0,0; PD;'
    return jobText



"""
    Receive layer to mill and target board. Ideally this can mill wires or routedCircles for a given layer. Assume the tool
    was recently initialized prior to this mill job. 

    Recall that the minimum mechanical resolution is 0.00625mm/step = 0.246mil/step.

    NOTE: Currently, millLayer uses the coordinate locations specified in XML. They may need to be normalized with respect to the
    coordinate system of the MDX-15. 
        This also assumes a constant width for the wire routes. 
"""
def millJobByLayer(targetLayer, board):
    wireRoutes = board.wires
    circleRoutes = board.routedCircles
    jobText = 'PU;'

    # Begin milling wires on this layer
    for wire in wireRoutes:
        if(wire.layer == targetLayer):
            xInitial = round(wire.x1, 7)
            yInitial = round(wire.y1, 7)
            xDest = round(wire.x2, 7)
            yDest = round(wire.y2, 7)
            jobText += 'PA{},{};MC1;PD;PA{},{}'.format(xInitial, yInitial, xDest, yDest)
            jobText += 'PU;MC0\n\n'
    
    for circle in circleRoutes:
        if(circle.layer == targetLayer):
            xInitial = round(circle.x1, 7)
            yInitial = round(circle.y1, 7)
            xDest = round(circle.x2, 7)
            yDest = round(circle.y2, 7)
            jobText += 'PA{},{};MC1;PD;PA{},{}'.format(xInitial, yInitial, xDest, yDest)
            jobText += 'PU;MC0\n\n'

    return jobText



"""
    Proof of concept below, will need to improved upon
"""
try:
    myBoard = brdParse.makeBoard()
except:
    sys.exit(-1)

nonEmptyLayers = []
for wire in myBoard.wires:
    if(wire.layer not in nonEmptyLayers):
        nonEmptyLayers.append(wire.layer)
for circle in myBoard.routedCircles:
    if(circle.layer not in nonEmptyLayers):
        nonEmptyLayers.append(circle.layer)



"""
    Interface with user. Present all non-empty layers, receive as input the layer whose milling commands to produce, and output
    the RML commands to a file in the same directory. 
"""
while(True):
    menuNumber = 1
    if(len(nonEmptyLayers) < 1):
        print('No non-empty layers detected. Check board file.\n')
        sys.exit(0)
        
    for menuNumber, thisLayer in enumerate(nonEmptyLayers, start=1):
        print(str(menuNumber) + '. Layer ' + str(thisLayer))
    
    print('Select a target mill job (or Q to quit): ', end='')
    millLayer = input()
    
    if(millLayer.lower() == 'q'):
        break
    elif((not millLayer.isnumeric()) or (int(millLayer) not in range(1, menuNumber + 1))):
        print('\nInvalid mill job, please input a job among those listed\n')
    
    # HERE IS WHERE JOB COMMANDS ARE CREATED
    else:
        targetMillLayer = nonEmptyLayers[int(millLayer)-1]
        import os
        print(millJobByLayer(targetMillLayer, myBoard), end='\n\n')
        try:
            with open('millJob.mill', 'w+') as fp:
                fp.write(millJobByLayer(targetMillLayer, myBoard))
        except:
            raise