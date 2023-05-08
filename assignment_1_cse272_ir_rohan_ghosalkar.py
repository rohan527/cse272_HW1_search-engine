# -*- coding: utf-8 -*-
"""Assignment 1_CSE272_IR_Rohan Ghosalkar.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1Pm4-3OkVzhEN3QxHUau3YDXdxj_6BW7j

### HW 1: Search Engine
"""

#I used the input files that I uploaded to my drive.
#If you are using the colab notebook, please make sure to change the location of the files.
from google.colab import drive
drive.mount('/content/drive')

#We import all the necessary libraries 
import re
import math
import csv
import numpy as np
import pandas as pd
import nltk
from nltk.corpus import stopwords
nltk.download("stopwords")

#We will also need to install Whoosh (similar to Lucene, but in Python instead of Java)
!pip install whoosh

#Import all the necessary modules from the Whoosh library
from whoosh.index import create_in
import whoosh.index as index
from whoosh.fields import *
from whoosh.qparser import QueryParser
from whoosh.filedb.filestore import FileStorage
from whoosh.filedb.filestore import RamStorage
from whoosh.analysis import StemmingAnalyzer
from whoosh.writing import AsyncWriter
from whoosh.qparser import MultifieldParser
from whoosh import qparser
import whoosh.scoring as scoring

"""Data Parsing

In summary, this function reads a file containing a collection of documents in a specific format and yields each document one at a time as a dictionary with keys representing different fields (e.g., title, abstract, author) and values representing the content of those fields for the current document.
"""

#This function parses the input data that and returns it in the form of a dictionary
def read_documents():
    curr_doc = None
    curr_col = None
    # Open the file for reading
    with open('/content/drive/MyDrive/23 - Spring Quarter/CSE 272 - IR/HW 1/ohsumed.88-91', 'r+') as lines:
        # Loop through each line in the file
        for line in lines:
            # Remove the newline character at the end of the line
            line = line[:-1]
            # Check if the line indicates the start of a new document
            if line.startswith(".I"):
                if curr_doc is not None:
                    # Return the current curr_doc dictionary and start for the new document
                    yield curr_doc
                curr_doc = dict()
            # We check for the UID
            elif line.startswith('.U'):
                curr_col = "docid"
            # We check for the source
            elif line.startswith('.S'):
                curr_col = "source"
            # We check for the mesh terms
            elif line.startswith('.M'):
                curr_col = "mesh_terms"
            # We check for the title
            elif line.startswith('.T'):
                curr_col = "title"
            # We check for publication
            elif line.startswith('.P'):
                curr_col = "publication"
            # We check for abstract
            elif line.startswith('.W'):
                curr_col = "abstract"
            # We check for author
            elif line.startswith('.A'):
                curr_col = "author"
            else:
                curr_doc[curr_col] = line
    # Yield the final document
    yield curr_doc
    return

"""Query Parsing

In summary, this code reads a file containing a set of queries in a specific format and parses each query, creating a dictionary object for each one. Each dictionary object contains the query number, query title, and query description. These dictionaries are then stored in a list of queries for later use.
"""

queries = list()
# Open the file containing the queries for reading
with open("/content/drive/MyDrive/23 - Spring Quarter/CSE 272 - IR/HW 1/query.ohsu.1-63", "r+") as lines:
    current_query = None
    # Loop through each line in the file
    for line in lines:
        # Remove the newline character at the end of the line
        line = line[:-1]
        # Check if the line indicates the start of a new query
        if '<top>' in line:
            current_query = dict()
        # Check if the line indicates the end of a query
        elif '</top>' in line:
            # Add the completed query to the list of queries and start a new query
            queries.append(current_query)
            current_query = dict()
        # Check if the line contains the query number
        elif '<num>' in line:
            current_query["num"] = line.split(':')[1].strip()
        # Check if the line contains the query title
        elif '<title>' in line:
            current_query["title"] = line.split('>')[1].strip()
        # Check if the line contains the query description
        elif (not '<desc>' in line and len(line) > 2):
            current_query["description"] = line

"""Indexing

This function creates an index using the Whoosh library. It defines a schema with several fields (title, abstract, mesh_terms, publication, author, docid), each with specific properties such as the type of indexing or whether they are stored in the index.

The function then creates an index using the schema, and initializes an AsyncWriter object to add documents to the index. It loops through all the documents in the ohsumed.88-91 file, reading them using the read_documents() function, and adds them to the index using the AsyncWriter.

Each document is added to the index with only the filtered_fields specified in the schema using add_document() function. The writer is then committed after every 50000th document is added to the index.

Finally, the storage is closed and the function returns the created index.
"""

def create_index():
    # Define the fields to be indexed and stored
    filtered_fields = ["title", "abstract", "mesh_terms", "publication", "author", "docid"]
    schema = Schema(title=TEXT(stored=False, phrase=False), 
    abstract=TEXT(stored=False, phrase=True, analyzer=StemmingAnalyzer(stoplist=stopwords.words('english'))), mesh_terms=KEYWORD(stored=False), 
    publication = KEYWORD(stored=False), 
    author = KEYWORD(stored=False), 
    docid = ID(stored=True))

    # Create the index storage
    storage = FileStorage("indexed").create()

    # Create the index
    ix = storage.create_index(schema)
    
    # Create an async writer to add documents to the index
    writer = AsyncWriter(ix, delay=0.2, writerargs={'limitmb':1024, 'procs':8, 'segment':True})

    # Iterate over the documents and add them to the index
    for i, d in enumerate(read_documents()):
        writer.add_document(**{k:v for k,v in d.items() if k in filtered_fields})

    # Commit the changes to the index and close the storage
    writer.commit()
    storage.close()
    print(("Indexing done"))

    # Return the index
    return ix

