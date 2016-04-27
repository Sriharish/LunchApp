#!/usr/bin/python

#Please note security is very weak in this application and therefore please do not use in production. This is a POC and rough prototype implementation  only.

#import libs
from flask import Flask, jsonify, request
from OpenSSL import SSL
import json, hashlib, mysql.connector, time

#setup local ssl cert
context = SSL.Context(SSL.SSLv23_METHOD)
context.use_privatekey_file('eatr.key')
context.use_certificate_file('eatr.cert')

#global variables
key = 'none'
address = '127.0.0.1'
portnum = 8080
ssl = False
cities = []
categories = []
categories_formal = []
cur = None
cnx = None
tokens = {}
token_life = 3600
link_w = 0.1
history_w = 0.45
cuisine_w = 0.35
convergence_r = 1.0
		
#flask
app = Flask(__name__)

#find average days since visit history for a given set of users and a single business
def find_business_history(business_id,user_ids):
	sum_days_since = 0
	#query for all given users
	for user_id in user_ids:
		cur.execute("SELECT days_since FROM history WHERE business_id=%s AND user_id=%s", (business_id,user_id,))
		for item in cur:
			if item is not None:
				#print item
				sum_days_since = sum_days_since + item[0]
	#print sum_days_since*1.0 / len(user_ids)
	return sum_days_since*1.0 / len(user_ids) # return average

#find history as function of business id and rank
def find_history(business_ids,user_ids):
	history = {}
	sum_history = 0.0001
	max_history = 0.0001
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
		
#find avf cuisine ratings
def cousine_avg_ratings(user_ids,cousine_len):
	cuisine = [0]*cousine_len
	num_users = len(user_ids)
	for user_id in user_ids:
		cur.execute("SELECT * FROM users WHERE user_id=%s", (user_id,))
		for item in cur:
			if item is not None:
				#print item
				for i in range(0,cousine_len):
					cuisine[i] = cuisine[i] + (item)[i]
	for i in range(0,cousine_len):
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
	count = 0.0001
	links = {}
	from_vector = []
	to_vector = []
	from_stars = 0.0
	to_stars = 0.0
	#get from outlinks
	cur.execute("SELECT * FROM business WHERE business_id=%s", (from_business_id,))
	for item in cur:
		if item is not None:
			from_vector = item[0:cousine_len]
	#get from stars
	cur.execute("SELECT stars FROM business WHERE business_id=%s", (from_business_id,))
	for item in cur:
		if item is not None:
			from_stars = item[0]
	for to_business_id in business_ids:
		#get to inlinks
		cur.execute("SELECT * FROM business WHERE business_id=%s", (to_business_id,))
		for item in cur:
			if item is not None:
				to_vector = item[0:cousine_len]
		#get to stars
		cur.execute("SELECT stars FROM business WHERE business_id=%s", (to_business_id,))
		for item in cur:
			if item is not None:
				to_stars = item[0]
			
		links[to_business_id] = compare_cousine(from_vector,to_vector,cousine_len)*(5.0-abs(from_stars-to_stars))
		count += links[to_business_id]
	for to_business_id in business_ids:
		links[to_business_id] = links[to_business_id]*1.0/count
	return links

#rank cuisine & how it matches users
def rank_business_cousine(cuisine,business_ids,cousine_len):
	count = 0.0001
	cousine_ranks = {}
	to_vector = []
	for to_business_id in business_ids:
		cur.execute("SELECT * FROM business WHERE business_id=%s", (to_business_id,))
		for item in cur:
			if item is not None:
				to_vector = item[0:cousine_len]
		cousine_ranks[to_business_id] = compare_cousine(cuisine,to_vector,cousine_len)
		#print cousine_ranks[to_business_id]
		count += cousine_ranks[to_business_id]
	for to_business_id in business_ids:
		cousine_ranks[to_business_id] = cousine_ranks[to_business_id]*1.0/count
	return cousine_ranks

