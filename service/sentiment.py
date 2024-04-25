import string
import pandas as pd
import numpy as np
import re
import nltk
import pickle

from nltk.tokenize import word_tokenize
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
from nltk.corpus import stopwords
nltk.download('stopwords')

from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences

# Load the pre-trained sentiment analysis model
model = load_model('./saved_model/model-cnn-word2vec-3-classes-stemming.h5')


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


        factory = StemmerFactory()
        def stem_wrapper(text):
            stemmer = factory.create_stemmer()
            return stemmer.stem(text)



        stop_words = stopwords.words('indonesian')
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

        # Convert list of texts into a DataFrame
        df = pd.DataFrame(data)
        
        # Pastikan kolom 'predicted_label' ada, jika tidak, buat dan set semua nilai menjadi NaN
        if 'predicted_label' not in df.columns:
            df['predicted_label'] = np.nan
            df['predicted_probability_netral'] = np.nan
            df['predicted_probability_negatif'] = np.nan
            df['predicted_probability_positif'] = np.nan

        # Filter dokumen yang belum diproses
        to_process_df = df[df['predicted_label'].isna()]

        if not to_process_df.empty:
            
            # # Text preprocessing
            to_process_df['processed_text'] = to_process_df['full_text'].apply(lower_case)
            to_process_df['processed_text'] = to_process_df['processed_text'].apply(remove_tweet_special)
            to_process_df['processed_text'] = to_process_df['processed_text'].apply(remove_number)
            to_process_df['processed_text'] = to_process_df['processed_text'].apply(remove_punctuation)
            to_process_df['processed_text'] = to_process_df['processed_text'].apply(remove_whitespace_LT)
            to_process_df['processed_text'] = to_process_df['processed_text'].apply(remove_whitespace_multiple)
            to_process_df['processed_text'] = to_process_df['processed_text'].apply(remove_singl_char)
            to_process_df['processed_text'] = to_process_df['processed_text'].apply(word_tokenize_wrapper)
            to_process_df['processed_text'] = to_process_df['processed_text'].apply(normalized_term)
            to_process_df['processed_text'] = to_process_df['processed_text'].apply(lambda x: [stem_wrapper(word) for word in x])
            to_process_df['processed_text'] = to_process_df['processed_text'].apply(stopwords_removal)
            to_process_df['processed_text'] = to_process_df['processed_text'].apply(' '.join)

            print("Text preprocessing done!")

            # # Convert the text data to sequences
            with open('./utils/tokenizer-3classes.pickle', 'rb') as handle:
                tokenizer = pickle.load(handle)

            sequences = tokenizer.texts_to_sequences(to_process_df['processed_text'])
            padded_sequences = pad_sequences(sequences, maxlen=100, truncating='post')

            # # Predict the sentiment of the text data
            predictions = model.predict(padded_sequences)
            predicted_labels = []
            predicted_probabilities = []  # Menyimpan probabilitas prediksi untuk semua kelas

            for pred in predictions:
                # Menentukan kelas berdasarkan nilai probabilitas tertinggi
                label_index = np.argmax(pred)
                if label_index == 0:
                    predicted_labels.append("Netral")
                elif label_index == 1:
                    predicted_labels.append("Negatif")
                else:
                    predicted_labels.append("Positif")
                
                # Menyimpan probabilitas prediksi untuk semua kelas
                predicted_probabilities.append(pred)  # Menyimpan array probabilitas dari softmax

            print("Prediction done!")

            # Menambahkan hasil prediksi dan probabilitas prediksi ke dalam data asli
            to_process_df['predicted_label'] = predicted_labels
            to_process_df['predicted_probability_netral'] = [prob[0] for prob in predicted_probabilities]
            to_process_df['predicted_probability_negatif'] = [prob[1] for prob in predicted_probabilities]
            to_process_df['predicted_probability_positif'] = [prob[2] for prob in predicted_probabilities]

            # Menggabungkan hasil kembali ke dataframe asli
            df.update(to_process_df)

        return df.to_dict(orient='records')
   
    






