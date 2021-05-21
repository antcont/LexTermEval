'''
converting from 1:1 term list to m:n list, by grouping the id
then go back to LexTerm
exported as:
id(TABSEPARATOR)italianTerm(PIPESEPARATOR)italianTerm(TABSEPARATOR)germanTerm...
'''

import pandas as pd
import numpy as np
from collections import defaultdict


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

conceptIds = list(conceptIds)

#  build skeleton
new_dict = {}
itTermsEmpty = []
deTermsEmpty = []
for concept in conceptIds:
    new_dict[concept] = [itTermsEmpty, deTermsEmpty]

#print(new_dict)

# tentativo ignorante: fare id:it e id:de separatamente (nello stesso ordine), poi mergiali
IT_dict = defaultdict(set)
DE_dict = defaultdict(set)
for index, row in df_terms.iterrows():
    ID = row["id"]
    itTerm = row["it"]
    deTerm = row["de"]
    IT_dict[ID].add(itTerm)
    DE_dict[ID].add(deTerm)

print(IT_dict)
print(DE_dict)


merged_dict = {}
for k, v in IT_dict.items():
    merged_dict[k] = (v, DE_dict[k])

print(merged_dict)

# now exporting
export_as_text = []
for id, (it, de) in merged_dict.items():
    it_terms = []
    de_terms = []
    for itterm in it:
        it_terms.append(itterm)
    for determ in de:
        de_terms.append(determ)
    export_as_text.append("%s\t%s\t%s" % (id, "|".join(it_terms), "|".join(de_terms)))

#print("\n".join(export_as_text))

with open(r"C:\Users\anton\Documents\Documenti importanti\SSLMIT FORLI M.A. SPECIALIZED TRANSLATION 2019-2021\tesi\Evaluation (Automatic + Manual)\merged_termlist_id_m-n.txt", "w", encoding="utf-8") as exp:
    exp.write("\n".join(export_as_text))









