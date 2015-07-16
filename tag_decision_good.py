from sql_driver import sql_driver
import numpy as np
import sys
import test_model 
import cv2
import os
import math
import test_features_extraction as test_ft
from sklearn.externals import joblib
import gmm_training as model


def score_tag(feature_vector, model):
    prob = model.score([feature_vector])
    return math.e ** (prob[0] / 100000.0)

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


def log_tag_answers(asked, answers, object_id):
    con = sql_driver().connect('localhost', 'iSpy_team', 'password', 'iSpy_features')
    with con:
        cur = con.cursor()

    for question in range(0, len(asked)):
        cur.execute("INSERT into QuestionAnswers (object, tag, answer) VALUES (" + str(object_id) + ", '" + asked[question] + "', " + str(answers[question]) + ")")
    con.commit()
    con.close()


def get_tval(cursor):
    cursor.execute('SELECT yes_answers/total_answers FROM Pqd')

    result = cursor.fetchall()

    tvals = []
    for r in result:
        tvals.append(float(r[0]))

    return tvals


def get_questions_answers(object_id, cursor):
    cursor.execute('SELECT qid, oid, answer from answers where oid = %s LIMIT 4200', (object_id))

    results = cursor.fetchall()

    questions_answers = {}
    for i in range(1, 289):
        questions_answers[i] = []

    for qid, oid, answer in results:
        for i in range(1, 289):
            if int(qid) == i:
                questions_answers[i].append(int(answer))

    return questions_answers


def get_tag(question_id, cursor):
    cursor.execute('SELECT tag from Tags where id = %s', (question_id))

    return cursor.fetchone()[0]


def get_t(object_id, question_id, cursor):

    tag = get_tag(question_id, cursor)

    cursor.execute('SELECT COUNT(*) \
                    FROM Descriptions \
                    WHERE description like %s \
                    AND objectID = %s', ('%{0}%'.format(tag), object_id))

    return cursor.fetchone()[0]


def gen_init_prob(cursor):
    objects = {}

    for i in range(1, 18):
        objects[i] = get_questions_answers(i, cursor)

    return objects


def get_best_question(objects, pO, asked_questions, cursor, start, Pi):
    tvals = get_tval(cursor)
    probabilities = []

    top = (17 - start - 1)/2 + start + 1
    bottom = 17 - top
    bestDifference = 0
    bestD = 0

    for i in range(0, 17):
        probabilities.append(0)

    for i in range(1, 18):
        for j in range(1, 289):
            if j not in asked_questions:
                T = get_t(i, j, cursor)
                num_yes = sum(objects[i][j])
                length = len(objects[i][j])

                if Pi[i-1][j-1] == -1:
                    probabilities[i-1] = pO[i-1] * (tvals[T] + (num_yes + 1.0)/(length + 2.0))
                else:
                    probabilities[i-1] = pO[i-1] * (tvals[T] + (num_yes + 1.0)/(length + 2.0) + Pi[i-1][j-1])
                probabilities.sort()
                probabilities.reverse()

                topProb = 0
                bottomProb = 0

                for x in range(start, top):
                    topProb = topProb + probabilities[x]

                for x in range(top, 17):
                    bottomProb = bottomProb + probabilities[x]

                topProb = topProb/(0.0 + top)
                bottomProb = bottomProb/(0.0 + bottom)

                if(abs(topProb - bottomProb) > bestDifference):
                    bestDifference = abs(topProb - bottomProb)
                    bestD = j

    return bestD


def get_question(question_id, cursor):
    cursor.execute('SELECT question from questions where qid = %s', (question_id))

    return cursor.fetchone()[0]


def get_object(object_id, cursor):
    cursor.execute('SELECT name from objects where id = %s', (object_id))

    return cursor.fetchone()[0]


def guess(pO):
    pO_sorted = np.sort(pO)

    if pO_sorted[pO_sorted.size - 1] - pO_sorted[pO_sorted.size - 2] >= 0.1:
        return True
    else:
        return False


def ask_question(objects, pO, question_id, answers, cursor, Pi):
    tvals = get_tval(cursor)

    while True:
        answer = raw_input('{0} yes/no: '.format(get_question(question_id, cursor)))
        if answer == 'yes':
            answers.append(True)
            for i in range(1, 18):
                T = get_t(i, question_id, cursor)
                num_yes = sum(objects[i][question_id])
                length = len(objects[i][question_id])
                if Pi[i-1][question_id-1] == -1:
                    pO[i-1] = pO[i-1] * (tvals[T] + (num_yes + 1.0)/(length + 2.0))
                else:
                    pO[i-1] = pO[i-1] * (tvals[T] + (num_yes + 1.0)/(length + 2.0) + Pi[i-1][question_id-1])
            break
        elif answer == 'no':
            answers.append(False)
            for i in range(1, 18):
                T = get_t(i, question_id, cursor)
                num_yes = sum(objects[i][question_id])
                length = len(objects[i][question_id])
                if Pi[i-1][question_id-1] == -1:
                    pO[i-1] = pO[i-1] * (1 - tvals[T] + (length - num_yes + 1.0)/(length + 2.0))
                else:
                    pO[i-1] = pO[i-1] * (1 - tvals[T] + (length - num_yes + 1.0)/(length + 2.0) - Pi[i-1][question_id-1])
            break
        else:
            print 'Try again!'

    pO = pO / sum(pO)

    pO_sorted = np.sort(pO)

    diff = 0
    bestDiff = 0

    for x in range(0, pO_sorted.size-1):
        if pO_sorted[x+1] - pO_sorted[x] > diff:
            diff = pO_sorted[x+1] - pO_sorted[x]
            bestDiff = x

    return answers, pO, bestDiff


def main():
    connection = mdb.connect('localhost', 'iSpy_team', 'password', 'iSpy_features')
    cursor = connection.cursor()

    asked_questions = []
    pO = np.full(17, float(1.0/17.0))
    answers = []

    Pi = gen_image_probabilities(1, cursor)

    objects = gen_init_prob(cursor)
    start = 0
    while True:
        best_question = get_best_question(objects, pO, asked_questions, cursor, start, Pi)
        ask_question(objects, pO, best_question, answers, cursor, Pi)
        asked_questions.append(best_question)
        start = get_subset_split(pO)
        if guess(pO):
            object_id = np.argsort(pO)[pO.size-1] + 1
            #object_name = get_object(object_id, cursor)
            raw_input("Is your object: '{0}'? yes/no: ".format(object_id))
            break

    connection.close()


if __name__ == '__main__':
        sys.exit(main())
