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
        
@app.route('/common_interests', methods=['GET'])
def query_common_interests():
    try:
        user_id_1 = request.args.get('user_id_1')
        user_id_2 = request.args.get('user_id_2')

        if not user_id_1 or not user_id_2:
            return jsonify({"error": "Both user_id_1 and user_id_2 must be provided."}), 400

        query = '''
        MATCH (u1:User {user_id: $user_id_1})-[:Is_interest_in]->(i:Interest)<-[:Is_interest_in]-(u2:User {user_id: $user_id_2})
        RETURN i.field_name AS common_interests
        '''
        
        with connect_db() as session:
            df_rels = run_query_to_pandas(session, query, {"user_id_1": user_id_1, "user_id_2": user_id_2})
            
        result = df_rels.to_dict(orient="records")
        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

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

@app.route('/top_interactor', methods=['GET'])
def query_top_interactor():
    """Find the user with the most relationships."""
    try:
        query = '''
        MATCH (u:User)-[r]->()
        RETURN u.username AS username, COUNT(r) AS relationship_count
        ORDER BY relationship_count DESC
        LIMIT 1
        '''

        with connect_db() as session:
            df_rels = run_query_to_pandas(session, query)
            
        result = df_rels.to_dict(orient="records")
        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/neo4j/initialize', methods=['POST'])
