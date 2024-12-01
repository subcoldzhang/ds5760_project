'''Module for serving API requests'''

from app import app
from bson.json_util import dumps, loads
from flask import request, jsonify
import json
import ast # helper library for parsing data from string
from importlib.machinery import SourceFileLoader
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime

# 1. Connect to the client 
client = MongoClient(host="localhost", port=27017)

# Import the utils module
utils = SourceFileLoader('*', "D:/OneDrive - Vanderbilt/Desktop/Hillbert's PC Files/My Grad Life/Fall 2024/DS5760_NoSQL/FinalProject/ds5760_project/app/utils.py").load_module()

# 2. Select the database
db = client.platform # 'use platform'
# Select the collection
user = db.user
post = db.post
interest = db.interest
friendship = db.friendship 
like = db.like
comment = db.comment

@app.route('/')
def get_initial_response():
    # Message to the user
    message = {
        'apiVersion': 'v1.0',
        'status': '200',
        "message": "Welcome to the Friendship platform!"
        }
    resp = jsonify(message)
    # Returning the object
    return resp

############################## Query 1 ##############################
#####################################################################
@app.route('/search_by_user_id/<user_id>', methods=['GET'])
def search_by_user_id(user_id):
    '''
       Function to find user by id.
       Input is id. Id will follows /search_by_user_id/.
       Normal output is detail information of user. 
       If user_id doesn't exist, then it will print error 404, No This user.
       If there are other errors, error 500 or error 404 (not found) will be returned.
    '''
    try:
        # Query the document
        result = user.find({"user_id": int(user_id)})
        
        # If document not found
        if not result:
            return jsonify({"message": "No This user"}), 404
        
        return dumps(result), 200

    except Exception as e:
        # Error while trying to create customers
        # Add message for debugging purpose
        return jsonify({"error": str(e)}), 400
    
@app.route('/search_by_post_id/<post_id>', methods=['GET'])
def search_by_post_id(post_id):
    '''
       Function to find post by id.
       Input is id. Id will follows /search_by_post_id/.
       Normal output is detail information of post. 
       If post_id doesn't exist, then it will print error 404, No This post.
       If there are other errors, error 500 or error 404 (not found) will be returned.
    '''
    try:
        # Query the document
        result = post.find({"post_id": int(post_id)})
        
        # If document not found
        if not result:
            return jsonify({"message": "No This post"}), 404
        
        return dumps(result), 200

    except Exception as e:
        # Error while trying to create customers
        # Add message for debugging purpose
        return jsonify({"error": str(e)}), 400
    
@app.route('/search_by_interest_id/<interest_id>', methods=['GET'])
def search_by_interest_id(interest_id):
    '''
       Function to find interest by id.
       Input is id. Id will follows /search_by_interest_id/.
       Normal output is detail information of interest. 
       If interest_id doesn't exist, then it will print error 404, No This interest.
       If there are other errors, error 500 or error 404 (not found) will be returned.
    '''
    try:
        # Query the document
        result = interest.find({"interest_id": int(interest_id)})
        
        # If document not found
        if not result:
            return jsonify({"message": "No This interest"}), 404
        
        return dumps(result), 200

    except Exception as e:
        # Error while trying to create customers
        # Add message for debugging purpose
        return jsonify({"error": str(e)}), 400

############################## Query 2 ##############################
#####################################################################
@app.route('/create/user', methods=['POST'])
def create_user():
    '''
       Function to create a new user.
       Input is a detail data of user of json version.
       Normal output is User successfully created. 
       If any required fields are missing, it will return error 400 with a message.
    '''
    try:
        # Create new users
        user_data = request.get_json()
        # Check if there are necessary elements
        required_fields = ['user_id', 'username', 'age', 'location', 'bio']
        
        for value in required_fields:
            if not value in required_fields:
                return jsonify({"error": f"Missing required element"}), 400
        
        user.insert_one(user_data)
        return jsonify({"message": "User successfully created."}), 201

    except Exception as e:
        # Error while trying to create customers
        # Add message for debugging purpose
        return jsonify({"error": str(e)}), 500

