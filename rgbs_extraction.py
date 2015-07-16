#!/usr/bin/env python

import cv2
import math
import numpy as np
from matplotlib import pyplot as plt

def normalize(v):
    norm=np.linalg.norm(v)
    if norm==0: 
       return v
    return v/norm


def  RGBS(img):

    image = img

    # grab the image channels, initialize the tuple of colors,
    # the figure and the flattened feature vector
    chans = cv2.split(image)
    colors = ("b", "g", "r")
    plt.figure()
    #plt.title("'Flattened' Color Histogram")
    #plt.xlabel("Bins")
    #plt.ylabel("# of Pixels")
    features = []
     
    # loop over the image channels
    for (chan, color) in zip(chans, colors):
        # create a histogram for the current channel and
        # concatenate the resulting histograms for each/hist.
        # channel
        hist = cv2.calcHist([chan], [0], None, [25], [0, 256])
        hist = hist/hist.max()

        features.extend(hist)

    #### CALCULATE HSV HISTOGRAM ########################

    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    #hist = cv2.calcHist( [hsv], [0, 1], None, [180, 256], [0, 180, 0, 256] )
    chans = cv2.split(hsv)  # take the S channel 

    S = chans[1]

    hist2 = cv2.calcHist([S], [0], None, [25], [0, 256])
    hist2 = normalize(hist2)

    features.extend(hist2) 
    #plt.plot(features)
    #plt.show()

    return np.asarray(features)