def initialize_db():
    try:
        with connect_db() as session:
            wipe_out_db(session)
            sample_data_query = '''
            CREATE
                (u5:User {user_id: '5', username: 'emma_w', age: 22, birth: '2002-05-14', location: 'Chicago', bio: 'Nature lover'}),
                (u6:User {user_id: '6', username: 'mike89', age: 30, birth: '1994-12-02', location: 'Seattle', bio: 'Tech enthusiast'}),
                (u7:User {user_id: '7', username: 'sophia', age: 27, birth: '1997-03-28', location: 'Boston', bio: 'Coffee addict'}),
                (u8:User {user_id: '8', username: 'liam', age: 29, birth: '1995-09-10', location: 'Austin', bio: 'Music is life'}),
                (u9:User {user_id: '9', username: 'olivia', age: 24, birth: '2000-11-30', location: 'Miami', bio: 'Sun and beach'}),
                (u10:User {user_id: '10', username: 'noah', age: 31, birth: '1993-07-07', location: 'Denver', bio: 'Love hiking'}),
                (u11:User {user_id: '11', username: 'zzzzyh', age: 24, birth: '2000-07-21', location: 'Beijing', bio: 'Love ds5760'}),
                (p5:Post {post_id: '5', topic: 'Nature', timestamp: '2024-09-15T09:30:00', content: 'Exploring the mountains.'}),
                (p6:Post {post_id: '6', topic: 'Technology', timestamp: '2024-08-20T14:00:00', content: 'New advancements in AI.'}),
                (p7:Post {post_id: '7', topic: 'Coffee', timestamp: '2024-07-22T08:15:00', content: 'Best coffee shops in town.'}),
                (p8:Post {post_id: '8', topic: 'Music', timestamp: '2024-06-30T19:45:00', content: 'My new song is out!'}),
                (p9:Post {post_id: '9', topic: 'Travel', timestamp: '2024-05-18T12:00:00', content: 'Trip to the Bahamas.'}),
                (p10:Post {post_id: '10', topic: 'Hiking', timestamp: '2024-04-05T07:00:00', content: 'Top trails to explore.'}),
                (i3:Interest {interest_id: '3', field_name: 'Nature', introduction: 'All about nature.'}),
                (i4:Interest {interest_id: '4', field_name: 'Technology', introduction: 'Latest tech trends.'}),
                (i5:Interest {interest_id: '5', field_name: 'Music', introduction: 'Music lovers unite.'}),
                (ch3:Channel {channel_id: '3', channel_name: 'NatureChannel'}),
                (ch4:Channel {channel_id: '4', channel_name: 'TechTalk'}),
                (ch5:Channel {channel_id: '5', channel_name: 'MusicWorld'}),
                (u5)-[:Is_friend_of {timestamp: '2023-07-01T09:00:00'}]->(u6),
                (u6)-[:Is_friend_of {timestamp: '2023-07-01T09:00:00'}]->(u5),
                (u7)-[:Is_friend_of {timestamp: '2023-07-05T10:00:00'}]->(u8),
                (u8)-[:Is_friend_of {timestamp: '2023-07-05T10:00:00'}]->(u7),
                (u7)-[:Is_friend_of {timestamp: '2023-07-01T09:00:00'}]->(u6),
                (u6)-[:Is_friend_of {timestamp: '2023-07-01T09:00:00'}]->(u7),
                (u9)-[:Is_friend_of {timestamp: '2023-07-10T11:00:00'}]->(u10),
                (u10)-[:Is_friend_of {timestamp: '2023-07-10T11:00:00'}]->(u9),
                (u5)-[:Is_friend_of {timestamp: '2023-08-01T12:00:00'}]->(u1),
                (u1)-[:Is_friend_of {timestamp: '2023-08-01T12:00:00'}]->(u5),
                (u6)-[:Is_friend_of {timestamp: '2023-08-05T13:00:00'}]->(u2),
                (u2)-[:Is_friend_of {timestamp: '2023-08-05T13:00:00'}]->(u6),
                (u5)-[:Posted {timestamp: '2024-09-15T09:30:00'}]->(p5),
                (u6)-[:Posted {timestamp: '2024-08-20T14:00:00'}]->(p6),
                (u7)-[:Posted {timestamp: '2024-07-22T08:15:00'}]->(p7),
                (u8)-[:Posted {timestamp: '2024-06-30T19:45:00'}]->(p8),
                (u9)-[:Posted {timestamp: '2024-05-18T12:00:00'}]->(p9),
                (u10)-[:Posted {timestamp: '2024-04-05T07:00:00'}]->(p10),
                (u5)-[:Is_interest_in {timestamp: '2024-01-15T14:30:00'}]->(i3),
                (u6)-[:Is_interest_in {timestamp: '2024-02-20T15:45:00'}]->(i4),
                (u7)-[:Is_interest_in {timestamp: '2024-03-25T16:00:00'}]->(i5),
                (u8)-[:Is_interest_in {timestamp: '2024-04-30T17:15:00'}]->(i5),
                (u9)-[:Is_interest_in {timestamp: '2024-05-05T18:30:00'}]->(i3),
                (u10)-[:Is_interest_in {timestamp: '2024-06-10T19:45:00'}]->(i3),
                (p5)-[:Posted_on {timestamp: '2024-09-15T09:30:00'}]->(ch3),
                (p6)-[:Posted_on {timestamp: '2024-08-20T14:00:00'}]->(ch4),
                (p7)-[:Posted_on {timestamp: '2024-07-22T08:15:00'}]->(ch5),
                (p8)-[:Posted_on {timestamp: '2024-06-30T19:45:00'}]->(ch5),
                (p9)-[:Posted_on {timestamp: '2024-05-18T12:00:00'}]->(ch3),
                (p10)-[:Posted_on {timestamp: '2024-04-05T07:00:00'}]->(ch3),
                (c1:Comment {comment_id: '1', post_id: '1', user_id: '2', content: 'Great post!', timestamp: '2024-10-01T12:00:00'}),
                (c2:Comment {comment_id: '2', post_id: '2', user_id: '3', content: 'Interesting thoughts.', timestamp: '2024-11-01T16:00:00'}),
                (c3:Comment {comment_id: '3', post_id: '3', user_id: '1', content: 'I agree!', timestamp: '2024-11-01T17:00:00'}),
                (c4:Comment {comment_id: '4', post_id: '5', user_id: '6', content: 'Amazing scenery!', timestamp: '2024-09-15T10:00:00'}),
                (c5:Comment {comment_id: '5', post_id: '6', user_id: '5', content: 'Very informative.', timestamp: '2024-08-20T15:00:00'}),
                (u2)-[:Publish {timestamp: '2024-10-01T12:00:00'}]->(c1),
                (c1)-[:Is_on {timestamp: '2024-10-01T12:00:00'}]->(p1),
                (u3)-[:Publish {timestamp: '2024-11-01T16:00:00'}]->(c2),
                (c2)-[:Is_on {timestamp: '2024-11-01T16:00:00'}]->(p2),
                (u1)-[:Publish {timestamp: '2024-11-01T17:00:00'}]->(c3),
                (c3)-[:Is_on {timestamp: '2024-11-01T17:00:00'}]->(p3),
                (u6)-[:Publish {timestamp: '2024-09-15T10:00:00'}]->(c4),
                (c4)-[:Is_on {timestamp: '2024-09-15T10:00:00'}]->(p5),
                (u5)-[:Publish {timestamp: '2024-08-20T15:00:00'}]->(c5),
                (c5)-[:Is_on {timestamp: '2024-08-20T15:00:00'}]->(p6),
                (u1)-[:Like {timestamp: '2024-10-02T08:00:00'}]->(p2),
                (u2)-[:Like {timestamp: '2024-11-02T09:00:00'}]->(p3),
                (u3)-[:Like {timestamp: '2024-10-03T10:00:00'}]->(p1),
                (u4)-[:Like {timestamp: '2024-09-15T11:00:00'}]->(p5),
                (u5)-[:Like {timestamp: '2024-08-21T12:00:00'}]->(p6)
            '''
            session.run(sample_data_query)

        return jsonify({"message": "Database initialized successfully."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
