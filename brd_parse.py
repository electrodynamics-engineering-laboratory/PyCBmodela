"""
    WIP .brd parse script for use with Modela MDX-15 milling machine. Current 
    functionality is:
        -Printing a list of layers and parts in the board file.

    To run, place this script and a single .brd file in a directory and run
    >python3 brd_parse.py

    22 May 2020
"""
import sys





class Board:
    def __init__(self):
        self.info = {
            'width' : -1,
            'height' : -1,
            'wires' : '',
            'circles' : '',
            'parts' : [],
            'layers' : {},
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
        sys.exit(-1)



"""
    Parse an XML file for layers and parts. 

    ?? For layers actually used on physical board, 
    parse for layers under <elements> or <signals> ??
"""
def parseXML(XMLfile):
    import xml.etree.ElementTree as ET
    try:
        tree = ET.parse(XMLfile)
        root = tree.getroot()

        layerDict = {}
        layersTag = next(root.iter('layers'))           # Access the layers tag
        for layer in layersTag.iter('layer'):
            layerNumber = int(layer.get('number'))
            layerName = layer.get('name')
            layerDict[layerNumber] = layerName
        
        partsList = []
        elementsTag = next(root.iter('elements'))       # Access the elements tag
        for boardElement in elementsTag.iter('element'):
            elementName = boardElement.get('name')
            elementLibrary = boardElement.get('library')
            partsList.append((elementName, elementLibrary))

        myBoard = Board()
        # myBoard.wires = wireList
        # myBoard.circles = circleList
        myBoard.parts = partsList
        myBoard.layers = layerDict
        return myBoard

    except:
        print('Error parsing .brd file.')
        raise
        sys.exit(-1)



"""
    Detect file, parse XML, print to terminal.
"""
targetFile = findbrd()
targetBoard = Board()
targetBoard = parseXML(targetFile)

# Proof of concept, will be deleted later
print('Layers detected from layers XML tag:\n--------------------')
for layerNum in targetBoard.layers:
    print(str(layerNum) + ': ' + targetBoard.layers[layerNum])

print('\nParts detected from elements XML tag:\n--------------------')
for partPair in targetBoard.parts:
    print(str(partPair[0]) + ': ' + partPair[1])