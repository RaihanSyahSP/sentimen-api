import string
import pandas as pd
import numpy as np
import re
import nltk
import pickle

from nltk.tokenize import word_tokenize
from mpstemmer import MPStemmer
from nltk.corpus import stopwords
nltk.download('stopwords')
stemmer = MPStemmer()

from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences

# Load the pre-trained sentiment analysis model
model = load_model('./saved_model/model-cnn-lstm-no-testing.h5')


class Sentiment:
    def classify_sentiment(data):

        def lower_case(text):
            return text.lower()

        def remove_tweet_special(text):
            # remove tab, new line, ans back slice
            text = text.replace('\\t'," ").replace('\\n'," ").replace('\\u'," ").replace('\\',"")
            # remove non ASCII (emoticon, chinese word, .etc)
            text = text.encode('ascii', 'replace').decode('ascii')
            # remove mention, link, hashtag
            text = ' '.join(re.sub("([@#][A-Za-z0-9]+)|(\w+:\/\/\S+)"," ", text).split())
            # remove incomplete URL
            return text.replace("http://", " ").replace("https://", " ")

        def remove_number(text):
            return re.sub(r"\d+", "", text)

        def remove_punctuation(text):
            return text.translate(str.maketrans("","",string.punctuation))

        def remove_whitespace_LT(text):
            return text.strip()

        def remove_whitespace_multiple(text):
            return re.sub('\s+',' ',text)

        def remove_singl_char(text):
            return re.sub(r"\b[a-zA-Z]\b", "", text)

        def remove_repeated_char(text):
            return re.sub(r'(.)\1+', r'\1', text)

        def word_tokenize_wrapper(text):
            return word_tokenize(text)


        ## normalization
        normalizad_word = pd.read_csv("./utils/kamus-alay.csv")

        normalizad_word_dict = {}

        for index, row in normalizad_word.iterrows():
            if row[0] not in normalizad_word_dict:
                normalizad_word_dict[row[0]] = row[1] 

        def normalized_term(document):
            return [normalizad_word_dict[term] if term in normalizad_word_dict else term for term in document]


        def stem_wrapper(term):
            return [stemmer.stem(word) for word in term]
        

        stop_words = stopwords.words('indonesian')

        # Hapus kata "tidak" dari daftar stopword
        stop_words = [word for word in stop_words if word not in ['tidak', 'baik', 'jelek', 'jangan', 'belum', 'bukan', "enggak", "engga", "bener", "benar"]]

        # ---------------------------- manualy add stopword  ------------------------------------
        # append additional stopword
        stop_words.extend(["yg", "dg", "rt", "dgn", "ny", "d", 'klo', 
                            'kalo', 'amp', 'biar', 'bikin', 'bilang', 
                            'gak', 'ga', 'krn', 'nya', 'nih', 'sih', 
                            'si', 'tau', 'tdk', 'tuh', 'utk', 'ya', 
                            'jd', 'jgn', 'sdh', 'aja', 'n', 't', 
                            'nyg', 'hehe', 'pen', 'u', 'nan', 'loh', 'rt',
                            '&amp', 'yah'])

        # ----------------------- add stopword from txt file ------------------------------------
        # read txt stopword using pandas
        txt_stopword = pd.read_csv("./utils/stopwords.txt", names= ["stopwords"], header = None)

        # convert stopword string to list & append additional stopword
        stop_words.extend(txt_stopword["stopwords"][0].split(' '))

        # ---------------------------------------------------------------------------------------

        # convert list to dictionary
        stop_words = set(stop_words)


        #remove stopword pada list token
        def stopwords_removal(words):
            return [word for word in words if word not in stop_words]
        
        def convert_negation(tokens):
            negations = {'tidak', 'jangan', 'belum', 'bukan', 'enggak'}
            result = []
            skip_next = False

            for i, word in enumerate(tokens):
                if skip_next:
                    skip_next = False
                    continue
                if word in negations and i + 1 < len(tokens):
                    next_word = tokens[i + 1]
                    result.append(f'{word}_{next_word}')
                    skip_next = True
                else:
                    result.append(word)

            return result
        
        def replace_nan_with_none(data):
            return data.applymap(lambda x: None if pd.isna(x) else x)

        df = pd.DataFrame(data)
        
        if 'predicted_sentiment' not in df.columns:
            df['predicted_sentiment'] = np.nan
            df['probability_sentiment'] = np.nan

        # Filter dokumen yang belum diproses
        # to_process_df = df[df['predicted_sentiment'].isna()]

        if not df.empty:
            
            # # Text preprocessing
            df['processed_text'] = df['full_text'].apply(lower_case)
            df['processed_text'] = df['processed_text'].apply(remove_tweet_special)
            df['processed_text'] = df['processed_text'].apply(remove_number)
            df['processed_text'] = df['processed_text'].apply(remove_punctuation)
            df['processed_text'] = df['processed_text'].apply(remove_whitespace_LT)
            df['processed_text'] = df['processed_text'].apply(remove_whitespace_multiple)
            df['processed_text'] = df['processed_text'].apply(remove_singl_char)
            df['processed_text'] = df['processed_text'].apply(remove_repeated_char)
            df['processed_text'] = df['processed_text'].apply(word_tokenize_wrapper)
            df['processed_text'] = df['processed_text'].apply(normalized_term)
            df['processed_text'] = df['processed_text'].apply(stem_wrapper)
            df['processed_text'] = df['processed_text'].apply(stopwords_removal)
            df['processed_text'] = df['processed_text'].apply(convert_negation)
            df['processed_text'] = df['processed_text'].apply(' '.join)

            print("Text preprocessing done!")

            # # Convert the text data to sequences
            with open('./utils/tokenizer-cnn-lstm-no-testing.pickle', 'rb') as handle:
                tokenizer = pickle.load(handle)

            sequences = tokenizer.texts_to_sequences(df['processed_text'])
            padded_sequences = pad_sequences(sequences, maxlen=50, truncating='post', padding='post')

            # # Predict the sentiment of the text data
            predictions = model.predict(padded_sequences)
            # print(predictions)
            predicted_labels = []
            predicted_probabilities = []  # Menyimpan probabilitas prediksi untuk semua kelas

            for pred in predictions:

                probability_positive = pred[0] 
                probability_negative = 1 - probability_positive

                # Menambahkan probabilitas prediksi ke dalam list
                predicted_probabilities.append({'positive': probability_positive, 'negative': probability_negative})

                # 2 kelas
                if pred > 0.5:
                    predicted_labels.append("Positif")
                else:
                    predicted_labels.append("Negatif")
                # predicted_probabilities.append(pred)    
            print("Prediction done!")

            # Menambahkan hasil prediksi dan probabilitas prediksi ke dalam data asli
            df['predicted_sentiment'] = predicted_labels
            df['probability_sentiment'] = [predicted_probabilities[i]['positive'] if predicted_labels[i] == 'Positif' else predicted_probabilities[i]['negative'] for i in range(len(predicted_labels))]

            # Menggabungkan hasil kembali ke dataframe asli
            df.update(df)
        
        # Ganti NaN dengan None sebelum mengembalikan sebagai JSON
        df = replace_nan_with_none(df)

        return df.to_dict(orient='records')
    
    @staticmethod
    def calculate_sentiment_percentages(data):
        total = len(data)
        positive = sum(1 for item in data if item['predicted_sentiment'] == 'Positif')
        negative = total - positive
        return {
            'positive': (positive / total) * 100,
            'negative': (negative / total) * 100
        }

    @staticmethod
    def calculate_sentiment_percentages_by_topic(data):
        topics = {}
        for item in data:
            topic = item.get('topic', 'unknown')
            if topic not in topics:
                topics[topic] = {'total': 0, 'positive': 0, 'negative': 0}
            topics[topic]['total'] += 1
            if item['predicted_sentiment'] == 'Positif':
                topics[topic]['positive'] += 1
            else:
                topics[topic]['negative'] += 1
        
        percentages_by_topic = {}
        for topic, counts in topics.items():
            percentages_by_topic[topic] = {
                'positive': (counts['positive'] / counts['total']) * 100,
                'negative': (counts['negative'] / counts['total']) * 100
            }
        
        return percentages_by_topic
    






