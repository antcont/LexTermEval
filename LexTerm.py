"""
todo: trying to implement first evaluation on an (old) hypothesis, with hard-copying, terms annotation and
 correct/wrong annotation


Included lemmatisation of split compound terms (MUCH SLOWER; it allows to match 316 terms (vs. 305))
TODO: (only for final tests) re-add lemmatisation of compound words for evaluation
todo: when making CLI, insert parameter for lemmatisation of compound words (it slows donw the process heavily)

"""
import spacy
from spacy.matcher import PhraseMatcher
from spacy.util import filter_spans
from charsplit import Splitter
import treetaggerwrapper
from Levenshtein import distance  # needed for coupling matched term - term in full termbase.
    # compute it for each German term in the termbase ->   edit_distance = distance(matched_term, termbase term)
    # then sort it from the lowest Levenshtein edit distance and pick the one with the lowest score
import operator
import csv

from collections import Counter


#  termList is in the following format: id(TABSEPARATOR)italianTerm(PIPESEPARATOR)italianTerm(TABSEPARATOR)germanTerm...
termList = r"C:\Users\anton\Documents\Documenti importanti\SSLMIT FORLI M.A. SPECIALIZED TRANSLATION 2019-2021\tesi\Evaluation (Automatic + Manual)\merged_termlist_id_m-n_lemmatised_TT.txt"
testSet = r"C:\Users\anton\Documents\Documenti importanti\SSLMIT FORLI M.A. SPECIALIZED TRANSLATION 2019-2021\tesi\Evaluation (Automatic + Manual)\testset+reference_2000_1 - detokenized+base+base_lemma.txt"
output = r"C:\Users\anton\Documents\Documenti importanti\SSLMIT FORLI M.A. SPECIALIZED TRANSLATION 2019-2021\tesi\Evaluation (Automatic + Manual)\testset+reference_2000_1 - detokenized+base+base_lemma._EXPERIMENT1.1.txt"


def lemmatise(text, lang):
    '''
    TreeTagger lemmatisation (applied to German compounds after splitting)
    '''
    tagger = treetaggerwrapper.TreeTagger(TAGLANG=lang)
    tags = tagger.tag_text(text)
    mytags = treetaggerwrapper.make_tags(tags)
    lemma_list = []
    for tag in mytags:
        try:
            lemma_list.append(tag.lemma)
        except AttributeError:
            # if NoTag, ignore
            continue
    return " ".join(lemma_list)


def tb_string2dict(termList):
    '''
    termList: a list of strings in the following format:
    id(TABSEPARATOR)italianTerm(PIPESEPARATOR)italianTerm(TABSEPARATOR)germanTerm(PIPESEPARATOR)germanTerm...

    returns: a dictionary with key = concept_IDs and value a tuple of two lists with Italian terms and German terms each
    {'6979': (['indennità di espropriazione', 'indennità di esproprio', 'indennizzo'], ['Enteignungsentschädigung', 'Entschädigung']), …}
    '''
    it_de = []
    for biterm in termList:
        it_de.append(tuple(biterm.split("\t")))  # list of tuples (ID, ItTerms, DeTerms)
    id_terms = {}
    for (id, termsIt, termsDe) in it_de:
        termsIt = [x for x in termsIt.split("|")]
        termsDe = [x for x in termsDe.split("|")]
        id_terms[id] = (termsIt, termsDe)
        #print(id_terms)
        #print()
    return id_terms


print("Loading data...")
with open(termList, "r", encoding="utf-8") as termlist:
    terms = termlist.read().splitlines()

with open(testSet, "r", encoding="utf-8") as testset:
    test = testset.read().splitlines()

test_ = []
for test_ref in test:
    test_.append(tuple(test_ref.split("\t")))  #  list of tuples tuple -> (id, src, ref, src_lemma, ref_lemma)



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

# a list of tuples (sentenceID, src, ref, hyp, src_l, ref_l, hyp_l, conceptID, terminology_entry, src_term, hyp_term, C/W)
annotated_data = []
counter_correct = 0
counter_wrong = 0

#  adding all Italian terms to matcher_it
id_terms = tb_string2dict(terms)
for id, (it, de) in id_terms.items():
    pattern_it = [nlp_it.make_doc(term) for term in it]  # converting Str to Doc (needed by PhraseMatcher)
    matcher_it.add(str(id), pattern_it)   # adding Italian terms to PhraseMatcher, with concept ID

