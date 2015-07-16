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

import matplotlib
matplotlib.use('Agg')

import cv2
import test_features_extraction as test_ft
from sklearn.externals import joblib
import gmm_training as model
from sklearn import mixture

import model_retraining_for_game as retrain
import object_learning_for_game as first
import extract_tags_per_game as extract
import warnings
    

def build_pqd(cursor, con, tags):
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


def test_object_classifiers():
    results = []
    
    for x in range(1,18):
	#image_path = os.getcwd() + '/test_images/' + str(x) + '/1.jpg'
	#image = cv2.imread(image_path)
	image_path = '/local2/awh0047/iSpy/ispy_python_old/cropped_ims/obj' + str(x) + '/3.jpg'
	image = cv2.imread(image_path)
	image_path = os.getcwd() + '/test_images/' + str(x) + '/2.jpg'
	image2 = cv2.imread(image_path)
	image_path = os.getcwd() + '/test_images/' + str(x) + '/3.jpg'
	image3 = cv2.imread(image_path)
	image_path = os.getcwd() + '/test_images/' + str(x) + '/4.jpg'
	image4 = cv2.imread(image_path)
	image_path = os.getcwd() + '/test_images/' + str(x) + '/5.jpg'
	image5 = cv2.imread(image_path)

	feature_vector = []
	feature_vector.append(test_ft.FeatureExtraction(image))
	#feature_vector.append(test_ft.FeatureExtraction(image2))
	#feature_vector.append(test_ft.FeatureExtraction(image3))
	#feature_vector.append(test_ft.FeatureExtraction(image4))
	#feature_vector.append(test_ft.FeatureExtraction(image5))
	#feature_vector = np.asarray(feature_vector)
	#
	#model_folder = os.getcwd() + '/object_classifiers/' + str(x+1) + '_classifier.pkl'
	#model_clone = joblib.load(model_folder)
	#
	##dbn_folder = os.getcwd() + '/object_classifiers/' + str(x) + '_dbn_classifier.pkl'
	##dbn_clone = joblib.load(dbn_folder)
	#
	#preds = model_clone.predict(feature_vector)
	#dbn_preds = dbn_clone.predict(np.atleast_2d(feature_vector))
	
	#with open("results.txt", "a") as myfile:
	#    myfile.write("Object " + str(x) + ": \n")
	#    myfile.write("GMM\n")
	#    myfile.write(classification_report([1,1,0,0,1], preds))
	#    #myfile.write("\n")
	#    #myfile.write("DBN\n")
	#    #myfile.write(classification_report([1,1,0,0,1], dbn_preds))
	#    myfile.write("\n\n")
	results.append(identify_objects(feature_vector, x))
    return results


def identify_objects(feature_vector, object_id):
    answers = []
    models = []
    
    for objectID in range(1,18):
	model_folder = os.getcwd() + '/object_classifiers/' + str(objectID) + '_classifier.pkl'
	model_clone = joblib.load(model_folder)
	models.append(model_clone)
	
	answers.append(model_clone.predict(feature_vector))
    
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
    

def build_object_classifiers(cursor, con):
    
    for id in range(1,18):
	feature_matrix = []
	feature_matrix_labels = []
	count = 0
	#for obs_id in range(1,18):
	object_matrix = []
	cursor.execute("SELECT COUNT(*) FROM FeatureInfo WHERE feature_id='0' AND observation_id='{0}'".format(id))
	num_of_images_per_observation=cursor.fetchone()[0]
	
	cursor.execute("SELECT feature_id,feature_value FROM FeatureInfo WHERE observation_id='{0}'".format(id))
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
		    
	feature_matrix=np.asarray(feature_matrix)
	feature_matrix_labels = np.asarray(feature_matrix_labels)
	
	#dbn = DBN([feature_matrix.shape[1], 300, 2], learn_rates = 0.3, learn_rate_decays = 0.9, epochs = 100, verbose = 0)
	#dbn.fit(feature_matrix, feature_matrix_labels)
	#joblib.dump(dbn, 'object_classifiers/' + str(id) + '_dbn_classifier.pkl')
	
	g = mixture.GMM(n_components=2, covariance_type = 'tied')
	g.fit(feature_matrix)
	joblib.dump(g, 'object_classifiers/' + str(id) +'_classifier.pkl') #NAME OF FOLDER TO SAVE THE NEW RETRAINED MODELS		
	
	#feature_matrix_labels = np.array(feature_matrix_labels)
	#y_train_pred = g.predict(feature_vector)
	#print classification_report([1,0,0,1,1,1], y_train_pred)

