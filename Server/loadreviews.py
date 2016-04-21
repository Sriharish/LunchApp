#!/usr/bin/python
import json, sqlite3, mysql.connector
count = 0

def load():
	with open('.lunchapp.conf','r') as infile: 
		results = json.load(infile)
		#print results
		#if 'key' in results:
		#	key = results['key']
		if 'db' in results and 'dbhost' in results and 'dbwu' in results and 'dbwp' in results:
			#try:
			cnx = mysql.connector.connect(user=results['dbwu'],password=results['dbwp'],host=results['dbhost'],database=results['db']);
			cursor = cnx.cursor()
	
	loadreviews(cursor)
	
	cnx.commit()
	cursor.close()
	cnx.close()

def loadreviews(cursor):
	global count
	try:
		cursor.execute('''CREATE TABLE reviews (business_id VARCHAR(32), user_id VARCHAR(32), stars DECIMAL(2,1), content TEXT, date VARCHAR(16))''')
	except mysql.connector.Error as err:
		print err
	try:
		cursor.execute('''CREATE INDEX reviews_index ON reviews (business_id)''')
	except mysql.connector.Error as err:
		print err
	
	with open('yelp_academic_dataset_review.json','r') as reviewsfile: 
		for line in reviewsfile:
			review = json.loads(line)
			cursor.execute("INSERT INTO reviews VALUES (%s,%s,%s,%s,%s)", (review['business_id'],review['user_id'],review['stars'],review['text'],review['date']))
			print count
			count = count + 1
			#if count == 100:
			#	break
			
if __name__ == '__main__':
	load()