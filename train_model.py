import pandas as pd
import re
import nltk
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from nltk.stem import WordNetLemmatizer
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

# Download NLTK resources if not already
nltk.download("punkt")
nltk.download("stopwords")
nltk.download('wordnet')
from nltk.corpus import stopwords

df = pd.read_csv("UpdatedResumeDataSet.csv")

lemmatizer = WordNetLemmatizer()

def clean_text(text):
    # Remove URLs
    text = re.sub(r"http\S+|www\S+|https\S+", "", text, flags=re.MULTILINE) 
    # Remove numbers and punctuation
    text = re.sub(r"[^a-zA-Z\s]", "", text)  
    # Lowercase
    text = text.lower()
    # Tokenize
    tokens = nltk.word_tokenize(text)
    # Remove stopwords and lemmatize
    tokens = [
        lemmatizer.lemmatize(word) 
        for word in tokens if word not in stopwords.words("english")
    ]
    return " ".join(tokens)

df["cleaned_resume"] = df["Resume"].apply(clean_text)

X = df["cleaned_resume"]
y = df["Category"]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)


model = Pipeline([
    ("tfidf", TfidfVectorizer(max_features=5000)),
    ("clf", LogisticRegression(max_iter=2000))
])

model.fit(X_train, y_train)


y_pred = model.predict(X_test)
print("Accuracy:", accuracy_score(y_test, y_pred))

with open("resume_model.pkl", "wb") as f:
    pickle.dump(model, f)

print("Model training complete. Saved as resume_model.pkl")
