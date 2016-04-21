create table business (sushi INTEGER, italian INTEGER, steakhouses INTEGER, deli INTEGER, tex_mex INTEGER, american INTEGER, thai INTEGER, cajun INTEGER, cafe INTEGER, greek INTEGER, chinese INTEGER, burgers INTEGER, indian INTEGER, latin INTEGER, korean INTEGER, southern INTEGER, vietnamese INTEGER, pizza INTEGER, seafood INTEGER, comfort INTEGER, mexican INTEGER, japanese INTEGER, spanish INTEGER, soul INTEGER, fast_food INTEGER, business_id TEXT PRIMARY KEY, name TEXT, stars REAL, review_count INTEGER, latitude REAL, longitude REAL, city TEXT);
.separator ","
.import business.csv business
create table users (sushi INTEGER, italian INTEGER, steakhouses INTEGER, deli INTEGER, tex_mex INTEGER, american INTEGER, thai INTEGER, cajun INTEGER, cafe INTEGER, greek INTEGER, chinese INTEGER, burgers INTEGER, indian INTEGER, latin INTEGER, korean INTEGER, southern INTEGER, vietnamese INTEGER, pizza INTEGER, seafood INTEGER, comfort INTEGER, mexican INTEGER, japanese INTEGER, spanish INTEGER, soul INTEGER, fast_food INTEGER, user_id TEXT PRIMARY KEY, name TEXT, latitude REAL, longitude REAL, city TEXT);
.separator ","
.import users.csv users
create table history (days_since INTEGER, vists INTEGER, business_id TEXT, user_id TEXT, PRIMARY KEY (business_id,user_id));
.separator ","
.import history.csv history