import torch
import transformers
from transformers.pipelines.pt_utils import KeyDataset
from tqdm import tqdm
import json
import datasets
import pickle

from llm_prompts import SYSTEM_PROMPT


# load RSC dataset from Huggingface
dataset = datasets.load_dataset("badrabdullah/royal_society_corpus_metadata")

ds_num_rows = dataset['train'].num_rows

print(f"Number of rows in the dataset: {ds_num_rows}")

doc2snippet = {}

for i in tqdm(range(ds_num_rows)):

    row_id = dataset['train'][i]['id']
    title = dataset['train'][i]['title']
    jrnl = dataset['train'][i]['journal']
    year = dataset['train'][i]['year']
    author = dataset['train'][i]['author']
    text_snippet = ' '.join(dataset['train'][i]['text'].split()[:2000])

    str_output = f"Article ID: '{row_id}'\n"
    str_output += f"Title: '{title}'\n"
    str_output += f"Journal: '{jrnl}'\n"
    str_output += f"Year: '{year}'\n"
    str_output += f"Author: '{author}'\n"
    str_output += f"Text snippet: '{text_snippet}'\n"

    doc2snippet[row_id] = str_output

len(doc2snippet)

model_id = "NousResearch/Hermes-2-Pro-Llama-3-8B"


pipeline = transformers.pipeline(
    "text-generation",
    model=model_id,
    model_kwargs={"torch_dtype": torch.bfloat16},
    device_map="auto",
)
    
user_message = "Read this article and generate a valid YAML file as per your guidelines:"

def add_article_prompt_column(example):

    user_input = f"{user_message}: {doc2snippet[example['id']]}"

    messages = [
      {"role": "system", "content": SYSTEM_PROMPT},
      {"role": "user", "content": user_input},
    ]

    prompt = pipeline.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
    )

    return {
        "prompt": prompt
    }



dataset = dataset.map(add_article_prompt_column)


mark_str = '<|im_end|>\n<|im_start|>assistant\n'
mark_str_len = len(mark_str)

terminators = [
    pipeline.tokenizer.eos_token_id,
    pipeline.tokenizer.convert_tokens_to_ids("<|eot_id|>")
]

doc2yaml = {}

def run_LLM(decade):
    """
    Given a decade, run the LLM on each document,
    and return a dictionary articel_id --> LLM generated text
    """

    sample_dataset = dataset['train'].filter(lambda x: x['decade'] == decade)

    print(f"Num of articles in the {decade} decade: {len(sample_dataset)}")

    outputs = pipeline(KeyDataset(sample_dataset, "prompt"),
        max_new_tokens=512,
        eos_token_id=terminators,
        do_sample=False,
        #temperature=0.6,
        #top_p=0.9,
        #top_k=35
    )

    for i, out in enumerate(outputs):

        print('---')

        out_str = out[0]["generated_text"][out[0]["generated_text"].find(mark_str) + mark_str_len:]
        doc_id = sample_dataset[i]['id']
        doc_title = sample_dataset[i]['title']

        doc2yaml[doc_id] = out_str
        print(i, doc_id, doc_title)
        print(out_str)

        break

    # with open(f"/content/drive/MyDrive/LLM_output/doc2yaml_{decade}.pkl", 'wb') as f:
    #     pickle.dump(doc2yaml, f)


run_LLM(1660)