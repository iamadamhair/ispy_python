#!/usr/bin/python
import os
import math
import time
import csv
from sql_driver import sql_driver
import numpy as np 
import random
import sys
import operator
#from nolearn.dbn import DBN
from sklearn.metrics import classification_report
from sklearn.svm import SVC

import matplotlib
matplotlib.use('Agg')

import cv2
import test_features_extraction as test_ft
from sklearn.externals import joblib
import gmm_training as model
from sklearn import mixture

import feature_update2 as feat
import model_retraining_for_game as retrain
import object_learning_for_game as first
import extract_tags_per_game as extract
import warnings
    

def fill_featureinfo(con):
    for game_id in range(0,31):
	first.Object_Learning(game_id, con)


def model_training_1(game_id, cursor):
    if game_id == 0:
	for tag in range(1,290):
	    feature_vector = []
	    for obj_id in range(1,18):
		if get_t(obj_id, tag, cursor) > 2:
		    folder = os.getcwd()+"/cropped_ims"
		    objID = x
		    # for each object folder, load all images
		    current_folder = folder + "/obj" + str(obj_id)
		    captures =  os.listdir(current_folder)
		    for image in captures:
			    image_path = current_folder + "/" + image
			    img = cv2.imread(image_path)
				
    elif game_id in range(1,16):
	pass
    else:
	pass


def model_evaluation_1(con, game_id):
#    folder = os.getcwd() + '/GAMES/Game' + str(game_id)
#    captures =  os.listdir(folder)
#    for image in captures:
#	print image
#	if image.endswith('.jpg'):
#		objID = image[3:5]
#		if '.' in objID:
#		    objID = objID[0:1]
#		img = cv2.imread(folder + "/" + image)
#		vector = feat.get_feature_vector(con,img)
    with con:
	cursor = con.cursor()
    
    Pi = gen_image_probabilities_evaluation(game_id, cursor)
    with open("evaluation1.txt", "a") as myfile:
	myfile.write(str(game_id) + " game: \n")
	for obj in range(0,17):
	    for tag in range(0,289):
		if Pi[obj][tag] >= 0:
		    myfile.write(str(obj + 1) + " object: " + str(tag+ 1) + " -> " + get_tag(tag+1,cursor) + " tag: " + str(Pi[obj][tag]) + " score \n")
	myfile.write("\n")
    myfile.close() 
    
    
def model_evaluation_2(con, game_id):
    with con:
	cursor = con.cursor()
    
    Pi = gen_image_probabilities_evaluation(game_id, cursor)
    with open("evaluation2.txt", "a") as myfile:
	myfile.write(str(game_id) + " game: \n")
	for obj in range(0,17):
	    for tag in range(0,289):
		if Pi[obj][tag] >= 0:
		    myfile.write(str(obj + 1) + " object: " + str(tag+ 1) + " -> " + get_tag(tag+1,cursor) + " tag: " + str(Pi[obj][tag]) + " score \n")
	myfile.write("\n")
    myfile.close() 
    

def model_evaluation_3(con, game_id):
    with con:
	cursor = con.cursor()
    
    Pi = gen_image_probabilities_evaluation(game_id, cursor)
    with open("evaluation3.txt", "a") as myfile:
	myfile.write(str(game_id) + " game: \n")
	for obj in range(0,17):
	    for tag in range(0,289):
		if Pi[obj][tag] >= 0:
		    myfile.write(str(obj + 1) + " object: " + str(tag+ 1) + " -> " + get_tag(tag+1,cursor) + " tag: " + str(Pi[obj][tag]) + " score \n")
	myfile.write("\n")
    myfile.close() 


def build_pqd_without_object(cursor, con, tags, skip_object, skip_tags):
    cursor.execute("DELETE FROM Pqd")
    con.commit()
    
    probabilityD = [0,0,0,0,0,0,0]
    denominator = [0,0,0,0,0,0,0]
            
    for objectID in range(1,18):
	if objectID != skip_object:
	    print objectID
	    for tag in range(0, 289):
		if tags[tag] not in skip_tags:
		    cursor.execute("SELECT * FROM Descriptions WHERE description like '%" + tags[tag] + "%' AND objectID = " + str(objectID))
		    T = len(cursor.fetchall())
		
		    #T is a based on a tag and an object description. T is how many times a tag is used in an object's description. It can be 0-6
		    
		    cursor.execute("SELECT * FROM QuestionAnswers WHERE tag = '" + tags[tag] + "' AND object = " + str(objectID) + " AND answer = TRUE")
		    count = len(cursor.fetchall())
		    
		    #count is the number of times someone answered yes to a tag/object pair
		    
		    cursor.execute("SELECT * FROM QuestionAnswers WHERE tag = '" + tags[tag] + "' AND object = " + str(objectID))
		    D = len(cursor.fetchall())
		    
		    #D is the total number of times a tag/object pair has been asked (yesses and nos)
		    
		    probabilityD[T] = probabilityD[T] + count
		    denominator[T] = denominator[T] + D
		    #For the T value based on the specific tag/object pair, update the probability of all tag/object pairs with the same T value
	        
    for freq in range(0,7):
        #This puts the sum of the yes answers and the total answers into the row that corresponds with the T value
        cursor.execute("INSERT INTO Pqd (t_value, yes_answers, total_answers) VALUES (%s, %s, %s)", (freq, probabilityD[freq], denominator[freq]))
        con.commit()
        print probabilityD[freq]
	
    
def build_pqd(cursor, con, tags):
    # Pqd is the probability that an the answer will be yes to a keyword asked about an object where the keyword shows up X number of times in the descriptions
    # Summed over all objects where a keyword shows up X number of times
    
    probabilityD = [0,0,0,0,0,0,0]
    denominator = [0,0,0,0,0,0,0]
            
    for objectID in range(1,18):
        print objectID
        for tag in range(0, 289):
            cursor.execute("SELECT * FROM Descriptions WHERE description like '%" + tags[tag] + "%' AND objectID = " + str(objectID))
            T = len(cursor.fetchall())
        
	    #T is a based on a tag and an object description. T is how many times a tag is used in an object's description. It can be 0-6
	    
            cursor.execute("SELECT * FROM QuestionAnswers WHERE tag = '" + tags[tag] + "' AND object = " + str(objectID) + " AND answer = TRUE")
            count = len(cursor.fetchall())
            
	    #count is the number of times someone answered yes to a tag/object pair
	    
            cursor.execute("SELECT * FROM QuestionAnswers WHERE tag = '" + tags[tag] + "' AND object = " + str(objectID))
            D = len(cursor.fetchall())
	    
	    #D is the total number of times a tag/object pair has been asked (yesses and nos)
            
            probabilityD[T] = probabilityD[T] + count
            denominator[T] = denominator[T] + D
	    #For the T value based on the specific tag/object pair, update the probability of all tag/object pairs with the same T value
	        
    for freq in range(0,7):
        #This puts the sum of the yes answers and the total answers into the row that corresponds with the T value
        cursor.execute("INSERT INTO Pqd (t_value, yes_answers, total_answers) VALUES (%s, %s, %s)", (freq, probabilityD[freq], denominator[freq]))
        con.commit()
        print probabilityD[freq]


def add_answerset(cursor, gameID, con):
    for objectID in range(1,18):
	cursor.execute("SELECT answer FROM Answers WHERE objectID = %s AND answerSet = %s", (objectID, gameID))
	answers = cursor.fetchall()
	for qid in range(1,290):
	    cursor.execute("INSERT INTO answers (qid, oid, answer) VALUES (%s, %s, %s)", (qid, objectID, answers[qid-1][0]))
    con.commit()


def copy_into_answers(cursor, tags):
    # QuestionAnswers holds just the answer set data
    # Copies the pure data into a table that will be appended to throughout gameplay
    
    cursor.execute("SELECT tag, answer, object from QuestionAnswers")
    results = cursor.fetchall()
    
    for result in results:
	cursor.execute("SELECT id from Tags where tag = %s", (result[0]))
	qid = cursor.fetchone()[0]
	cursor.execute("INSERT INTO answers (qid, oid, answer) VALUES (%s, %s, %s)", (qid, result[2], result[1]))
   
   
def RetrieveFeatureVector(feature_info,start,end):

    feature_vector=[]
   
    for index in xrange(start,end):  
	feature_vector.append(feature_info[index][1])
    return feature_vector


def test_object_classifiers_svm(cursor):    
    #for i in range(0, len(vectors)):
    #    print "Model " + str(i)
    #    for j in range(0, len(vectors)):
    #	print models[i].predict(vectors[j])
    
    models = []
    
    for objectID in range(1,18):
	model_folder = os.getcwd() + '/object_classifiers_SVM/' + str(objectID) + '_model.pkl'
	model_clone = joblib.load(model_folder)
	models.append(model_clone)
    
    for objid in range(0,len(models)):
	print objid
	expected = []
	vectors = []
	predicted = []
	for x in range(1,18):
	    #for img in range(1,8):
	    cursor.execute("SELECT COUNT(*) FROM FeatureInfo WHERE feature_id='0' AND observation_id='{0}'".format(x))
	    num_of_images_per_observation=cursor.fetchone()[0]
	    cursor.execute("SELECT feature_id,feature_value FROM FeatureInfo WHERE observation_id='{0}'".format(x))
	    feature_info=cursor.fetchall()
	    
	    vv_seperator=len(feature_info)/num_of_images_per_observation
	    
	    new_fv=0 #flag to show when a feature vector given a capture starts (index in feature_info tuple)
	    end_of_fv=vv_seperator#flag to show when a feature vector given a capture ends (index in feature_info tuple)
     
	    for capture_id in xrange(0,num_of_images_per_observation): 
		feature_vector=RetrieveFeatureVector(feature_info,new_fv,end_of_fv) #create a feature vector given a capture 
		new_fv=new_fv+vv_seperator #update starting index of the vector
		end_of_fv=end_of_fv+vv_seperator #update ending index of the vector
		vectors.append(feature_vector) #insert feature vectors into a matrix for each tag
		#vectors.append(test_ft.FeatureExtraction(image))
		if objid+1 == x:
		    expected.append(1)
		else:
		    expected.append(0)
	
	for i in range(0,len(expected)):
	    predicted.append(models[objid].predict(vectors[i]))
	
	expected = np.asarray(expected)
	predicted = np.asarray(predicted)
	print classification_report(expected, predicted)
    

def test_object_classifiers(cursor):

#    results = []
#    for x in range(1,18):
#	image_path = os.getcwd() + '/test_images/' + str(x) + '/1.jpg'
#	image = cv2.imread(image_path)
#	image_path = '/local2/awh0047/iSpy/ispy_python_old/cropped_ims/obj' + str(x) + '/3.jpg'
#	image = cv2.imread(image_path)
##	image_path = os.getcwd() + '/test_images/' + str(x) + '/2.jpg'
##	image2 = cv2.imread(image_path)
##	image_path = os.getcwd() + '/test_images/' + str(x) + '/3.jpg'
##	image3 = cv2.imread(image_path)
##	image_path = os.getcwd() + '/test_images/' + str(x) + '/4.jpg'
##	image4 = cv2.imread(image_path)
##	image_path = os.getcwd() + '/test_images/' + str(x) + '/5.jpg'
##	image5 = cv2.imread(image_path)
##
#	feature_vector = []
#	feature_vector.append(test_ft.FeatureExtraction(image))
#	#feature_vector.append(test_ft.FeatureExtraction(image2))
#	#feature_vector.append(test_ft.FeatureExtraction(image3))
#	#feature_vector.append(test_ft.FeatureExtraction(image4))
#	#feature_vector.append(test_ft.FeatureExtraction(image5))
#	#feature_vector = np.asarray(feature_vector)
#	#
#	model_folder = os.getcwd() + '/object_classifiers/' + str(x+1) + '_classifier.pkl'
#	model_clone = joblib.load(model_folder)
#	#
#	##dbn_folder = os.getcwd() + '/object_classifiers/' + str(x) + '_dbn_classifier.pkl'
#	##dbn_clone = joblib.load(dbn_folder)
#	#
#	#preds = model_clone.predict(feature_vector)
#	#dbn_preds = dbn_clone.predict(np.atleast_2d(feature_vector))
#	
#	#with open("results.txt", "a") as myfile:
#	#    myfile.write("Object " + str(x) + ": \n")
#	#    myfile.write("GMM\n")
#	#    myfile.write(classification_report([1,1,0,0,1], preds))
#	#    #myfile.write("\n")
#	#    #myfile.write("DBN\n")
#	#    #myfile.write(classification_report([1,1,0,0,1], dbn_preds))
#	#    myfile.write("\n\n")
#	print len(feature_vector)
#	print len(feature_vector[0])
#	results.append(identify_objects(feature_vector, x))
##    return results 
    models = []
    
    for objectID in range(1,18):
	model_folder = os.getcwd() + '/object_classifiers/' + str(objectID) + '_classifier.pkl'
	model_clone = joblib.load(model_folder)
	models.append(model_clone)
