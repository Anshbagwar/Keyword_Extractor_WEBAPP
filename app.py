import pickle
from flask import Flask, render_template, request
import re
import nltk
from nltk.stem.wordnet import WordNetLemmatizer
from nltk.corpus import stopwords

app = Flask(__name__)

# Load pickled models
with open('counter_vector.pkl', 'rb') as f:
    cv = pickle.load(f)

with open('tfidf.pkl', 'rb') as f:
    tfidf_transformer = pickle.load(f)

with open('feature_names.pkl', 'rb') as f:
    feature_names = pickle.load(f)



# Predefined stop words
base_stop_words = set(stopwords.words('english'))
custom_stop_words = {"fig", "figure", "image", "sample", "using", "show", "result",
                     "large", "also", "one", "two", "three", "four", "five", "seven",
                     "eight", "nine"}
stop_words = base_stop_words.union(custom_stop_words)

def preprocess_text(txt):
    txt = txt.lower()
    txt = re.sub(r"<.*?>", " ", txt)
    txt = re.sub(r"[^a-zA-Z]", " ", txt)
    txt = re.findall(r'\b\w+\b', txt)

    tokens = [w for w in txt if w not in stop_words and len(w) >= 3]
    lemmatizer = WordNetLemmatizer()
    lemmatized = [lemmatizer.lemmatize(word) for word in tokens]
    return " ".join(lemmatized)

def sort_coo(coo_matrix):
    tuples = zip(coo_matrix.col, coo_matrix.data)
    return sorted(tuples, key=lambda x: (x[1], x[0]), reverse=True)

def extract_topn_from_vector(feature_names, sorted_items, topn=10):
    sorted_items = sorted_items[:topn]
    results = {}
    for idx, score in sorted_items:
        feature = feature_names[idx]
        results[feature] = round(score, 3)
    return results

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/extract_keywords', methods=['POST'])
def extract_keywords():
    file = request.files['file']
    if file.filename == '':
        return render_template('index.html', error="No document selected")

    text = file.read().decode('utf-8', errors='ignore')
    preprocessed = preprocess_text(text)
    tfidf_vector = tfidf_transformer.transform(cv.transform([preprocessed]))
    sorted_items = sort_coo(tfidf_vector.tocoo())
    keywords = extract_topn_from_vector(feature_names, sorted_items, 20)
    return render_template('keywords.html', keywords=keywords)

@app.route('/search_keywords', methods=['POST'])
def search_keywords():
    search = request.form['search'].strip()
    if search:
        matched_keywords = [kw for kw in feature_names if search.lower() in kw.lower()]
        return render_template('keywordslist.html', keywords=matched_keywords[:20])
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
