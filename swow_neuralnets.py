# -*- coding: utf-8 -*-
"""Swow_neuralnets.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1CM0Ow-_94iobbbJmQPPjgT1lRA9rQGjm

### Imports & data wrangling
"""

import nltk
# nltk.download("wordnet")
# nltk.download("stopwords")
# nltk.download("punkt")

import pandas as pd
import numpy as np
from collections import Counter
import math
import sklearn as sk
import matplotlib.pyplot as plt
# import tensorflow as tf
from nltk.corpus import wordnet as wn
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from sklearn.model_selection import train_test_split
stop = stopwords.words("english")
from tqdm import tqdm
tqdm.pandas()

# Reading in the data file, from Small World of Words
sw_df = pd.read_csv("https://github.com/ellissc/foundations_202/blob/main/data/SWOW-EN.R100.csv.zip?raw=true", compression='zip')

# General data cleaning (setting type, lowercasing those data)
sw_df = sw_df.astype({"cue":str, "R1":str,"R2":str,"R3":str})
for col in ["cue","R1","R2","R3"]:
  sw_df[col] = sw_df[col].str.lower()

# Removing the built-in index column
sw_df = sw_df.drop(columns = "Unnamed: 0")

#Adding column with just the year
sw_df["year_created"] = pd.DatetimeIndex(sw_df["created_at"]).year

#Creating a column with the participant age relative to a common point
common_point = 2018
sw_df["relative_age"] = (common_point - sw_df["year_created"]) + sw_df["age"]

# Change relative age to decade
def decade_bin(age):
  return math.floor(age/10)*10

sw_df['relative_age'] = sw_df['relative_age'].apply(decade_bin)

sw_df = sw_df[["relative_age", "cue","R1","R2","R3"]]
sw_df.head()

# First, remove stop words from the cues
# sw_df["cue"] = sw_df["cue"].apply(lambda x: ' '.join([word for word in x.split() if word not in (stop)]))

#Check for leftover multi-word entries
cue_no_space = np.invert(sw_df.cue.str.contains(" "))

#Remove leftover multi-word entries
sw_df = sw_df[cue_no_space]

# Note: removing stopwords this way had some unintended effects, going to just select for cues/rows without a space.

# Add column with number of valid responses, normalized
sw_df["valid_responses"] = (sw_df[["R1", "R2","R3"]] != "nan").sum(axis = 1)/3
sw_df

# calculate frequency of each response
responses = sw_df[["R1","R2","R3"]].values.ravel()
counts = Counter(responses)
total = sum(counts.values())
frequencies = {k: v/total for k, v in counts.items()}

for col in ['R1','R2','R3']:
  new_col = col+'_freq'
  sw_df[new_col] = sw_df[col].map(frequencies)

sw_df

# Add columns, wordnet wu-palmer similarity for each word -- 1 as most similar
def wup_sim(cue, response):
  # print(cue)
  # print(len(wn.synsets(cue)))

  if len(wn.synsets(cue)) != 0: #check if cue synset exists
    cue_syn = wn.synsets(cue)[0]

    if " " not in response: #single word responses
      if len(wn.synsets(response)) != 0 and response != "nan":
        response_syn = wn.synsets(response)[0]
        max_sim = cue_syn.wup_similarity(response_syn)
      else:
        max_sim = 0

    elif ' ' in response: #multi word responses
      max_sim = 0
      tokens = word_tokenize(response)
      filtered_tokens = [word for word in tokens if not word in stop] #removing stop words here
      # print(filtered_tokens)

      for subword in filtered_tokens: #cycle through subwords
        if len(wn.synsets(subword)) != 0 and response != 'nan': #check if subword synset exists
          response_syn = wn.synsets(subword)[0]
          # print(response_syn, cue_syn)
          sim = cue_syn.wup_similarity(response_syn)

          if sim == None: #Handle weird cases where they aren't related
            sim = 0

          if sim >= max_sim:
            max_sim = sim

  else:
    max_sim = 0

  return max_sim

sw_df['R1_dist'] = sw_df.progress_apply(lambda x: wup_sim(x["cue"], x['R1']), axis = 1)
#https://stackoverflow.com/questions/19914937/applying-function-with-multiple-arguments-to-create-a-new-pandas-column

# Ideally, it would be better to use word embeddings like counter-fitted paragrams or histwords (then create a similarity per decade, etc) to do these word sim evals, but that's outside the scope of this version

sw_df['R2_dist'] = sw_df.progress_apply(lambda x: wup_sim(x["cue"], x['R2']), axis = 1)

sw_df['R3_dist'] = sw_df.progress_apply(lambda x: wup_sim(x["cue"], x['R3']), axis = 1)

sw_df.to_csv('swow_data_nn_mods.csv')

# Subsetting the data
inputs = sw_df[['valid_responses', 'R1_freq', 'R2_freq', 'R3_freq', 'R1_dist','R2_dist','R3_dist']]
targets = sw_df['relative_age']

"""## Model

Features: cue, responses 1-3 (all indexes)

Hope to identify age. 
"""

# #Split into training and test sets
# (train_inputs, test_inputs, train_targets, test_targets) = train_test_split(inputs.to_numpy(), targets.to_numpy(), test_size=0.33)

# #Checking the shape
# train_inputs.shape

# train_targets.shape

# model = tf.keras.Sequential([
#                              tf.keras.layers.InputLayer(input_shape = 7),
#                              tf.keras.layers.Dense(128, activation = "relu"),
#                              tf.keras.layers.Dense(1)
# ])

# model.summary()

# model.compile(optimizer = 'adam',
#               loss = tf.keras.losses.BinaryCrossentropy(),
#               metrics = ['accuracy'])

# model.fit(train_inputs, train_targets, epochs = 10, verbose = 1)

# """Eval on test set"""

# test_loss, test_acc = model.evaluate(test_inputs, test_targets, verbose = 2)

# """Simple predictions"""

# predictions = model.predict(test_inputs)

# test_inputs[14] #test input set

# test_targets[14] #Correct label

# predictions[14] #NN's prediction