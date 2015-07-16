#!/usr/bin/python
# -*- coding: utf-8 -*-


"""
def Insert(cur,i):
############ INSERT  ITEMS ##########################
 if i==0:
    cur.execute("INSERT INTO TagInfo(observation_id,tag) VALUES('5','blue')")#set the tag_color name
    cur.execute("INSERT INTO TagInfo(observation_id,tag) VALUES('3','blue')")#set the tag_color name
    cur.execute("INSERT INTO TagInfo(observation_id,tag) VALUES('13','blue')")#set the tag_color name
    cur.execute("INSERT INTO TagInfo(observation_id,tag) VALUES('73','blue')")#set the tag_color name
    cur.execute("INSERT INTO TagInfo(observation_id,tag) VALUES('83','blue')")#set the tag_color name

    cur.execute("INSERT INTO TagInfo(observation_id,tag) VALUES('7','black')")#set the tag_color name

    
    for index in xrange(0,586):
      cur.execute("INSERT INTO FeatureInfo(observation_id,feature_id,feature_value) VALUES(83,0,100)")#set the tag_color name
      cur.execute("INSERT INTO FeatureInfo(observation_id,feature_id,feature_value) VALUES(73,0,63)")#set the tag_color name
      cur.execute("INSERT INTO FeatureInfo(observation_id,feature_id,feature_value) VALUES(13,0,0.4)")#set the tag_color name
      cur.execute("INSERT INTO FeatureInfo(observation_id,feature_id,feature_value) VALUES(5,0,35)")#set the tag_color name
      cur.execute("INSERT INTO FeatureInfo(observation_id,feature_id,feature_value) VALUES(3,1,0.06)")#set the tag_color name        
 else : 
    cur.execute("INSERT INTO TagInfo(observation_id,tag) VALUES('{0}','green')".format(i))#set the tag_color name
"""  

    

############ INSERT FEATURE VECTORS FOR EACH OBJECT TO THE DATABASE ##########################
def InsertFeatureVector(con,obs_id,feature_id,feature_value,game_id):
 cur = con.cursor()
 cur.execute("INSERT INTO FeatureInfo(observation_id,feature_id,feature_value,game_id) VALUES('{0}','{1}','{2}','{3}')".format(obs_id,feature_id,feature_value,game_id))#set the tag_color name
 #con.commit()








