
from config.db import db
from bson import ObjectId
from pymongo import results  
from datetime import datetime
from flask import jsonify

class Tweet:
    # def getTweetByKeyword(keyword, limit):
    #     return db.sample.find({'full_text': {'$regex': keyword, '$options': 'i'}}).limit(limit)

    # def parse_date(date_str):
    #     # Format: "Tue Feb 20 12:07:34 +0000 2024"
    #     # Konversi string ke datetime object dengan zona waktu
    #     return datetime.strptime(date_str, '%a %b %d %H:%M:%S %z %Y')
       
    
    # def filter_tweets_by_date(tweets, start_date, end_date):
    #     filtered_tweets = []
    #     print(f"Filtering tweets from {start_date} to {end_date}")  # Debugging
    #     print(f"Found {len(tweets)} tweets")  # Debugging
    #     start_datetime = datetime.strptime(f"{start_date} 00:00:00 +0000", "%Y-%m-%d %H:%M:%S %z")
    #     end_datetime = datetime.strptime(f"{end_date} 23:59:59 +0000", "%Y-%m-%d %H:%M:%S %z")
    #     for tweet in tweets:
    #         # Use parse_date to get the datetime object from tweet's created_at
    #         tweet_datetime = Tweet.parse_date(tweet['created_at'])
    #         # Perform the comparison using datetime objects
    #         print(tweet_datetime, start_datetime, end_datetime)  # Debugging
    #         if start_datetime <= tweet_datetime <= end_datetime:
    #             print("Tweet is within the date range")  # Debugging
    #             print(tweet['full_text'])  # Debugging
    #             filtered_tweets.append(tweet)
    #     return filtered_tweets

    # def getTweetsByKeyword(keyword, limit, start_date, end_date):
    #     cursor = db.sample.find({'full_text': {'$regex': keyword, '$options': 'i'}}).limit(limit)
    #     tweets = list(cursor)
    #     print(f"Found {len(tweets)} tweets")  # Debugging
    #     return Tweet.filter_tweets_by_date(tweets, start_date, end_date)

    # def getTweetsByKeyword(keyword, limit, start_date, end_date):
    #     # Mengubah string tanggal ke objek datetime dengan zona waktu
    #     start_datetime = datetime.strptime(f"{start_date} 00:00:00 +0000", "%Y-%m-%d %H:%M:%S %z")
    #     end_datetime = datetime.strptime(f"{end_date} 23:59:59 +0000", "%Y-%m-%d %H:%M:%S %z")
    #     print(f"Filtering tweets from {start_datetime} to {end_datetime}")  # Debugging
    #     print(start_datetime.isoformat(), end_datetime.isoformat())  # Debugging

    #     # Membuat query yang juga memfilter berdasarkan rentang tanggal
    #     cursor = db.sample.find({
    #         'full_text': {'$regex': keyword, '$options': 'i'},
    #         'created_at': {
    #             '$gte': start_datetime.isoformat(),
    #             '$lte': end_datetime.isoformat()
    #         }
    #     }).limit(limit)

    #     tweets = list(cursor)
    #     print(f"Found {len(tweets)} tweets after applying date filter")  # Debugging

    #     return tweets

    def getTweetsByKeyword(keyword, limit, start_date, end_date):
        start_datetime = datetime.strptime(f"{start_date} 00:00:00 +0000", "%Y-%m-%d %H:%M:%S %z")
        end_datetime = datetime.strptime(f"{end_date} 23:59:59 +0000", "%Y-%m-%d %H:%M:%S %z")
        print(f"Filtering tweets from {start_datetime} to {end_datetime}")  # Debugging
        
        # Contoh query dengan aggregation pipeline
        # Menggunakan JavaScript di dalam MongoDB aggregation
        cursor = db.sample.aggregate([
        {
            '$match': {
                'full_text': {'$regex': keyword, '$options': 'i'}
            }
        },
        {
            '$addFields': {
                'parsed_date': {'$toDate': '$created_at'}
            }
        },
        {
            '$match': {
                'parsed_date': {'$gte': start_datetime, '$lte': end_datetime}
            }
        },
        {
            '$limit': limit
        }
        ])
        return list(cursor)
    
    def insertTweets(data):
        try:
            result = db.sample.insert_many(data)
            print(f"Inserted {len(result.inserted_ids)} documents")
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    def updateSentiment(data):

        for item in data:
            # Convert the string representation of ObjectId back to ObjectId
            document_id = ObjectId(item['_id'])

            update_data = {
                "predicted_label": item['predicted_label'],
                "predicted_probability_netral": item['predicted_probability_netral'],
                "predicted_probability_negatif": item['predicted_probability_negatif'],
                "predicted_probability_positif": item['predicted_probability_positif'],
                # "processed_text": item['processed_text'],
            }

            result = db.sample.update_one({'_id': document_id}, {'$set': update_data})
            print(f"Updating {document_id}: {result.matched_count} document(s) matched, {result.modified_count} document(s) updated.")

            # Fetch existing document to see what's currently stored
            # existing_document = db.sample.find_one({'_id': document_id})
            # print("Existing document:", existing_document)  # Debugging

            # # Determine if update is needed
            # if existing_document:
            #     needs_update = any(
            #         existing_document.get(key) != update_data[key]
            #         for key in update_data.keys()
            #         if key in existing_document
            #     )
            #     print("Needs update:", needs_update)  # Debugging

            #     # Update if needed
            #     if needs_update:
            #         result = db.sample.update_one({'_id': document_id}, {'$set': update_data})
            #         print(f"Updating {document_id}: {result.matched_count} document(s) matched, {result.modified_count} document(s) updated.")
            #     else:
            #         print(f"No update needed for {document_id}: Existing data matches new data.")
            # else:
            #     print("No document found with ID:", document_id)

            