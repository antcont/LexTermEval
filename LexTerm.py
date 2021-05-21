"""
TERMINI 1:1

- creare esternamente un dataset con id_segmento, source-reference, source-reference_lemmatizzato


TODO:
-



"""
import spacy
from spacy.matcher import PhraseMatcher
from spacy.util import filter_spans
from charsplit import Splitter
from collections import Counter

termList = r"C:\Users\anton\Documents\Documenti importanti\SSLMIT FORLI M.A. SPECIALIZED TRANSLATION 2019-2021\tesi\Evaluation (Automatic + Manual)\merged_termlist_id_m-n.txt"
#  termList is in the following format: id(TABSEPARATOR)italianTerm(PIPESEPARATOR)italianTerm(TABSEPARATOR)germanTerm...
testSet = r"C:\Users\anton\Documents\Documenti importanti\SSLMIT FORLI M.A. SPECIALIZED TRANSLATION 2019-2021\tesi\Evaluation (Automatic + Manual)\testset+reference_2000_1_lemmatised_TreeTagger.txt"


print("Loading data...")
with open(termList, "r", encoding="utf-8") as termlist:
    terms = termlist.read().splitlines()

with open(testSet, "r", encoding="utf-8") as testset:
    test = testset.read().splitlines()

it_de = []
for biterm in terms:
    it_de.append(tuple(biterm.split("\t")))        # creating list of tab-separated ID-ItTerms-DeTerms

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

'''#  adding an ID to each concept
id_terms = {}
for id_, biterm in enumerate(it_de):
    id_terms[id_] = biterm'''

#  converting termlist to a dictionary with key = concept_IDs and value a tuple of two lists with Italian terms and German terms each
#  {'6979': (['indennità di espropriazione', 'indennità di esproprio', 'indennizzo'], ['Enteignungsentschädigung', 'Entschädigung']), …}
id_terms = {}
for (id, termsIt, termsDe) in it_de:
    termsIt = [x for x in termsIt.split("|")]
    termsDe = [x for x in termsDe.split("|")]
    id_terms[id] = (termsIt, termsDe)
    print(id_terms)

#  loading Spacy models and instantiating the PhraseMatchers for each language
print("Loading SpaCy...\n")
nlp_de = spacy.load("de_core_news_lg")
nlp_it = spacy.load("it_core_news_lg")
matcher_it = PhraseMatcher(nlp_it.vocab, attr="LOWER")
matcher_de = PhraseMatcher(nlp_de.vocab, attr="LOWER")

print("Testing PhraseMatcher\n")

counter = 0                 # total matched terms
identified_terms = []
matched_after_split = []    # for testing purposes: see which additional matches have been found after compound-split

#  adding all Italian terms to matcher_it
for id, (it, de) in id_terms.items():
    pattern_it = [nlp_it.make_doc(term) for term in it]  # converting Str to Doc (needed by PhraseMatcher)
    matcher_it.add(str(id), pattern_it)   # adding Italian terms to PhraseMatcher, with concept ID


