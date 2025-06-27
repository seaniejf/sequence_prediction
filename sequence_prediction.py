from itertools import product
from string import ascii_uppercase
import re
from collections import defaultdict
from collections import Counter
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix, classification_report, roc_auc_score
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import hashlib

def remove_timestamps(lines):
    return [re.sub(r'^\[\s*\d+\.\d+\]\s*', '', line) for line in lines]

def encode_terms_with_map(s):
    remove_timestamps(s)

    gen = (''.join(p) for i in range(1, 10) for p in product(ascii_uppercase, repeat=i))
    seen = {}
    words = re.findall(r'\b\w+\b', s.lower())
    encoded = []
    for word in words:
        key = word.lower()
        if key not in seen:
            seen[key] = next(gen)
        encoded.append(seen[key])
    return encoded, words


def find_repeated_patterns(encoded_doc, doc_terms, pattern_length=3):
    seen = defaultdict(list)
    for i in range(len(encoded_doc) - pattern_length + 1):
        pattern = tuple(encoded_doc[i:i + pattern_length])
        seen[pattern].append(i)

    for pattern, indices in seen.items():
        if len(indices) > 1:
            print(f"\nPattern: {' '.join(pattern)}")
            for idx in indices:
                print(f"  At index {idx}: {' '.join(doc_terms[idx:idx + pattern_length])}")






def find_anomalies(encoded_doc):

    freq = Counter(encoded_doc)
    total_terms = len(encoded_doc)
    unique_terms = sum(1 for term in freq if freq[term] == 1)
    unique_percent = (unique_terms / total_terms) * 100 if total_terms > 0 else 0

    print(f"\nTotal terms: {total_terms}")
    print(f"Anomalies (Unique Terms): {unique_terms}")
    print(f"Percentage of anomalies: {unique_percent:.2f}%")

def predict_next(encoded_doc, window=3, steps=3):
    label_set = sorted(set(encoded_doc))
    label_to_int = {label: idx for idx, label in enumerate(label_set)}
    int_to_label = {idx: label for label, idx in label_to_int.items()}
    int_encoded = [label_to_int[label] for label in encoded_doc]

    X, y = [], []
    for i in range(len(int_encoded) - window):
        X.append(int_encoded[i:i + window])
        y.append(int_encoded[i + window])

    if not X:
        print("Not enough data for prediction.")
        return

    # Convert to smaller dtype and flatten X to avoid extra dimension
    X = np.array(X, dtype=np.int16)
    y = np.array(y, dtype=np.int16)
    if X.ndim == 3:
        X = X.reshape(X.shape[0], -1)

    clf = RandomForestClassifier(n_estimators=30, 
    max_depth=15)
    clf.fit(X, y)

    y_pred = clf.predict(X)
    print("\nAccuracy:", accuracy_score(y, y_pred))
    print("\nPrecision:", precision_score(y, y_pred, average='weighted'))
    print("\nRecall:", recall_score(y, y_pred, average='weighted'))
    print("\nF1score:", f1_score(y, y_pred, average='weighted'))

    current_seq = int_encoded[-window:]
    predicted_labels = []

    for _ in range(steps):
        # Ensure current_seq is 2D and correct dtype
        pred = clf.predict(np.array([current_seq], dtype=np.int16))[0]
        predicted_labels.append(pred)
        current_seq = current_seq[1:] + [pred]

    print(f"\nPrediction based on last {window} labels ({' '.join([int_to_label[i] for i in int_encoded[-window:]])}):")
    print(f"→ Predicted next {steps} labels: {' '.join([int_to_label[p] for p in predicted_labels])}")
    return [int_to_label[p] for p in predicted_labels]

# Example usage
#document = "The quick brown fox jumps over the lazy dog and the quick brown fox hurt himself as he jumps over the lazy dog too quick and the fox hurt himself"
#encoded_doc, doc_terms = encode_terms_with_map(document)
#print("Encoded Document:\n", ' '.join(encoded_doc))
#find_repeated_patterns(encoded_doc, doc_terms, pattern_length=3)
#predict_next(encoded_doc, window=3, steps=3)

#with open(r"C:\Users\seani\Downloads\lyrics1.txt", "r", encoding="utf-8") as file:
    #document2 = file.read()
#encoded_doc2, doc_terms2 = encode_terms_with_map(document2)
#print("Encoded Document:\n", ' '.join(encoded_doc2))
#find_repeated_patterns(encoded_doc2, doc_terms2, pattern_length=4)
#predict_next(encoded_doc2, window=3, steps=4)

#with open(r"C:\Users\seani\Downloads\lyrics2.txt", "r", encoding="utf-8") as file:
    #document3 = file.read()
#encoded_doc3, doc_terms3 = encode_terms_with_map(document3)
#print("Encoded Document:\n", ' '.join(encoded_doc3))
#find_repeated_patterns(encoded_doc3, doc_terms3, pattern_length=4)
#predict_next(encoded_doc3, window=3, steps=4)

# Read both files and merge into one big document for global encoding
file_paths = [
    r"C:\Users\seani\Downloads\logs\01\dmesg.log",
    r"C:\Users\seani\Downloads\logs\05\dmesg.log",
    r"C:\Users\seani\Downloads\logs\20\dmesg.log"
]
all_text = ""
doc_term_counts = []
for path in file_paths:
    with open(path, "r", encoding="utf-8") as file:
        text = file.read()
        all_text += text + "\n"
        _, terms = encode_terms_with_map(text)
        doc_term_counts.append(len(terms))

for i, path in enumerate(file_paths):
    print(f"Number of terms in {path}: {doc_term_counts[i]}")

encoded_doc, doc_terms = encode_terms_with_map(all_text)
find_anomalies(encoded_doc)
#find_repeated_patterns(encoded_doc, doc_terms, pattern_length=5)
predict_next(encoded_doc, window=5, steps=3)
