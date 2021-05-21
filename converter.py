'''
converting from 1:1 term list to m:n list, by grouping the id
then go back to LexTerm
as {id:((italian terms), (german terms))}
'''

import pandas as pd
import numpy as np

terms = r"C:\Users\anton\Documents\Documenti importanti\SSLMIT FORLI M.A. SPECIALIZED TRANSLATION 2019-2021\tesi\Evaluation (Automatic + Manual)\anteprima_termini_Bluterm_parziale.xls"

#  importing xlsx as Pandas dataframe
df_terms = pd.read_excel(terms, header=0)
print(df_terms)

#  trying to merge rows by ID
# https://stackoverflow.com/questions/41949507/how-to-merge-rows-with-strings-based-on-column-value-int-in-pandas-dataframe

#  building an empty dataframe with only IDs

conceptIds = set()
for index, row in df_terms.iterrows():
    conceptIds.add(row["id"])
len_concepts = len(conceptIds)

#  creating skeleton of dataframe
df = pd.DataFrame(index=conceptIds)
#df['id'] = list(conceptIds)
df['it'] = np.empty((len(df), 0)).tolist()
df['de'] = np.empty((len(df), 0)).tolist()
print(df)

#  populate the Dataframe by adding terms
for index, row in df_terms.iterrows():
    itTerm = row["it"]
    deTerm = row["de"]
    ID = row["id"]
    df.loc[ID, "it"] = df.loc[ID, "it"].apply(lambda x: x.append(itTerm))
    print("works")

print(df)






'''for i in range(len_concepts):




for index, row in df_terms.iterrows():
    id = row["id"]
    itTerm = row["it"]
    deTerm = row["de"]
    if id not in new_dict.keys():
        # create skeleton of the row with the first structures
        new_dict[id] = (set(it), set(de))
    else:  # if id already in new_dict
        # append terms to existing row'''