#    
    for objid in range(0,17):
	print objid
	expected = []
    	predicted = []
	vectors = []
	for i in range(1,18):
	    feature_matrix = []
	    feature_matrix_labels = []
	    count = 0
	    #for obs_id in range(1,18):
	    object_matrix = []
	    cursor.execute("SELECT COUNT(*) FROM FeatureInfo WHERE feature_id='0' AND observation_id='{0}'".format(i))
	    num_of_images_per_observation=cursor.fetchone()[0]
	    
	    cursor.execute("SELECT feature_id,feature_value FROM FeatureInfo WHERE observation_id='{0}'".format(i))
	    feature_info=cursor.fetchall()
	    
	    vv_seperator=len(feature_info)/num_of_images_per_observation
	    
	    new_fv=0 #flag to show when a feature vector given a capture starts (index in feature_info tuple)
	    end_of_fv=vv_seperator#flag to show when a feature vector given a capture ends (index in feature_info tuple)
     
	    for capture_id in xrange(0,num_of_images_per_observation):
		temp = []
		feature_vector=RetrieveFeatureVector(feature_info,new_fv,end_of_fv) #create a feature vector given a capture 
		new_fv=new_fv+vv_seperator #update starting index of the vector
		end_of_fv=end_of_fv+vv_seperator #update ending index of the vector
		temp.append(feature_vector)
		vectors.append(temp) #insert feature vectors into a matrix for each tag
		if objid + 1 == i:
		    expected.append(1)
		else:
		    expected.append(0)
	    #    else:
	    #	feature_matrix_labels.append(0)
#

	for i in range(0,len(expected)):
	    predicted.append(models[objid].predict(vectors[i])[0])
	
	#expected = np.asarray(expected)
	#predicted = np.asarray(predicted)
	print classification_report(expected, predicted)


def identify_objects(feature_vector, object_id):
    answers = []
    models = []
    
    for objectID in range(1,18):
	model_folder = os.getcwd() + '/object_classifiers/' + str(objectID) + '_classifier.pkl'
	model_clone = joblib.load(model_folder)
	models.append(model_clone)
	
	answers.append(model_clone.predict(feature_vector))
	print model_clone.predict(feature_vector)
    
    bestGuess = 0
    bestPred = -100000000
    
    answers = np.asarray(answers)
    if sum(answers) > 1:
	for objectID in range(1,18):
	    if answers[objectID-1][0] == 1:
		score = models[objectID-1].score(feature_vector)
		if score[0] > bestPred:
		    bestGuess = objectID
		    bestPred = score[0]
	return bestGuess
    elif sum(answers) == 0:
	bestPred = -1
    else:
	for objectID in range(1,18):
	    if answers[objectID-1] == 1:
		bestPred = objectID
		
    return bestPred


def test_object_classifiers_over_time(cursor,con):
    for i in range(0, 31):
	first.Object_Learning(i,con)
	build_object_classifiers(cursor,con)
	results = test_object_classifiers()
	correct = 0
	with open("agreement.txt", "a") as myfile:
            myfile.write(str(i) + "\n")
            for i in range(0,len(results)):
                myfile.write("Object: " + str(i+1) + " Guessed: " + str(results[i]) + "\n")
		if results[i] == i+1:
		    correct += 1
            myfile.write("Identified " + str(correct/float(len(results))) + " of objects correctly \n")
    

def build_object_classifiers_svm(cursor, con):
    # Builds SVM classifiers for each object using available images
    # Uses positive and negative examples in training

    for oid in range(1,18):
	feature_matrix = []
	labels = []
	count = 0
	#for obs_id in range(1,18):
	object_matrix = []
	cursor.execute("SELECT COUNT(*) FROM FeatureInfo WHERE feature_id='0' AND observation_id='{0}'".format(oid))
	num_of_images_per_observation=cursor.fetchone()[0]
	print num_of_images_per_observation
	cursor.execute("SELECT feature_id,feature_value FROM FeatureInfo WHERE observation_id='{0}'".format(oid))
	feature_info=cursor.fetchall()
	
	vv_seperator=len(feature_info)/num_of_images_per_observation
	
	new_fv=0 #flag to show when a feature vector given a capture starts (index in feature_info tuple)
	end_of_fv=vv_seperator#flag to show when a feature vector given a capture ends (index in feature_info tuple)
 
	for capture_id in xrange(0,num_of_images_per_observation): 
	    feature_vector=RetrieveFeatureVector(feature_info,new_fv,end_of_fv) #create a feature vector given a capture 
	    new_fv=new_fv+vv_seperator #update starting index of the vector
	    end_of_fv=end_of_fv+vv_seperator #update ending index of the vector
	    feature_matrix.append(feature_vector) #insert feature vectors into a matrix for each tag
	    labels.append(1)
	
	for i in range(0,1):
	
	    rand_obj = np.random.randint(1,18)
		
	    cursor.execute("SELECT COUNT(*) FROM FeatureInfo WHERE feature_id='0' AND observation_id='{0}'".format(rand_obj))
	    num_of_images_per_observation=cursor.fetchone()[0]
    
	    cursor.execute("SELECT feature_id,feature_value FROM FeatureInfo WHERE observation_id='{0}'".format(rand_obj))
	    feature_info=cursor.fetchall()
	    
	    vv_seperator=len(feature_info)/num_of_images_per_observation
	    new_fv=0 #flag to show when a feature vector given a capture starts (index in feature_info tuple)
	    end_of_fv=vv_seperator#flag to show when a feature vector given a capture ends (index in feature_info tuple)
	    
	    for capture_id in xrange(0,num_of_images_per_observation): 
		feature_vector=RetrieveFeatureVector(feature_info,new_fv,end_of_fv) #create a feature vector given a capture 
		new_fv=new_fv+vv_seperator #update starting index of the vector
		end_of_fv=end_of_fv+vv_seperator #update ending index of the vector
		feature_matrix.append(feature_vector) #insert feature vectors into a matrix for each tag
		labels.append(0)
	
	print len(feature_matrix)
	
	svm = SVC()
	svm.fit(feature_matrix, labels)
	joblib.dump(svm, 'object_classifiers_SVM/' + str(id) + '_model.pkl') #NAME OF FOLDER TO SAVE RETRAINED SVM MODELS


def build_specific_object_classifier(cursor, con, oid, gameID):
    feature_matrix = []
    labels = []
    count = 0
    #for obs_id in range(1,18):
    object_matrix = []
    cursor.execute("SELECT COUNT(*) FROM FeatureInfo WHERE feature_id='0' AND observation_id='{0}' AND game_id <='{1}'".format(oid, gameID))
    num_of_images_per_observation=cursor.fetchone()[0]
    print num_of_images_per_observation
    cursor.execute("SELECT feature_id,feature_value FROM FeatureInfo WHERE observation_id='{0}' AND game_id <='{1}'".format(oid, gameID))
    feature_info=cursor.fetchall()
    
    vv_seperator=len(feature_info)/num_of_images_per_observation
    
    new_fv=0 #flag to show when a feature vector given a capture starts (index in feature_info tuple)
    end_of_fv=vv_seperator#flag to show when a feature vector given a capture ends (index in feature_info tuple)

    for capture_id in xrange(0,num_of_images_per_observation): 
	feature_vector=RetrieveFeatureVector(feature_info,new_fv,end_of_fv) #create a feature vector given a capture 
	new_fv=new_fv+vv_seperator #update starting index of the vector
	end_of_fv=end_of_fv+vv_seperator #update ending index of the vector
	feature_matrix.append(feature_vector) #insert feature vectors into a matrix for each tag
	labels.append(1)
    
    for i in range(0,1):
    
	rand_obj = np.random.randint(1,18)
	    
	cursor.execute("SELECT COUNT(*) FROM FeatureInfo WHERE feature_id='0' AND observation_id='{0}' AND game_id <='{1}'".format(rand_obj, gameID))
	num_of_images_per_observation=cursor.fetchone()[0]

	cursor.execute("SELECT feature_id,feature_value FROM FeatureInfo WHERE observation_id='{0}' AND game_id <='{1}'".format(rand_obj, gameID))
	feature_info=cursor.fetchall()
	
	vv_seperator=len(feature_info)/num_of_images_per_observation
	new_fv=0 #flag to show when a feature vector given a capture starts (index in feature_info tuple)
	end_of_fv=vv_seperator#flag to show when a feature vector given a capture ends (index in feature_info tuple)
	
	for capture_id in xrange(0,num_of_images_per_observation): 
	    feature_vector=RetrieveFeatureVector(feature_info,new_fv,end_of_fv) #create a feature vector given a capture 
	    new_fv=new_fv+vv_seperator #update starting index of the vector
	    end_of_fv=end_of_fv+vv_seperator #update ending index of the vector
	    feature_matrix.append(feature_vector) #insert feature vectors into a matrix for each tag
	    labels.append(0)
    
    print len(feature_matrix)
    
    svm = SVC()
    svm.fit(feature_matrix, labels)
    joblib.dump(svm, 'object_classifiers_SVM/' + str(id) + '_model.pkl') #NAME OF FOLDER TO SAVE RETRAINED SVM MODELS


def build_object_classifiers(cursor, con):
    # Take all object images available and use them to build GMM classifiers for each object
    # Only positive examples
    
    for oid in range(1,18):
	feature_matrix = []
	feature_matrix_labels = []
	count = 0
	#for obs_id in range(1,18):
	object_matrix = []
	cursor.execute("SELECT COUNT(*) FROM FeatureInfo WHERE feature_id='0' AND observation_id='{0}'".format(oid))
	num_of_images_per_observation=cursor.fetchone()[0]
	
	cursor.execute("SELECT feature_id,feature_value FROM FeatureInfo WHERE observation_id='{0}'".format(oid))
	feature_info=cursor.fetchall()
	
	vv_seperator=len(feature_info)/num_of_images_per_observation
	
	new_fv=0 #flag to show when a feature vector given a capture starts (index in feature_info tuple)
	end_of_fv=vv_seperator#flag to show when a feature vector given a capture ends (index in feature_info tuple)
 
	for capture_id in xrange(0,num_of_images_per_observation): 
	    feature_vector=RetrieveFeatureVector(feature_info,new_fv,end_of_fv) #create a feature vector given a capture 
	    new_fv=new_fv+vv_seperator #update starting index of the vector
	    end_of_fv=end_of_fv+vv_seperator #update ending index of the vector
	    feature_matrix.append(feature_vector) #insert feature vectors into a matrix for each tag
	    #if id == obs_id:
	    feature_matrix_labels.append(1)
	#    else:
	#	feature_matrix_labels.append(0)
	#feature_matrix=np.asarray(feature_matrix)
	#feature_matrix_labels = np.asarray(feature_matrix_labels)
	print feature_matrix[0]
	#dbn = DBN([feature_matrix.shape[1], 300, 2], learn_rates = 0.3, learn_rate_decays = 0.9, epochs = 100, verbose = 0)
	#dbn.fit(feature_matrix, feature_matrix_labels)
	#joblib.dump(dbn, 'object_classifiers/' + str(id) + '_dbn_classifier.pkl')
		
	g = mixture.GMM(n_components=2, covariance_type = 'tied')
	g.fit(feature_matrix)
	joblib.dump(g, 'object_classifiers/' + str(id) +'_classifier.pkl') #NAME OF FOLDER TO SAVE THE NEW RETRAINED MODELS    