for (it_sent, de_sent) in test_:            # iterating over pairs of sourceIT-referenceDE in the test set
    print("Next sentence pair...")
    doc_it = nlp_it(it_sent, disable=['parser', 'ner'])         # TODO: also try make_doc here (maybe more efficient)

    # matching terms in the source sentence;
    # as_spans=True is needed by filter_spans to remove overlapping matches by retaining greedy matches.
    # to allow overlapping matches, set as_spans=False, remove filter_spans and change the following for loop
    matches_it = matcher_it(doc_it, as_spans=True)
    # filtering out duplicates or overlaps. When spans overlap, the (first) longest span is preferred over shorter spans
    # https://spacy.io/api/top-level#util.filter_spans
    matches_it = filter_spans(matches_it)

    #for match_id, start, end in matches_it:        # if as_spans=False and no filter_spans() is applied

    for span in matches_it:                         # iterating over each single term match on the sentence
        start = span.start
        end = span.end
        match_id = span.label
        concept_id = nlp_it.vocab.strings[match_id]             # getting the concept ID of the Italian matched term
        print(concept_id)
        matched_term_it = doc_it[start:end]                     # getting the Italian matched term by slicing the doc
        print(matched_term_it)
        #  now checking if the correspondent German term is in the reference sentence
        Ita, De = id_terms[concept_id]   # getting the DE equivalents using the concept ID of the IT matched term
        pattern_de = [nlp_de.make_doc(term) for term in De]             # converting DE term(s) from str to Doc
        matcher_de.add(concept_id, pattern_de)           # adding DE term(s) to the DE matcher
        doc_de = nlp_de(de_sent, disable=['parser', 'ner'])     # TODO: also try make_doc here, too
        matches_de = matcher_de(doc_de)                         # checking if DE term matches in DE sentence
        '''try:
            matcher_de.remove(concept_id)  # cleaning up matcher for next iterations
        except KeyError:
            pass'''


        if not matches_de:   # if no match is found in the German reference sentence, I retry after splitting compounds
            splitter = Splitter()
            splitted_text = []            # the new sentence that will be searched for matches after compound splitting
            for token in doc_de:
                split_token = splitter.split_compound(token.text)  # output is a list of tuples (score, word, word)
                hyp = split_token[0]        # considering only the first splitting hypothesis
                if hyp[0] > 0.9:                # tweak threshold; over 0.9 seems legit
                    splitted_text.append(hyp[1])   # appending first word of compound
                    splitted_text.append(hyp[2])   # appending second element of compound
                    print("Compound splitted: ", hyp)
                else:  # if score is under threshold, i.e., word is not a compound, append original unsplitted token
                    splitted_text.append(token.text)
            splitted_text = " ".join(splitted_text)             # sentence as string
            print(splitted_text)

            #  reconvert Str to Doc for PhraseMatcher
            splitted_sent_de_doc = nlp_de.make_doc(splitted_text)

            # now retrying to match on splitted_sent_de_doc
            matches_de = matcher_de(splitted_sent_de_doc)           # checking if DE term matches in DE sentence

            if not matches_de:
                # if still no matches...
                print("[NO MATCH] German equivalent absent in reference.")
                print(id_terms[concept_id])
                print(it_sent, "\n", de_sent, "\n")
            else: # if matches_de (meaning a match has been found but ONLY AFTER COMPOUND SPLITTING); for testing only # todo: remove else after testing!
                for match_id, start, end in matches_de:
                    concept_id = nlp_it.vocab.strings[match_id]
                    matched_after_split.append((id_terms[concept_id], it_sent, de_sent))


        try:
            matcher_de.remove(concept_id)  # cleaning up matcher for next iterations
        except KeyError:                   # occurred when there were overlapping matches todo: test if try-except is now removable
            pass

        #  here matches_de is either the first matches or the matches after compound splitting
        for match_id, start, end in matches_de:             # iterating over each match in the DE sentence
            print("[MATCH] German equivalent found in reference.")
            concept_id = nlp_it.vocab.strings[match_id]     # getting the concept ID
            # ...
            # HARD-COPY ROW, DO STUFF, ANNOTATE, ETC ETC
            # ...
            matched_term_de = doc_de[start:end]             # get the matched term by slicing the doc
            #print(matched_term_de)

            identified_terms.append([concept_id, id_terms[concept_id]])
            print(concept_id, "\t", id_terms[concept_id])
            print(it_sent, "\n", de_sent, "\n")
            counter += 1

            ''' except Exception as exc:
            print(exc.message)'''


print(identified_terms)  # todo: need to convert to a dict to do counting with Counter
# print(matched_after_split)
# printing matches after compound splitting nicely
for ((ITTERMS, DETERMS), ITSENT, DESENT) in matched_after_split:
    print(ITTERMS, "\t", DETERMS)
    print(ITSENT)
    print(DESENT)
    print()

print(counter)










