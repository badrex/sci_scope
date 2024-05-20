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

# Hugging Face imports
from datasets import load_dataset

# parse command line arguments 
model_id = sys.argv[1]
output_file = sys.argv[2]


# load a Hugging Face dataset
rsc_dataset = load_dataset("badrabdullah/royal_society_corpus_metadata")
print(f"Num of documents: {len(rsc_dataset['train'])}")


documents: List[str] = rsc_dataset['train']['text']

article_identifiers: List[str] = rsc_dataset['train']['id']


# This will trigger the model download and initialization
#model_id = 'BAAI/bge-small-en-v1.5'
embedding_model = TextEmbedding(model_id)
print(f"The model {model_id} is ready to use.")

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