# basic imports 
import sys
from collections import defaultdict, Counter
import numpy as np
import glob
import json
from tqdm import tqdm
import pickle

# import embedding framework FastEmbed
from fastembed import TextEmbedding
from typing import List, Dict


# parse command line arguments 
model_id = sys.argv[1]
output_file = sys.argv[2]
add_topics = sys.argv[3]

# read JSON files from disk
json_files: List = [
    json_file_id.split('/')[-1][:-5]
    for json_file_id in glob.glob('../data/json_files/*.json')
]

# get a dict where each entry is a JSON file
doc2json: Dict[str, dict] = {}

for doc in tqdm(json_files):
    # open the file in read mode
    file_path = "../data/json_files/" + doc + ".json"
    with open(file_path, "r", encoding='utf-8',) as file:
        # load the JSON data
        doc2json[doc] = json.load(file)


print(f"Num of JSON objects: {len(doc2json)}")



documents: List[str] = [
    doc2json[doc]['tldr'] for doc in doc2json
]


article_identifiers: List[str] = [
    doc2json[doc]['article_id'] for doc in doc2json
]

topics_sentences: List[str] = [
    'This article discusses the following topics: ' +
    ', '.join(doc2json[doc]['topics'][:-1]) + 
    ', and ' + doc2json[doc]['topics'][-1] + '.'
    for doc in doc2json
]

documents_plus_topics: List[str] = [
    ' '.join((doc, topics)) for doc, topics in zip(documents, topics_sentences)
]

print(documents_plus_topics[-1])

# This will trigger the model download and initialization
#model_id = 'BAAI/bge-small-en-v1.5'
embedding_model = TextEmbedding(model_id)
print(f"The model {model_id} is ready to use.")

# reminder this is a generator
if add_topics == 'with_topics':
    embeddings_generator = embedding_model.embed(documents_plus_topics)

elif add_topics == 'only_topics':
    embeddings_generator = embedding_model.embed(topics_sentences)  

else:
    embeddings_generator = embedding_model.embed(documents)  

embeddings: List[str] = [] 

for emb in tqdm(embeddings_generator, total=len(documents)):
    embeddings.append(emb)


# turn embedding array into a dict to preserve article IDs
doc2embedding: Dict[str, np.array] = {
    doc: emb for doc, emb in zip(article_identifiers, embeddings)
}

# save dict into disc as a pickle object
# output_file = doc2embedding.pkl'
with open(f'../data/{output_file}', 'wb') as f:
    pickle.dump(doc2embedding, f)