def build_model(cursor, con, gameID, stopping_point):
#    for i in range(gameID, stopping_point):
#	retrain.Model_Retrain(i+1,con)
    
    np.set_printoptions(threshold='nan')
    
    #get all the different tags available
    cursor.execute("SELECT DISTINCT(tag) FROM TagInfoBk") 
    results=cursor.fetchall()
    
    tags = []
    for result in results:
	tags.append(result[0])
    
    count = 0
    
    #for each tag we select all the observation_ids that are related to it
    for tag in tags: 
	feature_matrix=[]#initialize feature matrix for each different tag
	feature_matrix_labels = [] # Labels to indicate if the example is positive or negative
	cursor.execute("SELECT DISTINCT(observation_id) FROM TagInfoBk WHERE tag=%s",(tag))
	tag_obs_ids=cursor.fetchall()
	cursor.execute('SELECT id FROM Tags WHERE tag = %s', (tag))
	qid = cursor.fetchone()[0]

	should_train = False
	#for every observation/object of this spesific tag
	for obs_id in tag_obs_ids:
	    
	    object_matrix = []
	    T = get_t(obs_id[0], qid, cursor)
	    if T >= 3:
		should_train = True
		count = count + 1
		cursor.execute("SELECT COUNT(*) FROM FeatureInfo WHERE feature_id='0' AND observation_id='{0}'".format(obs_id[0]))
		num_of_images_per_oservation=cursor.fetchall()
		
		cursor.execute("SELECT feature_id,feature_value FROM FeatureInfo WHERE observation_id='{0}'".format(obs_id[0]))
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
		
	#    elif T == 0:
	#	print tag, 'False'
	#	should_train = True
	#	count = count + 1
	#	cursor.execute("SELECT COUNT(*) FROM FeatureInfo WHERE feature_id='0' AND observation_id='{0}'".format(obs_id[0]))
	#	num_of_images_per_oservation=cursor.fetchall()
	#	
	#	cursor.execute("SELECT feature_id,feature_value FROM FeatureInfo WHERE observation_id='{0}'".format(obs_id[0]))
	#	feature_info=cursor.fetchall()
	#	
	#	vv_seperator=len(feature_info)/num_of_images_per_oservation[0][0]
	#	
	#	new_fv=0 #flag to show when a feature vector given a capture starts (index in feature_info tuple)
	#	end_of_fv=vv_seperator#flag to show when a feature vector given a capture ends (index in feature_info tuple)
	# 
	#	for capture_id in xrange(0,num_of_images_per_oservation[0][0]): 
	#	    feature_vector=RetrieveFeatureVector(feature_info,new_fv,end_of_fv) #create a feature vector given a capture 
	#	    #print len(feature_vector)
	#	    new_fv=new_fv+vv_seperator #update starting index of the vector
	#	    end_of_fv=end_of_fv+vv_seperator #update ending index of the vector
	#	    object_matrix.append(feature_vector) #insert feature vectors into a matrix for each tag
	#	
	#	feature_matrix.append(object_matrix)
	#	feature_matrix_labels.append(0)
		    
	if should_train:
	    feature_matrix=np.asarray(feature_matrix)
	    model.ModelTraining(tag, feature_matrix, 777) #training the model
	    
#	    model_file = os.getcwd()+'/GMM_model_777/' + tag + '_model.pkl'
#	    model_clone = joblib.load(model_file)
#
#	    feature_matrix_labels = np.array(feature_matrix_labels)
#            y_train_pred = model_clone.predict(feature_matrix)
#	    y_train_score = model_clone.score(feature_matrix)
#	    train_accuracy = np.mean(y_train_pred.ravel() == feature_matrix_labels.ravel()) * 100
#	    print "Training accuracy for " + tag + ": " + str(train_accuracy)
#	    print y_train_score
	    
    print count


