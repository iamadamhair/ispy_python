#!/usr/bin/python
import os
import itertools
import numpy as np
from scipy import linalg
import pylab as pl
import matplotlib as mpl
from sklearn import mixture
from sklearn.externals import joblib

def test(feature_vector, model_name):

	tags = []
	probabilities = []
	best_tags = []

	model_folder = os.getcwd()+'/'+model_name
	listing = os.listdir(model_folder)
	for model in listing:
    		if model.endswith('.pkl'):
			model_file = model_folder +'/'+model
			model_clone = joblib.load(model_file)
        		prob = model_clone.score([feature_vector])
			
			tags.append(model)
        		probabilities.append(prob[0])	
			print model + " -> " + str(prob[0]/1000000)
			

	probabilities=np.asarray(probabilities)  
      	ind=np.argpartition(probabilities,-10)[-10:] 	#get the indexes of the 10 most possible tags
      
      	ind=ind[np.argsort(probabilities[ind])] 	#sort these indexes regarding to their refered values

	for i in ind:
		#print tags[i]
          	best_tags.append(tags[i])  

	return best_tags
