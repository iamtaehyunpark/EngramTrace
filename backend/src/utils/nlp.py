"""Shared NLP resources; install corpora with the command in the README."""
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize

try:
    nltk_stop_words = set(stopwords.words('english'))
except LookupError as exc:
    raise RuntimeError(
        'NLTK data is missing. Run: python -m nltk.downloader '
        'stopwords punkt_tab wordnet'
    ) from exc

lemmatizer = WordNetLemmatizer()
