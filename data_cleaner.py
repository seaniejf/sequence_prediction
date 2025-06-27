import re
import string
from bs4 import BeautifulSoup
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import cleantext

PUNKT_RESOURCE = "tokenizers/punkt"

def ensure_nltk_resource(resource_name):
	try:
		nltk.data.find(resource_name)
	except LookupError:
		nltk.download(resource_name.split('/')[-1])

ensure_nltk_resource('tokenizers/punkt')
ensure_nltk_resource('tokenizers/punkt_tab')

class DataCleaner:
	def __init__(self):
		pass

	def is_all_punctuation(self, s):
		return all(char in string.punctuation for char in s)

	def is_date(self, s):
		return re.match(r'^\d{2}:\d{2}:\d{2}([\.:]\d{1,9})?$', s) is not None

	def is_number(self, s):
		try:
			float(s)
			return True
		except ValueError:
			try:
				int(s)
				return True
			except ValueError:
				return False

	def clean_data2(self, text):
		tokens = word_tokenize(text)
		final_tokens = []
		for token in tokens:
			if len(token) < 4:
				continue
			if self.is_all_punctuation(token):
				continue
			if self.is_number(token):
				continue
			if self.is_date(token):
				continue

			token = token.lower()
			if token in stopwords.words('english'):
				continue

			token.replace('\x1b', '') # Remove escape characters
			final_tokens.append(token)

		return ' '.join(final_tokens)

	def clean_data(self, text):
		hash_pattern = re.compile(r'\b[a-fA-F0-9]{4,}\b')
		hashless = re.sub(hash_pattern, '', text)

		soup = BeautifulSoup(hashless, "html.parser")
		cleaned_text = cleantext.clean(soup,
				fix_unicode=True,               # fix various unicode errors
				to_ascii=True,                  # transliterate to closest ASCII representation
				lower=True,                     # lowercase text
				no_line_breaks=True,            # fully strip line breaks as opposed to only normalizing them
				no_urls=True,                   # replace all URLs with a special token
				no_emails=False,                # replace all email addresses with a special token
				no_phone_numbers=False,         # replace all phone numbers with a special token
				no_numbers=True,                # replace all numbers with a special token
				no_digits=True,                 # replace all digits with a special token
				no_currency_symbols=False,      # replace all currency symbols with a special token
				no_punct=True,                  # remove punctuations
				replace_with_punct="",          # instead of removing punctuations you may replace them
				replace_with_url="",
				replace_with_email="<EMAIL>",
				replace_with_phone_number="<PHONE>",
				replace_with_number="",
				replace_with_digit="",
				replace_with_currency_symbol="<CURRENCY>",
				lang="en"                       # set to 'de' for German special handling
			)

		tokens = word_tokenize(cleaned_text)
		final_tokens = []
		for token in tokens:
			if len(token) < 3:
				continue
			if token not in stopwords.words('english'):
				final_tokens.append(token)

		return ' '.join(final_tokens)