def get_t(object_id, question_id, cursor):

    tag = get_tag(question_id, cursor)

    cursor.execute('SELECT COUNT(*) \
                    FROM Descriptions \
                    WHERE description like %s \
                    AND objectID = %s', ('%{0}%'.format(tag), object_id))

    return cursor.fetchone()[0]


def get_tval(cursor):
    cursor.execute('SELECT yes_answers/total_answers FROM Pqd')

    result = cursor.fetchall()

    tvals = []
    for r in result:
        tvals.append(float(r[0]))

    return tvals
 
    
def get_questions_answers(object_id, cursor):
    cursor.execute('SELECT qid, oid, answer from answers where oid = %s', (object_id))

    results = cursor.fetchall()

    questions_answers = {}
    for i in range(1, 290):
        questions_answers[i] = []

    for qid, oid, answer in results:
        for i in range(1, 290):
            if int(qid) == i:
                questions_answers[i].append(int(answer))

    return questions_answers


def get_tag(question_id, cursor):
    cursor.execute('SELECT tag from Tags where id = %s', (question_id))

    return cursor.fetchone()[0]


def get_p_tag(cursor):    
    p_tags = []
    tags = get_tags(cursor)
    for tag in range(1,290):
	answers = {}
	cursor.execute("SELECT COUNT(*) FROM answers WHERE qid = %s and answer = TRUE", tag)
	answers[1] = cursor.fetchone()[0]
	cursor.execute("SELECT COUNT(*) FROM answers WHERE qid = %s and answer = FALSE", tag)
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
    feature_vectors = []
    for i in range(1,18):
	image_path = os.getcwd() + '/GAMES/Game' + str(game_id) + '/obj' + str(i) + '.jpg'
	image = cv2.imread(image_path)
	feature_vectors.append(test_ft.FeatureExtraction(image))
	
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
	    
    return models, feature_vectors


def gen_image_probabilities(game_id, cursor):
    models, feature_vectors = get_model_info(cursor, game_id)
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
    
    for i in available_models:
	total = 0
	for j in range(0,17):
	    total = total + probabilities[j][i]
	for j in range(0,17):
	    probabilities[j][i] = probabilities[j][i] / total
   
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


def get_best_question_tag_entropy(objects, asked_questions, pO, start, cursor, game_id, Pi, p_tags):
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