def build_model(cursor, con, gameID, stopping_point, evaluation_method, questions = {}, answers = {}, skip = {}):
#    for i in range(gameID, stopping_point):
#	retrain.Model_Retrain(i+1,con)
    
    # Builds models for all keywords using different methods (Currently only 1 and 3 work)
    # Method 3 has some brief notes about how it work
    np.set_printoptions(threshold='nan')
    
    #get all the different tags available
    cursor.execute("SELECT DISTINCT(tag) FROM TagInfoBk") 
    results=cursor.fetchall()
    
    tags = []
    for result in results:
	tags.append(result[0])
    
    count = 0
    # Builds models by using images where the answer set has a yes for the paring as a positive example
    if evaluation_method == 1:
	#for each tag we select all the observation_ids that are related to it
	for tag in tags: 
	    feature_matrix=[]#initialize feature matrix for each different tag
	    feature_matrix_labels = [] # Labels to indicate if the example is positive or negative
	    #cursor.execute("SELECT DISTINCT(observation_id) FROM TagInfoBk WHERE tag=%s",(tag))
	    cursor.execute("SELECT DISTINCT(observation_id) FROM TagInfoBk")
	    tag_obs_ids=cursor.fetchall()
	    cursor.execute('SELECT id FROM Tags WHERE tag = %s', (tag))
	    qid = cursor.fetchone()[0]
    
	    should_train = False
	    #for every observation/object of this spesific tag
	    for obs_id in tag_obs_ids:
		
		object_matrix = []
		T = get_t(obs_id[0], qid, cursor)
		if gameID == 0:
		    if T >= 3:
			should_train = True
			count = count + 1
			cursor.execute("SELECT COUNT(*) FROM FeatureInfo WHERE feature_id='0' AND observation_id='{0}' AND game_id='{1}' ".format(obs_id[0], gameID))
			num_of_images_per_oservation=cursor.fetchall()
			
			cursor.execute("SELECT feature_id,feature_value FROM FeatureInfo WHERE observation_id='{0}' AND game_id='{1}'".format(obs_id[0],gameID))
			feature_info=cursor.fetchall()
			
			vv_seperator=len(feature_info)/num_of_images_per_oservation[0][0]
			
			new_fv=0 #flag to show when a feature vector given a capture starts (index in feature_info tuple)
			end_of_fv=vv_seperator#flag to show when a feature vector given a capture ends (index in feature_info tuple)
		 
			for capture_id in xrange(0,num_of_images_per_oservation[0][0]): 
			    feature_vector=RetrieveFeatureVector(feature_info,new_fv,end_of_fv) #create a feature vector given a capture 
			    #print len(feature_vector)
			    new_fv=new_fv+vv_seperator #update starting index of the vector
			    end_of_fv=end_of_fv+vv_seperator #update ending index of the vector
			    feature_matrix.append(feature_vector) #insert feature vectors into a matrix for each tag
			
			feature_matrix_labels.append(1)
		else:
		#elif gameID < 16:
		    model_folder = os.getcwd() + '/GMM_model_777'
		    listing = os.listdir(model_folder)
		    has_model = []
		    for mod in listing:
			    if mod.endswith('.pkl'):
				model_clone = joblib.load(model_folder + '/' + mod)
				T = mod.split('_', 1)[0]
				T = T.lower()
				has_model.append(T)
		    for game in range(0, gameID+1):
			if tag.lower() in has_model:
			    if game == 0:
				should_train = True
				count = count + 1
				cursor.execute("SELECT COUNT(*) FROM FeatureInfo WHERE feature_id='0' AND observation_id='{0}' AND game_id='{1}' ".format(obs_id[0], game))
				num_of_images_per_oservation=cursor.fetchall()
				
				cursor.execute("SELECT feature_id,feature_value FROM FeatureInfo WHERE observation_id='{0}' AND game_id='{1}'".format(obs_id[0],game))
				feature_info=cursor.fetchall()
				
				vv_seperator=len(feature_info)/num_of_images_per_oservation[0][0]
				
				new_fv=0 #flag to show when a feature vector given a capture starts (index in feature_info tuple)
				end_of_fv=vv_seperator#flag to show when a feature vector given a capture ends (index in feature_info tuple)
			 
				for capture_id in xrange(0,num_of_images_per_oservation[0][0]): 
				    feature_vector=RetrieveFeatureVector(feature_info,new_fv,end_of_fv) #create a feature vector given a capture 
				    #print len(feature_vector)
				    new_fv=new_fv+vv_seperator #update starting index of the vector
				    end_of_fv=end_of_fv+vv_seperator #update ending index of the vector
				    feature_matrix.append(feature_vector) #insert feature vectors into a matrix for each tag
				
				feature_matrix_labels.append(1)
			    else:
				answer_data = np.genfromtxt(os.getcwd()+'/Answers/Game'+str(game)+'.csv',dtype=str, delimiter='\t')
				#cursor.execute("SELECT id FROM Tags where tag ='{0}'".format(tag))
				#tag_id = cursor.fetchone()[0]
				if answer_data[int(obs_id[0])-1][qid-1] == 'yes' or answer_data[int(obs_id[0])-1][qid-1] is 'yes':
				    should_train = True
				    count = count + 1
				    cursor.execute("SELECT COUNT(*) FROM FeatureInfo WHERE feature_id='0' AND observation_id='{0}' AND game_id='{1}' ".format(obs_id[0], game))
				    num_of_images_per_oservation=cursor.fetchall()
				    
				    cursor.execute("SELECT feature_id,feature_value FROM FeatureInfo WHERE observation_id='{0}' AND game_id='{1}'".format(obs_id[0],game))
				    feature_info=cursor.fetchall()
				    
				    vv_seperator=len(feature_info)/num_of_images_per_oservation[0][0]
				    
				    new_fv=0 #flag to show when a feature vector given a capture starts (index in feature_info tuple)
				    end_of_fv=vv_seperator#flag to show when a feature vector given a capture ends (index in feature_info tuple)
			     
				    for capture_id in xrange(0,num_of_images_per_oservation[0][0]): 
					feature_vector=RetrieveFeatureVector(feature_info,new_fv,end_of_fv) #create a feature vector given a capture 
					#print len(feature_vector)
					new_fv=new_fv+vv_seperator #update starting index of the vector
					end_of_fv=end_of_fv+vv_seperator #update ending index of the vector
					feature_matrix.append(feature_vector) #insert feature vectors into a matrix for each tag
				    
				    feature_matrix_labels.append(1)
					
	    if should_train:
		print len(feature_matrix)
		feature_matrix=np.asarray(feature_matrix)
		model.ModelTraining(tag, feature_matrix, 777) #training the model
    elif evaluation_method == 2:
	pass
    # Up to game 15, uses images that received a yes as positive and no as negative (All questions)
    # Beyond that, only uses keywords from the game (Much smaller subset)
    elif evaluation_method == 3:
	#for each tag we select all the observation_ids that are related to it
	for tag in tags:
	    if tag not in skip:
		feature_matrix=[]#initialize feature matrix for each different tag
		feature_matrix_labels = [] # Labels to indicate if the example is positive or negative
		#cursor.execute("SELECT DISTINCT(observation_id) FROM TagInfoBk WHERE tag=%s",(tag))
		cursor.execute("SELECT DISTINCT(observation_id) FROM TagInfoBk")
		tag_obs_ids=cursor.fetchall()
		cursor.execute('SELECT id FROM Tags WHERE tag = %s', (tag))
		qid = cursor.fetchone()[0]
	
		should_train = False
		#for every observation/object of this spesific tag
		for obs_id in tag_obs_ids:
		    
		    T = get_t(obs_id[0], qid, cursor)
		    # For game 0, if a tag has been used 3 or more times in the object descriptions, that object is used as a positive example
		    if gameID == 0:
			if T >= 3:
			    should_train = True
			    count = count + 1
			    cursor.execute("SELECT COUNT(*) FROM FeatureInfo WHERE feature_id='0' AND observation_id='{0}' AND game_id='{1}' ".format(obs_id[0], gameID))
			    num_of_images_per_oservation=cursor.fetchall()
			    
			    cursor.execute("SELECT feature_id,feature_value FROM FeatureInfo WHERE observation_id='{0}' AND game_id='{1}'".format(obs_id[0],gameID))
			    feature_info=cursor.fetchall()
			    
			    vv_seperator=len(feature_info)/num_of_images_per_oservation[0][0]
			    
			    new_fv=0 #flag to show when a feature vector given a capture starts (index in feature_info tuple)
			    end_of_fv=vv_seperator#flag to show when a feature vector given a capture ends (index in feature_info tuple)
		     
			    for capture_id in xrange(0,num_of_images_per_oservation[0][0]): 
				feature_vector=RetrieveFeatureVector(feature_info,new_fv,end_of_fv) #create a feature vector given a capture 
				#print len(feature_vector)
				new_fv=new_fv+vv_seperator #update starting index of the vector
				end_of_fv=end_of_fv+vv_seperator #update ending index of the vector
				feature_matrix.append(feature_vector) #insert feature vectors into a matrix for each tag
			    
				feature_matrix_labels.append(1)
			# An object is only a negative example if it is used 0 times
			elif T == 0:
			    count = count + 1
			    cursor.execute("SELECT COUNT(*) FROM FeatureInfo WHERE feature_id='0' AND observation_id='{0}' AND game_id='{1}' ".format(obs_id[0], gameID))
			    num_of_images_per_oservation=cursor.fetchall()
			    
			    cursor.execute("SELECT feature_id,feature_value FROM FeatureInfo WHERE observation_id='{0}' AND game_id='{1}'".format(obs_id[0],gameID))
			    feature_info=cursor.fetchall()
			    
			    vv_seperator=len(feature_info)/num_of_images_per_oservation[0][0]
			    
			    new_fv=0 #flag to show when a feature vector given a capture starts (index in feature_info tuple)
			    end_of_fv=vv_seperator#flag to show when a feature vector given a capture ends (index in feature_info tuple)
		     
			    for capture_id in xrange(0,num_of_images_per_oservation[0][0]): 
				feature_vector=RetrieveFeatureVector(feature_info,new_fv,end_of_fv) #create a feature vector given a capture 
				#print len(feature_vector)
				new_fv=new_fv+vv_seperator #update starting index of the vector
				end_of_fv=end_of_fv+vv_seperator #update ending index of the vector
				feature_matrix.append(feature_vector) #insert feature vectors into a matrix for each tag
			    
				feature_matrix_labels.append(0)
			print len(feature_matrix_labels)
		    # games up to 15 trained using all available answer data
		    elif gameID < 16:
			answer_data = np.genfromtxt(os.getcwd()+'/Answers/Game'+str(gameID)+'.csv',dtype=str, delimiter='\t')
			model_folder = os.getcwd() + '/GMM_model_777'
			listing = os.listdir(model_folder)
			has_model = []
			for mod in listing:
				if mod.endswith('.pkl'):
				    model_clone = joblib.load(model_folder + '/' + mod)
				    K = mod.split('_', 1)[0]
				    K = K.lower()
				    has_model.append(K)
			for game in range(0, gameID+1):
			    if tag.lower() in has_model:
				if game == 0:
				    if T >= 3:
					should_train = True
					count = count + 1
					cursor.execute("SELECT COUNT(*) FROM FeatureInfo WHERE feature_id='0' AND observation_id='{0}' AND game_id='{1}' ".format(obs_id[0], game))
					num_of_images_per_oservation=cursor.fetchall()
					
					cursor.execute("SELECT feature_id,feature_value FROM FeatureInfo WHERE observation_id='{0}' AND game_id='{1}'".format(obs_id[0],game))
					feature_info=cursor.fetchall()
					
					vv_seperator=len(feature_info)/num_of_images_per_oservation[0][0]
					
					new_fv=0 #flag to show when a feature vector given a capture starts (index in feature_info tuple)
					end_of_fv=vv_seperator#flag to show when a feature vector given a capture ends (index in feature_info tuple)
				 
					for capture_id in xrange(0,num_of_images_per_oservation[0][0]): 
					    feature_vector=RetrieveFeatureVector(feature_info,new_fv,end_of_fv) #create a feature vector given a capture 
					    #print len(feature_vector)
					    new_fv=new_fv+vv_seperator #update starting index of the vector
					    end_of_fv=end_of_fv+vv_seperator #update ending index of the vector
					    feature_matrix.append(feature_vector) #insert feature vectors into a matrix for each tag
					
					    feature_matrix_labels.append(1)
				    elif T == 0:
					should_train = True
					count = count + 1
					cursor.execute("SELECT COUNT(*) FROM FeatureInfo WHERE feature_id='0' AND observation_id='{0}' AND game_id='{1}' ".format(obs_id[0], game))
					num_of_images_per_oservation=cursor.fetchall()
					
					cursor.execute("SELECT feature_id,feature_value FROM FeatureInfo WHERE observation_id='{0}' AND game_id='{1}'".format(obs_id[0],game))
					feature_info=cursor.fetchall()
					
					vv_seperator=len(feature_info)/num_of_images_per_oservation[0][0]
					
					new_fv=0 #flag to show when a feature vector given a capture starts (index in feature_info tuple)
					end_of_fv=vv_seperator#flag to show when a feature vector given a capture ends (index in feature_info tuple)
				 
					for capture_id in xrange(0,num_of_images_per_oservation[0][0]): 
					    feature_vector=RetrieveFeatureVector(feature_info,new_fv,end_of_fv) #create a feature vector given a capture 
					    #print len(feature_vector)
					    new_fv=new_fv+vv_seperator #update starting index of the vector
					    end_of_fv=end_of_fv+vv_seperator #update ending index of the vector
					    feature_matrix.append(feature_vector) #insert feature vectors into a matrix for each tag
					
					    feature_matrix_labels.append(0)
				else:
				    answer_data = np.genfromtxt(os.getcwd()+'/Answers/Game'+str(game)+'.csv',dtype=str, delimiter='\t')
				    #cursor.execute("SELECT id FROM Tags where tag ='{0}'".format(tag))
				    #tag_id = cursor.fetchone()[0]
				    if answer_data[int(obs_id[0])-1][qid-1] == 'yes' or answer_data[int(obs_id[0])-1][qid-1] is 'yes':
					should_train = True
					count = count + 1
					cursor.execute("SELECT COUNT(*) FROM FeatureInfo WHERE feature_id='0' AND observation_id='{0}' AND game_id='{1}' ".format(obs_id[0], game))
					num_of_images_per_oservation=cursor.fetchall()
					
					cursor.execute("SELECT feature_id,feature_value FROM FeatureInfo WHERE observation_id='{0}' AND game_id='{1}'".format(obs_id[0],game))
					feature_info=cursor.fetchall()
					
					vv_seperator=len(feature_info)/num_of_images_per_oservation[0][0]
					
					new_fv=0 #flag to show when a feature vector given a capture starts (index in feature_info tuple)
					end_of_fv=vv_seperator#flag to show when a feature vector given a capture ends (index in feature_info tuple)
				 
					for capture_id in xrange(0,num_of_images_per_oservation[0][0]): 
					    feature_vector=RetrieveFeatureVector(feature_info,new_fv,end_of_fv) #create a feature vector given a capture 
					    #print len(feature_vector)
					    new_fv=new_fv+vv_seperator #update starting index of the vector
					    end_of_fv=end_of_fv+vv_seperator #update ending index of the vector
					    feature_matrix.append(feature_vector) #insert feature vectors into a matrix for each tag
					
					    feature_matrix_labels.append(1)
				    else:
					should_train = True
					count = count + 1
					cursor.execute("SELECT COUNT(*) FROM FeatureInfo WHERE feature_id='0' AND observation_id='{0}' AND game_id='{1}' ".format(obs_id[0], game))
					num_of_images_per_oservation=cursor.fetchall()
					
					cursor.execute("SELECT feature_id,feature_value FROM FeatureInfo WHERE observation_id='{0}' AND game_id='{1}'".format(obs_id[0],game))
					feature_info=cursor.fetchall()
					
					vv_seperator=len(feature_info)/num_of_images_per_oservation[0][0]
					
					new_fv=0 #flag to show when a feature vector given a capture starts (index in feature_info tuple)
					end_of_fv=vv_seperator#flag to show when a feature vector given a capture ends (index in feature_info tuple)
				 
					for capture_id in xrange(0,num_of_images_per_oservation[0][0]): 
					    feature_vector=RetrieveFeatureVector(feature_info,new_fv,end_of_fv) #create a feature vector given a capture 
					    #print len(feature_vector)
					    new_fv=new_fv+vv_seperator #update starting index of the vector
					    end_of_fv=end_of_fv+vv_seperator #update ending index of the vector
					    feature_matrix.append(feature_vector) #insert feature vectors into a matrix for each tag
					
					    feature_matrix_labels.append(0)
		    # Otherwise, use only questions from gameplay
		    else:
			model_folder = os.getcwd() + '/GMM_model_777'
			listing = os.listdir(model_folder)
			has_model = []
			for mod in listing:
				if mod.endswith('.pkl'):
				    model_clone = joblib.load(model_folder + '/' + mod)
				    K = mod.split('_', 1)[0]
				    K = K.lower()
				    has_model.append(K)
			for game in range(0, gameID+1):
			    print game
			    if tag.lower() in has_model:
				if game == 0:
				    if T >= 3:
					should_train = True
					count = count + 1
					cursor.execute("SELECT COUNT(*) FROM FeatureInfo WHERE feature_id='0' AND observation_id='{0}' AND game_id='{1}' ".format(obs_id[0], game))
					num_of_images_per_oservation=cursor.fetchall()
					
					cursor.execute("SELECT feature_id,feature_value FROM FeatureInfo WHERE observation_id='{0}' AND game_id='{1}'".format(obs_id[0],game))
					feature_info=cursor.fetchall()
					
					vv_seperator=len(feature_info)/num_of_images_per_oservation[0][0]
					
					new_fv=0 #flag to show when a feature vector given a capture starts (index in feature_info tuple)
					end_of_fv=vv_seperator#flag to show when a feature vector given a capture ends (index in feature_info tuple)
				 
					for capture_id in xrange(0,num_of_images_per_oservation[0][0]): 
					    feature_vector=RetrieveFeatureVector(feature_info,new_fv,end_of_fv) #create a feature vector given a capture 
					    #print len(feature_vector)
					    new_fv=new_fv+vv_seperator #update starting index of the vector
					    end_of_fv=end_of_fv+vv_seperator #update ending index of the vector
					    feature_matrix.append(feature_vector) #insert feature vectors into a matrix for each tag
					    feature_matrix_labels.append(1)
				    elif T == 0:
					should_train = True
					count = count + 1
					cursor.execute("SELECT COUNT(*) FROM FeatureInfo WHERE feature_id='0' AND observation_id='{0}' AND game_id='{1}' ".format(obs_id[0], game))
					num_of_images_per_oservation=cursor.fetchall()
					
					cursor.execute("SELECT feature_id,feature_value FROM FeatureInfo WHERE observation_id='{0}' AND game_id='{1}'".format(obs_id[0],game))
					feature_info=cursor.fetchall()
					
					vv_seperator=len(feature_info)/num_of_images_per_oservation[0][0]
					
					new_fv=0 #flag to show when a feature vector given a capture starts (index in feature_info tuple)
					end_of_fv=vv_seperator#flag to show when a feature vector given a capture ends (index in feature_info tuple)
				 
					for capture_id in xrange(0,num_of_images_per_oservation[0][0]): 
					    feature_vector=RetrieveFeatureVector(feature_info,new_fv,end_of_fv) #create a feature vector given a capture 
					    #print len(feature_vector)
					    new_fv=new_fv+vv_seperator #update starting index of the vector
					    end_of_fv=end_of_fv+vv_seperator #update ending index of the vector
					    feature_matrix.append(feature_vector) #insert feature vectors into a matrix for each tag
					    feature_matrix_labels.append(0)
				elif game < 16:
				    answer_data = np.genfromtxt(os.getcwd()+'/Answers/Game'+str(game)+'.csv',dtype=str, delimiter='\t')
				    #cursor.execute("SELECT id FROM Tags where tag ='{0}'".format(tag))
				    #tag_id = cursor.fetchone()[0]
				    if answer_data[int(obs_id[0])-1][qid-1] == 'yes' or answer_data[int(obs_id[0])-1][qid-1] is 'yes':
					should_train = True
					count = count + 1
					cursor.execute("SELECT COUNT(*) FROM FeatureInfo WHERE feature_id='0' AND observation_id='{0}' AND game_id='{1}' ".format(obs_id[0], game))
					num_of_images_per_oservation=cursor.fetchall()
					
					cursor.execute("SELECT feature_id,feature_value FROM FeatureInfo WHERE observation_id='{0}' AND game_id='{1}'".format(obs_id[0],game))
					feature_info=cursor.fetchall()
					
					vv_seperator=len(feature_info)/num_of_images_per_oservation[0][0]
					
					new_fv=0 #flag to show when a feature vector given a capture starts (index in feature_info tuple)
					end_of_fv=vv_seperator#flag to show when a feature vector given a capture ends (index in feature_info tuple)
				 
					for capture_id in xrange(0,num_of_images_per_oservation[0][0]): 
					    feature_vector=RetrieveFeatureVector(feature_info,new_fv,end_of_fv) #create a feature vector given a capture 
					    #print len(feature_vector)
					    new_fv=new_fv+vv_seperator #update starting index of the vector
					    end_of_fv=end_of_fv+vv_seperator #update ending index of the vector
					    feature_matrix.append(feature_vector) #insert feature vectors into a matrix for each tag
					
					    feature_matrix_labels.append(1)
				    elif answer_data[int(obs_id[0])-1][qid-1] == 'no' or answer_data[int(obs_id[0])-1][qid-1] is 'no':
					should_train = True
					count = count + 1
					cursor.execute("SELECT COUNT(*) FROM FeatureInfo WHERE feature_id='0' AND observation_id='{0}' AND game_id='{1}' ".format(obs_id[0], game))
					num_of_images_per_oservation=cursor.fetchall()
					
					cursor.execute("SELECT feature_id,feature_value FROM FeatureInfo WHERE observation_id='{0}' AND game_id='{1}'".format(obs_id[0],game))
					feature_info=cursor.fetchall()
					
					vv_seperator=len(feature_info)/num_of_images_per_oservation[0][0]
					
					new_fv=0 #flag to show when a feature vector given a capture starts (index in feature_info tuple)
					end_of_fv=vv_seperator#flag to show when a feature vector given a capture ends (index in feature_info tuple)
				 
					for capture_id in xrange(0,num_of_images_per_oservation[0][0]): 
					    feature_vector=RetrieveFeatureVector(feature_info,new_fv,end_of_fv) #create a feature vector given a capture 
					    #print len(feature_vector)
					    new_fv=new_fv+vv_seperator #update starting index of the vector
					    end_of_fv=end_of_fv+vv_seperator #update ending index of the vector
					    feature_matrix.append(feature_vector) #insert feature vectors into a matrix for each tag
					
					    feature_matrix_labels.append(0)
				else:
				    cursor.execute("SELECT id FROM Tags WHERE tag = '{0}'".format(tag))
				    tag_id = cursor.fetchone()[0]
				    if tag_id in questions[game][int(obs_id[0])]:
					index = questions[game][int(obs_id[0])].index(tag_id)
					#cursor.execute("SELECT id FROM Tags where tag ='{0}'".format(tag))
					#tag_id = cursor.fetchone()[0]
					if answers[game][int(obs_id[0])][index] == 1:
					    should_train = True
					    count = count + 1
					    cursor.execute("SELECT COUNT(*) FROM FeatureInfo WHERE feature_id='0' AND observation_id='{0}' AND game_id='{1}' ".format(obs_id[0], game))
					    num_of_images_per_oservation=cursor.fetchall()
					    
					    cursor.execute("SELECT feature_id,feature_value FROM FeatureInfo WHERE observation_id='{0}' AND game_id='{1}'".format(obs_id[0],game))
					    feature_info=cursor.fetchall()
					    
					    vv_seperator=len(feature_info)/num_of_images_per_oservation[0][0]
					    
					    new_fv=0 #flag to show when a feature vector given a capture starts (index in feature_info tuple)
					    end_of_fv=vv_seperator#flag to show when a feature vector given a capture ends (index in feature_info tuple)
				     
					    for capture_id in xrange(0,num_of_images_per_oservation[0][0]): 
						feature_vector=RetrieveFeatureVector(feature_info,new_fv,end_of_fv) #create a feature vector given a capture 
						#print len(feature_vector)
						new_fv=new_fv+vv_seperator #update starting index of the vector
						end_of_fv=end_of_fv+vv_seperator #update ending index of the vector
						feature_matrix.append(feature_vector) #insert feature vectors into a matrix for each tag
					    
						feature_matrix_labels.append(1)
					elif answers[game][int(obs_id[0])][index] == 0:
					    should_train = True
					    count = count + 1
					    cursor.execute("SELECT COUNT(*) FROM FeatureInfo WHERE feature_id='0' AND observation_id='{0}' AND game_id='{1}' ".format(obs_id[0], game))
					    num_of_images_per_oservation=cursor.fetchall()
					    
					    cursor.execute("SELECT feature_id,feature_value FROM FeatureInfo WHERE observation_id='{0}' AND game_id='{1}'".format(obs_id[0],game))
					    feature_info=cursor.fetchall()
					    
					    vv_seperator=len(feature_info)/num_of_images_per_oservation[0][0]
					    
					    new_fv=0 #flag to show when a feature vector given a capture starts (index in feature_info tuple)
					    end_of_fv=vv_seperator#flag to show when a feature vector given a capture ends (index in feature_info tuple)
				     
					    for capture_id in xrange(0,num_of_images_per_oservation[0][0]): 
						feature_vector=RetrieveFeatureVector(feature_info,new_fv,end_of_fv) #create a feature vector given a capture 
						#print len(feature_vector)
						new_fv=new_fv+vv_seperator #update starting index of the vector
						end_of_fv=end_of_fv+vv_seperator #update ending index of the vector
						feature_matrix.append(feature_vector) #insert feature vectors into a matrix for each tag
					    
						feature_matrix_labels.append(0)
			
		if should_train:
		    feature_matrix=np.asarray(feature_matrix)
		    #model.ModelTraining(tag, feature_matrix, 777) #training the model with GMM
		    model.ModelTrainingSVM(tag, feature_matrix, feature_matrix_labels, 777) #training the model with SVM
    print count


