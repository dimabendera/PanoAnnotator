import sys
import numpy as np
import math

from PyQt5.QtGui import QImage, QPixmap
from skimage import morphology, filters, draw, transform

import utils
import configs.Params as pm

def imageROI(data, lt, rb):

    regionDate = data[lt[0]:rb[0], lt[1]:rb[1]]
    return regionDate

def imageRegionMean(data, center, steps):

    lt, rb = imageRegionBox(center, steps, data.shape)
    roi = imageROI(data, lt, rb)
    mean = np.nanmean(roi)
    return mean

def imageRegionBox(center, steps, size):

    lt = (center[0] - steps[0], center[1] - steps[1])
    rb = (center[0] + steps[0], center[1] + steps[1])

    lt = checkImageBoundary(lt, size)
    rb = checkImageBoundary(rb, size)
    return lt, rb

def checkImageBoundary(pos, size):
        
    x = sorted([0, pos[0], size[0]])[1]
    y = sorted([0, pos[1], size[1]])[1]
    return (x, y)

def data2Pixmap(data):

    imgData = data * 255
    imgData = imgData.astype(dtype=np.uint8)
    image = QImage(imgData, data.shape[1], data.shape[0], 
                    QImage.Format_RGB888)
    pixmap = QPixmap.fromImage(image)
    return pixmap

def imageDilation(data, rad):

    ans = np.zeros(data.shape, dtype=np.float)
    for i in range(data.shape[2]):
        channel = data[:,:,i]
        ans[:,:,i] = morphology.dilation(channel, 
                            morphology.diamond(rad))
    return ans

def imageGaussianBlur(data, sigma):

    ans = np.zeros(data.shape, dtype=np.float)
    for i in range(data.shape[2]):
        channel = data[:,:,i]
        ans[:,:,i] = filters.gaussian(channel, sigma)
    return ans

def imagesMSE(data1, data2, size):

    data1r = transform.resize(data1, size, mode='constant')
    data2r = transform.resize(data2, size, mode='constant')

    mse = 0
    for i in range(3):
        err = np.sum((data1r[:,:,i] - data2r[:,:,i]) ** 2)
        err /= float(size[0]*size[1])
        mse += err
        #print(err)
    return mse
    

def imageDrawLine(data, p1, p2, color):

    rr, cc = draw.line(p1[1],p1[0],p2[1],p2[0])
    draw.set_color(data, [rr,cc], list(color))

def imageDrawPolygon(data, points, color):

    X = np.array([p[0] for p in points])
    Y = np.array([p[1] for p in points])
    rr, cc = draw.polygon(Y,X)
    draw.set_color(data, [rr,cc], list(color))

def imageDrawWallFace(data, wall):

    size = (data.shape[1], data.shape[0])
    axis = utils.vectorAlignAxis(wall.normal)
    color = axis2color(axis)

    isCrossUp, ul, ur = wall.edges[0].checkCross()
    isCrossDown, dl, dr = wall.edges[2].checkCross()

    polygon = []
    for edge in wall.edges:
        for point in edge.coords:
            polygon.append(utils.coords2pos(point, size))

    if not (isCrossUp or isCrossDown):
        utils.imageDrawPolygon(data, polygon, color)
    else:
        sampleNum = len(wall.edges[0].sample)
        iur = wall.edges[0].sample.index(ur)
        iul = iur + 1
        idr = wall.edges[2].sample.index(dr) + sampleNum*2
        idl = idr - 1
        uh = int((polygon[iur][1] + polygon[iul][1])/2)
        dh = int((polygon[idr][1] + polygon[idl][1])/2)

        polygon1 = polygon[:iur]+[(size[0],uh),(size[0],dh)]+polygon[idr:]
        polygon2 = [(0,uh)]+polygon[iul:idl]+[(0,dh)]
        utils.imageDrawPolygon(data, polygon1, color)
        utils.imageDrawPolygon(data, polygon2, color)

def imageDrawWallEdge(data, wall):

    size = (data.shape[1], data.shape[0])
    for edge in wall.edges:
        axis = utils.vectorAlignAxis(edge.vector)
        color = axis2color(axis)
        for i in range(len(edge.coords)-1):
            isCross, l, r = utils.pointsCrossPano(edge.sample[i],
                                                edge.sample[i+1])
            if not isCross:
                pos1 = utils.coords2pos(edge.coords[i], size)
                pos2 = utils.coords2pos(edge.coords[i+1], size)
                utils.imageDrawLine(data, pos1, pos2, color)
            else:
                lpos = utils.coords2pos(utils.xyz2coords(l), size)
                rpos = utils.coords2pos(utils.xyz2coords(r), size)
                ch = int((lpos[1] + rpos[1])/2)
                utils.imageDrawLine(data, lpos, (0,ch), color)
                utils.imageDrawLine(data, rpos, (size[0],ch), color)

def axis2color(axis):

    if axis == 0:
        color = (0,0,1)
    elif axis == 1:
        color = (1,0,0)
    elif axis == 2:
        color = (0,1,0)
    return color




