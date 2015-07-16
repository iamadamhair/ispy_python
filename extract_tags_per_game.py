#!/usr/bin/python
import os
import test_model 
import cv2
import test_features_extraction as test_ft
import numpy as np

folder = os.getcwd()+"/GAMES"
Games = os.listdir(folder)

def Extract_Tags(gameID):
	tags_per_game = []
	game_folder = folder + '/Game' + str(gameID)

	filename = game_folder + '/tags.txt' 
	#print filename
	f = open(filename, "w")

	model = 'GMM_model_' + str(gameID)


	object_files = os.listdir(game_folder)
	for objects in object_files:
		if objects.endswith('.jpg'):
			image_path = game_folder + '/' + objects
			#print image_path 
			img = cv2.imread(image_path)
			feature_vector = test_ft.FeatureExtraction(img)
			tags = test_model.test(feature_vector, model)
			for tag in tags:
				T = tag.split('_', 1)[0]
				if T not in tags_per_game:
					tags_per_game.append(T)
					print T
					f.write(T +'\n')	
	
	print game_folder 
	

#Extract_Tags(1)
