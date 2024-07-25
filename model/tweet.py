from config.db import db
from bson.int64 import Int64
from pymongo import results  
from datetime import datetime
from flask import jsonify


class Tweet:

    def getTweetsByIds(ids):
       # Convert IDs to string
        ids = [str(id_str) for id_str in ids]

        # Query the database
        query = {'id_str': {'$in': [Int64(id_str) for id_str in ids]}}
        print("Query being executed:", query)
        print("Querying Tweets by IDs:", ids)
        result = list(db.tweets.find(query))
    
        # Debugging output
        print("Result from DB:", result)
        return result
    
    def test_query():
        result = list(db.tweets.find({'id_str': {'$in': [Int64("1723128018716237841"), Int64("1723128111926243816")]}}))
        print("Test Query Result:", result)

     

    def getTweetsByKeyword(keyword, start_date=None, end_date=None):
        match_stage = {
            '$match': {
                'full_text': {'$regex': keyword, '$options': 'i'}
            }
        }
        
        pipeline = [match_stage]

        if start_date and end_date:
            start_datetime = datetime.strptime(f"{start_date} 00:00:00 +0000", "%Y-%m-%d %H:%M:%S %z")
            end_datetime = datetime.strptime(f"{end_date} 23:59:59 +0000", "%Y-%m-%d %H:%M:%S %z")
            print(f"Filtering tweets from {start_datetime} to {end_datetime}")  # Debugging
            
            add_fields_stage = {
                '$addFields': {
                    'parsed_date': {'$toDate': '$created_at'}
                }
            }
            match_date_stage = {
                '$match': {
                    'parsed_date': {'$gte': start_datetime, '$lte': end_datetime}
                }
            }

            pipeline.extend([add_fields_stage, match_date_stage])
        
        # pipeline.append({'$limit': limit})

        cursor = db.tweets.aggregate(pipeline)
        return list(cursor)
    
    def getLabeledTweetsByKeyword(keyword, start_date=None, end_date=None):
        match_stage = {
            '$match': {
                'full_text': {'$regex': keyword, '$options': 'i'},
                'predicted_sentiment': {'$exists': True}
            }
        }

        pipeline = [match_stage]

        if start_date and end_date:
            start_datetime = datetime.strptime(f"{start_date} 00:00:00 +0000", "%Y-%m-%d %H:%M:%S %z")
            end_datetime = datetime.strptime(f"{end_date} 23:59:59 +0000", "%Y-%m-%d %H:%M:%S %z")
            print(f"Filtering tweets from {start_datetime} to {end_datetime}")  # Debugging

            add_fields_stage = {
                '$addFields': {
                    'parsed_date': {'$toDate': '$created_at'}
                }
            }
            match_date_stage = {
                '$match': {
                    'parsed_date': {'$gte': start_datetime, '$lte': end_datetime}
                }
            }

            pipeline.extend([add_fields_stage, match_date_stage])

        cursor = db.tweets.aggregate(pipeline)
        return list(cursor)
        
    def updateSentiment(data):
        for item in data:
            # Use id_str instead of _id
            document_id_str = item['id_str']
            update_data = {
                "predicted_sentiment": item['predicted_sentiment'],
                "probability_sentiment": item['probability_sentiment'],
                # "processed_text": item['processed_text'],
            }
            db.tweets.update_one({'id_str': document_id_str}, {'$set': update_data})
        

                