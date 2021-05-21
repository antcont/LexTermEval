"""

- creare esternamente un dataset con id_segmento, source-reference, source-reference_lemmatizzato


TODO:
- convertire lista 1:1 in lista 3:3 , sulla base dell'id... per poter poi ritestare questo
- modifica per adattare a lista m:n, poi prova quella cosa del "greedy" per le sovrapposizioni
- implementa compound splitter da usare se non ci sono match in frasi tedesche
  (https://github.com/mariondimarco/SimpleCompoundSplitting)



"""
import spacy
from spacy.matcher import PhraseMatcher




termList = r"C:\Users\anton\Documents\Documenti importanti\SSLMIT FORLI M.A. SPECIALIZED TRANSLATION 2019-2021\tesi\Evaluation (Automatic + Manual)\prove_terms_it-de.txt"
testSet = r"C:\Users\anton\Documents\Documenti importanti\SSLMIT FORLI M.A. SPECIALIZED TRANSLATION 2019-2021\tesi\Evaluation (Automatic + Manual)\testset+reference_2000_1.txt"

termList = r"C:\Users\anton\Documents\Documenti importanti\SSLMIT FORLI M.A. SPECIALIZED TRANSLATION 2019-2021\tesi\Evaluation (Automatic + Manual)\prove_terms_it-de_lemmatised_TreeTagger.txt"
testSet = r"C:\Users\anton\Documents\Documenti importanti\SSLMIT FORLI M.A. SPECIALIZED TRANSLATION 2019-2021\tesi\Evaluation (Automatic + Manual)\testset+reference_2000_1_lemmatised_TreeTagger.txt"


print("Loading data...")
with open(termList, "r", encoding="utf-8") as termlist:
    terms = termlist.read().splitlines()

with open(testSet, "r", encoding="utf-8") as testset:
    test = testset.read().splitlines()

it_de = []
for biterm in terms:
    it_de.append(biterm.split("\t"))        # creating list of tab-separated Italian-German terms

test_ = []
for test_ref in test:
    test_.append(tuple(test_ref.split("\t")))  # tab-separated source-reference test set


'''
# check simple string-in-string matches
counter = 0
for testline in test_:
    for biterm in it_de:
        if biterm[0] in testline[0]:
            if biterm[1] in testline[1]:
                counter += 1
                print(biterm, "\t", testline)
print(counter)
'''

#  adding an ID to each concept
id_terms = {}
for id_, biterm in enumerate(it_de):
    id_terms[id_] = biterm

#  loading Spacy models and instantiating the matchers
print("Loading SpaCy...\n")
nlp_de = spacy.load("de_core_news_lg")
nlp_it = spacy.load("it_core_news_lg")
matcher_it = PhraseMatcher(nlp_it.vocab, attr="LOWER")
matcher_de = PhraseMatcher(nlp_de.vocab, attr="LOWER")


# for when I'll have more variants for one ID
# it_terms_matcher = [nlp_it(text) for text in term_list]

print("Testing PhraseMatcher\n")

counter = 0
identified_terms = []

#  adding all Italian terms to matcher_it
for id, it_de in id_terms.items():
    pattern_it = nlp_it.make_doc(it_de[0])  # converting Str to Doc (needed by PhraseMatcher)
    matcher_it.add(str(id), [pattern_it])   # adding Italian terms to PhraseMatcher, with concept ID

for (it_sent, de_sent) in test_:
    print("Next sentence pair...")
    doc_it = nlp_it(it_sent, disable=['parser', 'ner'])         # TODO: also try make_doc here
    matches_it = matcher_it(doc_it)                             # matching terms in the source sentence
    #
    # TODO: implement filter_spans() to filter out overlapping matches and retaining only the longest matches
    # https://stackoverflow.com/questions/59105346/longest-match-only-with-spacy-phrasematcher
    # https://spacy.io/api/top-level#util.filter_spans
    # if this doesn't work, implement some function to do it; or consider using Matcher,
    # which has a greedy="LONGEST" attribute
    #
    for match_id, start, end in matches_it:                     # iterating over each single match on the sentence
        concept_id = nlp_it.vocab.strings[match_id]             # get the concept ID of the Italian matched term
        print(concept_id)
        matched_term_it = doc_it[start:end]                     # get the Italian matched term by slicing the doc
        print(matched_term_it)
        #  now checking if the correspondent German term is in the reference sentence
        get_terms = id_terms[int(concept_id)]   # getting the DE equivalents using the concept ID of the IT matched term
        pattern_de = nlp_de.make_doc(get_terms[1])              # converting DE term(s) from str to Doc
        matcher_de.add(str(concept_id), [pattern_de])           # adding DE term(s) to the DE matcher,
        doc_de = nlp_de(de_sent, disable=['parser', 'ner'])     # TODO: also try make_doc here, too
        matches_de = matcher_de(doc_de)                         # checking if DE term matches in DE sentence
        try:
            matcher_de.remove(concept_id)  # cleaning up matcher for next iterations
        except KeyError:
            pass
        if not matches_de:
            print("[NO MATCH] German equivalent absent in reference.")
            print(id_terms[int(concept_id)])
            print(it_sent, "\n", de_sent, "\n")
        for match_id, start, end in matches_de:             # iterating over each match in the DE sentence
            print("[MATCH] German equivalent found in reference.")
            concept_id = nlp_it.vocab.strings[match_id]     # getting the concept ID
            # ...
            # HARD-COPY ROW, DO STUFF, ANNOTATE, ETC ETC
            # ...
            matched_term_de = doc_de[start:end]             # get the matched term by slicing the doc
            #print(matched_term_de)
            #
            identified_terms.append([concept_id, id_terms[int(concept_id)]])
            print(concept_id, "\t", id_terms[int(concept_id)])
            print(it_sent, "\n", de_sent, "\n")
            counter += 1

            ''' except Exception as exc:
            print(exc.message)'''


print(identified_terms)
print(counter)










