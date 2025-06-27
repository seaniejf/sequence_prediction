#!/usr/bin/env python3

import sys
import json
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS as sklearn_stopwords

# Sample text documents
with open(sys.argv[1], 'r', encoding='utf-8') as f:
	txtdata = json.load(f)

documents = [item['txt'] for item in txtdata]
print (f"Documents: {len(documents)}")

# documents = [
#    "Machine learning is fascinating.",
#    "Deep learning is a subset of machine learning.",
#    "Clustering is an unsupervised learning technique.",
#    "I love programming in Python.",
#    "Python is great for data science and machine learning."
#]

# Step 1: Convert text to TF-IDF features
#vectorizer = TfidfVectorizer(stop_words='english')
my_stop_words = list(sklearn_stopwords)
vectorizer = TfidfVectorizer(decode_error='ignore', lowercase=True, stop_words=my_stop_words, ngram_range=(1,4))
X = vectorizer.fit_transform(documents)

# Step 2: Apply K-Means clustering
kmeans = KMeans(n_clusters=10, random_state=42)
kmeans.fit(X)

# Step 3: Map cluster centers to feature names
feature_names = vectorizer.get_feature_names_out()
n_top_features = 10  # Number of top features to consider
used_names = set()  # To track used cluster names
cluster_names = []  # To store unique cluster names

for cluster_idx, cluster_center in enumerate(kmeans.cluster_centers_):
    # Get indices of top features for this cluster
    top_features_idx = cluster_center.argsort()[-n_top_features:][::-1]
    top_features = [feature_names[i] for i in top_features_idx]

    # Generate a unique cluster name
    for num_features in range(2, len(top_features) + 1):
        proposed_name = "_".join(top_features[:num_features])
        if proposed_name not in used_names:
            used_names.add(proposed_name)
            cluster_names.append(proposed_name)
            break

# Step 4: Print the cluster names
for cluster_idx, cluster_name in enumerate(cluster_names):
    print(f"Cluster {cluster_idx}: {cluster_name}")

# Step 3: Get cluster assignments
document_clusters = kmeans.labels_

# Step 4: List documents with their cluster
for doc_idx, cluster in enumerate(document_clusters):
    print(f"Document {doc_idx} (Cluster {cluster}): {documents[doc_idx][:100]}...")
