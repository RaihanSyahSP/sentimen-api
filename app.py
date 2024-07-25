import pickle
import os
import pandas as pd
import numpy as np
import re
import requests

from flask import Flask, request, jsonify
from config.db import db
from bson import ObjectId
from bson.int64 import Int64
from model.tweet import Tweet
from service.sentiment import Sentiment
from dotenv import load_dotenv

load_dotenv()
auth_token = os.getenv("AUTH_TOKEN")


app = Flask(__name__)

def serialize(data):
    if isinstance(data, ObjectId):
        return str(data)
    elif isinstance(data, dict):
        return {key: serialize(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [serialize(item) for item in data]
    else:
        return data


@app.route('/')
def index():
    return 'Hello World!'

@app.route('/classify-sentiment', methods=['POST'])
def classify_sentiment():
    try:
        # if request.headers.get('Authorization') != auth_token:
        #     return jsonify({"error": "Unauthorized"}), 401

        request_data = request.get_json()
        tweet_ids = request_data.get('tweet_ids', [])

        if not tweet_ids:
            return jsonify({"error": "No tweet_ids provided"}), 400

        # Filter out None values
        tweet_ids = [id_str for id_str in tweet_ids if id_str is not None]
        data = Tweet.getTweetsByIds(ids=tweet_ids)

        if not data:
            return jsonify({"error": "No tweets found for the given IDs"}), 404
        
        # Check if the tweets are already labeled
        unlabeled_data = [tweet for tweet in data if tweet.get('predicted_sentiment') is None]
        
        if unlabeled_data:
            # Classify sentiment for unlabeled tweets
            sentiment = Sentiment.classify_sentiment(data=unlabeled_data)
            Tweet.updateSentiment(sentiment)
            response_message = "Tweet has been labeled"
        else:
            response_message = "All tweets are already labeled"

        return jsonify({
            "success": response_message,
            "total_data": len(data), # Return the tweet data with labels
            "data" : serialize(data)
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# @app.route('/classify-sentiment', methods=['GET'])
# def get_result():
#     try:
#         keyword = request.args.get('keyword')
#         # jumlah_tweet = request.args.get('jumlah_tweet', 1000)
#         start_date = request.args.get('start_date') # Expected format: "YYYY-MM-DD"
#         end_date = request.args.get('end_date')  # Expected format: "YYYY-MM-DD"
        
#         keyword_regex = f".*{keyword}.*"
        
#          # Check for labeled tweets in the given date range
#         labeled_cursor = Tweet.getLabeledTweetsByKeyword(keyword=keyword_regex, start_date=start_date, end_date=end_date)

#         if labeled_cursor:
#             # Convert ObjectId to string
#             labeled_data = []
#             for tweet in labeled_cursor:
#                 tweet['_id'] = str(tweet['_id'])
#                 labeled_data.append(tweet)
#             return jsonify(labeled_data), 200

#         # If no labeled tweets found, get additional unlabeled tweets
#         cursor = Tweet.getTweetsByKeyword(keyword=keyword_regex, start_date=start_date, end_date=end_date)

#         if not cursor:
#             return jsonify({"error": "No tweets found"}), 404

#         # If there are tweets to be labeled, proceed with classification
#         data = [tweet.copy() for tweet in cursor]
#         for tweet in data:
#             tweet['_id'] = str(tweet['_id'])

#         sentiment = Sentiment.classify_sentiment(data=data)
#         Tweet.updateSentiment(sentiment)

#         return jsonify(sentiment), 200
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500     

@app.route('/visualize-sentiment', methods=['GET'])
def visualize_sentiment():
    try:
        keyword = request.args.get('keyword')
        num_topics = request.args.get('num_topics', '5')
        num_tweets = request.args.get('num_tweets', '1000')  # default value
        topic_filter = request.args.get('topic')  # Get the topic filter from request

        endpoint = f'http://topic-socialabs.unikomcodelabs.id/topic?keyword={keyword}&num_topics={num_topics}&num_tweets={num_tweets}'
        response = requests.get(endpoint)
        response_data = response.json()

        data = response_data['data']['documents_topic']
        len_data = len(data)
    
        # Filter data with predicted_sentiment
        data_with_sentiment = [item for item in data if 'predicted_sentiment' in item]

        if not data_with_sentiment:
            return jsonify({"error": "No tweets with sentiment data found"}), 404

        # Calculate overall sentiment percentage
        sentiment_percentage = Sentiment.calculate_sentiment_percentages(data=data_with_sentiment)

        # Calculate sentiment percentage by topic
        sentiment_percentage_by_topic = Sentiment.calculate_sentiment_percentages_by_topic(data=data_with_sentiment)

        if topic_filter:
            # Filter tweets by topic
            filtered_sentiment = [item for item in data_with_sentiment if item['topic'] == topic_filter]
            if filtered_sentiment:
                return jsonify(
                {
                    "sentiment": filtered_sentiment,
                    "sentiment_percentage_by_topic": sentiment_percentage_by_topic[topic_filter],
                    "total_data": len(filtered_sentiment)
                }), 200
            else:
                return jsonify(
                {
                    "sentiment": [],
                    "sentiment_percentage_by_topic": {},
                    "total_data": "No data found for the specified topic"
                }), 200
        else:
            return jsonify(
            {
                "sentiment": data_with_sentiment,
                "sentiment_percentage": sentiment_percentage,
                "sentiment_percentage_by_topic": sentiment_percentage_by_topic,
                "total_data": len_data
            }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)