def get_t(object_id, question_id, cursor):

    tag = get_tag(question_id, cursor)

    cursor.execute('SELECT COUNT(*) \
                    FROM Descriptions \
                    WHERE description LIKE %s \
                    AND objectID = %s', ('%{0}%'.format(tag), str(object_id)))

    return cursor.fetchone()[0]


def get_tval(cursor):
    cursor.execute('SELECT yes_answers/total_answers FROM Pqd')

    result = cursor.fetchall()

    tvals = []
    for r in result:
        tvals.append(float(r[0]))

    return tvals
 
    
def get_questions_answers(object_id, cursor):
<<<<<<< HEAD
    cursor.execute('SELECT qid, oid, answer from answers where oid = %s', (object_id))
=======
    cursor.execute('SELECT qid, oid, answer from answers where oid = "{0}"'.format(object_id))
>>>>>>> 495419c2c6a9d2ae51c7f0a6596ab7e5cd01340b

    results = cursor.fetchall()

    questions_answers = {}
    for i in range(1, 290):
        questions_answers[i] = []
<<<<<<< HEAD

=======
    x = 0
>>>>>>> 495419c2c6a9d2ae51c7f0a6596ab7e5cd01340b
    for qid, oid, answer in results:
        for i in range(1, 290):
            if int(qid) == i:
                questions_answers[i].append(int(answer))
