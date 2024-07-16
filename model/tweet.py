from config.db import db
from bson import ObjectId
from pymongo import results  
from datetime import datetime
from flask import jsonify


class Tweet:

    def getTweetsByKeyword(keyword, limit, start_date=None, end_date=None):
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
        
        pipeline.append({'$limit': limit})

        cursor = db.tweets.aggregate(pipeline)
        return list(cursor)
        
    def updateSentiment(data):
        for item in data:
            # Convert the string representation of ObjectId back to ObjectId
            document_id = ObjectId(item['_id'])
            update_data = {
                "predicted_sentiment": item['predicted_sentiment'],
                "probability_sentiment": item['probability_sentiment'],
                # "processed_text": item['processed_text'],
            }
            result = db.tweets.update_one({'_id': document_id}, {'$set': update_data})
            print(f"Updating {document_id}: {result.matched_count} document(s) matched, {result.modified_count} document(s) updated.")

            