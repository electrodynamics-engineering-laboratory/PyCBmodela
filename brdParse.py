"""
    This file serves to define the Board object and implements methods to detect a brd file, parse the file, and create a Board
    object. Current functionality is:
        -Creating board object with dimensions, perimeter, wires, circles, holes, vias, parts, layers. 

    NOTE: the unit parsed in the XML appears to default to mil, even when a board's dimensions in Autodesk Eagle
    are specified as mm. This is likely because the unit detected corresponds to the grid used in Eagle rather than the
    actual board dimensions. Going forward, units will be assumed mm.

    27 May 2020
"""





class Board:
    def __init__(self):
        self.info = {
            'width' : -1,
            'height' : -1,
            'unit' : 'mm',
        }

        # List of dictionaries with keys x1, y1, x2, y2, width, layer, curve
        self.perimeter : []

        # List of dictionaries with keys x1, y1, x2, y2, width, layer
        self.wires : []

        # List of dictionaries with keys x, y, radius, width, layer
        self.circles : []

        # List of dictionaries with keys x, y, drill
        self.holes : []

        # List of dictionaries with keys x, y, extent, drill
        self.vias : []
        
        # List of dictionaries with keys name, value, library, package, rot, x, y
        self.parts : []

        # Dictionary with int keys and str values
        self.layers : {}

        # List of dictionaries with keys vertices, width, layer
        self.polygons : []

        # List of dictionaries with keys x1, y1, x2, y2, width, layer
        # Could be merged with Board.wires later?
        self.routedCircles : []



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
        
        def getPerimeter():
            perimeterList = []
            plainTag = next(root.iter('plain'))
            for wire in plainTag.iter('wire'):
                perimeterList.append({
                    'x1' : float(wire.get('x1')),
                    'y1' : float(wire.get('y1')),
                    'x2' : float(wire.get('x1')),
                    'y2' : float(wire.get('y2')),
                    'width' : float(wire.get('width')),
                    # 'layer' : int(wire.get('layer')),             Dimension is stored in layer 20, so this is implicit
                    'curve' : wire.get('curve')
                })
            return perimeterList

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
            Take in the board's circles attribute and return a list of wires.

            Note that the minimum mechanical resolution is 0.00625mm/step = 0.246mil/step and 
            software resolution is 0.025mm/step = 0.984mil/step
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
        


        def getDimensions(boardPerimeter):
            minx = 999999
            miny = 999999
            maxx = -1
            maxy = -1
            for route in boardPerimeter:
                minx = min(minx, route['x1'])
                maxx = max(maxx, route['x2'])
                miny = min(miny, route['y1'])
                maxy = max(maxy, route['y2'])
            
            width = maxx - minx
            height = maxy - miny
            return (width, height)




        #########################################
        #                                       #
        #              Finalizing               #
        #                                       #
        #########################################

        myBoard = Board()                                           # Construct and return a Board object
        myBoard.perimeter = getPerimeter()
        myBoard.width, myBoard.height = getDimensions(myBoard.perimeter)
        myBoard.unit = 'mm'                                         # Units are assumed mm
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
    Detect file, parse XML, and return the Board object.
"""
def makeBoard():
    targetFile = findbrd()
    targetBoard = Board()
    targetBoard = parseXML(targetFile)
    return targetBoard