def get_best_question(objects, asked_questions, pO, start, cursor, game_id, Pi, p_tags):
    tvals = get_tval(cursor)

    top = (17 - start - 1)/2 + start + 1
    bottom = 17 - top
    bestDifference = 10
    bestD = 0
    
    probabilities_yes = []
    probabilities_no = [] 
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
	    
	if j not in asked_questions:
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
		
	    probabilities_yes = np.asarray(probabilities_yes)
	    probabilities_no = np.asarray(probabilities_no)
	    probabilities_yes = probabilities_yes / sum(probabilities_yes)
	    probabilities_no = probabilities_no / sum(probabilities_no)
	    
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
    probabilityD = get_tval(cursor)
    question_tag = tags[bestD-1]
    #answer = raw_input("Does it have " + tags[bestD-1] + "? (yes/no) ")
    #answer = answer.lower()
    answer = answer_data[OBJECT_WE_PLAY-1][bestD-1]
    print game_folder, OBJECT_WE_PLAY,objectlist[OBJECT_WE_PLAY-1][0],'qt->'+question_tag+' ' ,'ans->'+answer 

    if not (answer):
	    print game_folder, OBJECT_WE_PLAY,'qt->'+question_tag+' ' ,'sd'+answer+'<-', objectlist[OBJECT_WE_PLAY-1][0]
	    
	    sys.exit()
	    
    if answer == 'yes' or answer is 'yes':
	    answers.append(True)
	    if Pi[0][bestD-1] == -1:
		for objectID in range(0,17):
		    T = get_t(objectID+1, bestD, cursor)
		    N = sum(objects[objectID+1][bestD])
		    D = len(objects[objectID+1][bestD])
		    pO[objectID] = pO[objectID] * (probabilityD[T] + (N + 1)/(D + 2.0)) / 2 #/((p_tags[bestD-1][1] + 1) / float(p_tags[bestD-1][1] + p_tags[bestD-1][0] + 2))	
	    else:
		for objectID in range(0,17):
		    T = get_t(objectID+1, bestD, cursor)
		    N = sum(objects[objectID+1][bestD])
		    D = len(objects[objectID+1][bestD])
		    pO[objectID] = pO[objectID] * ((probabilityD[T] + (N + 1)/(D + 2.0) + Pi[objectID][bestD-1])) / 3 #/((p_tags[bestD-1][1] + 1) / float(p_tags[bestD-1][1] + p_tags[bestD-1][0] + 2))

    else:
	    if answer =='no' or answer is 'no':
			answers.append(False)
			if Pi[0][bestD-1] == -1:
			    for objectID in range(0,17):
				T = get_t(objectID+1, bestD, cursor)
				N = sum(objects[objectID+1][bestD])
				D = len(objects[objectID+1][bestD])
				pO[objectID] = pO[objectID] * ((1 - probabilityD[T]) + (D - N + 1)/(D + 2.0)) / 2 #/((p_tags[bestD-1][1] + 1) / float(p_tags[bestD-1][0] + p_tags[bestD-1][0] + 2))	    
			else:
			    for objectID in range(0,17):
				T = get_t(objectID+1, bestD, cursor)
				N = sum(objects[objectID+1][bestD])
				D = len(objects[objectID+1][bestD])
				pO[objectID] = pO[objectID] * (((1 - probabilityD[T]) + (D - N + 1)/(D + 2.0) + 1 - Pi[objectID][bestD-1])) / 3 #/((p_tags[bestD-1][0] + 1) / float(p_tags[bestD-1][1] + p_tags[bestD-1][0] + 2))
				    
    pO = pO / np.sum(pO)
    
    with open("example.txt", "a") as myfile:
	    myfile.write(question_tag + " -> " + answer+ " \n")
	    myfile.write(str(pO) + "\n")
	
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
    objectlist = []
    
    cursor.execute("SELECT DISTINCT(name) FROM NameInfo;")
    obj = cursor.fetchall()
    
    OBJ = np.asarray(obj)
    for OB in OBJ:
	    objectlist.append(OB)
	    
    return objectlist


def get_object_ids(cursor):
    obj_id = []

    cursor.execute("SELECT DISTINCT(observation_id) \
		   FROM NameInfo;")
    objid = cursor.fetchall()
    
    obj_ID = np.asarray(objid)
    for objID in obj_ID:
	    obj_id.append(objID[0])

    return obj_id


def get_tags(cursor):
    cursor.execute("SELECT tag \
		   FROM Tags")
    tags = cursor.fetchall()
    
    tags_list = []
    
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
    
    for i in range(0, len(questions)):
	T = get_t(object_id, questions[i], cursor)
	#print object_id, questions[i], answers[i]
	if answers[i] == True:
	    cursor.execute("SELECT yes_answers FROM Pqd where t_value = %s", T)
	    yes_count = cursor.fetchone()[0]
	    #print yes_count, 'yes'
	    cursor.execute("UPDATE Pqd SET yes_answers = %s WHERE t_value = %s", (yes_count + 1, T))
	    
	cursor.execute("SELECT total_answers FROM Pqd where t_value = %s", (T))
	total_count = cursor.fetchone()[0]
	#print total_count
	cursor.execute("UPDATE Pqd SET total_answers = %s WHERE t_value = %s", (total_count + 1, T))
	
	cursor.execute("INSERT INTO answers (oid, qid, answer) VALUES (%s, %s, %s)", (object_id, questions[i], answers[i]))
	    
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

    print guess2say
    print object_guess
    if object_guess == guess2say:
	print 'won'
	return 1
    else:
	print 'lost'
	return 0