#create pagerank row		
def pagerank_row(business_ids,user_ids,start_business_id,link_weight,history_weight,cuisine_weight,cousine_len,num_business,history,cousine_rank):
	link = rank_business_links(start_business_id,business_ids,cousine_len)
	rank = {}
	for business_id in business_ids:
		rank[business_id] = cuisine_weight*cousine_rank[business_id] + history_weight*history[business_id] + link_weight*link[business_id] + (1-cuisine_weight-history_weight-link_weight)*1.0/num_business
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
def pagerank_matrix(business_ids,user_ids,link_weight,history_weight,cuisine_weight):
	matrix = []
	#calc overall parms
	cousine_len = len(categories)
	num_business = len(business_ids)
	cuisine = cousine_avg_ratings(user_ids,cousine_len)
	history = find_history(business_ids,user_ids)
	cousine_rank = rank_business_cousine(cuisine,business_ids,cousine_len)
	
	for start_business_id in business_ids:
		print start_business_id
		matrix.append(pagerank_row(business_ids,user_ids,start_business_id,link_weight,history_weight,cuisine_weight,cousine_len,num_business,history,cousine_rank))
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
def pagerank(business_ids,user_ids,link_weight,history_weight,cuisine_weight,convergence_rss):
	vector = [0.0]*len(business_ids)
	previous_vector = [0.0]*len(business_ids)
	previous_vector[0] = 1.0
	matrix = pagerank_matrix(business_ids,user_ids,link_weight,history_weight,cuisine_weight)
	#print "Matrix", matrix
	while True:
		vector = pagerank_loop(matrix,previous_vector)
		print vector
		if convergence_rss > pagerank_convergence(previous_vector,vector):
			break
		#print vector
	return vector

	
def load():
	global key
	global address
	global portnum
	global ssl
	global cities
	global categories
	global categories_formal
	global cur
	global cnx
	global link_w
	global history_w
	global cuisine_w
	global convergence_r
	with open('.eatr.json','r') as infile: 
		results = json.load(infile)
		cities = ['Las Vegas']
		#load values
		if 'key' in results:
			key = results['key']
		if 'address' in results:
			address = results['address']
		if 'port' in results:
			portnum = results['port']
		if 'ssl' in results:
			ssl = results['ssl']
		if 'cities' in results:
			cities = results['cities']
		if 'cuisine' in results:
			categories_formal = results['cuisine']
			for cat in categories_formal:
				categories.append(colname(cat))
		if 'link_weight' in results:
			link_w = results['link_weight']
		if 'history_weight' in results:
			history_w = results['history_weight']
		if 'cuisine_weight' in results:
			cuisine_w= results['cuisine_weight']
		if 'convergence_rss' in results:
			convergence_r = results['convergence_rss']
		if 'db' in results and 'dbhost' in results and 'dbru' in results and 'dbrp' in results:
			cnx = mysql.connector.connect(user=results['dbru'],password=results['dbrp'],host=results['dbhost'],database=results['db']);
			cur = cnx.cursor()
	
def colname(name):
	return name.replace(' ','_').replace('-','_').replace('/','_').replace('&','_').replace('(','_').replace(')','_').lower()

#auth with email & password, return token	
def auth_email_passwd(email,password):
	h = hashlib.sha1()
	h.update(password)
	password = h.hexdigest()
	userid = ''
	query = '''SELECT user_id FROM users WHERE email=%s AND password=%s'''
	cur.execute(query, (email,password))
	for row in cur:
		if row is not None:
			print row
			userid = row[0]
	return gen_token(userid)
	
#gen token
def gen_token(user_id):
	global tokens
	start = time.time()
	print start
	h = hashlib.sha1()
	h.update(str(user_id)+str(start))
	t = h.hexdigest()
	tokens[t] = (start+token_life,user_id)
	return t

#auth token
def auth_token(token):
	current = time.time()
	for t in tokens:
		if t[0] > current:
			del t
	if token is None:
		return None
	elif token in tokens:
		return tokens[token][1]
	else:
		return None

#check if email exists
def check_email(email):
	query = '''SELECT email FROM users WHERE email=%s'''
	cur.execute(query, (email,))
	flag = False
	for row in cur:
		if row is not None:
			print row
			if email == row[0]:
				flag = True
	return flag
	
#check if username exists
def check_username(username):
	query = '''SELECT username FROM users WHERE username=%s'''
	cur.execute(query, (username,))
	flag = False
	for row in cur:
		if row is not None:
			print row
			if username == row[0]:
				flag = True
	return flag
	