@app.route('/create/interest', methods=['POST'])
def create_interest():
    '''
       Function to create a new interest.
       Input is a JSON object with interest details.
       Normal output is "Interest successfully created".
       If any required fields are missing, it will return error 400 with a message.
    '''
    try:
        interest_data = request.get_json()
        required_fields = ['interest_id', 'user_id', 'interest_name', 'description', 'timestamp']

        for field in required_fields:
            if field not in interest_data:
                return jsonify({"error": f"Missing required field"}), 400

        interest.insert_one(interest_data)
        return jsonify({"message": "Interest successfully created."}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/create/friendship', methods=['POST'])
def create_friendship():
    '''
       Function to create a new friendship.
       Input is a JSON object with friendship details.
       Normal output is "Friendship successfully created".
       If any required fields are missing, it will return error 400 with a message.
    '''
    try:
        friendship_data = request.get_json()
        required_fields = ['user_id_1', 'user_id_2', 'timestamp']

        for field in required_fields:
            if field not in friendship_data:
                return jsonify({"error": f"Missing required field: {field}"}), 400

        friendship.insert_one(friendship_data)
        return jsonify({"message": "Friendship successfully created."}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/create/like', methods=['POST'])
def create_like():
    '''
       Function to create a new like.
       Input is a JSON object with like details.
       Normal output is "Like successfully created".
       If any required fields are missing, it will return error 400 with a message.
    '''
    try:
        like_data = request.get_json()
        required_fields = ['like_id', 'user_id', 'post_id', 'timestamp']

        for field in required_fields:
            if field not in like_data:
                return jsonify({"error": f"Missing required field"}), 400

        like.insert_one(like_data)
        return jsonify({"message": "Like successfully created."}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/create/comment', methods=['POST'])
def create_comment():
    '''
       Function to create a new comment.
       Input is a JSON object with comment details.
       Normal output is "Comment successfully created".
       If any required fields are missing, it will return error 400 with a message.
    '''
    try:
        comment_data = request.get_json()
        required_fields = ['comment_id', 'post_id', 'user_id', 'content', 'timestamp']

        for field in required_fields:
            if field not in comment_data:
                return jsonify({"error": f"Missing required field"}), 400

        comment.insert_one(comment_data)
        return jsonify({"message": "Comment successfully created."}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500

############################## Query 3 ##############################
#####################################################################
@app.route('/delete_by_user_id', methods=['DELETE'])
def delete_by_user_id():
    """
       Function to delete the user.
       Input is id
       Normal output is 204. 
       If id doesn't exist, then it will print error 400, Id is required.
       If id doesn't be found in database, then it will print error 304, User not found.
       If there are other errors, error 500 or error 404 (not found) will be returned.
    """
    try:
        id = request.json.get('user_id')
        if not id:
            return jsonify({"error": "Id is required"}), 400

        delete =  user.delete_one({"user_id": id})

        print(delete.raw_result)
        if delete.deleted_count > 0 :
            # Prepare the response
            return 'User deleted successfully', 204
        else:
            # Resource not found
            return 'User not found', 404

    except Exception as e:
        # Error while trying to delete the resource
        # Add message for debugging purpose
        return jsonify({"error": str(e)}), 500

@app.route('/delete_by_post_id', methods=['DELETE'])
def delete_by_post_id():
    """
       Function to delete the post.
       Input is id
       Normal output is 204. 
       If id doesn't exist, then it will print error 400, Id is required.
       If id doesn't be found in database, then it will print error 304, post not found.
       If there are other errors, error 500 or error 404 (not found) will be returned.
    """
    try:
        id = request.json.get('id')
        if not id:
            return jsonify({"error": "Id is required"}), 400

        delete =  post.delete_one({"post_id": id})

        print(delete.raw_result)
        if delete.deleted_count > 0 :
            # Prepare the response
            return 'Post deleted successfully', 204
        else:
            # Resource not found
            return 'Post not found', 404

    except Exception as e:
        # Error while trying to delete the resource
        # Add message for debugging purpose
        return jsonify({"error": str(e)}), 500

@app.route('/delete_by_friendship_id', methods=['DELETE'])
def delete_by_friendship_id():
    """
       Function to delete a friendship.
       Input is user_id_1 and user_id_2 (both required).
       Normal output is 204 if deleted successfully.
       If either user_id_1 or user_id_2 is missing, it will print error 400.
       If the friendship is not found in the database, it will print error 404, friendship not found.
       If there are other errors, a 500 response will be returned.
    """
    try:
        user_id_1 = request.json.get('user_id_1')
        user_id_2 = request.json.get('user_id_2')

        if not user_id_1 or not user_id_2:
            return jsonify({"error": "Both user_id_1 and user_id_2 are required"}), 400

        delete = friendship.delete_one({
            "$or": [
                {"user_id_1": user_id_1, "user_id_2": user_id_2},
                {"user_id_1": user_id_2, "user_id_2": user_id_1}
            ]
        })

        if delete.deleted_count > 0:
            return 'Friendship deleted successfully', 204
        else:
            return 'Friendship not found', 404

    except Exception as e:
        # Error while trying to delete the resource
        # Add message for debugging purpose
        return jsonify({"error": str(e)}), 500

    
@app.route('/delete_by_interest_id', methods=['DELETE'])
def delete_by_interest_id():
    """
       Function to delete the interest.
       Input is id
       Normal output is 204. 
       If id doesn't exist, then it will print error 400, Id is required.
       If id doesn't be found in database, then it will print error 304, interest not found.
       If there are other errors, error 500 or error 404 (not found) will be returned.
    """
    try:
        id = request.json.get('id')
        if not id:
            return jsonify({"error": "Id is required"}), 400

        delete =  interest.delete_one({"interest_id": id})

        print(delete.raw_result)
        if delete.deleted_count > 0 :
            # Prepare the response
            return 'Interest deleted successfully', 204
        else:
            # Resource not found
            return 'Interest not found', 404

    except Exception as e:
        # Error while trying to delete the resource
        # Add message for debugging purpose
        return jsonify({"error": str(e)}), 500

@app.route('/delete_by_like_id', methods=['DELETE'])
def delete_by_like_id():
    """
       Function to delete the like.
       Input is id
       Normal output is 204. 
       If id doesn't exist, then it will print error 400, Id is required.
       If id doesn't be found in database, then it will print error 304, like not found.
       If there are other errors, error 500 or error 404 (not found) will be returned.
    """
    try:
        id = request.json.get('id')
        if not id:
            return jsonify({"error": "Id is required"}), 400

        delete =  like.delete_one({"like_id": id})

        print(delete.raw_result)
        if delete.deleted_count > 0 :
            # Prepare the response
            return 'Like deleted successfully', 204
        else:
            # Resource not found
            return 'Like not found', 404

    except Exception as e:
        # Error while trying to delete the resource
        # Add message for debugging purpose
        return jsonify({"error": str(e)}), 500

@app.route('/delete_by_comment_id', methods=['DELETE'])
def delete_by_comment_id():
    """
       Function to delete the comment.
       Input is id
       Normal output is 204. 
       If id doesn't exist, then it will print error 400, Id is required.
       If id doesn't be found in database, then it will print error 304, comment not found.
       If there are other errors, error 500 or error 404 (not found) will be returned.
    """
    try:
        id = request.json.get('id')
        if not id:
            return jsonify({"error": "Id is required"}), 400

        delete =  comment.delete_one({"comment_id": id})

        print(delete.raw_result)
        if delete.deleted_count > 0 :
            # Prepare the response
            return 'Comment deleted successfully', 204
        else:
            # Resource not found
            return 'Comment not found', 404

    except Exception as e:
        # Error while trying to delete the resource
        # Add message for debugging purpose
        return jsonify({"error": str(e)}), 500

############################## Query 4 ##############################
#####################################################################
@app.route('/update_by_user_name', methods=['PUT'])
def update_by_user():
    '''
       Function to update details of user by name.
       Input is name and new information.
       Normal output is user successfully updated. 
       If name doesn't exist, then it will print error 400, name is required.
       If name doesn't be found in database, then it will print error 304, user not found.
       If there are other errors, error 500 or error 404 (not found) will be returned.
    '''
    try:
        name = request.json.get('username')
        if not name:
            return jsonify({"error": "Name is required"}), 400
        
        # update details of user
        updated_data = ast.literal_eval(json.dumps(request.get_json()))
        # Query the document
        records_updated = user.update_one({'username': name}, {"$set": updated_data})

        if records_updated.modified_count > 0:
            # Prepare the response
            return jsonify({"message": "User successfully updated"}), 200
        else:
            # Resource not found
            return jsonify({"message": "User not found"}), 304

    except Exception as e:
        # Error while trying to delete the resource
        # Add message for debugging purpose
        return jsonify({"error": str(e)}), 500

@app.route('/update_by_post_id', methods=['PUT'])
def update_by_post_id():
    '''
       Function to update details of post by id
       Input is id and new information.
       Normal output is post successfully updated. 
       If id doesn't exist, then it will print error 400, id is required.
       If id doesn't be found in database, then it will print error 304, post not found.
       If there are other errors, error 500 or error 404 (not found) will be returned.
    '''
    try:
        id = request.json.get('id')
        if not id:
            return jsonify({"error": "Id is required"}), 400
        
        updated_data = ast.literal_eval(json.dumps(request.get_json()))
        # Query the document
        records_updated = post.update_one({'post_id': id}, {"$set": updated_data})

        if records_updated.modified_count > 0:
            # Prepare the response
            return jsonify({"message": "Post successfully updated"}), 200
        else:
            # Resource not found
            return jsonify({"message": "Post not found"}), 304

    except Exception as e:
        # Error while trying to delete the resource
        # Add message for debugging purpose
        return jsonify({"error": str(e)}), 500
    
@app.route('/update_by_comment_id', methods=['PUT'])
def update_by_comment_id():
    '''
       Function to update details of comment by id
       Input is id and new information.
       Normal output is comment successfully updated. 
       If id doesn't exist, then it will print error 400, id is required.
       If id doesn't be found in database, then it will print error 304, comment not found.
       If there are other errors, error 500 or error 404 (not found) will be returned.
    '''
    try:
        id = request.json.get('id')
        if not id:
            return jsonify({"error": "Id is required"}), 400
        
        updated_data = ast.literal_eval(json.dumps(request.get_json()))
        # Query the document
        records_updated = comment.update_one({'comment_id': id}, {"$set": updated_data})

        if records_updated.modified_count > 0:
            # Prepare the response
            return jsonify({"message": "Comment successfully updated"}), 200
        else:
            # Resource not found
            return jsonify({"message": "Comment not found"}), 304

    except Exception as e:
        # Error while trying to delete the resource
        # Add message for debugging purpose
        return jsonify({"error": str(e)}), 500

############################## Query 5 ##############################
#####################################################################
@app.route('/newpost', methods=['POST'])
def post_information():
    '''
       Function to create a new post.
       Input is a JSON object with post details.
       Normal output is "Post successfully created".
       If any required fields are missing, it will return error 400 with a message.
    '''
    try:
        post_data = request.get_json()
        required_fields = ['post_id', 'user_id', 'content', 'topic', 'timestamp']

        for field in required_fields:
            if field not in post_data:
                return jsonify({"error": f"Missing required field"}), 400

        post.insert_one(post_data)
        return jsonify({"message": "Post successfully created."}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500    

############################## Query 6 ##############################
#####################################################################
@app.route('/query_by_timestamp', methods=['GET'])
def query_by_timestamp():
    """
       Function to query posts by timestamp.
       Input are min_timestamp and max_timestamp in ISO format (e.g., "2024-11-01T00:00:00Z").
       Normal output is all posts with timestamps between min_timestamp and max_timestamp.
       If min_timestamp or max_timestamp is missing, it will return error 400.
       If there are other errors, error 500 will be returned.
    """
    try:
        min_timestamp = request.args.get('min_timestamp')
        max_timestamp = request.args.get('max_timestamp')

        if not min_timestamp or not max_timestamp:
            return jsonify({"error": "Min_timestamp and max_timestamp are required"}), 400

        posts = post.find({"timestamp": {"$gte": min_timestamp, "$lte": max_timestamp}})

        results = []

        # Convert ObjectId to string and prepare results
        for p in posts:
            p['_id'] = str(p['_id'])
            results.append(p)

        return jsonify(results), 200

    except Exception as e:
        # Return error message for debugging
        return jsonify({"error": str(e)}), 500

@app.route('/query_friends', methods=['GET'])
def query_friends():
    """
       Function to query a user's friend list.
       Input is username.
       Output is a list of usernames for the user's friends.
    """
    try:
        username = request.args.get('username')
        if not username:
            return jsonify({"error": "Username is required"}), 400

        friends = list(friendship.find({"$or": [{"username_1": username}, {"username_2": username}]}))
        friend_ids = set()

        for f in friends:
            if f["username_1"] == username:
                friend_ids.add(f["username_2"])
            else:
                friend_ids.add(f["username_1"])

        return jsonify(list(friend_ids)), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

############################## Query 7 ##############################
#####################################################################
@app.route('/query_top_posts', methods=['GET'])
def query_top_posts():
    """
       Function to query the top 3 most popular posts.
       The popularity of a post is determined by the number of likes.
       Output is a ranked list of post IDs and their like counts.
       If there are other errors, error 500 will be returned.
    """
    try:
        top_posts = list(like.aggregate([
            {"$group": {"_id": "$post_id", "like_count": {"$sum": 1}}},
            {"$sort": {"like_count": -1}},
            {"$limit": 3}
        ]))

        return jsonify(top_posts), 200

    except Exception as e:
        # Return error message for debugging
        return jsonify({"error": str(e)}), 500
    

@app.route('/query_most_common_interest', methods=['GET'])
def query_most_common_interest():
    """
       Function to query the top 3 most common interest.
       The popularity of a interest is determined by the number of likes.
       Output is a interest and its like counts.
       If there are other errors, error 500 will be returned.
    """
    try:
        common_interest = list(interest.aggregate([
            {"$group": {"_id": "$interest_name", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 1}
        ]))

        return jsonify(common_interest), 200

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