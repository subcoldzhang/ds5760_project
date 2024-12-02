from app import app
from bson.json_util import dumps, loads
from flask import request, jsonify
import json
import ast # helper library for parsing data from string
from importlib.machinery import SourceFileLoader
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime
import neo4j
import pandas as pd

def connect_db():
    driver = neo4j.GraphDatabase.driver(uri="neo4j://localhost:7687", auth=("neo4j","password")) # neo4j://0.0.0.0:7687
    session = driver.session(database="neo4j")
    return session
    
def wipe_out_db(session):
    # wipe out database by deleting all nodes and relationships
    
    # similar to SELECT * FROM graph_db in SQL
    query = "match (node)-[relationship]->() delete node, relationship"
    session.run(query)
    
    query = "match (node) delete node"
    session.run(query)

session = connect_db()

def run_query_to_pandas(session, query, parameters=None):
    """Run a query and return the results as a pandas DataFrame."""
    result = session.run(query, parameters)
    df = pd.DataFrame([r.values() for r in result], columns=result.keys())
    return df

def run_query_print_raw(session, query):
    result = session.run(query)
    
    for r in result:
        print(r.values())

############################## Query 8 ##############################
#####################################################################
@app.route('/top_interactor', methods=['GET'])
def query_top_interactor():
    """Find the user with the most relationships."""
    try:
        query = '''
        MATCH (u:User)-[r]->()
        RETURN u.username AS username, COUNT(r) AS relationship_count
        ORDER BY relationship_count DESC
        LIMIT 5
        '''

        with connect_db() as session:
            df_rels = run_query_to_pandas(session, query)
            
        result = df_rels.to_dict(orient="records")
        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

############################## Query 9 ##############################
#####################################################################
@app.route('/interest_based_grouping', methods=['GET'])
def query_interest_based_grouping():
    """Group users by shared interests to find clusters of users interested in similar topics."""
    try:
        query = '''
        MATCH (u:User)-[:Is_interested_in]->(i:Interest)
        RETURN i.interest_name AS interest, COLLECT(u.username) AS users
        ORDER BY size(users) DESC
        '''

        with connect_db() as session:
            df_rels = run_query_to_pandas(session, query)
        
        result = df_rels.to_dict(orient="records")
        return jsonify(result), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

############################## Query 10 #############################
#####################################################################
@app.route('/content_recommendation', methods=['GET'])
def query_content_recommendation():
    """Recommend new posts or users to follow based on past user interactions and interests."""
    try:
        username = request.args.get('username')
        if not username:
            return jsonify({"error": "Missing required parameter: username"}), 400

        query = '''
        MATCH (u:User {username: $username})-[:Is_interested_in]->(i:Interest)<-[:Is_interested_in]-(other:User)
        WITH other, COUNT(*) AS common_interests
        ORDER BY common_interests DESC
        LIMIT 5
        MATCH (other)-[:Posted]->(p:Post)
        RETURN p.content AS recommended_content, p.timestamp AS timestamp
        ORDER BY timestamp DESC
        LIMIT 5
        '''

        with connect_db() as session:
            df_rels = run_query_to_pandas(session, query, {"username": username})
        
        result = df_rels.to_dict(orient="records")
        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
############################## Query 11 #############################
#####################################################################
@app.route('/popular_topics_analysis', methods=['GET'])
def query_popular_topics_analysis():
    """Analyze trending topics by counting the frequency of specific hashtags in recent posts."""
    try:
        query = '''
        MATCH (p:Post)
        UNWIND p.hashtags AS hashtag
        WITH hashtag, COUNT(*) AS frequency
        RETURN hashtag, frequency
        ORDER BY frequency DESC
        LIMIT 10
        '''

        with connect_db() as session:
            df_rels = run_query_to_pandas(session, query)

        result = df_rels.to_dict(orient="records")
        return jsonify(result), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

############################## Query 12 ##############################
#####################################################################
@app.route('/friend_chain', methods=['GET'])
def query_friend_chain():
    try:
        username_1 = request.args.get('username_1')
        username_2 = request.args.get('username_2')

        if not username_1 or not username_2:
            return jsonify({"error": "Both username_1 and username_2 must be provided."}), 400
        query = '''
        MATCH path = shortestPath((u1:User {username: $username_1})-[:Is_friend_of*1..]-(u2:User {username: $username_2}))
        RETURN DISTINCT [n IN nodes(path) | n.username] AS path
        '''
        with connect_db() as session:
            df_rels = run_query_to_pandas(session, query, {"username_1": username_1, "username_2": username_2})

        result = df_rels.to_dict(orient="records")
        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

############################## Query 13 #############################
#####################################################################
@app.route('/user_engagement_metrics', methods=['GET'])
def query_user_engagement_metrics():
    """Track and analyze engagement metrics across posts."""
    try:
        query = '''
        MATCH (p:Post)<-[r:Like]-()
        RETURN p.post_id AS post_id, p.content AS content, COUNT(r) AS engagement_count
        ORDER BY engagement_count DESC
        LIMIT 5
        '''
        with connect_db() as session:
            df_rels = run_query_to_pandas(session, query)

        result = df_rels.to_dict(orient="records")
        return jsonify(result), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

############################## Query 14 #############################
#####################################################################
@app.route('/influential_users', methods=['GET'])
def query_influential_users():
    """Identify the top influential users on the platform based on metrics such as follower count and interaction levels."""
    try:
        query = '''
        MATCH (u:User)
        OPTIONAL MATCH (u)-[l:Like]->(p:Post)
        RETURN u.username AS username, COUNT(l) AS like_count
        ORDER BY like_count DESC
        LIMIT 5
        '''
        with connect_db() as session:
            df_rels = run_query_to_pandas(session, query)

        result = df_rels.to_dict(orient="records")
        return jsonify(result), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

############################## Query +1 #############################
#####################################################################
@app.route('/common_interests', methods=['GET'])
def query_common_interests():
    try:
        user_id_1 = int(request.args.get('user_id_1'))
        user_id_2 = int(request.args.get('user_id_2'))

        if not user_id_1 or not user_id_2:
            return jsonify({"error": "Both user_id_1 and user_id_2 must be provided."}), 400

        query = '''
        MATCH (u1:User {user_id: $user_id_1})-[:Is_interested_in]->(i:Interest)<-[:Is_interested_in]-(u2:User {user_id: $user_id_2})
        RETURN i.interest_name AS common_interests
        '''
        
        with connect_db() as session:
            df_rels = run_query_to_pandas(session, query, {"user_id_1": user_id_1, "user_id_2": user_id_2})
            
        result = df_rels.to_dict(orient="records")
        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

############################## Query +2 #############################
#####################################################################
@app.route('/no_active_users', methods=['GET'])
def query_no_active_users():
    try:
        query = '''
        MATCH (u:User)
        WHERE NOT (u)-[]-()
        RETURN u.username AS username
        '''
        with connect_db() as session:
            df_rels = run_query_to_pandas(session, query)

        result = df_rels.to_dict(orient="records")
        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

