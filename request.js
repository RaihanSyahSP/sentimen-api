

async function getTopicModelingResults(keyword, numTopics, numTweets) {
    const endpoint = `http://topic-socialabs.unikomcodelabs.id/topic?keyword=${keyword}&num_topics=${numTopics}&num_tweets=${numTweets}`;
    const response = await fetch(endpoint);
    if (!response.ok) {
        throw new Error(`Failed to get topic modeling results: ${response.statusText}`);
    }
    return response.json();
}

async function classifySentiment(documents) {
    const endpoint = "http://127.0.0.1:5000/classify-sentiment";
    const payload = { documents };
    const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
    });
    if (!response.ok) {
        throw new Error(`Failed to classify sentiment: ${response.statusText}`);
    }
    return response.json();
}

async function main() {
    try {
        const keyword = "prabowo";
        const numTopics = 5;
        const numTweets = 1000;

        // Get topic modeling results
        const topicModelingResults = await getTopicModelingResults(keyword, numTopics, numTweets);
        
        // Extract id_str from topic modeling results
         const documents = topicModelingResults.data.documents_topic.map((doc) => {
           const id = doc.id_str ? BigInt(doc.id_str) : BigInt(0);
           return id.toString();
         });
        
        console.log("Documents:", documents);

        if (documents.length === 0) {
            console.log("No documents found for the given keyword.");
            return;
        }

        // Classify sentiment of the documents
        const sentimentResults = await classifySentiment(documents);

        console.log("Sentiment Results:", sentimentResults);

    } catch (error) {
        console.error("An error occurred:", error.message);
    }
}

main();
