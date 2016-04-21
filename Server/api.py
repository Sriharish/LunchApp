#!/usr/bin/python
from flask import Flask, jsonify, request
from OpenSSL import SSL
import json
context = SSL.Context(SSL.SSLv23_METHOD)
context.use_privatekey_file('lunchapp.key')
context.use_certificate_file('lunchapp.cert')
key = ''

class Business:
	def __init__(self, id, name, stars, review_count, latitude, longitude, terms, categories):
		self.id = id
		self.name = name
		self.stars = stars
		self.review_count = review_count
		self.latitude = latitude
		self.longitude = longitude
		self.terms = terms
		self.categories = categories
	def display(self):
		print self.id, self.name, self.stars, self.review_count, self.latitude, self.longitude, self.terms, self.categories


#find average days since visit history for a given set of users and a single business
def find_business_history(business_id,user_ids):
	sum_days_since = 0
	#query for all given users
	for user_id in user_ids:
		results = cur.execute("SELECT days_since FROM history WHERE business_id=:businessid AND user_id=:userid", {"businessid": business_id,"userid": user_id})
		for item in results:
			#print item
			sum_days_since = sum_days_since + item[0]
	#print sum_days_since*1.0 / len(user_ids)
	return sum_days_since*1.0 / len(user_ids) # reutrn average

#find history as function of business id and rank
def find_history(business_ids,user_ids):
	history = {}
	sum_history = 0.0
	max_history = 0.0
	#query history
	for business_id in business_ids:
		history[business_id] = find_business_history(business_id,user_ids)
		if max_history < history[business_id]:
			max_history = history[business_id]
	#calculate based on max history
	for business_id in business_ids:
		history[business_id] = history[business_id]*1.0/max_history
		sum_history += history[business_id]
	for business_id in business_ids:
		history[business_id] = history[business_id]*1.0/sum_history
	return history
		
	
def cousine_avg_ratings(user_ids,cousine_len):
	
	cuisine = [0]*cousine_len
	num_users = len(user_ids)
	for user_id in user_ids:
		results = cur.execute("SELECT * FROM users WHERE user_id=:userid", {"userid": user_id})
		for item in results:
			#print item
			for i in range(0,len(cuisine)):
				cuisine[i] = cuisine[i] + (item)[i]
	for i in range(0,len(cuisine)):
		cuisine[i]=cuisine[i]*1.0/num_users
	#print cuisine
	return cuisine
	
#compare to cuisine vectors
def compare_cousine(from_vector,to_vector,cousine_len):
	count = 0
	for i in range(0,cousine_len):
		#if from_vector[i] == 1 and to_vector[i] == 1:
		count = count + from_vector[i]*to_vector[i]
	return count

#transport matrix calulations; rank by star diff x # category links	
def rank_business_links(from_business_id,business_ids,cousine_len):
	count = 0
	links = {}
	from_vector = []
	to_vector = []
	from_stars = 0.0
	to_stars = 0.0
	#get from outlinks
	results = (cur.execute("SELECT * FROM business WHERE business_id=:businessid", {"businessid": from_business_id}))
	for item in results:
		from_vector = item[0:cousine_len]
	#get from stars
	results = (cur.execute("SELECT stars FROM business WHERE business_id=:businessid", {"businessid": from_business_id}))
	for item in results:
		from_stars = item[0]
	for to_business_id in business_ids:
		#get to inlinks
		results = (cur.execute("SELECT * FROM business WHERE business_id=:businessid", {"businessid": to_business_id}))
		for item in  results:
			to_vector = item[0:cousine_len]
		#get to stars
		results = (cur.execute("SELECT stars FROM business WHERE business_id=:businessid", {"businessid": to_business_id}))
		for item in results:
			to_stars = item[0]
			
		links[to_business_id] = compare_cousine(from_vector,to_vector,cousine_len)*(5.0-abs(from_stars-to_stars))
		count += links[to_business_id]
	for to_business_id in business_ids:
		links[to_business_id] = links[to_business_id]*1.0/count
	return links

#rank cuisine & how it matches users
def rank_business_cousine(cuisine,business_ids,cousine_len):
	count = 0
	cousine_ranks = {}
	to_vector = []
	for to_business_id in business_ids:
		results = (cur.execute("SELECT * FROM business WHERE business_id=:businessid", {"businessid": to_business_id}))
		for item in results:
			to_vector = item[0:cousine_len]
		cousine_ranks[to_business_id] = compare_cousine(cuisine,to_vector,cousine_len)
		#print cousine_ranks[to_business_id]
		count += cousine_ranks[to_business_id]
	for to_business_id in business_ids:
		cousine_ranks[to_business_id] = cousine_ranks[to_business_id]*1.0/count
	return cousine_ranks

#create pagerank row		
def pagerank_row(business_ids,user_ids,start_business_id,link_weight,history_weight,cousine_weight):
	cousine_len = 25
	cuisine = cousine_avg_ratings(user_ids,cousine_len)
	history = find_history(business_ids,user_ids)
	link = rank_business_links(start_business_id,business_ids,cousine_len)
	cousine_rank = rank_business_cousine(cuisine,business_ids,cousine_len)
	num_business = len(business_ids)
	rank = {}
	for business_id in business_ids:
		rank[business_id] = cousine_weight*cousine_rank[business_id] + history_weight*history[business_id] + link_weight*link[business_id] + (1-cousine_weight-history_weight-link_weight)*1.0/num_business
	#convert to list
	list =  rank.items()
	list.sort()
	ranks = []
	sum = 0.0
	for item in list:
		sum += item[1]
		ranks.append(item[1])
	#print ranks,sum
	return ranks