for (id, src, ref, hyp, src_lemma, ref_lemma, hyp_lemma) in test_:
    print("Next sentence pair...")
    doc_it = nlp_it.make_doc(src_lemma)
    doc_it_or = nlp_it.make_doc(src)


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
        matched_term_it_or = doc_it_or[start:end]         # matched term in the original Italian sentence
        print(matched_term_it, "\t", matched_term_it_or)
        #  now checking if the correspondent German term is in the reference sentence
        Ita, De = id_terms[concept_id]   # getting the DE equivalents using the concept ID of the IT matched term
        pattern_de = [nlp_de.make_doc(term) for term in De]             # converting DE term(s) from str to Doc
        matcher_de.add(concept_id, pattern_de)           # adding DE term(s) to the DE matcher
        doc_de = nlp_de.make_doc(ref_lemma)
        doc_de_or = nlp_de.make_doc(ref)
        matches_de = matcher_de(doc_de, as_spans=True)                    # checking if DE term matches in DE sentence
        matches_de = filter_spans(matches_de)              # filtering overlapping matches (greedy)

        if not matches_de:   # if no match is found in the German reference sentence, I retry after splitting compounds
            splitter = Splitter()
            split_text = []            # the new sentence that will be searched for matches after compound splitting
            for token in doc_de:
                split_token = splitter.split_compound(token.text)  # output is a list of tuples (score, word, word)
                hyp_split = split_token[0]        # considering only the first splitting hypothesis
                if hyp_split[0] > 0.7:                # tweak threshold; over 0.9 seems legit
                    # TODO: remember to lemmatise compounds when doing official tests (much slower)
                    #split_text.append(lemmatise(hyp_split[1], "de"))  # lemmatising and appending first word of compound
                    #split_text.append(lemmatise(hyp_split[2], "de"))  # lemmatising and appending second element of compound
                    split_text.append(hyp_split[1])  # appending first word of compound (faster, no lemmatisation)
                    split_text.append(hyp_split[2])  # appending second element of compound (faster, no lemmatisation)
                    print("Compound has been split: ", hyp_split)
                else:  # if score is under threshold, i.e., word is not a compound, append original unsplit token
                    split_text.append(token.text)
            split_text = " ".join(split_text)             # sentence as string
            print(split_text)

            #  reconvert Str to Doc for PhraseMatcher
            doc_de = nlp_de.make_doc(split_text)   # overwriting the original Doc
            doc_de_or = nlp_de.make_doc(split_text)

            # now retrying to match on sentence with split compounds
            matches_de = matcher_de(doc_de, as_spans=True)           # checking if DE term matches in DE sentence
            matches_de = filter_spans(matches_de)                   # filtering overlapping matches (greedy)

            if not matches_de:
                # if still no matches...
                print("[NO MATCH] German equivalent absent in reference.")
                print(id_terms[concept_id])
                print(src, "\n", ref, "\n")
            else: # if matches_de (meaning a match has been found but ONLY AFTER COMPOUND SPLITTING); for testing only # todo: remove else after testing!
                for span in matches_de:  # iterating over each single term match on the sentence
                    start = span.start
                    end = span.end
                    match_id = span.label
                    concept_id = nlp_it.vocab.strings[match_id]
                    matched_after_split.append((id_terms[concept_id], src, ref))


        # here matches_de is either the match from the first search or the match after the compound splitting
        for span in matches_de:  # iterating over each single term match on the sentence
            start = span.start
            end = span.end
            match_id = span.label
            print("[MATCH] German equivalent found in reference.")
            concept_id = nlp_it.vocab.strings[match_id]     # getting the concept ID

            matched_term_de = doc_de[start:end]             # get the matched term by slicing the doc
            matched_term_de_or = doc_de_or[start:end]
            print(matched_term_de, "\t", matched_term_de_or)

            identified_terms.append([concept_id, id_terms[concept_id]])
            print(concept_id, "\t", id_terms[concept_id])
            print(src, "\n", ref, "\n")
            counter += 1

            # now checking for matches in the hypothesis sentence
            doc_hyp = nlp_de.make_doc(hyp_lemma)
            doc_hyp_or = nlp_de.make_doc(hyp)
            matches_de = matcher_de(doc_hyp, as_spans=True)  # checking if DE term matches in DE sentence
            matches_de = filter_spans(matches_de)  # filtering overlapping matches (greedy)

            if not matches_de:  # if no match is found in the German reference sentence, I retry after splitting compounds
                splitter = Splitter()
                split_text = []  # the new sentence that will be searched for matches after compound splitting
                for token in doc_hyp:
                    split_token = splitter.split_compound(token.text)  # output is a list of tuples (score, word, word)
                    hyp_split = split_token[0]  # considering only the first splitting hypothesis
                    if hyp_split[0] > 0.7:  # tweak threshold; over 0.9 seems legit
                        # TODO: remember to lemmatise compounds when doing official tests (much slower)
                        #split_text.append(lemmatise(hyp_split[1], "de"))  # lemmatising and appending first word of compound
                        #split_text.append(lemmatise(hyp_split[2], "de"))  # lemmatising and appending second element of compound
                        split_text.append(hyp_split[1])  # appending first word of compound (faster, no lemmatisation)
                        split_text.append(hyp_split[2])  # appending second element of compound (faster, no lemmatisation)
                        print("Compound has been split: ", hyp_split)
                    else:  # if score is under threshold, i.e., word is not a compound, append original unsplit token
                        split_text.append(token.text)
                split_text = " ".join(split_text)  # sentence as string
                print(split_text)

                #  reconvert Str to Doc for PhraseMatcher
                doc_hyp = nlp_de.make_doc(split_text)  # overwriting the original Doc
                doc_hyp_or = nlp_de.make_doc(split_text)

                # now retrying to match on sentence with split compounds
                matches_de = matcher_de(doc_hyp, as_spans=True)  # checking if DE term matches in DE sentence
                matches_de = filter_spans(matches_de)  # filtering overlapping matches (greedy)

                if not matches_de:
                    # if still no matches... append to annotated data as wrong/omitted term
                    # (sentenceID, src, ref, hyp, src_l, ref_l, hyp_l, conceptID, terminology_entry, src_term, hyp_term, C/W)
                    counter_wrong += 1
                    annotated_tuple = (id, src, ref, hyp, src_lemma, ref_lemma, hyp_lemma, concept_id,
                                       id_terms[concept_id], matched_term_it, "NA", "W")
                                        # "NA" because no term was found in hypothesis
                    annotated_data.append(annotated_tuple)
                    # here matches_de is either the match from the first search or the match after the compound splitting

            for span in matches_de:  # iterating over each single term match on the sentence
                counter_correct += 1
                start = span.start
                end = span.end
                match_id = span.label
                print("[MATCH] German equivalent found in hypothesis.")
                concept_id = nlp_it.vocab.strings[match_id]  # getting the concept ID

                matched_term_de = doc_hyp[start:end]  # get the matched term by slicing the doc
                matched_term_de_or = doc_hyp_or[start:end]

                # which term has been matched? compute Levenshtein edit distance to pair them up
                lev_dist = []
                for deTerm in De:
                    edit_distance = distance(str(matched_term_de_or), deTerm)  # todo: move conversion to string up?
                    lev_dist.append((edit_distance, deTerm))
                # sorting by lowest Levenshtein distance
                lev_dist.sort(key=operator.itemgetter(0))
                match_ = lev_dist[0]        # first tuple, lowest Levenshtein distance
                match = match_[1]           # matched term


                annotated_tuple = (id, src, ref, hyp, src_lemma, ref_lemma, hyp_lemma, concept_id,
                                   id_terms[concept_id], matched_term_it, matched_term_de_or, "C")
                # "NA" because no term was found in hypothesis
                annotated_data.append(annotated_tuple)

        matcher_de.remove(concept_id)  # cleaning up German matcher for next iterations


print(identified_terms)  # todo (later if needed): need to convert to a dict to do counting with Counter
# print(matched_after_split)
# printing matches after compound splitting nicely
for ((ITTERMS, DETERMS), ITSENT, DESENT) in matched_after_split:
    print(ITTERMS, "\t", DETERMS)
    print(ITSENT)
    print(DESENT)
    print()



print("Evaluated terms: ", counter)
print("Correct terms: ", counter_correct)
print("Wrong/omitted terms: ", counter_wrong)
print("LexTermEval score: ", (counter_correct/counter)*100)

#  exporting as TSV file
with open(output, "w", encoding="utf-8") as out:
    tsv_writer = csv.writer(out, delimiter='\t', lineterminator='\n')
    tsv_writer.writerow(["sentenceID", "source", "reference", "hypothesis", "source_lemmatised", "reference_lemmatised",
                         "hypothesis_lemmatised", "conceptID", "terms", "matched_term_source",
                         "matched_term_hypothesis", "C/W"])
    for (a, b, c, d, e, f, g, h, i, j, k, l) in annotated_data:
        tsv_writer.writerow([a, b, c, d, e, f, g, h, i, j, k, l])

print("Done.")

