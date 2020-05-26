"""
    Current functionality is:
        -Creating board object with wires, circles, holes, vias, parts, layers. 

    To run, place this script and a single .brd file in a directory and run
    >python3 brd_parse.py

    Ongoing Questions
        -Consider polygons (e.g. ground) as wire?
    

    -store board dimensions
    -looking into modela minimum path length

    25 May 2020
"""
import sys





class Board:
    def __init__(self):
        self.info = {
            'width' : -1,
            'height' : -1,
            'unit' : None,
            
            # List of dictionaries with keys x1, y1, x2, y2, width, layer
            'wires' : [],

            # List of dictionaries with keys x, y, radius, width, layer
            'circles' : [],

            # List of dictionaries with keys x, y, drill
            'holes' : [],

            # List of dictionaries with keys x, y, extent, drill
            'vias' : [],
            
            # List of dictionaries with keys name, value, library, package, rot, x, y
            'parts' : [],

            # Dictionary with int keys and str values
            'layers' : {},

            # List of dictionaries with keys vertices, width, layer
            'polygons' : [],

            # List of dictionaries with keys x1, y1, x2, y2, width, layer
            # Could be merged with Board.wires later?
            'routedCircles' : []
        }



"""
    Find and return the brd file in this directory.
"""
def findbrd():
    import os
    brdFileList = [brdFile for brdFile in os.listdir('./') if brdFile.endswith('.brd')]
    if len(brdFileList) > 1:
        print('Multiple board files detected. Remove unneeded board files from the working directory.')
        return None
    elif not len(brdFileList):
        print ('No board files detected. Place one board file in the working directory.')
        return None
    try:
        return open('./' + brdFileList[0])
    except:
        print('Error opening .brd file.')
        raise



"""
    Parse an XML file for board physical features.
"""
def parseXML(XMLfile):
    import xml.etree.ElementTree as ET
    try:
        tree = ET.parse(XMLfile)
        root = tree.getroot()



        #########################################
        #                                       #
        #           Parsing Functions           #
        #                                       #
        #########################################

        def getUnit():
            gridTag = next(root.iter('grid'))
            unit = gridTag.get('unit')
            return unit

        def parseWires():
            wiresList = []
            signalsTag = next(root.iter('signals'))                 # Access signals tag
            for wireElement in signalsTag.iter('wire'):
                """
                    Will eventually need to check for valid coordinates
                """
                wiresList.append({
                    'x1' : float(wireElement.get('x1')),
                    'y1' : float(wireElement.get('y1')),
                    'x2' : float(wireElement.get('x2')),
                    'y2' : float(wireElement.get('y2')),
                    'width' : float(wireElement.get('width')),
                    'layer' : int(wireElement.get('layer'))
                })
            return wiresList
        
        def parseCircles():
            circlesList = []
            plainTag = next(root.iter('plain'))                     # Access the plain tag
            for circle in plainTag.iter('circle'):
                circlesList.append({
                    'x' : float(circle.get('x')),
                    'y' : float(circle.get('y')),
                    'radius' : float(circle.get('radius')),
                    'width' : float(circle.get('width')),
                    'layer' : int(circle.get('layer'))
                })                                                  # Note that circles are nothing more than holes at 
            return circlesList                                      # a point. Routes are added later

        def parseHoles():
            holesList = []
            plainTag = next(root.iter('plain'))                     # Access the plain tag
            for holeElement in plainTag.iter('hole'):
                """
                    Will eventually need to check for valid coordinates
                """
                holesList.append({
                    'x' : float(holeElement.get('x')),
                    'y' : float(holeElement.get('y')),
                    'drill' : float(holeElement.get('drill'))
                })
            return holesList

        def parseParts():
            partsList = []
            elementsTag = next(root.iter('elements'))               # Access the elements tag
            for boardElement in elementsTag.iter('element'):
                partsList.append({
                    'name' : boardElement.get('name'),
                    'library' : boardElement.get('library'),
                    'package' : boardElement.get('package'),
                    'value' : boardElement.get('value'),
                    'x' : float(boardElement.get('x')),
                    'y' : float(boardElement.get('y')),
                    'rot' : boardElement.get('rot')                 # None if does not exist
                })
            return partsList
            
        def parseVias():
            viasList = []
            signalsTag = next(root.iter('signals'))                 # Access the signals tag
            for viaElement in signalsTag.iter('via'):
                viasList.append({
                    'x' : float(viaElement.get('x')),
                    'y' : float(viaElement.get('y')),
                    'extent' : viaElement.get('extent'),
                    'drill' : float(viaElement.get('drill')),
                })
            return viasList

        def parseLayers():
            layerDict = {}
            layersTag = next(root.iter('layers'))                   # Access the layers tag
            for layer in layersTag.iter('layer'):
                layerNumber = int(layer.get('number'))
                layerName = layer.get('name')
                layerDict[layerNumber] = layerName
            return layerDict
        
        def parsePolygons():
            polygonList = []
            signalsTag = next(root.iter('signals'))                 # Access signals tag
            for polygon in signalsTag.iter('polygon'):
                polygonWidth = float(polygon.get('width'))
                polygonLayer = int(polygon.get('layer'))
                polygonVertices = []                                # Construct a list of dictionaries to hold coords and curve
                for vertex in polygon.iter('vertex'):               # Append each vertex (x, y, curve) to the polygon's vertices list
                    vx = float(vertex.get('x'))
                    vy = float(vertex.get('y'))
                    if vertex.get('curve') is None:
                        vcurve = None
                    else:
                        vcurve = float(vertex.get('curve'))
                    polygonVertices.append({
                        'x' : vx,
                        'y' : vy,
                        'curve' : vcurve
                    })
                polygonList.append({
                    'vertices' : polygonVertices,
                    'width' : polygonWidth,
                    'layer' : polygonLayer
                })
            return polygonList
                        


        #########################################
        #                                       #
        #            Helper Functions           #
        #                                       #
        #########################################

        """
            Take in the board's circles attribute and return a list of wires
        """
        def circleToRoutes(boardCircles):
            import math
            circleRoutes = []
            for circle in boardCircles:
                circlex = circle['x']
                circley = circle['y']
                circleradius = circle['radius']
                width = circle['width']
                layer = circle['layer']

                for i in range(0, 40):
                    x1 = circlex + (circleradius * math.cos(9*i * (math.pi / 180)))
                    y1 = circley + (circleradius * math.sin(9*i * (math.pi / 180)))
                    x2 = circlex + (circleradius * math.cos(9*(i+1) * (math.pi / 180)))
                    y2 = circley + (circleradius * math.sin(9*(i+1) * (math.pi / 180)))

                    circleRoutes.append({
                        'x1' : x1,
                        'y1' : y1,
                        'x2' : x2,
                        'y2' : y2,
                        'width' : width,
                        'layer' : layer
                    })
            return circleRoutes



        #########################################
        #                                       #
        #              Finalizing               #
        #                                       #
        #########################################

        myBoard = Board()                                           # Construct and return a Board object
        myBoard.unit = getUnit()
        myBoard.wires = parseWires()
        myBoard.circles = parseCircles()
        myBoard.holes = parseHoles()
        myBoard.vias = parseVias()
        myBoard.parts = parseParts()
        myBoard.layers = parseLayers()
        myBoard.polygons = parsePolygons()
        myBoard.routedCircles = circleToRoutes(myBoard.circles)
        return myBoard

    except:
        print('Error parsing .brd file.')
        raise





