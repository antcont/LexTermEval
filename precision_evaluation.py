'''
TSV file for evaluation of LexTermEval precision on 100 random sentences
input is the TSV report file from LexTermEval.py
'''

import pandas as pd

path = r"path\to\LexTermEval.py\tsv\report\file"
out = r"path\to\output\tsv\file"



with open(path, "r", encoding="utf-8") as f:
    file = f.read().splitlines()

line_dict = {}

#  blacklist to keep the most frequently evaluated terms to appear in the file. Keep if interested in qualitative
#  observations, remove if you are to evaluate precision.
blacklist = ["zuständig", "zuständigen", "zuständige", "artikel", "artikels", "artikeln", "art .", "absatz", "abs .",
             "gesetze", "gesetzes", "personal", "gesetz", "bestimmung", "bestimmungen", "land", "landes", "unterlagen",
             "dekret", "dekrets", "anlagen", "absätze", "anhang", "beitrags", "betrag", "betrags", "beträge", "buchstabe",
             "buchstaben", "zuständig", "zuständige",
             "anlage", "beitrag", "beiträge", "leistung", "leistungen", "durchführungsverordnungen", "durchführungsverordung"]

for line in file:
    a, b, c, d, e, f, g, h, i, j, k, l, m, n, o, p, q = line.split("\t")
    sent_id = b
    termDe = l
    line_dict[line] = b

evaluation_list = []

count = 0
for row, sentID in line_dict.items():
    a, b, c, d, e, f, g, h, i, j, k, l, m, n, o, p, q = row.split("\t")
    if l.lower() in blacklist:
        print("found blacklist")
        print(l)
        continue   # avoiding blacklisted terms
    if row not in evaluation_list:
        evaluation_list.append(row)
        for _row, _sentID in line_dict.items():
            if _sentID == sentID:
                if _row not in evaluation_list:
                    if l.lower() in blacklist:
                        print("found blacklist")
                        print(l)
                        continue
                    else:
                        evaluation_list.append(_row)
        count += 1
        if count > 100:
            break

print(len(evaluation_list))

with open(out, "w", encoding="utf-8") as o:
    o.write("\n".join(evaluation_list))