"""Boolean Algorithm

Boolean search or inverted index search helps us identify the document's relevancy. After we have indexed all of our documents, we do an inverted index search based on either AND/OR/NOT. The output is a match based on the search terms and how much of a match it is with the corpus or input set. 
"""

def boolean(index_dir, queries, outputfile='boolean.txt', run='boolean'):
    # Open the index directory
    ix = index.open_dir(index_dir)

    # Create a query parser for multiple fields with OrGroup
    qp = MultifieldParser(["abstract","title"], schema=ix.schema, group=qparser.OrGroup)

    # Print the index
    print(ix)

    with ix.searcher() as s:

        with open(outputfile,'w+') as output:

            for i, q in enumerate(queries):

                # Parse the query using the query parser
                query = qp.parse(q['description'])

                # Search the index with the parsed query and retrieve top 50 results
                results = s.search(query, limit=50)

                # Iterate over each result
                for rank, result in enumerate(results):

                    # Write the result to the output file in the required format
                    output.write('{0} Q0 {1} {2} {3} {4}\n'.format(q["num"], result['docid'], result.rank, result.score, run))

"""Term Frequency (tf) Algorithm

Term frequency (TF) search is a technique used by search engines to rank search results based on the frequency of the search terms in each document. The idea behind TF search is that documents containing a higher frequency of search terms will likely be more relevant to the user's query.
"""

def tf(index_dir, queries, outputfile='tf.txt', run='tf'):
    # Open the index directory
    ix = index.open_dir(index_dir)

    # Create a query parser for multiple fields with OrGroup
    qp = MultifieldParser(["abstract","title"], schema=ix.schema, group=qparser.OrGroup)

    with ix.searcher() as s:

        with open(outputfile,'w+') as output:
          
            for i, q in enumerate(queries):

                # Parse the query using the query parser
                query = qp.parse(q['description'])

                # Search the index with the parsed query and retrieve top 50 results
                results = s.search(query, limit=50)

                # Iterate over each result
                for rank, result in enumerate(results):

                    scores = np.log(1 + result.score) 

                    # Write the result to the output file in the required format
                    output.write('{0} Q0 {1} {2} {3} {4}\n'.format(q["num"], result['docid'], result.rank, scores, run))

"""Term Frequency - Inverse Document Frequency (td-idf) Algorithm

Term frequency-inverse document frequency (TF-IDF) search is a technique used by search engines to rank search results based on the relevance of the search terms to the documents in a collection. TF-IDF search considers the frequency of the search terms in each document and the rarity of the search terms across the entire collection.
"""

def tf_idf(index_dir, queries, outputfile='evaluation.txt', run='tf_idf'):
    # Open the index directory
    ix = index.open_dir(index_dir)

    # Create a query parser for multiple fields with OrGroup
    qp = MultifieldParser(["abstract","title"], schema=ix.schema, group=qparser.OrGroup)
    print(ix)


    with ix.searcher(weighting=scoring.TF_IDF()) as s:

        with open(outputfile,'w+') as output:

            for i, q in enumerate(queries):

                # Parse the query using the query parser
                query = qp.parse(q['description'])

                # Search the index with the parsed query and retrieve top 50 results
                results = s.search(query, limit=50)

                # Iterate over each result
                for rank, result in enumerate(results):

                    # Write the result to the output file in the required format
                    output.write('{0} Q0 {1} {2} {3} {4}\n'.format(q["num"], result['docid'], result.rank, result.score, run))

"""Custom Algorithm

The score is defined as the sum of the product of the weight and the number of occurrences of each query term in the title and abstract fields, plus a constant factor. Weights are assigned based on the field: 5 for the title field, 2 for the abstract field. If a query term occurs in both fields of a document, the maximum weight is used.

In the  code, we define a custom scoring function custom_score_fn that calculates the score for each document based on the number of occurrences of each query term in the title and abstract fields. We assign weights based on the field and add a constant factor to the final score. We then use this function in the with ix.searcher(weighting=custom_score_fn) as s: line to apply it during search.
"""

def custom_score_fn(searcher, fieldname, text, matcher):
    score = 0
    if fieldname == 'title':
        weight = 5
    elif fieldname == 'abstract':
        weight = 2
    else:
        weight = 1
        
    for t in text:
        df = searcher.doc_frequency(fieldname, t)
        tf = matcher.value_as("frequency")
        if df > 0:
            score += weight * tf * (1 + math.log(searcher.doc_count() / df))
    score += 0.5  # constant factor
    return score


def custom(index_dir, queries, outputfile='custom.txt', run='custom'):
    ix = index.open_dir(index_dir)
    qp = MultifieldParser(["abstract","title"], schema=ix.schema, group=qparser.OrGroup)
    with ix.searcher(weighting=custom_score_fn) as s:
        with open(outputfile,'w+') as output:
            for i, q in enumerate(queries):
                query = qp.parse(q['description'])
                results = s.search(query, limit=50)
                for rank, result in enumerate(results):
                    output.write('{0} Q0 {1} {2} {3} {4}\n'.format(q["num"], result['docid'], result.rank, result.score, run))

"""Creating log files


Here we try to create the log files with the top 50 documents that are retrived from the search algorithms along with the score for each of the documents. 


(You can uncomment the create_index() if you want to do the indexing again or else you can also simply add the folder "indexed" with the python file and run the code)
"""

#create_index()

if __name__ == '__main__':
  tf_idf("indexed", queries, outputfile="tf_idf.txt", run='TF_idf')
  boolean("indexed", queries, outputfile="boolean.txt", run='boolean')
  tf("indexed", queries, outputfile="tf.txt", run='TF')
  custom("indexed", queries, outputfile="custom.txt", run='custom')