"""
    Detect file, parse XML, print to terminal.
"""
targetFile = findbrd()
targetBoard = Board()
targetBoard = parseXML(targetFile)



# Proof of concept, will be deleted later
print('Unit detected:\n--------------------')
print(targetBoard.unit)

print('\n\nLayers detected:\n--------------------')
for layerNum in targetBoard.layers:
    print(str(layerNum) + ': ' + targetBoard.layers[layerNum])



print('\n\nParts detected:\n--------------------')
for part in targetBoard.parts:
    print(part['name'] + ' ' + part['value'] + ' ' + part['library'] + ' ' + part['package'] + ' detected at ' + str((part['x'], part['y'])) + ', rotation ' + str(part['rot']))



print('\n\nWires detected:\n--------------------')
wiresInEachLayer = [None] * 100
for wire in targetBoard.wires:
    if wiresInEachLayer[wire['layer']] is not None:
        wiresInEachLayer[wire['layer']].append(((wire['x1'], wire['y1']), (wire['x2'], wire['y2'])))
    else:
        wiresInEachLayer[wire['layer']] = [((wire['x1'], wire['y1']), (wire['x2'], wire['y2']))]

for layerNumber, wire in enumerate(wiresInEachLayer):
    if wire is not None:
        print('Layer ' + str(layerNumber) + ':')
        for wireRoute in wire:
            print(wireRoute)



print('\n\nCircles detected:\n--------------------')
for circle in targetBoard.circles:
    print(str((circle['x'], circle['y'])) + ', radius: ' + str(circle['radius']) + ', width: ' + str(circle['width']) + ', layer: ' + str(circle['layer']))



print('\n\nHoles detected:\n--------------------')
for hole in targetBoard.holes:
    print(str((hole['x'], hole['y'])) + ', drill size: ' + str(hole['drill']))



print('\n\nVias detected:\n--------------------')
for via in targetBoard.vias:
    print(str((via['x'], hole['y'])) + ', drill size: ' + str(via['drill']) + ', extent: ' + via['extent'])



print('\n\nPolygons detected:\n--------------------')
for polygon in targetBoard.polygons:
    print('Polygon at layer ' + str(polygon['layer']) + ' with width ' + str(polygon['width']))
    for vertex in polygon['vertices']:
        print('   ' + str(vertex))



print('\n\nRouted circles:\n--------------------')
routedCirclesInEachLayer = [None] * 100
for routedCircles in targetBoard.routedCircles:
    if routedCirclesInEachLayer[routedCircles['layer']] is not None:
        routedCirclesInEachLayer[routedCircles['layer']].append(((routedCircles['x1'], routedCircles['y1']), (routedCircles['x2'], routedCircles['y2'])))
    else:
        routedCirclesInEachLayer[routedCircles['layer']] = [((routedCircles['x1'], routedCircles['y1']), (routedCircles['x2'], routedCircles['y2']))]

for layerNumber, routedCircles in enumerate(routedCirclesInEachLayer):
    if routedCircles is not None:
        print('Layer ' + str(layerNumber) + ':')
        for routedCirclesRoute in routedCircles:
            print(routedCirclesRoute)