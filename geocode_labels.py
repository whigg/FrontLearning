u"""
geocode_labels.py
by Yara Mohajerani 11/2018

Convert the true labels to geocoded csv files

Update History
    11/2018 - Forked from postProcessing.py
"""

import numpy as np
from PIL import Image
import matplotlib.pyplot as plt
from skimage.graph import route_through_array
import shapefile
import os
import sys
import getopt
from osgeo import ogr
from osgeo import osr
import urllib
from pyproj import Proj,transform

#############################################################################################
#############################################################################################

#This function to make a list of the labels with threshold label
def generateLabelList(indir):
    labelList=[]
    for fil in os.listdir(indir):
        if fil.endswith('_Front.png'):
            labelList.append(fil.replace('_Front.png',''))
    return(labelList)


#############################################################################################
# These functions are to create a list of indices used to find the line label

# get glacier names
def getGlacierList(labelList,glaciersFolder):
    f=open(os.path.join(glaciersFolder,'Scene_Glacier_Dictionary.csv'),'r')
    lines=f.read()
    f.close()
    lines=lines.split('\n')
    glacierList = []
    for sceneID in labelList:
        for line in lines:
            line=line.split(',')
            if line[0]==sceneID:   
                glacierList.append(line[1])
    return(glacierList)



def obtainSceneCornersProjection(sceneID,glaciersFolder,glacier):
    f=open(os.path.join(glaciersFolder, glacier, '%s Image Data.csv'%glacier),'r')
    lines=f.read()
    f.close()
    lines=lines.split('\n')
    for line in lines:
        line=line.split(',')
        if line[1][:-4]==sceneID:
            corners=[]
            projection=int(line[2])
            for i in range(4,12):
                corners.append(float(line[i]))
    return(corners,projection)

def geoCoordsToImagePixels(coords,corners, projection, imageSize):
    coords=reprojectPolygon(coords,3413,projection)
    # fx(x,y) = ax + by + cxy + d
    A=np.array([[corners[0],corners[1],corners[0]*corners[1],1], #lower left corner,
               [corners[2],corners[3],corners[2]*corners[3],1], #lower right corner
               [corners[4], corners[5], corners[4] * corners[5],1], #upper right corner
               [corners[6], corners[7], corners[6] * corners[7],1]]) #upper left corner
    #option 1
    bx = np.array([[0],[imageSize[0]],[imageSize[0]],[0]])
    by = np.array([[imageSize[1]],[imageSize[1]],[0], [0] ])
    Cx=np.dot(np.linalg.inv(A),bx)

    Cy = np.dot(np.linalg.inv(A), by)
    imagePixels=[]
    for coord in coords:
        pixelX=Cx[0]*coord[0] + Cx[1]*coord[1] + Cx[2]*coord[0]*coord[1] + Cx[3]
        pixelY=Cy[0]*coord[0] + Cy[1]*coord[1] + Cy[2]*coord[0]*coord[1] + Cy[3]
        if pixelX>0 and pixelX<imageSize[0]-1 and pixelY>0 and pixelY<imageSize[1]-1:
            imagePixels.append([round(pixelX),round(pixelY)])
    return(np.array(imagePixels))

def reprojectPolygon(polygon,inputCRS,outputCRS):
    inProj = Proj(init='epsg:'+str(inputCRS))
    outProj = Proj(init='epsg:'+str(outputCRS))
    x1,y1 = -11705274.6374,4826473.6922
    x2,y2 = transform(inProj,outProj,x1,y1)
    outputPolygon=[]
    for point in polygon:
        x = point[0]
        y = point[1]
        x2,y2 = transform(inProj,outProj,x,y)
        outputPolygon.append([x2,y2])

    return np.array(outputPolygon)