<<<<<<< HEAD
=======
	    x+=1
    print x
>>>>>>> 495419c2c6a9d2ae51c7f0a6596ab7e5cd01340b

    return questions_answers


def get_tag(question_id, cursor):
<<<<<<< HEAD
    cursor.execute('SELECT tag from Tags where id = %s', (question_id))
=======
    cursor.execute('SELECT tag from Tags where id = "{0}"'.format(question_id))
>>>>>>> 495419c2c6a9d2ae51c7f0a6596ab7e5cd01340b

    return cursor.fetchone()[0]


def get_p_tag(cursor):
    # The P tag is the number of times a question has been answered true for a specific object
    # IE black and scissors has its own P tag
    p_tags = []
    tags = get_tags(cursor)
    for tag in range(1,290):
	answers = {}
<<<<<<< HEAD
	cursor.execute("SELECT COUNT(*) FROM answers WHERE qid = %s and answer = TRUE", tag)
	answers[1] = cursor.fetchone()[0]
	cursor.execute("SELECT COUNT(*) FROM answers WHERE qid = %s and answer = FALSE", tag)
=======
	cursor.execute('SELECT COUNT(*) FROM answers WHERE qid = "{0}" and answer = TRUE'.format(tag))
	answers[1] = cursor.fetchone()[0]
	cursor.execute('SELECT COUNT(*) FROM answers WHERE qid = "{0}" and answer = FALSE'.format(tag))
>>>>>>> 495419c2c6a9d2ae51c7f0a6596ab7e5cd01340b
	answers[0] = cursor.fetchone()[0]
	p_tags.append(answers)
	#print tags[tag-1] + " prob yes: " + str(p_tags[tag-1][1]/ (float(p_tags[tag-1][0] + p_tags[tag-1][1]))) + " prob no: " +  str(p_tags[tag-1][0]/ (float(p_tags[tag-1][0] + p_tags[tag-1][1])))
	
    return p_tags


def gen_init_prob(cursor):
    objects = {}

    for i in range(1, 18):
        objects[i] = get_questions_answers(i, cursor)

    return objects


def test_images(cursor):
    Pi = gen_image_probabilities(1, cursor)
    for i in range(0,17):
	for j in range(0,289):
	    print i, get_tag(j+1, cursor), Pi[i][j]
	print max(Pi[i]), min(Pi[i])


def score_tag(feature_vector, model):
    prob = model.score([feature_vector])
    return math.e ** (prob[0] / 100000.0)


def test_unknown_image(cursor, tags, gameID):
    for img in range(1,18):
        image_path = os.getcwd() + '/GAMES/Game' + str(gameID) + '/obj' + str(img) + '.jpg'
        image = cv2.imread(image_path)
        feature_vector = test_ft.FeatureExtraction(image)
        
        models = {}
        model_folder = os.getcwd()+'/GMM_model_777'
        listing = os.listdir(model_folder)
        
        for model in listing:
        	if model.endswith('.pkl'):
        	    model_clone = joblib.load(model_folder + '/' + model)
        	    T = model.split('_', 1)[0]
        	    T = T.lower()
        	    cursor.execute("SELECT id FROM Tags WHERE tag = %s", (T))
        	    qid = cursor.fetchone()[0]
        	    models[qid] = model_clone
        
        probability = []
        for j in range(1, 290):
        	if j in models:
        	    probability.append(score_tag(feature_vector, models[j]))
        	else:
        	    probability.append(0)

        agreement = {}
        for i in range(0,289):
            cursor.execute("SELECT answer FROM Answers WHERE objectID = %s AND tag = %s AND answerSet = %s", (img, tags[i], gameID))
            answer = cursor.fetchone()[0]
            if probability[i] > 0.50:
                if answer == True:
                    agreement[i] = 1
                else:
                    agreement[i] = 0
        	    #print tags[i] + " yes " + str(probability[i])
            elif probability[i] == 0:
        	    pass
            else:
                if answer == False:
                    agreement[i] = 1
                else:
                    agreement[i] = 0
        	    #print tags[i] + " no " + str(probability[i])

        total = 0
        for i in agreement:
            #print tags[i], agreement[i]
            total = total + agreement[i]

        print "Agreed " + str(total/float(len(agreement))) + " of the time on object " + str(img)

        with open("agreement.txt", "a") as myfile:
            myfile.write(str(gameID) + "\n")
            for i in agreement:
                myfile.write(tags[i] + " " + str(agreement[i]) + " " + str(probability[i]) + "\n")
            myfile.write("Agreed " + str(total/float(len(agreement))) + " of the time on object " + str(img) + "\n")


def get_model_info(cursor, game_id):
    # Get all of the model vectors from the database
    feature_matrix = []
    feature_matrix_labels = []
    for i in range(1,18):
	cursor.execute("SELECT COUNT(*) FROM FeatureInfo WHERE feature_id='0' AND observation_id='{0}' AND game_id < '{1}' ".format(i, game_id))
	num_of_images_per_oservation=cursor.fetchall()
	
	cursor.execute("SELECT feature_id,feature_value FROM FeatureInfo WHERE observation_id='{0}' AND game_id < '{1}'".format(i,game_id))
	feature_info=cursor.fetchall()
	
	vv_seperator=len(feature_info)/num_of_images_per_oservation[0][0]
	
	new_fv=0 #flag to show when a feature vector given a capture starts (index in feature_info tuple)
	end_of_fv=vv_seperator#flag to show when a feature vector given a capture ends (index in feature_info tuple)
	matrix_labels = []
	matrix = []
	
	for capture_id in xrange(0,num_of_images_per_oservation[0][0]): 
	    feature_vector=RetrieveFeatureVector(feature_info,new_fv,end_of_fv) #create a feature vector given a capture 
	    #print len(feature_vector)
	    new_fv=new_fv+vv_seperator #update starting index of the vector
	    end_of_fv=end_of_fv+vv_seperator #update ending index of the vector
	    matrix.append(feature_vector) #insert feature vectors into a matrix for each tag
	    matrix_labels.append(1)
	feature_matrix.append(matrix)
	feature_matrix_labels.append(matrix_labels)
	#image_path = os.getcwd() + '/GAMES/Game' + str(game_id) + '/obj' + str(i) + '.jpg'
	#image = cv2.imread(image_path)
	#feature_vectors.append(test_ft.FeatureExtraction(image))
	
    models = {}
    model_folder = os.getcwd()+'/SVM_model_777'
    listing = os.listdir(model_folder)
    
    for model in listing:
	if model.endswith('.pkl'):
	    
	    model_clone = joblib.load(model_folder + '/' + model)
	    T = model.split('_', 1)[0]
	    T = T.lower()
<<<<<<< HEAD
	    cursor.execute("SELECT id FROM Tags WHERE tag = %s", (T))
=======
	    cursor.execute('SELECT id FROM Tags WHERE tag = "{0}"'.format(T))
>>>>>>> 495419c2c6a9d2ae51c7f0a6596ab7e5cd01340b
	    qid = cursor.fetchone()[0]
	    models[qid] = model_clone

    return models, feature_matrix, feature_matrix_labels


def gen_image_probabilities_evaluation(game_id, cursor):
    models, feature_vectors, feature_vector_labels = get_model_info(cursor, game_id)
    available_models = []
    probabilities = {}
    for i in range(0, 17):
	probability = []
	for j in range(1, 290):
	    if j in models:
		probability.append(score_tag(feature_vectors[i], models[j]))
		available_models.append(j-1)
	    else:
		pass
		probability.append(-1)
	probabilities[i] = probability
	print "Image " + str(i + 1) + " processed"
    
#    for i in available_models:
#	total = 0
#	for j in range(0,17):
#	    total = total + probabilities[j][i]
#	for j in range(0,17):
#	    probabilities[j][i] = probabilities[j][i] / total
#   
    return probabilities


def gen_image_probabilities(game_id, cursor):
    # Collect all keyword classifiers and feature vectors of objects in the game space
    models, feature_vectors, labels = get_model_info(cursor, game_id)
    available_models = []
    probabilities = {}
    for i in range(0, 17):
	probability = []
	for j in range(1, 290):
	    if j in models:
		# Score feature vector against keyword classifier and save the probability
		probability.append(models[j].score(feature_vectors[i], labels[i]))
		available_models.append(j-1)
		beans = models[j].score(feature_vectors[i], labels[i])
		if beans > 0:
		    print j, beans
	    else:
		# If no keyword classifier is available, score as -1 so we can skip later
		probability.append(-1)
	probabilities[i] = probability
	print "Image " + str(i + 1) + " processed"
   
    return probabilities
   