#update history based on selection
@app.route('/eatr/api/v1.0/select', methods=['GET'])
def select():
	t = auth_token(request.args.get('token'))
	if t is not None:
		try:
			user_ids = request.args.getlist('user_ids')
			business_id = request.args.get('business_id')
			if user_ids is None:
				user_is = t;
			else:
				user_ids.append(t)
				
			for id in user_ids:
				query = '''UPDATE history SET days_since=days_since+1 WHERE user_id=%s'''
				cur.execute(query,(id,))
				cnx.commit()
				query = '''UPDATE history SET visits=visits+1 WHERE user_id=%s AND business_id=%s'''
				cur.execute(query,(id,business_id))
				cnx.commit()
				
			
			return jsonify({'status': 0})
		except mysql.connector.Error as err:
			print err
			return jsonify({'status': 2, 'error': str(err)})
	else:
		return jsonify({'status': 1})			
				
#run recommendation algorithm
@app.route('/eatr/api/v1.0/recommendation', methods=['GET'])
def recommendation():
	t = auth_token(request.args.get('token'))
	print t
	if t is not None:
		try:
			#lat = request.args.get('lat')
			#lng = request.args.get('lng')
			type  = request.args.get('type')
			if type is None:
				type = 'all'
			link  = request.args.get('link_weight')
			if link is None:
				link = link_w
			history = request.args.get('history_weight')
			if history is None:
				history = history_w
			cuisine = request.args.get('cuisine_weight')
			if cuisine is None:
				cuisine = cuisine_w
			rss = request.args.get('convergence_rss')
			if rss is None:
				rss = convergence_r
			
			user_ids = request.args.getlist('user_ids')
			if user_ids is None:
				user_is = t;
			else:
				user_ids.append(t)
				
			query = '''SELECT city FROM users WHERE user_id=%s'''
			cur.execute(query,(t,))
			city = ''
			for row in cur:
				if row is not None:
					city = row[0]
			
			
			#get business_ids
			qvalues = (city,1)
			if type == 'all':
				query = '''SELECT business_id FROM business WHERE city=%s'''
				qvalues = (city,)
			if type == 'latenight':
				query = '''SELECT business_id FROM business WHERE city=%s AND latenight=%s'''
			if type == 'lunch':
				query = '''SELECT business_id FROM business WHERE city=%s AND lunch=%s'''
			if type == 'dinner':
				query = '''SELECT business_id FROM business WHERE city=%s AND dinner=%s'''
			if type == 'brunch':
				query = '''SELECT business_id FROM business WHERE city=%s AND brunch=%s'''
			if type == 'breakfast':
				query = '''SELECT business_id FROM business WHERE city=%s AND breakfast=%s'''
					
			business_ids = []
			print query, qvalues
			cur.execute(query,qvalues)
			for row in cur:
				if row is not None:
					business_ids.append(row[0])
							
			#rank
			rank = pagerank(business_ids,user_ids,link,history,cuisine,rss)
			
			output = []
			for i in range(0,len(business_ids)):
				cur.execute("SELECT name FROM business WHERE business_id=%s", (business_ids[i],))
				for name in cur:
					if name is not None:
						output.append((name[0],rank[i],business_ids[i]))
			output.sort(key=lambda tup: tup[1],reverse=True)
			return jsonify({'status': 0, 'recomendations': output})
		except mysql.connector.Error as err:
			print err
			return jsonify({'status': 2, 'error': str(err)})
	else:
		return jsonify({'status': 1})
	
#create user
@app.route('/eatr/api/v1.0/user', methods=['GET'])
def user():
	k = request.args.get('key')
	print k, key
	if k != key or key == 'none':
		return jsonify({'status': 1})
	else:
		try:
			username = request.args.get('username')
			password = request.args.get('password')
			h = hashlib.sha1()
			h.update(password)
			password = h.hexdigest()
			city = (request.args.get('city')).replace('_',' ')
			if city is None:
				city = 'Las Vegas'
			distance = 0.0 #request.args.get('distance')
			email = request.args.get('email')
			phone = request.args.get('phone')
			h = hashlib.sha1()
			h.update(str(username)+str(password)+str(city)+str(distance)+str(email)+str(phone))
			userid= h.hexdigest()
			
			if check_email(email):
				return jsonify({'status': 2, 'error': 'email already in use'})
				
			if check_username(username):
				return jsonify({'status': 3, 'error': 'username already in use'})
			
			query = '''INSERT INTO users ('''
			for cat in categories:
					query += cat + ''','''
			query += '''user_id, username, email, password, phone, distance, city) VALUES ('''
			for i in range(0,len(categories)+6):
					query += '''%s,'''
			query += '''%s)'''
			
			qvalues = tuple([0]*len(categories)) + (userid,username,email,password,phone,distance,city)
			
			cur.execute(query,qvalues)
			cnx.commit()
			
			business_ids = []
			cur.execute('''SELECT business_id FROM business WHERE city=%s''',(city,))
			for row in cur:
				if row is not None:
					business_ids.append(row[0])
			
			for bid in business_ids:
				cur.execute('''INSERT INTO history (days_since, visits, business_id, user_id) VALUES (%s,%s,%s,%s)''',(0,0,bid,userid))
				cnx.commit()
			
			return jsonify({'status': 0}) # 'userid': userid})
		except mysql.connector.Error as err:
			print err
			return jsonify({'status': 4, 'error': str(err)})
		
