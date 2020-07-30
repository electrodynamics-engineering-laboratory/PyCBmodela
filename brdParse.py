"""
    This file serves to define the Board object and implements methods to detect a brd file, parse the file, and create a Board
    object. Current functionality is:
        -Creating board object with dimensions, perimeter, wires, circles, holes, vias, parts, layers. 

    NOTE: the unit parsed in the XML appears to default to mil, even when a board's dimensions in Autodesk Eagle
    are specified as mm. This is likely because the unit detected corresponds to the grid used in Eagle rather than the
    actual board dimensions. Going forward, units will be assumed mm.

    29 July 2020
"""





"""
    Board class with attributes:
        -perimeter: list of Perimeter objects
        -wires: list of Wire objects
        -circles: list of Circle objects
        -holes: list of Hole objects
        -vias: list of Via objects
        -parts: list of Part objects
        -layers: dictionary with int keys -> str values
        -polygons: list of Polygon objects
        -routedCircles: list of RoutedCircle objects
"""
class Board:
    def __init__(self):
        self.info = {
            'width' : -1,
            'height' : -1,
            'unit' : 'mm',
        }

        self.perimeter : []
        self.wires : []
        self.circles : []
        self.holes : []
        self.vias : []
        self.parts : []
        self.layers : {}
        self.polygons : []
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
                class Perimeter:
                    def __init__(self):
                        self.x1 = float(wire.get('x1'))
                        self.y1 = float(wire.get('y1'))
                        self.x2 = float(wire.get('x2'))
                        self.y2 = float(wire.get('y2'))
                        self.width = float(wire.get('width'))
                        # self.layer = int(wire.get('layer'))       # Dimension is stored in layer 20, so this is implicit
                        self.curve = wire.get('curve')
                thisPerimeter = Perimeter()
                perimeterList.append(thisPerimeter)
            return perimeterList

        def parseWires():
            wiresList = []
            signalsTag = next(root.iter('signals'))                 # Access signals tag
            for wireElement in signalsTag.iter('wire'):
                """
                    Will eventually need to check for valid coordinates
                """
                class Wire:
                    def __init__(self):
                        self.x1 = float(wireElement.get('x1'))
                        self.y1 = float(wireElement.get('y1'))
                        self.x2 = float(wireElement.get('x2'))
                        self.y2 = float(wireElement.get('y2'))
                        self.width = float(wireElement.get('width'))
                        self.layer = int(wireElement.get('layer'))
                thisWire = Wire()
                wiresList.append(thisWire)
            return wiresList
        
        def parseCircles():
            circlesList = []
            plainTag = next(root.iter('plain'))                     # Access the plain tag
            for circle in plainTag.iter('circle'):
                class Circle:
                    def __init__(self):
                        self.x = float(circle.get('x'))
                        self.y = float(circle.get('y'))
                        self.radius = float(circle.get('radius'))
                        self.width = float(circle.get('width'))
                        self.layer = int(circle.get('layer'))
                thisCircle = Circle()
                circlesList.append(thisCircle)                      # Note that circles are nothing more than holes at 
            return circlesList                                      # a point. Routes are added later

        def parseHoles():
            holesList = []
            plainTag = next(root.iter('plain'))                     # Access the plain tag
            for holeElement in plainTag.iter('hole'):
                """
                    Will eventually need to check for valid coordinates
                """
                class Hole:
                    def __init__(self):
                        self.x = float(holeElement.get('x'))
                        self.y = float(holeElement.get('y'))
                        self.drill = float(holeElement.get('drill'))
                thisHole = Hole()
                holesList.append(thisHole)
            return holesList
            
        def parseVias():
            viasList = []
            signalsTag = next(root.iter('signals'))                 # Access the signals tag
            for viaElement in signalsTag.iter('via'):
                class Via:
                    def __init__(self):
                        self.x = float(viaElement.get('x'))
                        self.y = float(viaElement.get('y'))
                        self.extent = viaElement.get('extent')
                        self.drill = float(viaElement.get('drill'))
                thisVia = Via()
                viasList.append(thisVia)
            return viasList

        def parseParts():
            partsList = []
            elementsTag = next(root.iter('elements'))               # Access the elements tag
            for boardElement in elementsTag.iter('element'):
                class Part:
                    def __init__(self):
                        self.name = boardElement.get('name')
                        self.library = boardElement.get('library')
                        self.package = boardElement.get('package')
                        self.value = boardElement.get('value')
                        self.x = float(boardElement.get('x'))
                        self.y = float(boardElement.get('y'))
                        self.rot = boardElement.get('rot')
                thisPart = Part()
                partsList.append(thisPart)
            return partsList

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
                polygonVertices = []                                # Construct a list of Vertex objects to hold coords and curve
                for vertex in polygon.iter('vertex'):               # Append each vertex (x, y, curve) to the Polygon object's  vertices list
                    vx = float(vertex.get('x'))
                    vy = float(vertex.get('y'))
                    if vertex.get('curve') is None:
                        vcurve = None
                    else:
                        vcurve = float(vertex.get('curve'))
                    class Vertex:
                        def __init__(self):
                            self.x = vx
                            self.y = vy
                            self.curve = vcurve
                    thisVertex = Vertex()
                    polygonVertices.append(thisVertex)
                class Polygon:
                    def __init__(self):
                        self.vertices = polygonVertices
                        self.width = polygonWidth
                        self.layer = polygonLayer
                thisPolygon = Polygon()
                polygonList.append(thisPolygon)
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

            Suggested improvement: calculate greatest number of segments the circle can be composed of to create circle of given 
            radius without going below minimum mechanical resolution
        """
        def circleToRoutes(boardCircles):
            import math
            circleRoutes = []
            for circle in boardCircles:
                circlex = circle.x
                circley = circle.y
                circleradius = circle.radius
                width = circle.width
                layer = circle.layer

                numSegments = 40
                segmentAngle = 360/numSegments
                for i in range(0, numSegments):
                    x1 = circlex + (circleradius * math.cos(segmentAngle*i * (math.pi / 180)))
                    y1 = circley + (circleradius * math.sin(segmentAngle*i * (math.pi / 180)))
                    x2 = circlex + (circleradius * math.cos(segmentAngle*(i+1) * (math.pi / 180)))
                    y2 = circley + (circleradius * math.sin(segmentAngle*(i+1) * (math.pi / 180)))
                    class RoutedCircle:
                        def __init__(self):
                            self.x1 = x1
                            self.y1 = y1
                            self.x2 = x2
                            self.y2 = y2
                            self.width = width
                            self.layer = layer
                    routedCircle = RoutedCircle()
                    circleRoutes.append(routedCircle)
            return circleRoutes
        


        def getDimensions(boardPerimeter):
            minx = 999999
            miny = 999999
            maxx = -1
            maxy = -1
            for route in boardPerimeter:
                minx = min(minx, route.x1)
                maxx = max(maxx, route.x2)
                miny = min(miny, route.y1)
                maxy = max(maxy, route.y2)
            
            width = maxx - minx
            height = maxy - miny
            return (width, height)




        #########################################
        #                                       #
        #         Board Object Creation         #
        #                                       #
        #########################################

        myBoard = Board()
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