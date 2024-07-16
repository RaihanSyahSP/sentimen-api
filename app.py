import pickle
import os
import pandas as pd
import numpy as np
import re
import requests

from flask import Flask, request, jsonify
from config.db import db
from model.tweet import Tweet
from service.sentiment import Sentiment
from dotenv import load_dotenv

load_dotenv()
auth_token = os.getenv("AUTH_TOKEN")


app = Flask(__name__)

def clean_data(data):
    for doc in data:
        for key, value in doc.items():
            if pd.isna(value):
                doc[key] = None
        if 'topic_probability':
            del doc ['topic_probability']   # atau nilai default yang sesuai
        if '__v' in doc:
            del doc['__v']
    return data

@app.route('/')
def index():
    return 'Hello World!'

@app.route('/classify-sentiment', methods=['GET'])
def get_result():
    try:
        keyword = request.args.get('keyword')
        jumlah_tweet = request.args.get('jumlah_tweet', 1000)
        start_date = request.args.get('start_date') # Expected format: "YYYY-MM-DD"
        end_date = request.args.get('end_date')  # Expected format: "YYYY-MM-DD"

        # if not (start_date and end_date):
        #     return jsonify({"error": "Start date and end date must be provided"}), 400
        
        keyword_regex = f".*{keyword}.*"
        
        cursor = Tweet.getTweetsByKeyword(keyword=keyword_regex, limit=jumlah_tweet, start_date=start_date, end_date=end_date)

        if not cursor:
            return jsonify({"error": "No tweets found"}), 404

        # classify sentiment
        data = []
        for tweet in cursor:
            tweet_data = tweet.copy()  # Make a copy of the dictionary to modify it
            tweet_data['_id'] = str(tweet['_id'])  # Convert ObjectId to string
            data.append(tweet_data)

        sentiment = Sentiment.classify_sentiment(data=data)

        # add atribut sentiment to database
        Tweet.updateSentiment(sentiment)

        return jsonify(sentiment), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500     

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
    
        # Calculate overall sentiment percentage
        sentiment_percentage = Sentiment.calculate_sentiment_percentages(data=data)

        # Calculate sentiment percentage by topic
        sentiment_percentage_by_topic = Sentiment.calculate_sentiment_percentages_by_topic(data=data)

        if topic_filter:
            # Filter tweets by topic
            filtered_sentiment = [item for item in data if item['topic'] == topic_filter]
            return jsonify(
            {
                "sentiment": filtered_sentiment,
                "sentiment_percentage_by_topic": sentiment_percentage_by_topic[topic_filter],
                "total_data": len(filtered_sentiment) if filtered_sentiment else "No data found for the specified topic"
            }), 200
        else:
            return jsonify(
            {
                "sentiment": data,
                "sentiment_percentage": sentiment_percentage,
                "sentiment_percentage_by_topic": sentiment_percentage_by_topic,
                "total_data": len_data
            }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)

