from sys import exit

driver = None

try:
	import MySQLdb
	driver = MySQLdb
	print "Using mysqldb"
except ImportError:
	print "mysqldb not found, trying pymysql"
	
	try:
		import pymysql
		driver = pymysql
		print "Using pymysql"
	except ImportError:
		print "pymysql not found, aborting"
		exit()

def sql_driver():
	return driver
