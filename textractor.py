#!/usr/bin/env python3
#
import os
import argparse
import textwrap
import json
import datetime
import hashlib
import logging
from venv import logger

import concurrent
import textract
import fitz
from pdfminer.high_level import extract_text
from ridge import MyRidgePredictor
from data_cleaner import DataCleaner

TOOL_NAME="textractor"
SUPPORTED_DOC_TYPES = ('.pdf', '.ps', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt', '.rtf', '.odt', '.ods', '.odp')

# training_file: file containing training_lib data in json format
MIN_TEXT_SIZE_BYTES=100

CACHE_DIR=os.path.join(os.path.expanduser('~'), '.cache', TOOL_NAME)

class Textractor:

	def __init__(self):
		self.cleaner = DataCleaner()

	def extract_text_from_pdf(self, pdf_path):
		try:
			text = extract_text(pdf_path)
			return text
		except Exception as e:
			logger.error("Error extracting text from pdf %s: %s", pdf_path, e)
			return ""

	def extract_text_from_non_pdf(self, file_path):
		try:
			text = textract.process(file_path).decode('utf-8')
			return text
		except Exception as e:
			logger.error("Error extracting text from non-pdf %s: %s", file_path, e)
			return ""

	def textraction(self, file_path):
		if file_path.lower().endswith('pdf'):
			text = self.extract_text_from_pdf(file_path)
		else:
			text = self.extract_text_from_non_pdf(file_path)

		return self.cleaner.clean_data(text)

	def calculate_md5(self, file_path):
		# Initialize the MD5 hasher
		hasher = hashlib.md5()

		# Open the file in binary mode and read in chunks
		with open(file_path, 'rb') as file:
			# Read the file in chunks to handle large files efficiently
			for chunk in iter(lambda: file.read(4096), b""):
				hasher.update(chunk)

		# Return the hex representation of the hash
		return hasher.hexdigest()

	def add_one_document(self, src_path, dst_dir, classifier):
		md5_hash = self.calculate_md5(src_path)
		out_file = os.path.join(dst_dir, f'{md5_hash}.json')

		if os.path.exists(out_file):
			logger.warning("File %s already exists, skipping.", out_file)
			return

		text = self.textraction(src_path)
		if MIN_TEXT_SIZE_BYTES > len(text):
			logger.warning("File %s < %d bytes, skipping.", src_path, MIN_TEXT_SIZE_BYTES)
		else:
			logger.info("Extracting %s to %s", src_path, out_file)
			self.write_json(out_file, {'src': src_path, 'dst': out_file, 'classifier': classifier,'txt': text})

	def extract_tree(self, root, dst_dir, classifier):
		with concurrent.futures.ThreadPoolExecutor() as executor:
			futures = []
			for froot, _, files in os.walk(root):
				for f in files:
					if not f.lower().endswith(SUPPORTED_DOC_TYPES):
						continue

					fpath = os.path.join(froot, f)
					if MIN_TEXT_SIZE_BYTES < os.path.getsize(fpath):
						futures.append(executor.submit(self.add_one_document, fpath, dst_dir, classifier))

			concurrent.futures.wait(futures)

			for future in concurrent.futures.as_completed(futures):
				try:
					future.result()
				except Exception as e:
					logger.error("Error processing file: %s", e)
					continue

	def build_cache_file(self, cache_dir, cache_name):
		cache_data = []
		for froot, _, files in os.walk(cache_dir):
			for fname in files:
				data_file = os.path.join(froot, fname)
				data = self.read_json(data_file)
				cache_data.append({'id': data['src'], 'classifier': data['classifier'], 'txt': data['txt']})

		cache_file = os.path.join(CACHE_DIR, cache_name)
		self.write_json(cache_file, cache_data)

	def read_json(self, src):
		with open(src, 'r', encoding='utf-8', errors='ignore') as f:
			return json.load(f)

	def write_json(self, dst, record):
			with open(dst,"w", encoding='utf-8') as f:
				json.dump(record, f, indent=4)

def build_training_data(training_src, cache_file):
	logger.info("Building training cache...")
	training_dst = os.path.join(CACHE_DIR, 'training')
	os.makedirs(training_dst, exist_ok=True)

	tractor = Textractor()
	directories = [d for d in os.listdir(training_src) if os.path.isdir(os.path.join(training_src, d))]
	for directory in directories:
		if directory.startswith("_"):
			continue
		cat_src = os.path.join(training_src, directory)
		cat_dst = os.path.join(training_dst, directory)
		os.makedirs(cat_dst, exist_ok=True)
		tractor.extract_tree(cat_src, cat_dst, directory)

	logger.info("Building training cache file...")
	tractor.build_cache_file(training_dst, cache_file)

def classify_docs(predict_src, cache_file):
	logger.info("Classifying documents...")
	predict_dst = os.path.join(CACHE_DIR, 'predict')
	os.makedirs(predict_dst, exist_ok=True)

	tractor = Textractor()

	if os.path.isdir(predict_src):
		tractor.extract_tree(predict_src, predict_dst, None)
	elif os.path.isfile(predict_src):
		tractor.add_one_document(predict_src, predict_dst, None)
	else:
		print("Unknown filesource type", predict_src)
		return

	logger.info("Building prediction cache file...")
	tractor.build_cache_file(predict_dst, cache_file)

def update_pdf_keywords(pdf_path, keywords):
	logger.warning("Updating %s with keywords: %s", pdf_path, keywords)
	return

	doc = fitz.open(pdf_path)
	doc.set_metadata({"keywords": keywords})  # Update Keywords
	doc.save(pdf_path, incremental=True)  # Save without overwriting other metadata


def update_all_pdfs_keywords(update_file):
	with open(update_file, 'r', encoding='utf-8', errors='ignore') as f:
		results = json.load(f)

	for result in results:
		pdf_path = result['id']
		keywords = result['classifier']
		update_pdf_keywords(pdf_path, keywords)

def args_handler():
	prog = os.path.basename(__file__)
	parser = argparse.ArgumentParser(
		prog=prog,
		formatter_class=argparse.RawDescriptionHelpFormatter,
		epilog=textwrap.dedent(f'''
			{__file__} -d /path/to/data.json -t /path/to/travel.xlsx
		'''))

	parser.add_argument("-c", "--classify", action="store", help="base dir for the search")
	parser.add_argument("-t", "--training_lib", action="store", help="original source docs")
	parser.add_argument("-u", "--update", action="store_true", help="turn on verbosity")
	parser.add_argument("-v", "--verbose", action="store_true", help="turn on verbosity")
	return parser.parse_args()

if __name__ == "__main__":
	start = datetime.datetime.now()
	file_prefix = start.strftime("%Y%m%d_%H%M%S")
	args = args_handler()

	# Configure logging for this script only
	logger = logging.getLogger(__name__)  # Create a logger specific to textractor.py
	logger.setLevel(logging.INFO)  # Set the log level for this logger
	handler = logging.StreamHandler()  # Log to the console
	formatter = logging.Formatter('%(threadName)s - %(asctime)s - %(levelname)s - %(message)s')
	handler.setFormatter(formatter)
	logger.addHandler(handler)
	logging.getLogger().setLevel(logging.WARNING)  # Set the root logger to WARNING

	predictor = MyRidgePredictor(cache_dir=CACHE_DIR)

	if args.training_lib:
		logger.info("Building training data...")
		training_cache_file = os.path.join(CACHE_DIR, 'training_cache.json')
		build_training_data(args.training_lib, training_cache_file)

		logger.info("Training model...")
		predictor.train_model(training_cache_file)

		report_file = f"{file_prefix}_report.log"
		predictor.report(report_file)

	if args.classify:
		logger.info("Classifying documents...")
		classify_cache_file = os.path.join(CACHE_DIR, 'predict_cache.json')
		classify_docs(args.classify, classify_cache_file)

		results_file = f"{file_prefix}_results.json"
		predictor.predict(classify_cache_file, results_file)

		if args.update:
			logger.info("Updating PDFs...")
			update_all_pdfs_keywords(results_file)

	logger.info("Elapsed time: %s", datetime.datetime.now() - start)
