#!/usr/bin/python

import numpy as np
import feature_update2 as feat
import os
from sql_driver import sql_driver
import cv2
import db_data_retrieval as train
import re

def Model_Retrain(stopping_point, con):
	with con:
	    cur = con.cursor()

	# for all segmented objects insert their feature vectors to the DB

	game_folders = []
	folder = os.getcwd()+"/GAMES"

	#game_folders_idx = range(25,30) #RETRAIN EVERY 5 NEW PHOTOS
	game_folders_idx = range(stopping_point-2,stopping_point-1) #THE GAME ID YOU WANT TO USE FOR RETRAINING
	for game in game_folders_idx:
		game_folder = folder + '/Game' + str(game+1)
		game_folders.append(game_folder)
	
	for game in game_folders:
		Objects = os.listdir(game)
		for obj in Objects:
			if obj.endswith('.jpg'):
				temp =  str(os.path.splitext(obj)[0])
				objID = int(temp[3:])
				#print temp, objid
				print game
				image_path = game + '/obj' + str(objID) + ".jpg"
				print image_path
				img = cv2.imread(image_path)
				feat.FeatureUpdate(con,img,str(objID))
	con.commit()

	#train.CreateFeatureTable(cur,stopping_point)	
		
		
	