def get_best_question_old(objects, asked_questions, pO, start, cursor, game_id, Pi, p_tags):
    tvals = get_tval(cursor)
    probabilities_yes = []
    probabilities_no = []

    top = (17 - start - 1)/2 + start + 1
    bottom = 17 - top
    bestDifference = 0
    bestD = 0

    for i in range(0, 17):
        probabilities_yes.append(0)
	probabilities_no.append(0)

    
    for j in range(1, 290):
	if j not in asked_questions:
	    for i in range(1, 18): 
                T = get_t(i, j, cursor)
                num_yes = sum(objects[i][j])
                length = len(objects[i][j])
	    		
		if Pi[i-1][j-1] == -1:
		    probabilities_yes[i-1] = pO[i-1] * (tvals[T] + (num_yes + 1.0)/(length + 2.0))#/((p_tags[j-1][1] + 1) / float(p_tags[j-1][1] + p_tags[j-1][0] + 2))
		    probabilities_no[i-1] = pO[i-1] * ((1 - tvals[T]) + (length - num_yes + 1.0)/(length + 2.0))#/((p_tags[j-1][0] + 1) / float(p_tags[j-1][1] + p_tags[j-1][0] + 2))
		else:
		    probabilities_yes[i-1] = pO[i-1] * (tvals[T] + (num_yes + 1.0)/(length + 2.0) + Pi[i-1][j-1])#/((p_tags[j-1][1] + 1) / float(p_tags[j-1][1] + p_tags[j-1][0] + 2))
		    probabilities_no[i-1] = pO[i-1] * ((1 - tvals[T]) + (length - num_yes + 1.0)/(length + 2.0) + 1 - Pi[i-1][j-1])#/((p_tags[j-1][0] + 1) / float(p_tags[j-1][1] + p_tags[j-1][0] + 2))
		
	    yes = probabilities_yes[i-1] / (probabilities_no[i-1] + probabilities_yes[i-1])
	    no = probabilities_no[i-1] / (probabilities_no[i-1] + probabilities_yes[i-1])

	    probabilities_yes.sort()
	    probabilities_yes.reverse()
	    
	    yes_indices = np.argsort(probabilities_yes)

	    topProbYes = 0
	    bottomProbYes = 0

	    bottomProbNo = 0
	    topProbNo = 0

	    for x in range(start, top):
		topProbYes = topProbYes + probabilities_yes[x]
		topProbNo = topProbNo + probabilities_no[yes_indices[x]]

	    for x in range(top, 17):
		bottomProbYes = bottomProbYes + probabilities_yes[x]
		bottomProbNo = bottomProbNo + probabilities_no[yes_indices[x]]

	    topProbYes = topProbYes/(0.0 + top)
	    bottomProbYes = bottomProbYes/(0.0 + bottom)
	    
	    topProbNo = topProbNo/(0.0 + top)
	    bottomProbNo = bottomProbNo/(0.0 + bottom)

	    if(abs(topProbYes - bottomProbYes) + abs(topProbNo - bottomProbNo) > bestDifference):
		bestDifference = abs(topProbYes - bottomProbYes) + abs(topProbNo - bottomProbNo)
		bestD = j
		

    return bestD


def get_best_question_tag(objects, asked_questions, pO, start, cursor, game_id, Pi, p_tags):
    tvals = get_tval(cursor)
    probabilities_yes = []
    probabilities_no = []

    top = (17 - start - 1)/2 + start + 1
    bottom = 17 - top
    bestDifference = 0
    bestD = 0
      
    for i in range(0, 17):
        probabilities_yes.append(0)
	probabilities_no.append(0)

    pO_sorted = np.argsort(pO)
    objects_considered = pO_sorted[start:]
    for i in range(0,len(objects_considered)):
	objects_considered[i] += 1
    
    for j in range(1, 290):
	yes = 0
	no = 0
	
	p_for_yes = 0
	p_for_no = 0
	
	pi_given_yes_times_log = 0
	pi_given_no_times_log = 0
	    
	if j not in asked_questions and j is not 285:
	    for i in objects_considered:
		
		T = get_t(i, j, cursor)
		num_yes = sum(objects[i][j])
		length = len(objects[i][j])
			
		if Pi[i-1][j-1] == -1:
		    probabilities_yes[i-1] = pO[i-1] * (tvals[T] + (num_yes + 1.0)/(length + 2.0))#/((p_tags[j-1][1] + 1) / float(p_tags[j-1][1] + p_tags[j-1][0] + 2))
		    probabilities_no[i-1] = pO[i-1] * ((1 - tvals[T]) + (length - num_yes + 1.0)/(length + 2.0))#/((p_tags[j-1][0] + 1) / float(p_tags[j-1][1] + p_tags[j-1][0] + 2))
		else:
		    probabilities_yes[i-1] = pO[i-1] * (tvals[T] + (num_yes + 1.0)/(length + 2.0) + Pi[i-1][j-1])#/((p_tags[j-1][1] + 1) / float(p_tags[j-1][1] + p_tags[j-1][0] + 2))
		    probabilities_no[i-1] = pO[i-1] * ((1 - tvals[T]) + (length - num_yes + 1.0)/(length + 2.0) + 1 - Pi[i-1][j-1])#/((p_tags[j-1][0] + 1) / float(p_tags[j-1][1] + p_tags[j-1][0] + 2))
		
		p_for_yes += pO[i-1] * num_yes / length
		p_for_no += pO[i-1] * (length - num_yes) / length
		
		yes  += probabilities_yes[i-1]
		no += probabilities_no[i-1]
		
		pi_given_yes_times_log += probabilities_yes[i-1] * math.log(probabilities_yes[i-1], 2)
		pi_given_no_times_log += probabilities_no[i-1] * math.log(probabilities_no[i-1], 2)
	    
	    
	    yes = yes / len(objects_considered)
	    no = no / len(objects_considered)
	    
	    #entropy = -p_for_yes * pi_given_yes_times_log - p_for_no * pi_given_no_times_log
	    entropy = - yes * math.log(yes, 2) - no * math.log(no, 2)
	    if entropy > bestDifference:
		bestD = j
		bestDifference = entropy

    return bestD


def get_best_question_new(objects, asked_questions, pO, start, cursor, game_id, Pi, p_tags):
    # Finds the question that best splits our current subset of objects
    tvals = get_tval(cursor)

    # Get top and bottom halves of current subset
    top = (17 - start - 1)/2 + start + 1
    bottom = 17 - top
    bestDifference = 10
    bestD = 0
    
    probabilities_yes = []
    probabilities_no = [] 
    for i in range(0, 17):
        probabilities_yes.append(0)
	probabilities_no.append(0)

    # We only consider objects beyond the start index when deciding
    # Objects below the index are still updated when the question is asked and can shift back into play, but decisions are not made based on them while they're below start
    pO_sorted = np.argsort(pO)
    objects_considered = pO_sorted[start:]
    for i in range(0,len(objects_considered)):
	objects_considered[i] += 1
    
    # Look over all tags    
    for j in range(1, 290):
	yes = 0
	no = 0
	
	p_for_yes = 0
	p_for_no = 0
	
	pi_given_yes_times_log = 0
	pi_given_no_times_log = 0
	    
	# Don't reask questions
	if j not in asked_questions:
	    # Only look at objects in the correct subset
	    for i in objects_considered:
		
		T = get_t(i, j, cursor)
		num_yes = sum(objects[i][j])
		length = len(objects[i][j])
			
		if Pi[i-1][j-1] == -1:
		    probabilities_yes[i-1] = pO[i-1] * (tvals[T] + (num_yes + 1.0)/(length + 2.0)) / 2
		    probabilities_no[i-1] = pO[i-1] * ((1 - tvals[T]) + (length - num_yes + 1.0)/(length + 2.0)) / 2
		else:
		    probabilities_yes[i-1] = pO[i-1] * (tvals[T] + (num_yes + 1.0)/(length + 2.0) + Pi[i-1][j-1]) / 3
		    probabilities_no[i-1] = pO[i-1] * ((1 - tvals[T]) + (length - num_yes + 1.0)/(length + 2.0) + 1 - Pi[i-1][j-1]) / 3
	    
	    # Normalize the probabilities
	    probabilities_yes = np.asarray(probabilities_yes)
	    probabilities_no = np.asarray(probabilities_no)
	    probabilities_yes = probabilities_yes / sum(probabilities_yes)
	    probabilities_no = probabilities_no / sum(probabilities_no)
	    
	    # Do some fancy math to find out which tag lowers total entropy the most (AKA it gives us the most knowledge)
	    for i in objects_considered:
		num_yes = sum(objects[i][j])
		length = len(objects[i][j])
		
		p_for_yes += pO[i-1] * num_yes / length
		p_for_no += pO[i-1] * (length - num_yes) / length
		
		yes  += probabilities_yes[i-1]
		no += probabilities_no[i-1]
		
		pi_given_yes_times_log += probabilities_yes[i-1] * math.log(probabilities_yes[i-1], 2)
		pi_given_no_times_log += probabilities_no[i-1] * math.log(probabilities_no[i-1], 2)
	    
	    entropy = -p_for_yes * pi_given_yes_times_log - p_for_no * pi_given_no_times_log
	    if entropy < bestDifference:
		bestD = j
		bestDifference = entropy

    return bestD


def get_subset_split(pO):
    # When probabilities ordered least to greatest, returns index of largest difference between probabilities
    # System asks questions to try to split subset in half each time, so the split should move closer to the max probability each time
    bestDifference = 0
    
    pO_sorted = np.sort(pO)
    pO_args_sorted = np.argsort(pO)
    
    for x in range(0,17):
	print str(pO_args_sorted[x]) + " -> " + str(pO_sorted[x])

    diff = 0
    bestDiff = 0
    
    for x in range(0, pO_sorted.size-1):
	if pO_sorted[x+1] - pO_sorted[x] > diff:
	    diff = pO_sorted[x+1] - pO_sorted[x]
	    bestDiff = x

    return bestDiff


def ask_question(cursor, answer_data, OBJECT_WE_PLAY, bestD, answers, pO, tags, game_folder, objectlist, objects, Pi, p_tags):
    # Takes best question and updates all object probabilies based on the answer
<<<<<<< HEAD
    
    probabilityD = get_tval(cursor)
    question_tag = tags[bestD-1]
=======
        
    probabilityD = get_tval(cursor)
    print probabilityD
    question_tag = tags[bestD-1]
    print question_tag
>>>>>>> 495419c2c6a9d2ae51c7f0a6596ab7e5cd01340b
    #answer = raw_input("Does it have " + tags[bestD-1] + "? (yes/no) ")
    #answer = answer.lower()
    answer = answer_data[OBJECT_WE_PLAY-1][bestD-1]
    print game_folder, OBJECT_WE_PLAY,objectlist[OBJECT_WE_PLAY-1][0],'qt->'+question_tag+' ' ,'ans->'+answer 

    if not (answer):
	# Not sure why this is here, it's old code, never seen it actually run
	    print game_folder, OBJECT_WE_PLAY,'qt->'+question_tag+' ' ,'sd'+answer+'<-', objectlist[OBJECT_WE_PLAY-1][0]
	    
	    sys.exit()
	    
    if answer == 'yes' or answer is 'yes':
	    answers.append(True)
	    # If there's an image model it has positive value, otherwise -1
	    # Without image model the probability just updates based on Pq and Pqd
	    if Pi[0][bestD-1] == -1:
		for objectID in range(0,17):
		    T = get_t(objectID+1, bestD, cursor)
		    N = sum(objects[objectID+1][bestD])
		    D = len(objects[objectID+1][bestD])
<<<<<<< HEAD
		    pO[objectID] = pO[objectID] * (probabilityD[T] + (N + 1)/(D + 2.0)) / 2 #/((p_tags[bestD-1][1] + 1) / float(p_tags[bestD-1][1] + p_tags[bestD-1][0] + 2))	
