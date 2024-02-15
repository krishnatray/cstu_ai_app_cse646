"""
building_kb.py

# pip install openai
# pip3 install pinecone-client
# pip install PyPDF2
# pip install python-dotenv

"""


from openai import OpenAI
import dotenv
from PyPDF2 import PdfReader
import re
import os
import json
#import pinecone
from time import sleep
from pinecone import Pinecone, ServerlessSpec


from dotenv import load_dotenv
load_dotenv()
pinecone_api_key = os.getenv("PINECONE_API_KEY")
OpenAI.api_key = os.getenv("OPENAI_API_KEY")
#embed_model = "text-embedding-ada-002"
index_name = 'myindex'

pc = Pinecone( api_key=pinecone_api_key)

client = OpenAI()

# initialize connection to pinecone (get API key at app.pinecone.io)
# pinecone.init(
#     api_key=pinecone_api_key,
#     environment="asia-southeast1-gcp-free" # The environment value could be found at Pinecone website, once created
# )

# if 'myindex' not in pc.list_indexes().names():
#     pc.create_index(
#         name='my_index',
#         dimension=1536,
#         metric='euclidean',
#         spec=ServerlessSpec(
#             cloud='aws',
#             region='asia-southeast1-gcp-free'
#         )
#     )

index = pc.Index(index_name)

def get_embedding(text, model="text-embedding-3-small"):
   text = text.replace("\n", " ")
   return client.embeddings.create(input = [text], model=model).data[0].embedding


def mls_upsert(cstu_file, index_name, name_space, cstu_id, chunk_size, stride):
   # create a reader object
    print("Knowledge base file name:", cstu_file)
    reader = PdfReader(cstu_file)
    page_len = len(reader.pages)
    print("length of the knowledge base file:", page_len)
    doc = ""
    for i in range(page_len):
        doc += reader.pages[i].extract_text()
        print("page completed:", i)
    doc = doc.splitlines()
    print("The total lines: ", len(doc))

    #Connect to Pinecone index
    index = pc.Index(index_name)
    count = 0
    for i in range(0, len(doc), chunk_size):#The loop iterates over the document in steps of chunk_size
        #find begining and end of the chunk
        i_begin = max(0, i-stride)
        i_end = min(len(doc), i_begin+chunk_size)
        doc_chunk = doc[i_begin:i_end]
        print("-------------------------------------------------------------")
        print("The ", i//chunk_size + 1, " doc chunk text:", doc_chunk)
        texts = ""
        for x in doc_chunk:
            texts += x
        print("Texts:", texts)

        #Create embeddings of the chunk texts
        try:
            #res = openai.Embedding.create(input=texts, engine=embed_model)
            res = get_embedding(texts)
        except:
            done = False
            while not done:
                sleep(1)
                try:
                    # res = openai.Embedding.create(input=texts, engine=embed_model)
                    res = get_embedding(texts)
                    done = True
                except:
                    pass
        # import pdb; pdb.set_trace()
        print("Embeds length:", len(res))

        # Meta data preparation
        metadata = {
            "cstu_id": cstu_id + '_' + str(count),
            "text": texts
        }
        count += 1
        print("Upserted vector count is: ", count)
        print("==========================================================")

        #upsert to pinecone and corresponding namespace
        index.upsert(vectors=[(metadata["cstu_id"], res, metadata)], namespace=name_space)

mls_upsert(r"cstugpt_kb.pdf", "myindex", "cstu","cstu-kb", 8, 1)
# mls_upsert(r"cstugpt_qa.pdf", "cstugpt-kb", "cstu","cstu-qa", 3, 1)

index.describe_index_stats()