def seriesToNPoints(series,N):
    #find the total length of the series
    totalDistance=0
    for s in range(len(series[:,0])-1):
        totalDistance+=((series[s,0]-series[s+1,0])**2+(series[s,1]-series[s+1,1])**2)**0.5
    intervalDistance=totalDistance/(N-1)

    #make the list of points
    newSeries=series[0,:]
    currentS = 0
    currentPoint1=series[currentS,:]
    currentPoint2=series[currentS+1,:]
    for p in range(N-2):
        distanceAccrued = 0
        while distanceAccrued<intervalDistance:
            currentLineDistance=((currentPoint1[0]-currentPoint2[0])**2+(currentPoint1[1]-currentPoint2[1])**2)**0.5
            if currentLineDistance<intervalDistance-distanceAccrued:
                distanceAccrued+=currentLineDistance
                currentS+=1
                currentPoint1 = series[currentS, :]
                currentPoint2 = series[currentS + 1, :]
            else:
                distance=intervalDistance-distanceAccrued
                newX=currentPoint1[0]+(distance/currentLineDistance)*(currentPoint2[0]-currentPoint1[0])
                newY = currentPoint1[1] + (distance / currentLineDistance) * (currentPoint2[1] - currentPoint1[1])
                distanceAccrued=intervalDistance+1
                newSeries=np.vstack([newSeries,np.array([newX,newY])])
                currentPoint1=np.array([newX,newY])
    newSeries = np.vstack([newSeries, series[-1,:]])
    return(newSeries)

def fjordBoundaryIndices(glaciersFolder,glacier,corners,projection,imageSize):
    boundary1file=os.path.join(glaciersFolder,glacier,'Fjord Boundaries',glacier+' Boundary 1 V2.csv')
    boundary1=np.genfromtxt(boundary1file,delimiter=',')
    boundary2file = os.path.join(glaciersFolder,glacier,'Fjord Boundaries',glacier + ' Boundary 2 V2.csv')
    boundary2 = np.genfromtxt(boundary2file, delimiter=',')

    boundary1=seriesToNPoints(boundary1,1000)
    boundary2 = seriesToNPoints(boundary2, 1000)

    boundary1pixels = geoCoordsToImagePixels(boundary1,corners,projection,imageSize)
    boundary2pixels = geoCoordsToImagePixels(boundary2, corners, projection,imageSize)
    return(boundary1pixels,boundary2pixels)

def plotImageWithBoundaries(image,boundary1pixels,boundary2pixels):
    imArr = np.asarray(image)
    plt.contourf(imArr)
    plt.plot(boundary1pixels[:,0],boundary1pixels[:,1],'w-')
    plt.plot(boundary2pixels[:, 0], boundary2pixels[:, 1], 'w-')
    plt.gca().set_aspect('equal')
    plt.show()

def testBoundaryIndices():
    boundarySide1indices=[]
    boundarySide2indices=[]
    for j in range(30,180,10):
        boundarySide1indices.append([40,j])
        boundarySide2indices.append([160,j])
    return(np.array(boundarySide1indices),np.array(boundarySide2indices))



#############################################################################################
# These functions are to find the most probable front based on the NN solution

def leastCostSolution(imgArr,boundarySide1indices,boundarySide2indices,step):
    weight=1e22
    indices=[]
    for b1 in range(len(boundarySide1indices)):
        if b1 % step==0:
            startPoint = np.array(boundarySide1indices[b1],dtype=int)
            #if b1 % step == 0:
            #    print('    '+str(b1+1)+' of '+str(len(boundarySide1indices))+' indices tested')
            for b2 in range(len(boundarySide2indices)):
                if b2 % step ==0:
                    endPoint = np.array(boundarySide2indices[b2],dtype=int)
                    testIndices, testWeight = route_through_array(imgArr, (startPoint[1], startPoint[0]),\
                        (endPoint[1], endPoint[0]), geometric=True,\
                        fully_connected=True)
                    tmpIndices = np.array(testIndices)
                    testIndices=np.hstack([np.reshape(tmpIndices[:,1],(np.shape(tmpIndices)[0],1)),np.reshape(tmpIndices[:,0],(np.shape(tmpIndices)[0],1))])

                    if testWeight<weight:
                        weight=testWeight
                        indices=testIndices
    return(indices)


def plotImageWithSolution(image,solution):
    imArr = np.asarray(image)
    plt.contourf(imArr)
    plt.plot(solution[:,0],solution[:,1],'r-')
    plt.gca().set_aspect('equal')
    plt.show()




#############################################################################################
# These functions are to construct a shapefile from the geometric coordinates