#auth to app		
@app.route('/eatr/api/v1.0/auth', methods=['GET'])
def auth():
	email = request.args.get('email')
	password = request.args.get('password')
	token = auth_email_passwd(email,password)
	if token == '':
		return jsonify({'status': 1})
	else:
		return jsonify({'status': 0, 'token': token})
	
#get list of friends
@app.route('/eatr/api/v1.0/friends', methods=['GET'])
def friends():
	t = auth_token(request.args.get('token'))
	if t is not None:
		try:
			query = '''SELECT city FROM users WHERE user_id=%s'''
			cur.execute(query,(t,))
			city = ''
			for row in cur:
				if row is not None:
					city = row[0]
		
			query = '''SELECT user_id,username,email FROM users WHERE user_id!=%s AND city=%s'''
			cur.execute(query,(t,city))
			userids = []
			usernames = []
			emails = []
			for row in cur:
				if row is not None:
					userids.append(row[0])
					usernames.append(row[1])
					emails.append(row[2])
			return jsonify({'status': 0, 'user_ids': userids, 'usernames': usernames, 'emails': emails})
		except mysql.connector.Error as err:
			print err
			return jsonify({'status': 2, 'error': str(err)})
	else:
		return jsonify({'status': 1})

#set cuisine
@app.route('/eatr/api/v1.0/setcuisine', methods=['GET'])
def setcuisine():
	t = auth_token(request.args.get('token'))
	if t is not None:
		try:
			#modcuisine = request.args.getlist('cuisine')
			for cat in categories:
				 value = request.args.get(cat)
				 if value is not None:
					query = '''UPDATE users SET ''' + cat + '''=%s WHERE user_id=%s'''
					cur.execute(query,(float(value),t))
					cnx.commit()
			return jsonify({'status': 0})
		except mysql.connector.Error as err:
			print err
			return jsonify({'status': 3, 'error': str(err)})
		
		return jsonify({'status': 0})
	else:
		return jsonify({'status': 1})
	
	#return jsonify({'tasks': tasks})
	
#get cuisine
@app.route('/eatr/api/v1.0/getcuisine', methods=['GET'])
def getcuisine():
	t = auth_token(request.args.get('token'))
	if t is not None:
		try:
			query = '''SELECT * FROM users WHERE user_id=%s'''
			cur.execute(query,(t,))
			values = []
			for row in cur:
				if row is not None:
					values = (list(row))[0:len(categories)]
			cuisine = []
			for i in range(0,len(categories)):
				cuisine.append((categories_formal[i],categories[i],values[i]))
			return jsonify({'status': 0, 'cuisine': cuisine})
		except mysql.connector.Error as err:
			print err
			return jsonify({'status': 2, 'error': str(err)})
	else:
		return jsonify({'status': 1})

#info / status page to test if api is up & get basic data back
@app.route('/eatr/api/v1.0/info', methods=['GET'])
def info():
	#return categories & types
	return jsonify({'status': 0, 'cuisine': categories_formal, 'types': ['all','latenight', 'lunch', 'dinner', 'brunch', 'breakfast']})
	
if __name__ == '__main__':
	#load json config
	load()
	#launch
	if ssl:
		app.run(host=address,port=portnum,debug=False,threaded=True,ssl_context=context)
	else:
		app.run(host=address,port=portnum,debug=False,threaded=True)