#create pagerank matrix
def pagerank_matrix(business_ids,user_ids,link_weight,history_weight,cousine_weight):
	matrix = []
	for start_business_id in business_ids:
		matrix.append(pagerank_row(business_ids,user_ids,start_business_id,link_weight,history_weight,cousine_weight))
	#print matrix
	return matrix

#calculate pagerank iteration
def pagerank_loop(matrix,previous_vector):
	size = len(previous_vector)
	newvector = [0]*size
	for c in range(0,size):
		for r in range(0,size):
			newvector[c]+=previous_vector[r]*matrix[r][c]
	#print "Previousvector", previous_vector
	#print "Newvector     ", newvector
	return newvector

#check rss
def pagerank_convergence(previous_vector,vector):
	rss = 0.0
	for i in range(0,len(vector)):
		rss = pow(previous_vector[i]-vector[i],2)
	return rss

#run topic specific pagerank
def pagerank(business_ids,user_ids,link_weight,history_weight,cousine_weight,convergence_rss):
	vector = [0.0]*len(business_ids)
	previous_vector = [0.0]*len(business_ids)
	previous_vector[0] = 1.0
	matrix = pagerank_matrix(business_ids,user_ids,link_weight,history_weight,cousine_weight)
	#print "Matrix", matrix
	while True:
		vector = pagerank_loop(matrix,previous_vector)
		if convergence_rss > pagerank_convergence(previous_vector,vector):
			break
		#print vector
	return vector


	

#main code
conn = sqlite3.connect('lunchapp.db')
cur = conn.cursor()
example()
conn.commit()
conn.close()
		
		
#flask
app = Flask(__name__)

	
def load:
	with open('.lunchapp.conf','r') as infile: 
		results = json.load(infile)
		cities = ['Las Vegas']
		#print results
		if 'key' in results:
			k = results['key']
			if key != k:
				return jsonify({'error': "auth failure"})
		else:
			return jsonify({'error': "auth load failure"})
		if 'cities' in results:
			cities = results['cities']
			if city not in cities:
				return jsonify({'error': "city not found"})
		else:
			return jsonify({'error': "cities load failure"})
		if 'db' in results and 'dbhost' in results and 'dbru' in results and 'dbrp' in results:
			#try:
			cnx = mysql.connector.connect(user=results['dbru'],password=results['dbrp'],host=results['dbhost'],database=results['db']);
			cursor = cnx.cursor()

			
		business_ids = ['b0000','b0001','b0002','b0003','b0004','b0005','b0006','b0007']
		user_ids = ['u0000','u0001','u0002','u0003']
		link_weight = 0.1
		history_weight = 0.4
		cousine_weight = 0.3
		convergence_rss = 0.1
	
	for user in users:
		cur.execute('''SELECT cousine,dislikes,city FROM users WHERE username=%s''',(user,))
		for row in cur:
			if row is not None:
				for like in row[0]:
					if like in likes:
						likes[like] = likes[like] + 1
				for dislike in row[1]:
					if dislike in dislikes:
						dislikes[dislike] = dislikes[dislike] + 1
				if row[2] not in cities:
					cities[row[2]] = 1
	if len(cities) != 1:
		return jsonify({'error': "city failure"})
	city = cities[0]
	
	#build query
	query = '''SELECT * FROM businesses WHERE city=%s'''
	for dislike in dislikes:
		query += '''AND businesses.likes NOT LIKE \'''' + str(dislike) + '''\%\''''
	
	bizs = []
	cur.execute(query, (city,))
	for row in cur:
		if row is not None:
			biz.append(Business())
	
	
	cnx.commit()
	cursor.close()
	cnx.close()
			
def user():

	


@app.route('/lunchapp/api/v1.0/recomendation', methods=['GET'])
def recomendation():
	k = request.args.get('key')
	#lat = request.args.get('lat')
	#lng = request.args.get('lng')
	#link_weight  = request.args.get('link_weight ')
	#history_weight = request.args.get('history_weight')
	#cousine_weight = request.args.get('cousine_weight')
	#convergence_rss = request.args.get('convergence_rss')
	
	user_ids = request.args.getlist('user_ids')

	#example code
	rank = pagerank(business_ids,user_ids,link_weight,history_weight,cousine_weight,convergence_rss)
	output = {}
	for i in range(0,len(business_ids)):
		results = cur.execute("SELECT name FROM business WHERE business_id=:businessid", {"businessid": business_ids[i]})
		for name in results:
			output[name[0]] = rank[i]
	ordered_output = output.items()
	ordered_output.sort(key=lambda tup: tup[1],reverse=True)
	for option in ordered_output:
		print (str(option[0])+': '+str(option[1]))
	
#/lunchapp/api/v1.0/useradd&key=&username=
@app.route('/lunchapp/api/v1.0/useradd', methods=['GET'])
def useradd():
	k = request.args.get('key')
	first = request.args.get('first')
	last = request.args.get('last')
	userid = request.args.get('userid')
	city = (request.args.get('city')).replace('+',' ')
	distance = request.args.get('distance')
	dislikes = request.args.getlist('dislikes')
	load(key,city,users)
	return jsonify({'userid': })
	
#/lunchapp/api/v1.0/usercuisine&key=&username=
@app.route('/lunchapp/api/v1.0/usercuisine', methods=['GET'])
def usercuisine():
	k = request.args.get('key')
	userid = request.args.get('userid')
	cuisine = request.args.getlist('cuisine')
	#return jsonify({'tasks': tasks})

if __name__ == '__main__':
	load()
	app.run(host='127.0.0.1',port=8443,debug=True,threaded=True,ssl_context=context)