############################ Insert Data ############################
#####################################################################
@app.route('/neo4j/initialize', methods=['POST'])
def initialize_db():
    try:
        with connect_db() as session:
            with session.begin_transaction() as tx:
                wipe_out_db(tx)
                tx.run('''CREATE 
                            (u1:User {user_id: 1, username: 'Alice', age: 25, location: 'New York', bio: 'Love traveling and photography'}),
                            (u2:User {user_id: 2, username: 'Bob', age: 30, location: 'Los Angeles', bio: 'Tech enthusiast and gamer'}),
                            (u3:User {user_id: 3, username: 'Charlie', age: 22, location: 'Chicago', bio: 'Fitness junkie and foodie'}),
                            (u4:User {user_id: 4, username: 'Daisy', age: 28, location: 'San Francisco', bio: 'Passionate about art and music'}),
                            (u5:User {user_id: 5, username: 'Ethan', age: 35, location: 'Seattle', bio: 'Software developer, coffee lover'}),
                            (u6:User {user_id: 6, username: 'Fiona', age: 26, location: 'Boston', bio: 'Fitness trainer and health coach'}),
                            (u7:User {user_id: 7, username: 'George', age: 32, location: 'Austin', bio: 'Loves hiking and outdoor adventures'}),
                            (u8:User {user_id: 8, username: 'Hannah', age: 29, location: 'Denver', bio: 'Mountain lover and environmentalist'}),
                            (u9:User {user_id: 9, username: 'Ian', age: 27, location: 'Portland', bio: 'Cyclist and craft beer enthusiast'}),
                            (u10:User {user_id: 10, username: 'Jane', age: 31, location: 'Miami', bio: 'Beach lover and yoga practitioner'})
                ''')

                tx.run('''CREATE 
                            (p1:Post {post_id: 201, user_id: 1, content: 'Exploring the beautiful landscapes of New York this weekend!', topic: 'Travel', timestamp: '2024-11-25T08:00:00Z', hashtags: ['#NewYork', '#landscapes', '#Travel']}),
                            (p2:Post {post_id: 202, user_id: 1, content: 'Captured an amazing sunset over the Hudson River!', topic: 'Photography', timestamp: '2024-11-26T18:45:00Z', hashtags: ['#sunset', '#HudsonRiver', '#Photography']}),
                            (p3:Post {post_id: 203, user_id: 2, content: 'Just finished a 24-hour gaming marathon! Feeling accomplished!', topic: 'Gaming', timestamp: '2024-11-24T14:00:00Z', hashtags: ['#gaming', '#marathon', '#accomplished']}),
                            (p4:Post {post_id: 204, user_id: 4, content: 'Visited a local art gallery today. The modern art was so inspiring!', topic: 'Art', timestamp: '2024-11-22T10:30:00Z', hashtags: ['#art', '#gallery', '#modernArt']}),
                            (p5:Post {post_id: 205, user_id: 5, content: 'Had an amazing cup of coffee today at my favorite local roastery!', topic: 'Lifestyle', timestamp: '2024-11-23T09:15:00Z', hashtags: ['#coffee', '#roastery', '#Lifestyle']}),
                            (p6:Post {post_id: 206, user_id: 6, content: 'Sharing my favorite workout routine for staying fit!', topic: 'Fitness', timestamp: '2024-11-21T07:30:00Z', hashtags: ['#workout', '#fitness', '#stayFit']}),
                            (p7:Post {post_id: 207, user_id: 7, content: 'Just finished an epic hike in the Texas Hill Country. Feeling recharged!', topic: 'Adventure', timestamp: '2024-11-20T16:00:00Z', hashtags: ['#hiking', '#Texas', '#Adventure']}),
                            (p8:Post {post_id: 208, user_id: 9, content: 'Found an awesome new craft beer bar in Portland. Highly recommend it!', topic: 'Lifestyle', timestamp: '2024-11-19T19:00:00Z', hashtags: ['#craftBeer', '#Portland', '#bar']}),
                            (p9:Post {post_id: 209, user_id: 10, content: 'Yoga session on the beach at sunrise. Nothing better for the soul!', topic: 'Wellness', timestamp: '2024-11-18T06:00:00Z', hashtags: ['#yoga', '#beach', '#sunrise']}),
                            (p10:Post {post_id: 210, user_id: 1, content: 'Exploring Central Park in the fall is just magical!', topic: 'Travel', timestamp: '2024-11-27T15:00:00Z', hashtags: ['#CentralPark', '#fall', '#Travel']}),
                            (p11:Post {post_id: 211, user_id: 3, content: 'Cooked a delicious vegan meal today! Healthy and tasty!', topic: 'Food', timestamp: '2024-11-22T12:00:00Z', hashtags: ['#vegan', '#healthy', '#meal']}),
                            (p12:Post {post_id: 212, user_id: 4, content: 'Attended an open-air concert last night. The vibe was amazing!', topic: 'Music', timestamp: '2024-11-24T20:00:00Z', hashtags: ['#concert', '#vibe', '#music']}),
                            (p13:Post {post_id: 213, user_id: 5, content: 'Working on a new coding project. Loving the challenge!', topic: 'Technology', timestamp: '2024-11-26T14:30:00Z', hashtags: ['#coding', '#challenge', '#technology']}),
                            (p14:Post {post_id: 214, user_id: 6, content: 'Just completed a marathon! Feeling stronger than ever!', topic: 'Fitness', timestamp: '2024-11-25T10:00:00Z', hashtags: ['#marathon', '#fitness', '#stronger']}),
                            (p15:Post {post_id: 215, user_id: 7, content: 'Planning my next hiking trip to the Rockies! Any tips?', topic: 'Adventure', timestamp: '2024-11-23T18:00:00Z', hashtags: ['#hiking', '#Rockies', '#Adventure']}),
                            (p16:Post {post_id: 216, user_id: 9, content: 'Organizing a community cleanup event this weekend! Let us keep Denver clean!', topic: 'Environment', timestamp: '2024-11-21T09:00:00Z', hashtags: ['#community', '#cleanup', '#Denver']}),
                            (p17:Post {post_id: 217, user_id: 9, content: 'Biking through the Portland trails is always a great experience!', topic: 'Cycling', timestamp: '2024-11-20T08:30:00Z', hashtags: ['#biking', '#Portland', '#Cycling']}),
                            (p18:Post {post_id: 218, user_id: 10, content: 'Beach cleanup day was a success! Thanks to everyone who participated!', topic: 'Community', timestamp: '2024-11-19T11:00:00Z', hashtags: ['#beach', '#cleanup', '#community']}),
                            (p19:Post {post_id: 219, user_id: 3, content: 'Trying out a new workout routine. Loving the results so far!', topic: 'Fitness', timestamp: '2024-11-28T07:45:00Z', hashtags: ['#workout', '#fitness', '#results']}),
                            (p20:Post {post_id: 220, user_id: 2, content: 'Built my first custom keyboard today. It feels incredible!', topic: 'Technology', timestamp: '2024-11-27T13:00:00Z', hashtags: ['#customKeyboard', '#technology', '#incredible']})
                ''')

                tx.run('''CREATE 
                            (i1:Interest {interest_id: 401, interest_name: 'Photography', description: 'Capturing beautiful moments through the lens.'}),
                            (i2:Interest {interest_id: 402, interest_name: 'Travel', description: 'Exploring new places and cultures.'}),
                            (i3:Interest {interest_id: 403, interest_name: 'Cooking', description: 'Experimenting with different cuisines.'}),
                            (i4:Interest {interest_id: 404, interest_name: 'Gaming', description: 'Playing and reviewing the latest video games.'}),
                            (i5:Interest {interest_id: 405, interest_name: 'Fitness', description: 'Maintaining an active and healthy lifestyle.'}),
                            (i6:Interest {interest_id: 406, interest_name: 'Art', description: 'Appreciating modern and classical art.'}),
                            (i7:Interest {interest_id: 407, interest_name: 'Music', description: 'Attending concerts and discovering new artists.'}),
                            (i8:Interest {interest_id: 408, interest_name: 'Reading', description: 'Exploring in the library.'}),
                            (i9:Interest {interest_id: 409, interest_name: 'Coffee', description: 'Exploring different coffee roasts and brewing techniques.'}),
                            (i10:Interest {interest_id: 410, interest_name: 'Coding', description: 'Building projects and learning new programming languages.'}),
                            (i11:Interest {interest_id: 411, interest_name: 'Health & Wellness', description: 'Helping others achieve fitness goals.'}),
                            (i12:Interest {interest_id: 412, interest_name: 'Hiking', description: 'Exploring new trails and enjoying nature.'}),
                            (i13:Interest {interest_id: 413, interest_name: 'Camping', description: 'Setting up camp in the great outdoors.'}),
                            (i14:Interest {interest_id: 414, interest_name: 'Environmentalism', description: 'Participating in community clean-ups.'}),
                            (i15:Interest {interest_id: 415, interest_name: 'Mountain Climbing', description: 'Climbing peaks and exploring mountainous terrains.'}),
                            (i16:Interest {interest_id: 416, interest_name: 'Cycling', description: 'Exploring trails around Portland.'}),
                            (i17:Interest {interest_id: 417, interest_name: 'Yoga', description: 'Practicing yoga on the beach.'}),
                            (i18:Interest {interest_id: 418, interest_name: 'Community Service', description: 'Volunteering in local community events.'}),
                            (i19:Interest {interest_id: 419, interest_name: 'Beach Cleanup', description: 'Organizing beach cleanup activities.'})
                ''')

                tx.run('''CREATE                 
                            (c1:Comment {comment_id: 401, post_id: 201, user_id: 2, content: 'Looks amazing!', timestamp: '2024-11-25T12:15:00Z'}),
                            (c2:Comment {comment_id: 402, post_id: 201, user_id: 3, content: 'New York is wonderful!', timestamp: '2024-11-25T12:45:00Z'}),
                            (c3:Comment {comment_id: 403, post_id: 202, user_id: 1, content: 'Can you share the specs?', timestamp: '2024-11-24T16:15:00Z'}),
                            (c4:Comment {comment_id: 404, post_id: 203, user_id: 5, content: 'Congratulations on finishing the marathon!', timestamp: '2024-11-24T17:00:00Z'}),
                            (c5:Comment {comment_id: 405, post_id: 204, user_id: 6, content: 'Art galleries are so inspiring!', timestamp: '2024-11-23T11:30:00Z'}),
                            (c6:Comment {comment_id: 406, post_id: 205, user_id: 7, content: 'I love coffee too! Where is this place?', timestamp: '2024-11-23T12:00:00Z'}),
                            (c7:Comment {comment_id: 407, post_id: 206, user_id: 8, content: 'This workout routine looks great! Can you share more details?', timestamp: '2024-11-22T09:00:00Z'}),
                            (c8:Comment {comment_id: 408, post_id: 207, user_id: 9, content: 'That hike sounds epic!', timestamp: '2024-11-20T17:15:00Z'}),
                            (c9:Comment {comment_id: 409, post_id: 208, user_id: 1, content: 'I need to visit Portland for these amazing bars!', timestamp: '2024-11-19T21:00:00Z'}),
                            (c10:Comment {comment_id: 410, post_id: 209, user_id: 4, content: 'Yoga on the beach sounds like a dream!', timestamp: '2024-11-18T07:30:00Z'}),
                            (c11:Comment {comment_id: 411, post_id: 210, user_id: 10, content: 'Central Park in the fall is truly magical!', timestamp: '2024-11-27T15:45:00Z'}),
                            (c12:Comment {comment_id: 412, post_id: 211, user_id: 3, content: 'This meal looks so tasty! Care to share the recipe?', timestamp: '2024-11-22T13:15:00Z'}),
                            (c13:Comment {comment_id: 413, post_id: 212, user_id: 2, content: 'Concerts are always such a vibe!', timestamp: '2024-11-24T21:30:00Z'}),
                            (c14:Comment {comment_id: 414, post_id: 213, user_id: 6, content: 'Coding is such a rewarding challenge! Keep it up!', timestamp: '2024-11-26T15:30:00Z'}),
                            (c15:Comment {comment_id: 415, post_id: 214, user_id: 9, content: 'Congrats on completing the marathon! That is incredible!', timestamp: '2024-11-25T10:45:00Z'}),
                            (c16:Comment {comment_id: 416, post_id: 215, user_id: 8, content: 'I have some tips for hiking in the Rockies! Message me!', timestamp: '2024-11-23T18:45:00Z'}),
                            (c17:Comment {comment_id: 417, post_id: 216, user_id: 7, content: 'Community cleanup events are so fulfilling!', timestamp: '2024-11-21T10:15:00Z'}),
                            (c18:Comment {comment_id: 418, post_id: 217, user_id: 5, content: 'Cycling through Portland must be so refreshing!', timestamp: '2024-11-20T09:00:00Z'}),
                            (c19:Comment {comment_id: 419, post_id: 218, user_id: 4, content: 'It is amazing to see everyone pitching in for the cleanup!', timestamp: '2024-11-19T12:30:00Z'}),
                            (c20:Comment {comment_id: 420, post_id: 220, user_id: 3, content: 'Custom keyboards are so much fun to build!', timestamp: '2024-11-27T13:45:00Z'}),
                            (c21:Comment {comment_id: 421, post_id: 202, user_id: 9, content: 'That sunset must have been breathtaking!', timestamp: '2024-11-26T19:00:00Z'}),
                            (c22:Comment {comment_id: 422, post_id: 203, user_id: 7, content: 'Gaming marathons are the best! Congrats!', timestamp: '2024-11-24T18:30:00Z'}),
                            (c23:Comment {comment_id: 423, post_id: 204, user_id: 10, content: 'I love modern art! Which gallery did you visit?', timestamp: '2024-11-23T12:15:00Z'}),
                            (c24:Comment {comment_id: 424, post_id: 205, user_id: 1, content: 'Coffee lovers unite! Any recommendations for roasts?', timestamp: '2024-11-23T13:00:00Z'}),
                            (c25:Comment {comment_id: 425, post_id: 206, user_id: 2, content: 'Fitness routines are so motivating! Keep it up!', timestamp: '2024-11-22T10:30:00Z'}),
                            (c26:Comment {comment_id: 426, post_id: 207, user_id: 5, content: 'Hiking in Texas sounds like an amazing adventure!', timestamp: '2024-11-20T18:00:00Z'}),
                            (c27:Comment {comment_id: 427, post_id: 209, user_id: 8, content: 'Yoga is such a calming practice, especially by the ocean!', timestamp: '2024-11-18T08:00:00Z'}),
                            (c28:Comment {comment_id: 428, post_id: 211, user_id: 6, content: 'Healthy meals are the best! This looks delicious!', timestamp: '2024-11-22T14:00:00Z'}),
                            (c29:Comment {comment_id: 429, post_id: 214, user_id: 3, content: 'Running a marathon is a huge achievement! Congratulations!', timestamp: '2024-11-25T11:15:00Z'})
                ''')

                # Friendship connection
                tx.run('''
                MATCH (u1:User {user_id: 1}), (u2:User {user_id: 2})
                WITH u1, u2
                CREATE (u1)-[:Is_friend_of {timestamp: '2024-11-20T10:00:00Z'}]->(u2)
                ''')
                tx.run('''                
                MATCH (u1:User {user_id: 1}), (u3:User {user_id: 3})
                WITH u1, u3
                CREATE (u1)-[:Is_friend_of {timestamp: '2024-11-21T12:00:00Z'}]->(u3)
                ''')

                tx.run('''
                MATCH (u1:User {user_id: 1}), (u4:User {user_id: 4})
                WITH u1, u4
                CREATE (u1)-[:Is_friend_of {timestamp: '2024-11-22T11:30:00Z'}]->(u4)
                ''')                
                tx.run('''
                MATCH (u2:User {user_id: 2}), (u5:User {user_id: 5})
                WITH u2, u5
                CREATE (u2)-[:Is_friend_of {timestamp: '2024-11-19T09:00:00Z'}]->(u5)
                ''')

                tx.run('''
                MATCH (u2:User {user_id: 2}), (u6:User {user_id: 6})
                WITH u2, u6
                CREATE (u2)-[:Is_friend_of {timestamp: '2024-11-23T14:00:00Z'}]->(u6)
                ''')

                tx.run('''
                MATCH (u3:User {user_id: 3}), (u4:User {user_id: 4})
                WITH u3, u4
                CREATE (u3)-[:Is_friend_of {timestamp: '2024-11-24T16:00:00Z'}]->(u4)
                ''')

                tx.run('''
                MATCH (u3:User {user_id: 3}), (u7:User {user_id: 7})
                WITH u3, u7
                CREATE (u3)-[:Is_friend_of {timestamp: '2024-11-25T13:00:00Z'}]->(u7)
                ''')

                tx.run('''
                MATCH (u4:User {user_id: 4}), (u5:User {user_id: 5})
                WITH u4, u5
                CREATE (u4)-[:Is_friend_of {timestamp: '2024-11-26T15:30:00Z'}]->(u5)
                ''')

                tx.run('''
                MATCH (u4:User {user_id: 4}), (u8:User {user_id: 8})
                WITH u4, u8
                CREATE (u4)-[:Is_friend_of {timestamp: '2024-11-27T09:30:00Z'}]->(u8)
                ''')

                tx.run('''
                MATCH (u5:User {user_id: 5}), (u9:User {user_id: 9})
                WITH u5, u9
                CREATE (u5)-[:Is_friend_of {timestamp: '2024-11-18T08:00:00Z'}]->(u9)
                ''')

                tx.run('''
                MATCH (u5:User {user_id: 5}), (u10:User {user_id: 10})
                WITH u5, u10
                CREATE (u5)-[:Is_friend_of {timestamp: '2024-11-28T10:00:00Z'}]->(u10)
                ''')

                tx.run('''
                MATCH (u6:User {user_id: 6}), (u7:User {user_id: 7})
                WITH u6, u7
                CREATE (u6)-[:Is_friend_of {timestamp: '2024-11-17T13:30:00Z'}]->(u7)
                ''')

                tx.run('''
                MATCH (u6:User {user_id: 6}), (u8:User {user_id: 8})
                WITH u6, u8
                CREATE (u6)-[:Is_friend_of {timestamp: '2024-11-22T14:45:00Z'}]->(u8)
                ''')

                tx.run('''
                MATCH (u7:User {user_id: 7}), (u9:User {user_id: 9})
                WITH u7, u9
                CREATE (u7)-[:Is_friend_of {timestamp: '2024-11-25T16:00:00Z'}]->(u9)
                ''')

                tx.run('''
                MATCH (u8:User {user_id: 8}), (u10:User {user_id: 10})
                WITH u8, u10
                CREATE (u8)-[:Is_friend_of {timestamp: '2024-11-26T17:00:00Z'}]->(u10)
                ''')

                tx.run('''
                MATCH (u9:User {user_id: 9}), (u1:User {user_id: 1})
                WITH u9, u1
                CREATE (u9)-[:Is_friend_of {timestamp: '2024-11-27T11:00:00Z'}]->(u1)
                ''')

                tx.run('''
                MATCH (u10:User {user_id: 10}), (u3:User {user_id: 3})
                WITH u10, u3
                CREATE (u10)-[:Is_friend_of {timestamp: '2024-11-28T12:30:00Z'}]->(u3)
                ''')

                # Posted connection
                tx.run('''
                MATCH (u1:User {user_id: 1}), (p1:Post {post_id: 201})
                WITH u1, p1
                CREATE (u1)-[:Posted {timestamp: '2024-11-25T08:00:00Z'}]->(p1)
                ''')

                tx.run('''
                MATCH (u1:User {user_id: 1}), (p2:Post {post_id: 202})
                WITH u1, p2
                CREATE (u1)-[:Posted {timestamp: '2024-11-26T18:45:00Z'}]->(p2)
                ''')

                tx.run('''
                MATCH (u2:User {user_id: 2}), (p3:Post {post_id: 203})
                WITH u2, p3
                CREATE (u2)-[:Posted {timestamp: '2024-11-24T14:00:00Z'}]->(p3)
                ''')

                tx.run('''
                MATCH (u4:User {user_id: 4}), (p4:Post {post_id: 204})
                WITH u4, p4
                CREATE (u4)-[:Posted {timestamp: '2024-11-22T10:30:00Z'}]->(p4)
                ''')

                tx.run('''
                MATCH (u5:User {user_id: 5}), (p5:Post {post_id: 205})
                WITH u5, p5
                CREATE (u5)-[:Posted {timestamp: '2024-11-23T09:15:00Z'}]->(p5)
                ''')

                tx.run('''
                MATCH (u6:User {user_id: 6}), (p6:Post {post_id: 206})
                WITH u6, p6
                CREATE (u6)-[:Posted {timestamp: '2024-11-21T07:30:00Z'}]->(p6)
                ''')

                tx.run('''
                MATCH (u7:User {user_id: 7}), (p7:Post {post_id: 207})
                WITH u7, p7
                CREATE (u7)-[:Posted {timestamp: '2024-11-20T16:00:00Z'}]->(p7)
                ''')

                tx.run('''
                MATCH (u9:User {user_id: 9}), (p8:Post {post_id: 208})
                WITH u9, p8
                CREATE (u9)-[:Posted {timestamp: '2024-11-19T19:00:00Z'}]->(p8)
                ''')

                tx.run('''
                MATCH (u10:User {user_id: 10}), (p9:Post {post_id: 209})
                WITH u10, p9
                CREATE (u10)-[:Posted {timestamp: '2024-11-18T06:00:00Z'}]->(p9)
                ''')

                tx.run('''
                MATCH (u1:User {user_id: 1}), (p10:Post {post_id: 210})
                WITH u1, p10
                CREATE (u1)-[:Posted {timestamp: '2024-11-27T15:00:00Z'}]->(p10)
                ''')

                tx.run('''
                MATCH (u3:User {user_id: 3}), (p11:Post {post_id: 211})
                WITH u3, p11
                CREATE (u3)-[:Posted {timestamp: '2024-11-22T12:00:00Z'}]->(p11)
                ''')

                tx.run('''
                MATCH (u4:User {user_id: 4}), (p12:Post {post_id: 212})
                WITH u4, p12
                CREATE (u4)-[:Posted {timestamp: '2024-11-24T20:00:00Z'}]->(p12)
                ''')

                tx.run('''
                MATCH (u5:User {user_id: 5}), (p13:Post {post_id: 213})
                WITH u5, p13
                CREATE (u5)-[:Posted {timestamp: '2024-11-26T14:30:00Z'}]->(p13)
                ''')

                tx.run('''
                MATCH (u6:User {user_id: 6}), (p14:Post {post_id: 214})
                WITH u6, p14
                CREATE (u6)-[:Posted {timestamp: '2024-11-25T10:00:00Z'}]->(p14)
                ''')

                tx.run('''
                MATCH (u7:User {user_id: 7}), (p15:Post {post_id: 215})
                WITH u7, p15
                CREATE (u7)-[:Posted {timestamp: '2024-11-23T18:00:00Z'}]->(p15)
                ''')

                tx.run('''
                MATCH (u9:User {user_id: 9}), (p16:Post {post_id: 216})
                WITH u9, p16
                CREATE (u9)-[:Posted {timestamp: '2024-11-21T09:00:00Z'}]->(p16)
                ''')

                tx.run('''
                MATCH (u9:User {user_id: 9}), (p17:Post {post_id: 217})
                WITH u9, p17
                CREATE (u9)-[:Posted {timestamp: '2024-11-20T08:30:00Z'}]->(p17)
                ''')

                tx.run('''
                MATCH (u10:User {user_id: 10}), (p18:Post {post_id: 218})
                WITH u10, p18
                CREATE (u10)-[:Posted {timestamp: '2024-11-19T11:00:00Z'}]->(p18)
                ''')

                tx.run('''
                MATCH (u3:User {user_id: 3}), (p19:Post {post_id: 219})
                WITH u3, p19
                CREATE (u3)-[:Posted {timestamp: '2024-11-28T07:45:00Z'}]->(p19)
                ''')

                tx.run('''
                MATCH (u2:User {user_id: 2}), (p20:Post {post_id: 220})
                WITH u2, p20
                CREATE (u2)-[:Posted {timestamp: '2024-11-27T13:00:00Z'}]->(p20)
                ''')

                # Interest connection
                tx.run('''
                MATCH (u1:User {user_id: 1}), (i1:Interest {interest_id: 401})
                WITH u1, i1
                CREATE (u1)-[:Is_interested_in {timestamp: '2024-11-20T14:00:00Z'}]->(i1)
                ''')

                tx.run('''
                MATCH (u2:User {user_id: 2}), (i1:Interest {interest_id: 401})
                WITH u2, i1
                CREATE (u2)-[:Is_interested_in {timestamp: '2024-11-21T15:00:00Z'}]->(i1)
                ''')

                tx.run('''
                MATCH (u3:User {user_id: 3}), (i1:Interest {interest_id: 401})
                WITH u3, i1
                CREATE (u3)-[:Is_interested_in {timestamp: '2024-11-22T18:00:00Z'}]->(i1)
                ''')

                tx.run('''
                MATCH (u4:User {user_id: 4}), (i2:Interest {interest_id: 402})
                WITH u4, i2
                CREATE (u4)-[:Is_interested_in {timestamp: '2024-11-19T10:00:00Z'}]->(i2)
                ''')

                tx.run('''
                MATCH (u5:User {user_id: 5}), (i3:Interest {interest_id: 403})
                WITH u5, i3
                CREATE (u5)-[:Is_interested_in {timestamp: '2024-11-18T08:00:00Z'}]->(i3)
                ''')

                tx.run('''
                MATCH (u6:User {user_id: 6}), (i4:Interest {interest_id: 404})
                WITH u6, i4
                CREATE (u6)-[:Is_interested_in {timestamp: '2024-11-20T13:00:00Z'}]->(i4)
                ''')

                tx.run('''
                MATCH (u7:User {user_id: 7}), (i4:Interest {interest_id: 404})
                WITH u7, i4
                CREATE (u7)-[:Is_interested_in {timestamp: '2024-11-21T14:00:00Z'}]->(i4)
                ''')

                tx.run('''
                MATCH (u8:User {user_id: 8}), (i4:Interest {interest_id: 404})
                WITH u8, i4
                CREATE (u8)-[:Is_interested_in {timestamp: '2024-11-23T14:00:00Z'}]->(i4)
                ''')

                tx.run('''
                MATCH (u9:User {user_id: 9}), (i5:Interest {interest_id: 405})
                WITH u9, i5
                CREATE (u9)-[:Is_interested_in {timestamp: '2024-11-23T09:00:00Z'}]->(i5)
                ''')

                tx.run('''
                MATCH (u10:User {user_id: 10}), (i5:Interest {interest_id: 405})
                WITH u10, i5
                CREATE (u10)-[:Is_interested_in {timestamp: '2024-11-25T10:00:00Z'}]->(i5)
                ''')

                tx.run('''
                MATCH (u6:User {user_id: 6}), (i11:Interest {interest_id: 411})
                WITH u6, i11
                CREATE (u6)-[:Is_interested_in {timestamp: '2024-11-18T07:30:00Z'}]->(i11)
                ''')

                tx.run('''
                MATCH (u7:User {user_id: 7}), (i12:Interest {interest_id: 412})
                WITH u7, i12
                CREATE (u7)-[:Is_interested_in {timestamp: '2024-11-17T16:00:00Z'}]->(i12)
                ''')

                tx.run('''
                MATCH (u7:User {user_id: 7}), (i13:Interest {interest_id: 413})
                WITH u7, i13
                CREATE (u7)-[:Is_interested_in {timestamp: '2024-11-23T17:30:00Z'}]->(i13)
                ''')

                tx.run('''
                MATCH (u8:User {user_id: 8}), (i14:Interest {interest_id: 414})
                WITH u8, i14
                CREATE (u8)-[:Is_interested_in {timestamp: '2024-11-19T13:00:00Z'}]->(i14)
                ''')

                tx.run('''
                MATCH (u8:User {user_id: 8}), (i15:Interest {interest_id: 415})
                WITH u8, i15
                CREATE (u8)-[:Is_interested_in {timestamp: '2024-11-22T08:00:00Z'}]->(i15)
                ''')

                tx.run('''
                MATCH (u9:User {user_id: 9}), (i16:Interest {interest_id: 416})
                WITH u9, i16
                CREATE (u9)-[:Is_interested_in {timestamp: '2024-11-20T08:30:00Z'}]->(i16)
                ''')

                tx.run('''
                MATCH (u10:User {user_id: 10}), (i17:Interest {interest_id: 417})
                WITH u10, i17
                CREATE (u10)-[:Is_interested_in {timestamp: '2024-11-18T06:30:00Z'}]->(i17)
                ''')

                tx.run('''
                MATCH (u10:User {user_id: 10}), (i18:Interest {interest_id: 418})
                WITH u10, i18
                CREATE (u10)-[:Is_interested_in {timestamp: '2024-11-19T10:30:00Z'}]->(i18)
                ''')

                tx.run('''
                MATCH (u10:User {user_id: 10}), (i19:Interest {interest_id: 419})
                WITH u10, i19
                CREATE (u10)-[:Is_interested_in {timestamp: '2024-11-22T11:30:00Z'}]->(i19)
                ''')

                # Publish connection
                tx.run('''
                MATCH (u2:User {user_id: 2}), (c1:Comment {comment_id: 401})
                WITH u2, c1
                CREATE (u2)-[:Publish {timestamp: '2024-11-25T12:15:00Z'}]->(c1)
                ''')

                tx.run('''
                MATCH (u3:User {user_id: 3}), (c2:Comment {comment_id: 402})
                WITH u3, c2
                CREATE (u3)-[:Publish {timestamp: '2024-11-25T12:45:00Z'}]->(c2)
                ''')

                tx.run('''
                MATCH (u1:User {user_id: 1}), (c3:Comment {comment_id: 403})
                WITH u1, c3
                CREATE (u1)-[:Publish {timestamp: '2024-11-24T16:15:00Z'}]->(c3)
                ''')

                tx.run('''
                MATCH (u5:User {user_id: 5}), (c4:Comment {comment_id: 404})
                WITH u5, c4
                CREATE (u5)-[:Publish {timestamp: '2024-11-24T17:00:00Z'}]->(c4)
                ''')

                tx.run('''
                MATCH (u6:User {user_id: 6}), (c5:Comment {comment_id: 405})
                WITH u6, c5
                CREATE (u6)-[:Publish {timestamp: '2024-11-23T11:30:00Z'}]->(c5)
                ''')

                tx.run('''
                MATCH (u7:User {user_id: 7}), (c6:Comment {comment_id: 406})
                WITH u7, c6
                CREATE (u7)-[:Publish {timestamp: '2024-11-23T12:00:00Z'}]->(c6)
                ''')

                tx.run('''
                MATCH (u8:User {user_id: 8}), (c7:Comment {comment_id: 407})
                WITH u8, c7
                CREATE (u8)-[:Publish {timestamp: '2024-11-22T09:00:00Z'}]->(c7)
                ''')

                tx.run('''
                MATCH (u9:User {user_id: 9}), (c8:Comment {comment_id: 408})
                WITH u9, c8
                CREATE (u9)-[:Publish {timestamp: '2024-11-20T17:15:00Z'}]->(c8)
                ''')

                tx.run('''
                MATCH (u1:User {user_id: 1}), (c9:Comment {comment_id: 409})
                WITH u1, c9
                CREATE (u1)-[:Publish {timestamp: '2024-11-19T21:00:00Z'}]->(c9)
                ''')

                tx.run('''
                MATCH (u4:User {user_id: 4}), (c10:Comment {comment_id: 410})
                WITH u4, c10
                CREATE (u4)-[:Publish {timestamp: '2024-11-18T07:30:00Z'}]->(c10)
                ''')

                tx.run('''
                MATCH (u10:User {user_id: 10}), (c11:Comment {comment_id: 411})
                WITH u10, c11
                CREATE (u10)-[:Publish {timestamp: '2024-11-27T15:45:00Z'}]->(c11)
                ''')

                tx.run('''
                MATCH (u3:User {user_id: 3}), (c12:Comment {comment_id: 412})
                WITH u3, c12
                CREATE (u3)-[:Publish {timestamp: '2024-11-22T13:15:00Z'}]->(c12)
                ''')

                tx.run('''
                MATCH (u2:User {user_id: 2}), (c13:Comment {comment_id: 413})
                WITH u2, c13
                CREATE (u2)-[:Publish {timestamp: '2024-11-24T21:30:00Z'}]->(c13)
                ''')

                tx.run('''
                MATCH (u6:User {user_id: 6}), (c14:Comment {comment_id: 414})
                WITH u6, c14
                CREATE (u6)-[:Publish {timestamp: '2024-11-26T15:30:00Z'}]->(c14)
                ''')

                tx.run('''
                MATCH (u9:User {user_id: 9}), (c15:Comment {comment_id: 415})
                WITH u9, c15
                CREATE (u9)-[:Publish {timestamp: '2024-11-25T10:45:00Z'}]->(c15)
                ''')

                tx.run('''
                MATCH (u8:User {user_id: 8}), (c16:Comment {comment_id: 416})
                WITH u8, c16
                CREATE (u8)-[:Publish {timestamp: '2024-11-23T18:45:00Z'}]->(c16)
                ''')

                tx.run('''
                MATCH (u7:User {user_id: 7}), (c17:Comment {comment_id: 417})
                WITH u7, c17
                CREATE (u7)-[:Publish {timestamp: '2024-11-21T10:15:00Z'}]->(c17)
                ''')

                tx.run('''
                MATCH (u5:User {user_id: 5}), (c18:Comment {comment_id: 418})
                WITH u5, c18
                CREATE (u5)-[:Publish {timestamp: '2024-11-20T09:00:00Z'}]->(c18)
                ''')

                tx.run('''
                MATCH (u4:User {user_id: 4}), (c19:Comment {comment_id: 419})
                WITH u4, c19
                CREATE (u4)-[:Publish {timestamp: '2024-11-19T12:30:00Z'}]->(c19)
                ''')

                tx.run('''
                MATCH (u3:User {user_id: 3}), (c20:Comment {comment_id: 420})
                WITH u3, c20
                CREATE (u3)-[:Publish {timestamp: '2024-11-27T13:45:00Z'}]->(c20)
                ''')

                tx.run('''
                MATCH (u9:User {user_id: 9}), (c21:Comment {comment_id: 421})
                WITH u9, c21
                CREATE (u9)-[:Publish {timestamp: '2024-11-26T19:00:00Z'}]->(c21)
                ''')

                tx.run('''
                MATCH (u7:User {user_id: 7}), (c22:Comment {comment_id: 422})
                WITH u7, c22
                CREATE (u7)-[:Publish {timestamp: '2024-11-24T18:30:00Z'}]->(c22)
                ''')

                tx.run('''
                MATCH (u10:User {user_id: 10}), (c23:Comment {comment_id: 423})
                WITH u10, c23
                CREATE (u10)-[:Publish {timestamp: '2024-11-23T12:15:00Z'}]->(c23)
                ''')

                tx.run('''
                MATCH (u1:User {user_id: 1}), (c24:Comment {comment_id: 424})
                WITH u1, c24
                CREATE (u1)-[:Publish {timestamp: '2024-11-23T13:00:00Z'}]->(c24)
                ''')

                tx.run('''
                MATCH (u2:User {user_id: 2}), (c25:Comment {comment_id: 425})
                WITH u2, c25
                CREATE (u2)-[:Publish {timestamp: '2024-11-22T10:30:00Z'}]->(c25)
                ''')

                tx.run('''
                MATCH (u5:User {user_id: 5}), (c26:Comment {comment_id: 426})
                WITH u5, c26
                CREATE (u5)-[:Publish {timestamp: '2024-11-20T18:00:00Z'}]->(c26)
                ''')

                tx.run('''
                MATCH (u8:User {user_id: 8}), (c27:Comment {comment_id: 427})
                WITH u8, c27
                CREATE (u8)-[:Publish {timestamp: '2024-11-18T08:00:00Z'}]->(c27)
                ''')

                tx.run('''
                MATCH (u6:User {user_id: 6}), (c28:Comment {comment_id: 428})
                WITH u6, c28
                CREATE (u6)-[:Publish {timestamp: '2024-11-22T14:00:00Z'}]->(c28)
                ''')

                tx.run('''
                MATCH (u3:User {user_id: 3}), (c29:Comment {comment_id: 429})
                WITH u3, c29
                CREATE (u3)-[:Publish {timestamp: '2024-11-25T11:15:00Z'}]->(c29)
                ''')

                # Comment on Post connection
                tx.run('''
                MATCH (c1:Comment {comment_id: 401}), (p1:Post {post_id: 201})
                WITH c1, p1
                CREATE (c1)-[:Is_on {timestamp: '2024-11-25T12:15:00Z'}]->(p1)
                ''')

                tx.run('''
                MATCH (c2:Comment {comment_id: 402}), (p1:Post {post_id: 201})
                WITH c2, p1
                CREATE (c2)-[:Is_on {timestamp: '2024-11-25T12:45:00Z'}]->(p1)
                ''')

                tx.run('''
                MATCH (c3:Comment {comment_id: 403}), (p2:Post {post_id: 202})
                WITH c3, p2
                CREATE (c3)-[:Is_on {timestamp: '2024-11-24T16:15:00Z'}]->(p2)
                ''')

                tx.run('''
                MATCH (c4:Comment {comment_id: 404}), (p3:Post {post_id: 203})
                WITH c4, p3
                CREATE (c4)-[:Is_on {timestamp: '2024-11-24T17:00:00Z'}]->(p3)
                ''')

                tx.run('''
                MATCH (c5:Comment {comment_id: 405}), (p4:Post {post_id: 204})
                WITH c5, p4
                CREATE (c5)-[:Is_on {timestamp: '2024-11-23T11:30:00Z'}]->(p4)
                ''')

                tx.run('''
                MATCH (c6:Comment {comment_id: 406}), (p5:Post {post_id: 205})
                WITH c6, p5
                CREATE (c6)-[:Is_on {timestamp: '2024-11-23T12:00:00Z'}]->(p5)
                ''')

                tx.run('''
                MATCH (c7:Comment {comment_id: 407}), (p6:Post {post_id: 206})
                WITH c7, p6
                CREATE (c7)-[:Is_on {timestamp: '2024-11-22T09:00:00Z'}]->(p6)
                ''')

                tx.run('''
                MATCH (c8:Comment {comment_id: 408}), (p7:Post {post_id: 207})
                WITH c8, p7
                CREATE (c8)-[:Is_on {timestamp: '2024-11-20T17:15:00Z'}]->(p7)
                ''')

                tx.run('''
                MATCH (c9:Comment {comment_id: 409}), (p8:Post {post_id: 208})
                WITH c9, p8
                CREATE (c9)-[:Is_on {timestamp: '2024-11-19T21:00:00Z'}]->(p8)
                ''')

                tx.run('''
                MATCH (c10:Comment {comment_id: 410}), (p9:Post {post_id: 209})
                WITH c10, p9
                CREATE (c10)-[:Is_on {timestamp: '2024-11-18T07:30:00Z'}]->(p9)
                ''')

                tx.run('''
                MATCH (c11:Comment {comment_id: 411}), (p10:Post {post_id: 210})
                WITH c11, p10
                CREATE (c11)-[:Is_on {timestamp: '2024-11-27T15:45:00Z'}]->(p10)
                ''')

                tx.run('''
                MATCH (c12:Comment {comment_id: 412}), (p11:Post {post_id: 211})
                WITH c12, p11
                CREATE (c12)-[:Is_on {timestamp: '2024-11-22T13:15:00Z'}]->(p11)
                ''')

                tx.run('''
                MATCH (c13:Comment {comment_id: 413}), (p12:Post {post_id: 212})
                WITH c13, p12
                CREATE (c13)-[:Is_on {timestamp: '2024-11-24T21:30:00Z'}]->(p12)
                ''')

                tx.run('''
                MATCH (c14:Comment {comment_id: 414}), (p13:Post {post_id: 213})
                WITH c14, p13
                CREATE (c14)-[:Is_on {timestamp: '2024-11-26T15:30:00Z'}]->(p13)
                ''')

                tx.run('''
                MATCH (c15:Comment {comment_id: 415}), (p14:Post {post_id: 214})
                WITH c15, p14
                CREATE (c15)-[:Is_on {timestamp: '2024-11-25T10:45:00Z'}]->(p14)
                ''')

                tx.run('''
                MATCH (c16:Comment {comment_id: 416}), (p15:Post {post_id: 215})
                WITH c16, p15
                CREATE (c16)-[:Is_on {timestamp: '2024-11-23T18:45:00Z'}]->(p15)
                ''')

                tx.run('''
                MATCH (c17:Comment {comment_id: 417}), (p16:Post {post_id: 216})
                WITH c17, p16
                CREATE (c17)-[:Is_on {timestamp: '2024-11-21T10:15:00Z'}]->(p16)
                ''')

                tx.run('''
                MATCH (c18:Comment {comment_id: 418}), (p17:Post {post_id: 217})
                WITH c18, p17
                CREATE (c18)-[:Is_on {timestamp: '2024-11-20T09:00:00Z'}]->(p17)
                ''')

                tx.run('''
                MATCH (c19:Comment {comment_id: 419}), (p18:Post {post_id: 218})
                WITH c19, p18
                CREATE (c19)-[:Is_on {timestamp: '2024-11-19T12:30:00Z'}]->(p18)
                ''')

                tx.run('''
                MATCH (c20:Comment {comment_id: 420}), (p20:Post {post_id: 220})
                WITH c20, p20
                CREATE (c20)-[:Is_on {timestamp: '2024-11-27T13:45:00Z'}]->(p20)
                ''')

                tx.run('''
                MATCH (c21:Comment {comment_id: 421}), (p2:Post {post_id: 202})
                WITH c21, p2
                CREATE (c21)-[:Is_on {timestamp: '2024-11-26T19:00:00Z'}]->(p2)
                ''')

                tx.run('''
                MATCH (c22:Comment {comment_id: 422}), (p3:Post {post_id: 203})
                WITH c22, p3
                CREATE (c22)-[:Is_on {timestamp: '2024-11-24T18:30:00Z'}]->(p3)
                ''')

                tx.run('''
                MATCH (c23:Comment {comment_id: 423}), (p4:Post {post_id: 204})
                WITH c23, p4
                CREATE (c23)-[:Is_on {timestamp: '2024-11-23T12:15:00Z'}]->(p4)
                ''')

                tx.run('''
                MATCH (c24:Comment {comment_id: 424}), (p5:Post {post_id: 205})
                WITH c24, p5
                CREATE (c24)-[:Is_on {timestamp: '2024-11-23T13:00:00Z'}]->(p5)
                ''')

                tx.run('''
                MATCH (c25:Comment {comment_id: 425}), (p6:Post {post_id: 206})
                WITH c25, p6
                CREATE (c25)-[:Is_on {timestamp: '2024-11-22T10:30:00Z'}]->(p6)
                ''')

                tx.run('''
                MATCH (c26:Comment {comment_id: 426}), (p7:Post {post_id: 207})
                WITH c26, p7
                CREATE (c26)-[:Is_on {timestamp: '2024-11-20T18:00:00Z'}]->(p7)
                ''')

                tx.run('''
                MATCH (c27:Comment {comment_id: 427}), (p9:Post {post_id: 209})
                WITH c27, p9
                CREATE (c27)-[:Is_on {timestamp: '2024-11-18T08:00:00Z'}]->(p9)
                ''')

                tx.run('''
                MATCH (c28:Comment {comment_id: 428}), (p11:Post {post_id: 211})
                WITH c28, p11
                CREATE (c28)-[:Is_on {timestamp: '2024-11-22T14:00:00Z'}]->(p11)
                ''')

                tx.run('''
                MATCH (c29:Comment {comment_id: 429}), (p14:Post {post_id: 214})
                WITH c29, p14
                CREATE (c29)-[:Is_on {timestamp: '2024-11-25T11:15:00Z'}]->(p14)
                ''')

                # Like connection
                tx.run('''
                MATCH (u2:User {user_id: 2}), (p1:Post {post_id: 201})
                WITH u2, p1
                CREATE (u2)-[:Like {timestamp: '2024-11-25T09:00:00Z'}]->(p1)
                ''')

                tx.run('''
                MATCH (u3:User {user_id: 3}), (p1:Post {post_id: 201})
                WITH u3, p1
                CREATE (u3)-[:Like {timestamp: '2024-11-25T10:00:00Z'}]->(p1)
                ''')

                tx.run('''
                MATCH (u5:User {user_id: 5}), (p2:Post {post_id: 202})
                WITH u5, p2
                CREATE (u5)-[:Like {timestamp: '2024-11-26T19:30:00Z'}]->(p2)
                ''')

                tx.run('''
                MATCH (u1:User {user_id: 1}), (p3:Post {post_id: 203})
                WITH u1, p3
                CREATE (u1)-[:Like {timestamp: '2024-11-24T15:00:00Z'}]->(p3)
                ''')

                tx.run('''
                MATCH (u6:User {user_id: 6}), (p4:Post {post_id: 204})
                WITH u6, p4
                CREATE (u6)-[:Like {timestamp: '2024-11-22T11:00:00Z'}]->(p4)
                ''')

                tx.run('''
                MATCH (u7:User {user_id: 7}), (p5:Post {post_id: 205})
                WITH u7, p5
                CREATE (u7)-[:Like {timestamp: '2024-11-23T10:00:00Z'}]->(p5)
                ''')

                tx.run('''
                MATCH (u3:User {user_id: 3}), (p5:Post {post_id: 205})
                WITH u3, p5
                CREATE (u3)-[:Like {timestamp: '2024-11-23T11:00:00Z'}]->(p5)
                ''')

                tx.run('''
                MATCH (u9:User {user_id: 9}), (p6:Post {post_id: 206})
                WITH u9, p6
                CREATE (u9)-[:Like {timestamp: '2024-11-21T08:30:00Z'}]->(p6)
                ''')

                tx.run('''
                MATCH (u10:User {user_id: 10}), (p7:Post {post_id: 207})
                WITH u10, p7
                CREATE (u10)-[:Like {timestamp: '2024-11-20T17:00:00Z'}]->(p7)
                ''')

                tx.run('''
                MATCH (u8:User {user_id: 8}), (p8:Post {post_id: 208})
                WITH u8, p8
                CREATE (u8)-[:Like {timestamp: '2024-11-19T20:00:00Z'}]->(p8)
                ''')

                tx.run('''
                MATCH (u2:User {user_id: 2}), (p10:Post {post_id: 210})
                WITH u2, p10
                CREATE (u2)-[:Like {timestamp: '2024-11-27T16:00:00Z'}]->(p10)
                ''')

                tx.run('''
                MATCH (u4:User {user_id: 4}), (p12:Post {post_id: 212})
                WITH u4, p12
                CREATE (u4)-[:Like {timestamp: '2024-11-24T21:00:00Z'}]->(p12)
                ''')

                tx.run('''
                MATCH (u5:User {user_id: 5}), (p13:Post {post_id: 213})
                WITH u5, p13
                CREATE (u5)-[:Like {timestamp: '2024-11-26T15:00:00Z'}]->(p13)
                ''')

                tx.run('''
                MATCH (u7:User {user_id: 7}), (p14:Post {post_id: 214})
                WITH u7, p14
                CREATE (u7)-[:Like {timestamp: '2024-11-25T11:00:00Z'}]->(p14)
                ''')

                tx.run('''
                MATCH (u1:User {user_id: 1}), (p14:Post {post_id: 214})
                WITH u1, p14
                CREATE (u1)-[:Like {timestamp: '2024-11-25T12:00:00Z'}]->(p14)
                ''')

                tx.run('''
                MATCH (u10:User {user_id: 10}), (p15:Post {post_id: 215})
                WITH u10, p15
                CREATE (u10)-[:Like {timestamp: '2024-11-23T19:00:00Z'}]->(p15)
                ''')

                tx.run('''
                MATCH (u6:User {user_id: 6}), (p18:Post {post_id: 218})
                WITH u6, p18
                CREATE (u6)-[:Like {timestamp: '2024-11-19T12:00:00Z'}]->(p18)
                ''')

                tx.run('''
                MATCH (u4:User {user_id: 4}), (p19:Post {post_id: 219})
                WITH u4, p19
                CREATE (u4)-[:Like {timestamp: '2024-11-28T08:00:00Z'}]->(p19)
                ''')

                tx.run('''
                MATCH (u8:User {user_id: 8}), (p20:Post {post_id: 220})
                WITH u8, p20
                CREATE (u8)-[:Like {timestamp: '2024-11-27T14:00:00Z'}]->(p20)
                ''')

                tx.run('''
                MATCH (u5:User {user_id: 5}), (p20:Post {post_id: 220})
                WITH u5, p20
                CREATE (u5)-[:Like {timestamp: '2024-11-27T15:00:00Z'}]->(p20)
                ''')

        return jsonify({"message": "Database initialized successfully."}), 200
    except Exception as e:
        print(f"Error during database initialization: {str(e)}")
        return jsonify({"error": str(e)}), 500

############################ Handle 404 #############################
#####################################################################
@app.errorhandler(404)
def page_not_found(e):
    '''Send message to the user if route is not defined.'''

    message = {
        "err":
            {
                "msg": "This route is currently not supported."
            }
    }

    resp = jsonify(message)
    # Sending 404 (not found) response
    resp.status_code = 404
    # Returning the object
    return resp