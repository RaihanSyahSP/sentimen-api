import requests
import json

def get_topic_modeling_results(keyword, num_topics, num_tweets):
    endpoint = f'http://topic-socialabs.unikomcodelabs.id/topic?keyword={keyword}&num_topics={num_topics}&num_tweets={num_tweets}'
    response = requests.get(endpoint)
    if response.status_code != 200:
        raise Exception(f"Failed to get topic modeling results: {response.text}")
    return response.json()

def post_ids(documents):
    endpoint = 'http://127.0.0.1:5000/classify-sentiment'
    payload = {"tweet_ids": documents}
    headers = {'Content-Type': 'application/json'}
    response = requests.post(endpoint, json=payload, headers=headers)
    if response.status_code != 200:
        raise Exception(f"Failed to classify sentiment: {response.text}")
    return response.json()

def main():
    try:
        # Define your parameters
        keyword = "Prabowo"
        num_topics = 5
        num_tweets = 1000

        # Get topic modeling results
        topic_modeling_results = get_topic_modeling_results(keyword, num_topics, num_tweets)
        
        # Extract id_str from topic modeling results
        documents = [doc['id_str'] for doc in topic_modeling_results.get('data', {}).get('documents_topic', []) if 'id_str' in doc]
        if not documents:
            print("No documents found for the given keyword.")
            return

        # Classify sentiment of the documents
        sentiment_results = post_ids(documents)

        return json.dumps(sentiment_results, indent=2)
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()
