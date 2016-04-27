#!/usr/bin/python
import json, sys, io, re, mysql.connector, copy
from flask import jsonify

def load():
	with open('.eatr.json','r') as infile: 
		results = json.load(infile)
		cities = ['Las Vegas']
		cuisine = ['Restaurants']
		#print results
		if 'cities' in results:
			cities = results['cities']
		if 'cuisine' in results:
			cuisine = results['cuisine']
		if 'db' in results and 'dbhost' in results and 'dbsu' in results and 'dbsp' in results:
			#try:
			cnx = mysql.connector.connect(user=results['dbsu'],password=results['dbsp'],host=results['dbhost'],database=results['db']);
			cursor = cnx.cursor()
	
			createbusiness(cursor,cuisine)
			createusers(cursor,cuisine)
			createhistory(cursor)
	
			for city in cities:
				loadbusiness(cursor,cuisine,city,'yelp_academic_dataset_business.json')
	
	cnx.commit()
	cursor.close()
	cnx.close()

def colname(name):
	return name.replace(' ','_').replace('-','_').replace('/','_').replace('&','_').replace('(','_').replace(')','_').lower()

def createbusiness(cursor,cuisine):
	try:
		query = '''CREATE TABLE business ( '''
		for cat in cuisine:
			query += colname(cat) + ''' REAL, '''
		query += '''latenight INTEGER, lunch INTEGER, dinner INTEGER, brunch INTEGER, breakfast INTEGER, '''
		query += '''business_id VARCHAR(32) PRIMARY KEY, name VARCHAR(64), stars REAL, review_count INTEGER, latitude REAL, longitude REAL, city VARCHAR(32))'''
		cursor.execute(query)
	except mysql.connector.Error as err:
		print err

def createusers(cursor,cuisine):
	try:
		query = '''CREATE TABLE users ('''
		for cat in cuisine:
			query += colname(cat) + ''' REAL,'''
		query += '''user_id VARCHAR(64) PRIMARY KEY, username VARCHAR(32), email VARCHAR(256), password VARCHAR(64), phone INTEGER, distance REAL, city VARCHAR(32))'''
		cursor.execute(query)
	except mysql.connector.Error as err:
		print err

def createhistory(cursor):
	try:
		query = '''CREATE TABLE history (days_since INTEGER, visits INTEGER, business_id VARCHAR(32), user_id VARCHAR(64), PRIMARY KEY (business_id,user_id))'''
		cursor.execute(query)
	except mysql.connector.Error as err:
		print err		
		
def loadbusiness(cursor,cuisine,city,path):
	latenight = 0
	lunch = 0
	dinner = 0
	brunch = 0
	breakfast = 0
	query = '''INSERT INTO business ('''
	for cat in cuisine:
			query += colname(cat) + ''','''
	query += '''latenight, lunch, dinner, brunch, breakfast, business_id, name, stars, review_count, latitude, longitude, city) VALUES ('''
	for i in range(0,len(cuisine)+11):
			query += '''%s,'''
	query += '''%s)'''
	
	with open(path,'r') as businessfile: 
		for line in businessfile:
			#if bizcount > 25:
			#	break
			values = [0]*len(cuisine)
			business = json.loads(line)
			if 'city' in business:
				if city != business['city']:
					continue
			if 'categories' in business:
				if 'Restaurants' not in business['categories']:
					continue
				for cat in business['categories']:
					for i in range(0,len(cuisine)):
						if cat == cuisine[i]:
							values[i] = 1
							break			
							
			if 'attributes' in business:
				if 'Good For' in business['attributes']:
					#print business['attributes']['Good For']
					if 'latenight' in business['attributes']['Good For']:
						if business['attributes']['Good For']['latenight'] == True:
							values.append(1)
							latenight += 1
						else:
							values.append(0)
					else:
							values.append(0)
					if 'lunch' in business['attributes']['Good For']:
						if business['attributes']['Good For']['lunch'] == True:
							values.append(1)
							lunch += 1
						else:
							values.append(0)
					else:
							values.append(0)
					if 'dinner' in business['attributes']['Good For']:
						if business['attributes']['Good For']['dinner'] == True:
							values.append(1)
							dinner += 1
						else:
							values.append(0)
					else:
							values.append(0)
					if 'brunch' in business['attributes']['Good For']:
						if business['attributes']['Good For']['brunch'] == True:
							values.append(1)
							brunch += 1
						else:
							values.append(0)
					else:
							values.append(0)
					if 'breakfast' in business['attributes']['Good For']:
						if business['attributes']['Good For']['breakfast'] == True:
							values.append(1)
							breakfast += 1
						else:
							values.append(0)
					else:
							values.append(0)
				else:
					values.append(0)
					values.append(0)
					values.append(0)
					values.append(0)
					values.append(0)
			else:
				values.append(0)
				values.append(0)
				values.append(0)
				values.append(0)
				values.append(0)
			
					
			qvalues = tuple(values)
			qvalues = qvalues + (business['business_id'], business['name'], business['stars'], business['review_count'], business['latitude'], business['longitude'], business['city'])
			#print query, len(cuisine)+12, len(qvalues), business['name']
			#print business['business_id']
			cursor.execute(query, qvalues)
			#print business['business_id']
	print city,latenight,lunch,dinner,brunch,breakfast
		
if __name__ == '__main__':
	load()