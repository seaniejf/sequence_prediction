import os
import json
import argparse
import textwrap
import logging
import numpy as np
from sklearn.linear_model import RidgeClassifier
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import classification_report
import joblib

VECTORIZER_DATA_FILE = 'vectorizer.joblib'
CLASSIFIER_DATA_FILE = 'classifier.joblib'

class MyRidgePredictor:

	def __init__(self, cache_dir=None):
		self.cache_dir = cache_dir
		self.X_test = None
		self.y_test = None
		self.vectorizer_path = os.path.join(self.cache_dir, VECTORIZER_DATA_FILE)
		self.classifier_path = os.path.join(self.cache_dir, CLASSIFIER_DATA_FILE)
		self.vectorizer = None
		self.classifier = None

	def read_data_file(self, fname, training=True):
		try:
			with open(fname, 'r', encoding='utf=8', errors='ignore') as f:
				data = json.load(f)
		except Exception as e:
			logging.error("Error reading file %s: %s", fname, e)
			raise

		ids = [item['id'] for item in data] if not training else None
		classifiers = [item['classifier'] for item in data] if training else None
		text = [item['txt'] for item in data]

		return ids, classifiers, text

	def load_model(self):
		if self.vectorizer is None or self.classifier is None:
			if not os.path.exists(self.vectorizer_path) or not os.path.exists(self.classifier_path):
				raise FileNotFoundError("Model files not found. Please train the model first.")

			self.vectorizer = joblib.load(self.vectorizer_path)
			self.classifier = joblib.load(self.classifier_path)


	def train_model(self, training_file, alpha=0.5, do_stratify=False):
		_, classifiers, training_corpus = self.read_data_file(training_file)

		self.vectorizer = TfidfVectorizer(decode_error='ignore', lowercase=True, ngram_range=(1, 2))
		X = self.vectorizer.fit_transform(training_corpus)
		y = np.array(classifiers)
		stratify = y if do_stratify else None

		X_train, self.X_test, y_train, self.y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=stratify)

		self.classifier = RidgeClassifier(alpha=alpha)
		self.classifier.fit(X_train, y_train)

		if self.cache_dir:
			try:
				joblib.dump(self.vectorizer, self.vectorizer_path)
				joblib.dump(self.classifier, self.classifier_path)
			except Exception as e:
				raise OSError(f"Error saving training data {e}") from e

	def report(self, report_filename, limit=20):
		self.load_model()
		y_pred = self.classifier.predict(self.X_test)

		# open the file for writing
		with open(report_filename, 'w', encoding='utf-8') as f:
			y_pred = self.classifier.predict(self.X_test)
			# print the classification report to the file
			f.write(classification_report(self.y_test, y_pred))
			f.write("\n")

			coeff = self.classifier.coef_
			columns = self.vectorizer.get_feature_names_out()
			for i, class_label in enumerate(self.classifier.classes_):
				f.write(f"Top {limit} positive features for class {class_label}:\n")
				top_indices = np.argsort(coeff[i])[-limit:]
				top_features = [(columns[idx], coeff[i][idx]) for idx in top_indices]
				# sort top_features by value
				top_features.sort(key=lambda x: x[1], reverse=True)
				for feature, value in top_features:
					f.write(f"{feature}: {value}\n")
				f.write("\n")

	def predict(self, predict_file, output_file, line_length=100):
		self.load_model()

		ids, _, text = self.read_data_file(predict_file, training=False)

		# cleaned_txt = [self.preprocess_text(doc) for doc in text]
		X = self.vectorizer.transform(text)
		y_pred = self.classifier.predict(X)

		results = [{"id": id, "classifier": pred, "txt": txt[:line_length]} for id, pred, txt in zip (ids, y_pred, text)]

		try:
			with open(output_file, 'w', encoding='utf-8', errors='ignore') as f:
				json.dump(results, f, indent=4)
		except Exception as e:
			logging.error("Error writing to file %s: %s", output_file, e)
			raise

def args_handler():
	prog = __file__
	parser = argparse.ArgumentParser(
		prog=prog,
		formatter_class=argparse.RawDescriptionHelpFormatter,
		epilog=textwrap.dedent(f'''\
			{prog} -t training_file -p predict_file
			'''))

	parser.add_argument("-o", "--output_file", help="file to store results")
	parser.add_argument("-p", "--predict_file", help="data to classify")
	parser.add_argument("-t", "--training_file", help="data to train model")

	return parser.parse_args()

if __name__ == '__main__':
	args = args_handler()
	predictor = MyRidgePredictor()
	predictor.train_model(args.training_file)
	predictor.predict(args.predict_file, args.output_file)
