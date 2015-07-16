#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
This function retrieves the values which describe a specified feature and calls the update_db script to insert them to the database

19/6/2014
IRSS 2014 @ NCSR DEMOKRITOS
AUTHORS: Kostas Tsiakas/Papakostas Michalis

'''
import numpy as np

import LBP_extraction as lbp
import rgbs_extraction as col
import HOG_extraction as hog


import insert_db as ins


# UPDATE ALL FEATURES OF AN OBJECT
def FeatureExtraction(img):
    
     visual_vector=[]
     
     lbp_vector=TextureVector(img) #texture
     visual_vector.extend(lbp_vector)
     
     rgbs_vector=ColorVector(img) #color
     for i in rgbs_vector:
        visual_vector.append(i[0])
     
     hog_vector=ShapeVector(img) #shape
     for j in hog_vector[0]:
       visual_vector.append(j)
     
     return visual_vector




##########________TEXTURE FEATURE RETRIEVAL_________#############
def  TextureVector(img):
    
 lbp_vector=lbp.LBP(img)
 return lbp_vector
 
 
 ##########________COLOR FEATURE RETRIEVAL_________#############
def  ColorVector(img):
    
 rgbs_vector=col.RGBS(img)
 return rgbs_vector


 ##########________SHAPE FEATURE RETRIEVAL_________#############
def  ShapeVector(img):
    
 hog_vector=hog.HOG(img)
 return hog_vector