def imagePixelsToGeoCoords(pixels, corners, projection, imageSize):

    # fx(x,y) = ax + by + cxy + d
    A = np.array([[0, 0, 0 * 0, 1],  # lower left corner,
                  [imageSize[0], 0, imageSize[0] * 0, 1],  # lower right corner
                  [imageSize[0], imageSize[1], imageSize[0] * imageSize[1], 1],  # upper right corner
                  [0, imageSize[1], 0 * imageSize[1], 1]])  # upper left corner
    # option 1
    bx = np.array([[corners[0]], [corners[2]], [corners[4]], [corners[6]]])
    by = np.array([[corners[1]], [corners[3]], [corners[5]], [corners[7]]])
    Cx = np.dot(np.linalg.inv(A), bx)
    Cy = np.dot(np.linalg.inv(A), by)
    geoCoords = []
    for pixel in pixels:
        geoX = Cx[0] * pixel[0] + Cx[1] * pixel[1] + Cx[2] * pixel[0] * pixel[1] + Cx[3]
        geoY = Cy[0] * pixel[0] + Cy[1] * pixel[1] + Cy[2] * pixel[0] * pixel[1] + Cy[3]
        geoCoords.append([round(geoX), round(geoY)])
    geoCoords = reprojectPolygon(geoCoords, projection,3413)
    return (np.array(geoCoords))




def solutionToCSV(glacierList, labels, frontIndices, csvOutputFolder, cornersList, projectionList,imageSizeList):
    for ll in range(len(labels)):
        glacier=glacierList[ll]
        frontSolution = imagePixelsToGeoCoords(frontIndices[ll], cornersList[ll], projectionList[ll], imageSizeList[ll])
        outputFile = glacier + ' ' + labels[ll] + ' Profile.csv'
        output = []
        for c in range(len(frontSolution)):
            output.append([frontSolution[c, 0], frontSolution[c, 1]])
        output=np.array(output)
        np.savetxt(csvOutputFolder+'/'+outputFile,output,delimiter=',')




#############################################################################################
# All of the functions are run here
#-- main function to get user input and make training data
def main():
    #-- Read the system arguments listed after the program
    long_options = ['indir=','glacier=']
    optlist,arglist = getopt.getopt(sys.argv[1:],'=I:G:',long_options)

    indir = ''
    step = 50
    for opt, arg in optlist:
        if opt in ('-I','--indir'):
            indir = os.path.expanduser(arg)
        elif opt in ('-G','--glacier'):
            glacier = os.path.expanduser(arg)

    #-- directory setup
    #- current directory
    current_dir = os.path.dirname(os.path.realpath(__file__))
    headDirectory = os.path.join(current_dir,'..','FrontLearning_data')

    glaciersFolder=os.path.join(headDirectory,'Glaciers')

   
    csvOutputFolder = os.path.join(glaciersFolder,glacier,'Front Locations','3413 new')
    #-- make output folders
    if (not os.path.isdir(csvOutputFolder)):
        os.mkdir(csvOutputFolder)

    labelList=generateLabelList(indir)
    glacierList = getGlacierList(labelList,glaciersFolder)

    print(len(labelList))
    print(len(glacierList))

    frontIndicesList=[]
    cornersList=[]
    projectionList=[]
    imageSizeList=[]
    for ind,label in enumerate(labelList[:2]):
        if glacierList[ind] != glacier:
            sys.exit('Glacier Mismatch!')

        print('%i of %i'%(ind+1,len(labelList)))
        print('Working on label '+label)
        im = Image.open(os.path.join(indir, label + '_Front.png')).convert('L').transpose(Image.FLIP_LEFT_RIGHT)

        corners,projection=obtainSceneCornersProjection(label,glaciersFolder,glacier)
        cornersList.append(corners)
        projectionList.append(projection)
        imageSizeList.append(im.size)

        boundary1pixels,boundary2pixels=fjordBoundaryIndices(glaciersFolder,glacier,corners,projection,im.size)
        # plotImageWithBoundaries(im,boundary1pixels,boundary2pixels)

        solutionIndices = leastCostSolution(im,boundary1pixels,boundary2pixels,step)
        #solutionIndices = np.array(np.where(np.array(im)==0.))
        #print(solutionIndices)
        frontIndicesList.append(solutionIndices)

        plotImageWithSolution(im,solutionIndices)

    solutionToCSV(glacierList, labelList, frontIndicesList, csvOutputFolder, cornersList, projectionList,imageSizeList)

if __name__ == '__main__':
    main()