=======
		    print T, N, D
		    pO[objectID] = pO[objectID] * (probabilityD[T] + (N + 1)/(D + 2.0)) / 2 #/((p_tags[bestD-1][1] + 1) / float(p_tags[bestD-1][1] + p_tags[bestD-1][0] + 2))
		    print pO[objectID] * (probabilityD[T] + (N + 1)/(D + 2.0)) / 2
>>>>>>> 495419c2c6a9d2ae51c7f0a6596ab7e5cd01340b
	    else:
		for objectID in range(0,17):
		    T = get_t(objectID+1, bestD, cursor)
		    N = sum(objects[objectID+1][bestD])
		    D = len(objects[objectID+1][bestD])
<<<<<<< HEAD
		    pO[objectID] = pO[objectID] * ((probabilityD[T] + (N + 1)/(D + 2.0) + Pi[objectID][bestD-1])) / 3 #/((p_tags[bestD-1][1] + 1) / float(p_tags[bestD-1][1] + p_tags[bestD-1][0] + 2))
=======
		    print T, N, D
		    pO[objectID] = pO[objectID] * ((probabilityD[T] + (N + 1)/(D + 2.0) + Pi[objectID][bestD-1])) / 3 #/((p_tags[bestD-1][1] + 1) / float(p_tags[bestD-1][1] + p_tags[bestD-1][0] + 2))
		    print ((probabilityD[T] + (N + 1)/(D + 2.0) + Pi[objectID][bestD-1])) / 3
>>>>>>> 495419c2c6a9d2ae51c7f0a6596ab7e5cd01340b

    else:
	    if answer =='no' or answer is 'no':
			answers.append(False)
			# If there's an image model it has positive value, otherwise -1
			# Without image model the probability just updates based on Pq and Pqd
			if Pi[0][bestD-1] == -1:
			    for objectID in range(0,17):
				T = get_t(objectID+1, bestD, cursor)
				N = sum(objects[objectID+1][bestD])
				D = len(objects[objectID+1][bestD])
<<<<<<< HEAD
				pO[objectID] = pO[objectID] * ((1 - probabilityD[T]) + (D - N + 1)/(D + 2.0)) / 2 #/((p_tags[bestD-1][1] + 1) / float(p_tags[bestD-1][0] + p_tags[bestD-1][0] + 2))	    
=======
				print T, N, D
				pO[objectID] = pO[objectID] * ((1 - probabilityD[T]) + (D - N + 1)/(D + 2.0)) / 2 #/((p_tags[bestD-1][1] + 1) / float(p_tags[bestD-1][0] + p_tags[bestD-1][0] + 2))
				print ((1 - probabilityD[T]) + (D - N + 1)/(D + 2.0)) / 2
>>>>>>> 495419c2c6a9d2ae51c7f0a6596ab7e5cd01340b
			else:
			    for objectID in range(0,17):
				T = get_t(objectID+1, bestD, cursor)
				N = sum(objects[objectID+1][bestD])
				D = len(objects[objectID+1][bestD])
<<<<<<< HEAD
				pO[objectID] = pO[objectID] * (((1 - probabilityD[T]) + (D - N + 1)/(D + 2.0) + 1 - Pi[objectID][bestD-1])) / 3 #/((p_tags[bestD-1][0] + 1) / float(p_tags[bestD-1][1] + p_tags[bestD-1][0] + 2))
=======
				print T, N, D
				pO[objectID] = pO[objectID] * (((1 - probabilityD[T]) + (D - N + 1)/(D + 2.0) + 1 - Pi[objectID][bestD-1])) / 3 #/((p_tags[bestD-1][0] + 1) / float(p_tags[bestD-1][1] + p_tags[bestD-1][0] + 2))
				print (((1 - probabilityD[T]) + (D - N + 1)/(D + 2.0) + 1 - Pi[objectID][bestD-1])) / 3
>>>>>>> 495419c2c6a9d2ae51c7f0a6596ab7e5cd01340b
	
    # Normalize the probabilities so that all object probabilities will sum to 1				
    pO = pO / np.sum(pO)
    
    # Save the qustions to each answer and the updated probabilities
    with open("example.txt", "a") as myfile:
	    myfile.write(question_tag + " -> " + answer+ " \n")
	    myfile.write(str(pO) + "\n")
<<<<<<< HEAD
	
=======
        	
>>>>>>> 495419c2c6a9d2ae51c7f0a6596ab7e5cd01340b
    return pO, answers


def train_initial_model(game_id):
    start_time = time.time()	

    if game_id == 1:
    	for x in xrange(1,18):
    		desc_index = 6 * (x - 1)
    		os.system(" /usr/lib/jvm/java-7-oracle/bin/java -Djava.library.path=/local2/awh0047/iSpy/jnaoqi-1.14.5-linux64/lib -Dfile.encoding=UTF-8 -classpath /local2/awh0047/iSpy/ISPY/iSpy/ispy/bin:/local2/awh0047/iSpy/simplenlg-v4.4.2.jar:/local2/awh0047/iSpy/jaws-bin.jar:/local2/awh0047/iSpy/lucene-analyzers-common-4.6.0.jar:/local2/awh0047/iSpy/lucene-core-4.6.0.jar:/local2/awh0047/iSpy/stanford-corenlp-full-2014-08-27/stanford-corenlp-3.4.1.jar:/local2/awh0047/iSpy/jnaoqi-1.14.5-linux64/lib/jnaoqi-1.14.5.jar:/local2/awh0047/iSpy/stanford-corenlp-full-2014-08-27/stanford-corenlp-3.4.1-models.jar:/local2/awh0047/iSpy/mysql-connector-java-5.1.30-bin.jar ObjectDescription " + str(x) + " \"" + objectlist[x-1][0] + "\" \"" + descriptions_for_retraining[desc_index] + "\"") 
    	first.Object_Learning(1, con)
    	print "Initial learning complete"
    	extract.Extract_Tags(1)
    
    elif game_id < 7:
    	for x in xrange(1,18):
    		desc_index = 6 * (x - 1) + game_id - 1
    		os.system(" /usr/lib/jvm/java-7-oracle/bin/java -Djava.library.path=/local2/awh0047/iSpy/jnaoqi-1.14.5-linux64/lib -Dfile.encoding=UTF-8 -classpath /local2/awh0047/iSpy/ISPY/iSpy/ispy/bin:/local2/awh0047/iSpy/simplenlg-v4.4.2.jar:/local2/awh0047/iSpy/jaws-bin.jar:/local2/awh0047/iSpy/lucene-analyzers-common-4.6.0.jar:/local2/awh0047/iSpy/lucene-core-4.6.0.jar:/local2/awh0047/iSpy/stanford-corenlp-full-2014-08-27/stanford-corenlp-3.4.1.jar:/local2/awh0047/iSpy/jnaoqi-1.14.5-linux64/lib/jnaoqi-1.14.5.jar:/local2/awh0047/iSpy/stanford-corenlp-full-2014-08-27/stanford-corenlp-3.4.1-models.jar:/local2/awh0047/iSpy/mysql-connector-java-5.1.30-bin.jar ObjectDescription " + str(x) + " \"" + objectlist[x-1][0] + "\" \"" + descriptions_for_retraining[desc_index] + "\"")	
    	retrain.Model_Retrain(game_id, con)
    	print "Learning for game " + str(game_id) + " complete"
    	extract.Extract_Tags(game_id)
    	
    else:
    	csv_answers = np.genfromtxt(folder+'/Answers/Game'+str(game_id-1)+'.csv',dtype=str, delimiter='\t')
    	for x in xrange(1,18):
    		tag_built_description = ""
    		for i in xrange(0, len(tags)):
    			if csv_answers[x-1][i] == 'yes' or csv_answers[x-1][i] is 'yes':
    				tag_built_description = tag_built_description + tags[i] + " "
    		os.system(" /usr/lib/jvm/java-7-oracle/bin/java -Djava.library.path=/local2/awh0047/iSpy/jnaoqi-1.14.5-linux64/lib -Dfile.encoding=UTF-8 -classpath /local2/awh0047/iSpy/ISPY/iSpy/ispy/bin:/local2/awh0047/iSpy/simplenlg-v4.4.2.jar:/local2/awh0047/iSpy/jaws-bin.jar:/local2/awh0047/iSpy/lucene-analyzers-common-4.6.0.jar:/local2/awh0047/iSpy/lucene-core-4.6.0.jar:/local2/awh0047/iSpy/stanford-corenlp-full-2014-08-27/stanford-corenlp-3.4.1.jar:/local2/awh0047/iSpy/jnaoqi-1.14.5-linux64/lib/jnaoqi-1.14.5.jar:/local2/awh0047/iSpy/stanford-corenlp-full-2014-08-27/stanford-corenlp-3.4.1-models.jar:/local2/awh0047/iSpy/mysql-connector-java-5.1.30-bin.jar ObjectDescription " + str(x) + " \"" + objectlist[x-1][0] + "\" \"" + tag_built_description + "\"")
    	retrain.Model_Retrain(game_id, con)
    	print "Learning for game " + str(game_id) + " complete"
    	extract.Extract_Tags(game_id)
	    
    training_time = time.time() - start_time
    
    return training_time


def clear_tag_data():
    cursor.execute("DELETE FROM TagInfo;")
    cursor.execute("ALTER TABLE TagInfo AUTO_INCREMENT = 1;")


def build_object_list(cursor):
    # Get object NAMES so that we know what to say when guessing
    # Not necessary for simulated games since the computer basically asks itself, but good for human games
    objectlist = []
    
    cursor.execute("SELECT DISTINCT(name) FROM NameInfo;")
    obj = cursor.fetchall()
    
    OBJ = np.asarray(obj)
    for OB in OBJ:
	    objectlist.append(OB)
	    
    return objectlist


def get_object_ids(cursor):
    # Gets IDs of all objects currently in the databse (Right now that's 1-17, might change once we start learning unknown objects)
    obj_id = []

    cursor.execute("SELECT DISTINCT(observation_id) \
		   FROM NameInfo;")
    objid = cursor.fetchall()
    
    obj_ID = np.asarray(objid)
    for objID in obj_ID:
	    obj_id.append(objID[0])

    return obj_id


def get_tags(cursor):
    # Gets all tags from the database
    cursor.execute("SELECT tag \
		   FROM Tags")
    tags = cursor.fetchall()
    
    tags_list = []
    
    # Puts tags nicely into array, before was [[something],[something else]], now [something, something else]
    for tag in tags:
	tags_list.append(tag[0])
        
    return tags_list


def get_descriptions(oid, cursor):
    cursor.execute("SELECT description \
		   FROM Descriptions \
		   WHERE objectID = %s", (oid))
    descriptions = cursor.fetchall()
    
    return descriptions


def record_object_results(cursor, object_id, answers, questions, con, guess2say, result, gameID):
    # Puts results into the DB as well as writing them to file for examination
    
    for i in range(0, len(questions)):
	T = get_t(object_id, questions[i], cursor)
	#print object_id, questions[i], answers[i]
	if answers[i] == True:
<<<<<<< HEAD
	    cursor.execute("SELECT yes_answers FROM Pqd where t_value = %s", T)
	    yes_count = cursor.fetchone()[0]
	    #print yes_count, 'yes'
	    cursor.execute("UPDATE Pqd SET yes_answers = %s WHERE t_value = %s", (yes_count + 1, T))
	    
	cursor.execute("SELECT total_answers FROM Pqd where t_value = %s", (T))
	total_count = cursor.fetchone()[0]
	#print total_count
	cursor.execute("UPDATE Pqd SET total_answers = %s WHERE t_value = %s", (total_count + 1, T))

	cursor.execute("INSERT INTO answers (oid, qid, answer) VALUES (%s, %s, %s)", (str(object_id), questions[i], answers[i]))