def play_object(cursor, object_id, tags, gameID, all_games, objectlist, con, Pi):
    objects = gen_init_prob(cursor)
    folder =  os.getcwd()    
    
    p_tags = get_p_tag(cursor)
    
    answer_data = np.genfromtxt(folder+'/Answers/Game'+str(gameID)+'.csv',dtype=str, delimiter='\t')
    NoOfQuestions = 0
    pO = []
    game_folder = all_games + '/Game' + str(gameID)
    
    print "+++++++++++++++" + game_folder + "+++++++++++++++"

    initial_prob = 1/float(17)  
    for item in xrange(0, 17):
	pO.append(initial_prob)			
    
    pO = np.asarray(pO)	
 
    objects = gen_init_prob(cursor)

    askedQuestions = []
    answers = []
    split = 0
    #answer_data = np.genfromtxt('/local2/awh0047/iSpy/ispy_python/Answers/Game' + str(gameID) + '.csv',dtype=str, delimiter='\t')

    while np.sort(pO)[pO.size - 1] - np.sort(pO)[pO.size - 2] < 0.15:
	best_question = get_best_question(objects, askedQuestions, pO, split, cursor, gameID, Pi, p_tags)
	askedQuestions.append(best_question)
        pO, answers = ask_question(cursor, answer_data, object_id, best_question, answers, pO, tags, game_folder, objectlist, objects, Pi, p_tags)
	split = get_subset_split(pO)
    
    minimum=np.max(pO)
    itemindexes =[i for i,x in enumerate(pO) if x==minimum]
    A = np.asarray(objectlist)
    guess = A[itemindexes]
    guess2say =  guess[0][0]
    
    result = guess_object(pO, objectlist[object_id-1][0], guess2say)

    print len(askedQuestions)
    
    record_object_results(cursor, object_id, answers, askedQuestions, con, guess2say, result, gameID)
    
    return result, len(askedQuestions)


def play_round(cursor, tags, gameID, all_games, objectlist, con):
    obj_ids = get_object_ids(cursor)
    
    Pi = gen_image_probabilities(gameID, cursor)
    
    NoOfQuestions = 0
    round_wins = 0
    round_losses = 0
    avg_win = 0
    avg_lose = 0
    
    for OBJECT_WE_PLAY in obj_ids:
        result, number_of_questions = play_object(cursor, OBJECT_WE_PLAY, tags, gameID, all_games, objectlist, con, Pi)
	if result == 0:
	    round_losses = round_losses + 1
	    avg_lose = avg_lose + number_of_questions
	else:
	    round_wins = round_wins + 1
	    avg_win = avg_win + number_of_questions
	NoOfQuestions = number_of_questions + NoOfQuestions
	    
    record_round_results(gameID, round_wins, round_losses, NoOfQuestions)
    
    return round_wins, round_losses, NoOfQuestions, avg_win, avg_lose
    

def play_game(cursor, con):
    wins=0
    losses=0
    number_of_questions = 0
    avg_win = 0
    avg_lose = 0
    
    build_model(cursor, con, 1, 16)
    
    folder =  os.getcwd()
    all_games = folder + '/Human_Games'
    
    objectlist = build_object_list(cursor)
    tags = get_tags(cursor)

    for gameID in range(16,17):
	   round_wins, round_losses, round_questions, avg_for_win, avg_for_lose = play_round(cursor, tags, gameID, all_games, objectlist, con)
	   build_model(cursor, con, gameID, gameID+1)
           #test_unknown_image(cursor, tags, gameID)
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
    con = sql_driver().connect('localhost', 'iSpy_team', 'password', 'iSpy_features')
    with con:
	cursor = con.cursor()

    #test_images(cursor)
    #get_p_tag(cursor)
    #build_model(cursor, con, 1, 2)
    #build_object_classifiers(cursor,con)
    
    #first.Object_Learning(0,con)
    
    #test_object_classifiers()
    
    test_object_classifiers_over_time(cursor, con)
    
    #test_unknown_image(cursor, get_tags(cursor), 16)
    #add_answerset(cursor, 16, con)
    
    #play_game(cursor, con)
    #copy_into_answers(cursor, get_tags(cursor))
    #con.commit()
    #build_pqd(cursor, con, get_tags(cursor))
    
    pass
    
		      
if __name__ == '__main__':
        sys.exit(main())
	
