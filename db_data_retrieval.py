#!/usr/bin/python
# -*- coding: utf-8 -*-



'''
This function communicates with the database and when called, updates the
values describing the specific feature vector

19/6/2014
IRSS 2014 @ NCSR DEMOKRITOS
AUTHORS: Kostas Tsiakas/Papakostas Michalis

'''

import numpy as np

import LBP_extraction as lbp
import insert_db as ins
import gmm_training as model


############ CREATE FEATURE VECTOR FROM THE DATABASE ##########################
def RetrieveFeatureVector(cur,obs_id,feature_info,start,end):

 feature_vector=[]

 for index in xrange(start,end):  
     feature_vector.append(feature_info[index][1])
     # print feature_vector[0]
 return feature_vector

######################### RETRIEVE FEATURE TABLE FOR EACH TAG #####################

def CreateFeatureTable(cur,gameID):
 
 np.set_printoptions(threshold='nan')

 #get all the different tags available
 cur.execute("SELECT DISTINCT(tag) FROM TagInfo") 
 tags=cur.fetchall()
 
 
 #for each tag we select all the observation_ids that are related to it
 for index, tag in enumerate(tags): 
  
  feature_matrix=[]#initialize feature matrix for each different tag

  #get all the different observations/objects that are related to a given tag 
  cur.execute("SELECT DISTINCT(observation_id) FROM TagInfo WHERE tag='{0}'".format(tag[0]))
  tag_obs_ids=cur.fetchall()
  
  
  #for every observation/object of this spesific tag
  for obs_id in tag_obs_ids: 
  
   #get the number of different captures/feature-vectors for each observation/object
   cur.execute("SELECT COUNT(*) FROM FeatureInfo WHERE feature_id='0' AND observation_id='{0}'".format(obs_id[0]))
   num_of_images_per_oservation=cur.fetchall()
   #print num_of_images_per_oservation
   
   #get all the feature vectors that refer to a tag given an object in a python.tuple
   cur.execute("SELECT feature_id,feature_value FROM FeatureInfo WHERE observation_id='{0}'".format(obs_id[0]))
   feature_info=cur.fetchall()
   
   #get the length of each feature-vector
   vv_seperator=len(feature_info)/num_of_images_per_oservation[0][0]
   #print vv_seperator
   
   
   new_fv=0 #flag to show when a feature vector given a capture starts (index in feature_info tuple)
   end_of_fv=vv_seperator#flag to show when a feature vector given a capture ends (index in feature_info tuple)
   
   #for each capture of an object
   for capture_id in xrange(0,num_of_images_per_oservation[0][0]): 
   
    feature_vector=RetrieveFeatureVector(cur,obs_id[0],feature_info,new_fv,end_of_fv) #create a feature vector given a capture 
    print feature_vector
    new_fv=new_fv+vv_seperator #update starting index of the vector
    end_of_fv=end_of_fv+vv_seperator #update ending index of the vector
    #print tag[0],new_fv,end_of_fv
    feature_matrix.append(feature_vector) #insert feature vectors into a matrix for each tag
    
  #print tag[0],len(np.asarray(feature_matrix))

  # if obs_id[0]=='83':
  #print obs_id[0],'asdfsdf'
  feature_matrix=np.asarray(feature_matrix)
  model.ModelTraining(tag[0],feature_matrix,gameID) #training the model
  
  #if tag[0] =='handle':
  #    return feature_matrix
  
  #f = open('feature_vectors/'+tag[0]+'.txt', 'w')
  #f.write(str(feature_matrix))
  
  #if index==100:
   #   break;
    
    

    
    
    
    