=======
	    cursor.execute('SELECT yes_answers FROM Pqd where t_value = "{0}"'.format(T))
	    yes_count = cursor.fetchone()[0]
	    #print yes_count, 'yes'
	    cursor.execute('UPDATE Pqd SET yes_answers ="{0}" WHERE t_value ="{1}"'.format(yes_count + 1, T))
	    
	cursor.execute('SELECT total_answers FROM Pqd where t_value = "{0}"'.format(T))
	total_count = cursor.fetchone()[0]
	#print total_count
	cursor.execute('UPDATE Pqd SET total_answers ="{0}" WHERE t_value = "{1}"'.format(total_count + 1, T))

	cursor.execute('INSERT INTO answers (oid, qid, answer) VALUES ("{0}", "{1}", "{2}")'.format(str(object_id), questions[i], answers[i]))
>>>>>>> 495419c2c6a9d2ae51c7f0a6596ab7e5cd01340b
	    
	con.commit()

    if result == 0:
	result = 'lose'
    else:
	result = 'win'

    with open("game.txt", "a") as myfile:
	  myfile.write(str(gameID)+','+ str(object_id) +','+ str(guess2say)+"," + str(len(questions)) + "," + result  +  "\n")
    myfile.close()
    
    with open("answers.txt", "a") as answerfile:
	answerfile.write("\n" + str(gameID) + " " + str(object_id) + " " + result + "\n")
	for i in range(0, len(questions)):
	    answerfile.write(get_tag(questions[i], cursor) + " -> " + str(answers[i]) + "\n")
    answerfile.close()


def record_round_results(gameID, round_wins, round_losses, number_of_questions):
    
    with open("game.txt", "a") as myfile:
	myfile.write("Round " + str(gameID) + ": ")	  
	myfile.write("Wins=" + str(round_wins) + ', Losses='+str(round_losses))
	myfile.write(" Accuracy: " + str(round_wins/float(17)) + "\n")
	myfile.write("Average number of questions: " + str(number_of_questions/float(17)) + "\n")


def guess_object(pO, object_guess, guess2say):
    # Simply compare the object that the system thinks is most likely to the object currently in play
    
    print guess2say
    print object_guess
    if object_guess == guess2say:
	print 'won'
	return 1
    else:
	print 'lost'
	return 0


def get_single_object_tags(cursor):
    objects_and_their_tags = {}
    multiple_objects_tags = []

    for i in range(1,18):
	objects_and_their_tags[i] = []

    cursor.execute("SELECT tag FROM Tags")
    
    tags = []
    results = cursor.fetchall()
    
    for result in results:
	tags.append(result[0])
    
    for tag in tags:
	cursor.execute("SELECT distinct objectID FROM Descriptions WHERE description LIKE '%" + tag + "%'")
	results = cursor.fetchall()
	
	if len(results) == 1:
	    objects_and_their_tags[results[0][0]].append(tag)
	else:
	    multiple_objects_tags.append([tag, results])
    
    return objects_and_their_tags, multiple_objects_tags


def remove_tag_classifiers(tags):
    folder = os.getcwd() + '/GMM_model_777/'
    contents = os.listdir(folder)
    
    has_model = []
    for mod in contents:
	    if mod.endswith('.pkl'):
		K = mod.split('_', 1)[0]
		K = K.lower()
		has_model.append(K)   
    
    for tag in tags:
	if tag in has_model:
	    os.system('rm ' + folder + tag + '_model.pkl*')
	    
    
def remove_object_classifier(oid):
    model = os.getcwd() + '/object_classifiers_SVM/' + str(oid) + '_model.pkl'
    os.system('rm ' + model + '*')
    

def evaluate_single_object(cursor, con, evaluation_object):
    single_object_tags = get_single_object_tags(cursor)
    tags = get_tags(cursor)
        
    answers = []
    questions = []
    
    build_model(cursor, con, 30, 31, 3, questions, answers, single_object_tags[evaluation_object])
    build_object_classifiers_svm(cursor, con)
    build_pqd_without_object(cursor, con, tags, evaluation_object, single_object_tags[evaluation_object])
    
    for gameID in range(0,31):
	pass

	
def play_object(cursor, object_id, tags, gameID, all_games, objectlist, con, Pi):
    # Generate initial probabilities
    objects = gen_init_prob(cursor)
    folder =  os.getcwd()    
    
    # Get values necessary to score tag/objects for a Pqd value
    p_tags = get_p_tag(cursor)
    
    # Get answer data for question/object pairs from specific games (1-30)
    # Should really all be coming from DB since they're all there, anyway

    answer_data = np.genfromtxt(folder+'/Answers/Game'+str(gameID)+'.csv',dtype=str, delimiter='\t')
    NoOfQuestions = 0
    pO = []
    game_folder = all_games + '/Game' + str(gameID)
    
    print "+++++++++++++++" + game_folder + "+++++++++++++++"

    # All objects start as equally likely
    initial_prob = 1/float(17)  
    for item in xrange(0, 17):
	pO.append(initial_prob)			
    
    pO = np.asarray(pO)	
 
    askedQuestions = []
    answers = []
    split = 0
    #answer_data = np.genfromtxt('/local2/awh0047/iSpy/ispy_python/Answers/Game' + str(gameID) + '.csv',dtype=str, delimiter='\t')

    # The most likely object must be .15 more likely than the second most likely object before the system will make a guess
    # We call this the 'confidence threshold'
    while np.sort(pO)[pO.size - 1] - np.sort(pO)[pO.size - 2] < 0.15:
	# Find best question
	best_question = get_best_question_new(objects, askedQuestions, pO, split, cursor, gameID, Pi, p_tags)
	# Save under questions already asked
	askedQuestions.append(best_question)
	# Get updated probabilies based on the answer to the question
        pO, answers = ask_question(cursor, answer_data, object_id, best_question, answers, pO, tags, game_folder, objectlist, objects, Pi, p_tags)
	# Split the current subset into two more subsets
	split = get_subset_split(pO)
    
    # Get most likely object
    minimum=np.max(pO)
    itemindexes =[i for i,x in enumerate(pO) if x==minimum]
    A = np.asarray(objectlist)
    guess = A[itemindexes]
    guess2say =  guess[0][0]
    
    # Guess object (Compare what the system thinks is most likely to object currenly in play)
    result = guess_object(pO, objectlist[object_id-1][0], guess2say)

    print len(askedQuestions)
    
    # Save results
    record_object_results(cursor, object_id, answers, askedQuestions, con, guess2say, result, gameID)
    
    return result, len(askedQuestions), answers, askedQuestions


def play_round(cursor, tags, gameID, all_games, objectlist, con):
    # Get object IDs from DB (For now, always 1-17, might change later)
    obj_ids = get_object_ids(cursor)
    
    # Generate all image probabilities at once since this takes a little while
    Pi = gen_image_probabilities(gameID, cursor)
    
    # Initialize round stats to empty
    NoOfQuestions = 0
    round_wins = 0
    round_losses = 0
    avg_win = 0
    avg_lose = 0
    question_answers = {}
    questions_asked = {}
    
    # For each object in the set (1-17)
    for OBJECT_WE_PLAY in obj_ids:
	# Record individual object stats
        result, number_of_questions, answers, askedQuestions = play_object(cursor, OBJECT_WE_PLAY, tags, gameID, all_games, objectlist, con, Pi)
	if result == 0:
	    # Loss
	    round_losses = round_losses + 1
	    avg_lose = avg_lose + number_of_questions
	else:
	    # Win
	    round_wins = round_wins + 1
	    avg_win = avg_win + number_of_questions
	NoOfQuestions = number_of_questions + NoOfQuestions
	
	# Save questions and answers for later
	questions_asked[OBJECT_WE_PLAY] = askedQuestions
	question_answers[OBJECT_WE_PLAY] = answers

    # Save results    
    record_round_results(gameID, round_wins, round_losses, NoOfQuestions)
    
    return round_wins, round_losses, NoOfQuestions, avg_win, avg_lose, question_answers, questions_asked
    
    
def play_game(cursor, con):
    # Starts by initializing everything to zero since no games have been played, no questions asked, etc.
    
    wins=0
    losses=0
    number_of_questions = 0
    avg_win = 0
    avg_lose = 0
    questions_asked = {}
    question_answers = {}
    
    folder =  os.getcwd()
    all_games = folder + '/Human_Games'
    
    objectlist = build_object_list(cursor)
    tags = get_tags(cursor)

    # Plays games 16-30 because 1-15 are typically used as training data

    for gameID in range(16,31):
	# Collect a bunch of information each round
	round_wins, round_losses, round_questions, avg_for_win, avg_for_lose, questions, answers = play_round(cursor, tags, gameID, all_games, objectlist, con)
	
	# need the questions ans answers for certain model training methods
	questions_asked[gameID] = questions
	question_answers[gameID] = answers
	
	# Retrain the model
	build_model(cursor, con, gameID, gameID+1, 3, questions_asked, question_answers)
	#model_evaluation_3(con, gameID)
	#test_unknown_image(cursor, tags, gameID)
	
	# Update game stats
	wins = wins + round_wins
	losses = losses + round_losses
	number_of_questions = number_of_questions + round_questions
	avg_win = avg_for_win + avg_win
	avg_lose = avg_for_lose + avg_lose
    
    with open("game.txt", "a") as myfile:
       myfile.write("Wins=" + str(wins) + ', Losses='+str(losses) + ', Average number of questions=' + str(number_of_questions/float(wins+losses)) + '\n')
       myfile.write("Average questions for a win: " + str(avg_win/float(wins)) + " Average questions for a loss: " + str(avg_lose/float(losses)))
    print wins, losses


def main():
    
    # Lots of commented out functions, not really proper
    # To run the simulation, uncomment play_game(cursor, con)
    
    
    con = sql_driver().connect('localhost', 'iSpy_team', 'password', 'iSpy_features')
    with con:
	cursor = con.cursor()
    
    # This is to get a clean set of answers (seed answers, not test answers)
    # Pqd needs to be rebuilt because it updates to include test answers
    # Before you rebuild Pqd, must run "DELETE FROM Pqd" in mysql against the iSpy_features table

    #copy_into_answers(cursor, get_tags(cursor))
    #con.commit()
    #build_pqd(cursor, con, get_tags(cursor))

    # Builds the models necessary for gameplay (keyword models)
    # Not necessary to rerun each time unless you want to start fresh

    #build_model(cursor, con, 15, 16, 1, {}, {})


#    for game in range(16,31):
#	model_evaluation_1(con, game)   
#
    play_game(cursor, con)

    # Testing out different methods, nothing below should matter except build_object_classifiers(cursor, con)

    #build_object_classifiers_svm(cursor, con)
    #test_object_classifiers_svm(cursor)

    #build_model(cursor, con, 15, 17, 3, [], [])
#    test, test2, test3 = get_model_info(cursor, 12)
#    for key in test:
#	print test[key].score(test2[6], test3[6]), key

    #questions = {16:{1: [1,282], 2:[1,282], 3:[1,282], 4:[1,282], 5:[1,282], 6:[1,282], 7:[1,282], 8:[1,282], 9:[1,282], 10:[1,282], 11:[1,282], 12:[1,282], 13:[1,282], 14:[1,282], 15:[1,282], 16:[1,282], 17:[1,282]}}
    #answers = {16:{1: [1,0], 2:[1,0], 3:[1,0], 4:[1,0], 5:[1,0], 6:[1,0], 7:[1,0], 8:[1,0], 9:[1,0], 10:[1,0], 11:[1,0], 12:[1,0], 13:[1,0], 14:[1,0], 15:[1,0], 16:[1,0], 17:[1,0]}}
    #build_model(cursor, con, 16, 17, 3, questions, answers)
    
    #test_images(cursor)
    #get_p_tag(cursor)
    #build_model(cursor, con, 1, 2)
    
    # Builds GMM object classifiers used to classify an image against
    # Not currently used, the system has no logic to detect and add a new object
    
    #build_object_classifiers(cursor,con)
    
    #first.Object_Learning(0,con)
    
    #test_object_classifiers(cursor)
    #fill_featureinfo(con)
    #test_object_classifiers_over_time(cursor, con)
    
    #test_unknown_image(cursor, get_tags(cursor), 16)
    #add_answerset(cursor, 16, con)
    
    #gen_image_probabilities(1,cursor)
    
    #remove_tag_classifiers(['alarm', 'apple'])
    
    pass
    
		      
if __name__ == '__main__':
        sys.exit(main())
	
