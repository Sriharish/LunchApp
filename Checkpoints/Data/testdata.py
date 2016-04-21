#!/usr/bin/python
import json, requests, sys, io, unicodedata, time

places_key = ''
maps_key = places_key
geocoding_key = places_key

#get input path
#if len(sys.argv) != 2:
#	print "Error: Please provide path (./part1.py ./Data/)"
#	exit()

#path = sys.argv[1]

def set_coordinates(address):
	global lat
	global lng
	results = requests.get('https://maps.googleapis.com/maps/api/geocode/json?address='+address+'&key='+geocoding_key)
	coord = results.json()['results'][0]['geometry']['location']
	lat = coord['lat']
	lng = coord['lng']
	
def load(path):
	global keywords
	global bizmatrix
	count = 0
	with open(path,'r') as infile: 
		for keyword in json.load(infile)['keywords']:
			keywords[keyword] = count
			bizmatrix.append([0])
			count = count + 1

def decode_name(name):
	name = name.lower()
	#if 'inc' in name:
	#	name = name.replace('inc','')
	#if 'restaurant' in name:
	#	name = name.replace('restaurant','')
	#if 'bar' in name:
	#	name = name.replace('bar','')
	#if 'and' in name:
	#	name = name.replace('and','')
	return unicodedata.normalize('NFKD', name.strip()).encode('ascii', 'ignore')

def  next_pull(pagetoken, keyword, rounds):
	if rounds > 0:
		time.sleep(5)
		results = (requests.get('https://maps.googleapis.com/maps/api/place/nearbysearch/json?&pagetoken='+pagetoken+'&key='+places_key)).json()
		process(results,keyword)
		#print results
		if 'next_page_token' in results:
			next_pull((results['next_page_token']), keyword, rounds-1)
		


def inital_pull():
	global keywords
	for k in keywords:
		print ('@@@'+str(k))
		results = (requests.get('https://maps.googleapis.com/maps/api/place/nearbysearch/json?location='+str(lat)+','+str(lng)+'&radius='+str(rad)+'&keyword='+k+'&types=restaurant|bar|cafe&extensions&key='+places_key)).json()
		process(results,k)
		
		if 'next_page_token' in results:
			#print (results['next_page_token'])
			next_pull(results['next_page_token'],k,2)
		
		#with open(k+'.json','w') as outfile: 
		#	json.dump(results,outfile)


def get_time(dest):
	results = requests.get('https://maps.googleapis.com/maps/api/distancematrix/json?origins='+str(lat)+','+str(lng)+'&destinations='+dest+'&mode=driving&departure_time=now&units=imperial&traffic_model=pessimistic&key='+maps_key)
	return ((results.json())['rows'][0]['elements'][0]['duration']['value'])


def process(results,keyword):
	global biz
	global bizcount
	global bizmatrix
	global ratings
	for biz in results['results']:
		bizname = decode_name(biz['name'])
		
		if bizname not in bizs:
			bizs[bizname]=bizcount
			bizcount = bizcount + 1
			#expand matrix
			for i in range (0,len(keywords)):
				(bizmatrix[i]).append(0)
		print keywords[keyword], bizs[bizname]
		time = get_time(biz['vicinity'])
		(bizmatrix[keywords[keyword]])[bizs[bizname]] = 1
		
		if 'rating' in biz:
			print ('>>'+bizname+'='+str(biz['rating'])+'~'+str(time)+'s')
			ratings[bizname] = biz['rating']
		else:
			print ('>>'+bizname+'~'+str(time)+'s')
			ratings[bizname] = 0

		#with open(bizname+'.json','w') as outfile: #example found on stackoverflow on how to write json to a file in python
			#json.dump(biz,outfile)
		#if 
		#


address = 'Richardson+Bldg+TAMU'
lat=30.61
lng=-96.32
rad=32000
bizcount = 0
bizs = {} #bizname=id
keywords = {}#keyword=id
ratings = {}#bizname=rating
times = {}
keywords['Pizza'] = 0
keywords['Sea Food'] = 1
#keywords['Barbque'] = 2
#keywords['Steakhouse'] = 3
bizmatrix = [[0],[0]]#,[0],[0]]
		
#load('.keywords.json')
set_coordinates(address)
print lat, lng
#print keywords

inital_pull()


#print bizcount
#print bizs
#print bizmatrix
#print ratings