"""
LexTermEval
Fine-grained automatic evaluation of legal terminology in MT output

The expected test set file is a tab-separated file with:
sentence_id, source, reference, hypothesis, lemmatised_source, lemmatised_reference, lemmatised_hypothesis

"""
from spacy import load as spacy_load
from spacy.lang.it import Italian
from spacy.lang.de import German
from spacy.matcher import PhraseMatcher
from spacy.util import filter_spans
from charsplit import Splitter
import treetaggerwrapper
from Levenshtein import distance
import operator
import csv
from collections import Counter
import pickle
from hlepor import single_hlepor_score, hlepor_score

#  set filepaths
termListMatchRef = r"path\to\TB_m_lemmatised.pkl"  # termlist with AA lemmatised terms only, for matching purposes
termListMatchHyp = r"path\to\TB_full_lemmatised.pkl"
termListEval = r"path\to\TB_full.pkl"  # full termbase with all variants and tags
testSet = r"path\to\testset"
output = r"path\for\output\tsv\file"


#  instantiating compound splitter and TreeTagger
splitter = Splitter() 
tagger = treetaggerwrapper.TreeTagger(TAGLANG="de")

#  (black)list of prepositions and adverbs to avoid compound splitter to split preposition+noun
prep_de = [
    "an", "auf", "bis", "in", "neben", "vor", "zu", "nach", "aus", "mit", "gegen", "her", "hin", "ein", "ab"
]


def lemmatise(text):
    '''
    TreeTagger lemmatisation (applied to German compounds after splitting)
    '''
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


def check_overlap(matches_de, spanSet, n):
    '''
    A function to check if the n-th span in SpaCy's matches_de (output from PhraseMatcher) has already been evaluated
    (i.e., if it is in spanSet)
    spanSet is a set of (matched_term, span) tuples where annotated/evaluated terms are added

    This is done both on the German reference sentence and on the German MT hypothesis sentence, in order to
    prevent double annotation of a same term

    n: the position (0,1,2...) in matches_de to check

    returns: Bool (False: match has already been evaluated; True: match has not already been evaluated) and n
    '''
    span = matches_de[n]
    start = span.start
    end = span.end
    span_de = "%s-%s" % (start, end)
    matched_term_de = doc_de[start:end]  # get the matched term by slicing the doc
    if (str(matched_term_de), span_de) in spanSet:
        return False, n
    else:
        return True, n

def split_compounds(sent, thr, lemma=True):
    """
    Compound splitter for German sentences (https://github.com/dtuggener/CharSplit)
    It splits compounds according to a given threshold (thr)
    A lower threshold (0.5/0.6) allows for higher recall without influencing precision (we are looking for only the few
    German terms corresponding to the entry of the Italian matched term, therefore a risk of introducing noise
    is extremely low)

    sent = a sentence in Doc format
    thr = a float number between 0 and 1 (0.6 high recall, 0.9 high precision)
    lemma = lemmatising elements of split compound or not (very slow but necessary). Defaults to True.

    returns: split sentence in Doc format
    """
    split_text = []  # the "new" sentence that will be searched for matches after compound splitting
    for token in sent:
        split_token = splitter.split_compound(token.text)  # output is a list of tuples (score, word, word)
        hyp_split = split_token[0]  # considering only the first splitting hypothesis
        # (i.e., the one with highest score)
        if hyp_split[0] > thr and hyp_split[1].lower() not in prep_de:
            # if confidence score exceedes threshold and the split word is not preposition+noun
            if lemma:
                split_text.append(lemmatise(hyp_split[1]))  # lemmatising and appending first word of compound
                split_text.append(lemmatise(hyp_split[2]))  # lemmatising and appending second element of compound
            else:  # if lemma == False
                split_text.append(hyp_split[1])  # appending first word of compound (faster, no lemmatisation)
                split_text.append(hyp_split[2])  # appending second element of compound (faster, no lemmatisation)
            #print("Compound has been split: ", hyp_split)
        else:  # if score is under threshold, i.e., word is not a compound, append original unsplit token
            split_text.append(token.text)
    split_text = " ".join(split_text)  # sentence as string
    split_doc = nlp_de.make_doc(split_text)
    return split_doc



print("Loading data...")

with open(termListMatchRef, "rb") as termlistmatch:
    id_terms = pickle.load(termlistmatch)  # {id:([termsIT], [termsAA])}

with open(termListMatchHyp, "rb") as termlistmatch_full:
    id_terms_full = pickle.load(termlistmatch_full)  # {id:([termsIT], [termsAA|DE|AT...])}

with open(termListEval, "rb") as termlisteval:
    referenceTB = pickle.load(termlisteval)  # in the following format...
'''
{
    '28629': ({'immunità di gregge': ('NA', 'NA'),
               'immunità di comunità': ('NA', 'NA'),
               'immunità di gruppo': ('NA', 'NA')},
              {'Herdenimmunität': (['Südtirol', 'AT', 'DE', 'CH'], 'CNS', 'NA'),
               'Herdenschutz': (['Südtirol', 'AT', 'DE', 'CH'], 'CNS', 'NA')})
}
'''

# test set contains tab-separated (id, source, reference, hypothesis, lemmatised source, lemmatised reference,
# lemmatised hypothesis)
with open(testSet, "r", encoding="utf-8") as testset:
    test = testset.read().splitlines()

test_ = []
for test_ref in test:
    test_.append(tuple(test_ref.split("\t")))
    #  list of tuples -> (id, src, ref, hyp, src_lemma, ref_lemma, hyp_lemma)

#  loading/instantiating Spacy models and instantiating the PhraseMatchers for each language
print("Loading SpaCy...\n")
# nlp_de = spacy_load("de_core_news_lg")
# nlp_it = spacy_load("it_core_news_lg")
nlp_de = German()
nlp_it = Italian()
matcher_it = PhraseMatcher(nlp_it.vocab, attr="LOWER")
matcher_de = PhraseMatcher(nlp_de.vocab, attr="LOWER")

print("Start searching for matches...\n")

#  for testing purposes (todo: remove after testing?)
identified_terms = []
matched_after_split = []  # see which additional matches have been found thanks to compound-splitting

#  FINAL ANNOTATION DATA
# list of tuples (sentenceID, src, ref, hyp, src_l, ref_l, hyp_l, conceptID, terminology_entry, src_term, hyp_term,
# C/W, legal_system, tag, hLEPOR)
annotated_data = []

#  adding ALL Italian terms to the Italian PhraseMatcher
#  (with respective entry_ID from bistro to allow retrieval of German terms)
#  concept-oriented: terms and variants are "grouped" in the same search pattern
#  and are associated to the entry ID from bistro
for id, (it, de) in id_terms.items():
    pattern_it = [nlp_it.make_doc(term) for term in it]  # converting Str to Doc (needed by PhraseMatcher)
    matcher_it.add(str(id), pattern_it)  # adding all Italian terms to PhraseMatcher, with respective conceptID

#  starting automatic terminology evaluation
for (id, src, ref, hyp, src_lemma, ref_lemma, hyp_lemma) in test_:  # iterating over each sentence-tuple in the test-set

    # for each sentence in test set, creating a set of tuples (matched_term, span)
    # to avoid duplicate annotations in sentences with more than one term from the same concept
    match_spans_de_ref = set()
    match_spans_de_hyp = set()
    print("Next sentence pair...")

    doc_it = nlp_it.make_doc(src_lemma)  # Str to Doc (lemmatised)
    doc_it_or = nlp_it.make_doc(src)  # Str to Doc (original); used to retrieve the original form of the matched term

    matches_it = matcher_it(doc_it, as_spans=True)
    # matching terms in the source sentence;
    # as_spans=True is needed by filter_spans to remove overlapping matches by retaining greedy matches.
    # to allow overlapping matches, set as_spans=False, remove filter_spans and change the following for loop

    matches_it = filter_spans(matches_it)
    # filtering out overlapping matches, greedily.
    # "When spans overlap, the (first) longest span is preferred over shorter spans."
    # https://spacy.io/api/top-level#util.filter_spans
    # Same approach used by Farajian et al. 2018 (cfr. e-mail exchange with Farajian)

    # for match_id, start, end in matches_it:        # if as_spans=False and filter_spans() is not applied
    for span in matches_it:  # iterating over each single term match in the Italian source sentence
        start_it = span.start
        end_it = span.end
        match_id = span.label
        span_it = "%s-%s" % (start_it, end_it)
        concept_id = nlp_it.vocab.strings[match_id]  # getting the concept ID of the Italian matched term
        #print(concept_id)
        matched_term_it = doc_it[start_it:end_it]  # getting the Italian matched term by slicing the doc
        matched_term_it_or = doc_it_or[start_it:end_it]  # matched term in the original Italian sentence
        #print(matched_term_it, "\t", matched_term_it_or)

        #  now checking if the correspondent German term is in the reference sentence
        Ita, De = id_terms[concept_id]  # getting the DE equivalents using the concept ID of the IT matched term
        pattern_de = [nlp_de.make_doc(term) for term in De]  # converting DE term(s) from str to Doc
        matcher_de.add(concept_id, pattern_de)  # adding DE term(s) to the German PhraseMatcher (NB: only AA terms)
        doc_de = nlp_de.make_doc(ref_lemma)  # Str to Doc
        doc_de_or = nlp_de.make_doc(ref)  # Str to Doc
        matches_de = matcher_de(doc_de, as_spans=True)  # searching for term matches in the German reference sentence
        matches_de = filter_spans(matches_de)  # filtering overlapping matches (greedy)

        if not matches_de:  # if no match is found in the German reference sentence, I retry after splitting compounds
            doc_de = split_compounds(doc_de, 0.3, True) # splitting compounds and overwriting existing non-split doc_de

            # TODO: CHECK THE FOLLOWING: by doing so, I am overwriting the actual original non-lemmatised DE sentence,
            #  and, as a consequence, I am not annotating the actual term from the original sentence, but the lemmatised
            #  form. It's actually not a problem, but still, it is a small inconsistency. It is necessary if using the
            #  original form of the matched term to point to the reference termbase (not doing it would imply wrong
            #  spans and wrong (original) matched terms
            doc_de_or = doc_de              # todo: check: if useless, remove.

            # now re-trying to match on the German reference sentence with split compounds
            matches_de = matcher_de(doc_de, as_spans=True)  # checking for term matches in the German reference sentence
            matches_de = filter_spans(matches_de)  # filtering overlapping matches (greedy)

            if not matches_de:
                # if still no matches, the sentence is not annotated and therefore discarded from the test set
                #print("[NO MATCH] German equivalent term absent in reference.")
                #print(id_terms[concept_id])
                #print(src, "\n", ref, "\n")
                pass

            else:  # if matches_de (meaning a match has been found but ONLY AFTER COMPOUND SPLITTING); for testing only
                # todo: remove "else" after testing
                for span in matches_de:  # iterating over each single term match on the sentence
                    start = span.start
                    end = span.end
                    match_id = span.label
                    matched_after_split.append((id_terms[concept_id], src, ref))

        # hereafter, matches_de is/are the German match(es) in the reference sentence from either the first search
        # or the search after compound splitting
        if not matches_de:  # if no matches in reference sentence
            matcher_de.remove(concept_id)
            continue  # go the the next Italian match, therefore discarding the sentence from final test-set

        elif len(matches_de) == 1:  # if only one match in reference, no "disambiguation" needed
            span = matches_de[0]
            start = span.start
            end = span.end
            match_id = span.label
            span_de = "%s-%s" % (start, end)
            matched_term_de = doc_de[start:end]  # get the matched term by slicing the doc

        elif len(matches_de) > 1:  # if more than one match in German reference (for one match in IT)
            # here I am avoiding double annotation of a same term
            for i in range(len(matches_de)):
                # checking if term is not already annotated (see "check_overlap" function defined above)
                whichMatch, num = check_overlap(matches_de, match_spans_de_ref, i)
                if whichMatch:  # meaning the term has not yet been considered and annotated
                    span = matches_de[num]
                    start = span.start
                    end = span.end
                    match_id = span.label
                    span_de = "%s-%s" % (start, end)
                    matched_term_de = doc_de[start:end]  # get the matched term by slicing the doc
                    # add to set of already annotated terms, in order to avoid re-annotating in following iterations
                    match_spans_de_ref.add((str(matched_term_de), span_de))
                    break

        print("[MATCH] German equivalent term found in reference.")

        concept_id = nlp_it.vocab.strings[match_id]  # getting the concept ID

        matched_term_de = doc_de[start:end]  # get the matched term by slicing the doc
        matched_term_de_or = doc_de_or[start:end]  # todo: check. if useless, remove
        #print(matched_term_de, "\t", matched_term_de_or)

        identified_terms.append([concept_id, id_terms[concept_id]])  # todo: remove after testing?
        #print(concept_id, "\t", id_terms[concept_id])
        #print(src, "\n", ref, "\n")

        # now checking for matches in the German hypothesis sentence from the machine translation system
        # here I'm using the full termbase (with German terms from all legal systems, instead of only South Tyrol)

        matcher_de = PhraseMatcher(nlp_de.vocab, attr="LOWER")
        # RE-INSTANTIATING AN EMPTY GERMAN MATCHER INSTEAD OF REMOVING THE PATTERN FROM THE EXISTING MATCHER
        # because the following --> (matcher_de.remove(concept_id)) <-- raised an anomalous error
        # --> "Process finished with exit code -1073741819 (0xC0000005)"
        # probably due to a bug in SpaCy, cfr. https://github.com/explosion/spaCy/issues/6148


        #  getting DE terms from the full lemmatised reference TB (containing all terms, not only South Tyrol)
        itTerms, deTerms = id_terms_full[concept_id]  # getting TB entry through concept ID
        # getting German terms to be added to the PhraseMatcher and converting to Doc
        terms_matcher = [nlp_de.make_doc(term) for term in deTerms]
        matcher_de.add(concept_id, terms_matcher)  # adding all German term(s) to the German PhraseMatcher (full TB)

        doc_hyp = nlp_de.make_doc(hyp_lemma)  # Str to Doc
        doc_hyp_or = nlp_de.make_doc(hyp)  # Str to Doc
        matches_de = matcher_de(doc_hyp, as_spans=True)  # checking if DE term matches in German hyp sentence
        matches_de = filter_spans(matches_de)  # filtering overlapping matches (greedy)

        if not matches_de:
            # if no match is found in the German sentence, I retry after splitting compounds
            doc_hyp = split_compounds(doc_hyp, 0.3, True)  # splitting compounds and overwriting existing non-split doc_de
            #print(doc_hyp)

            # TODO: NB: I'm overwriting (for compound-split sentences) the original non-lemmatised hyp sentence with
            #  the split, lemmatised version, in order to retrieve the matched term using spans. (SEE ABOVE)
            doc_hyp_or = doc_hyp

            # now retrying to match on German hypothesis sentence with split compounds
            matches_de = matcher_de(doc_hyp, as_spans=True)  # checking for DE term matches in German hyp sentence
            matches_de = filter_spans(matches_de)  # filtering overlapping matches (greedy)

            if not matches_de:
                # if still no matches... append to annotated data as wrong/omitted, NEO: Non-equivalent term/omitted.
                # to assign NEO-S and NEO-NS, check Termstatus tags of German terms in entry
                # (sentenceID, src, ref, hyp, src_l, ref_l, hyp_l, conceptID,
                # terminology_entry, src_term, hyp_term, C/W, legal_system, tag)

                German_tags = set()    # set of Termstatus tags in German terms of the entry
                itTerms, deTerms = referenceTB[concept_id]  # getting German terms from full termbase using ID
                for deTerm, (spr, status, statusOLD) in deTerms.items():
                    German_tags.add(status)

                #  assigning NEO-S and NEO-NS according to the Termstatus tags of the German terms in the entry
                #  If the entry contains German standardised/recommended terms, assign NEO-S tag
                #  (non-equivalent/omitted term given a standardised/recommended German term),
                #  else: assign NEO-NS (non-equivalent/omitted term given a standardised/recommended German term).
                if "CS" in German_tags:    # if standardised/recommended German terms in entry
                    tag = "NEO-S"
                else:                      # if no standardised/recommended German terms in entry
                    tag = "NEO-NS"

                #  computing hLEPOR score
                hlepor = str(float("{:.3f}".format(single_hlepor_score(ref, hyp))))
                hlepor = hlepor.replace(".", ",")  # localizing decimal separator for Excel

                annotated_tuple = (id, src, ref, hyp, src_lemma, ref_lemma, hyp_lemma, concept_id,
                                   id_terms_full[concept_id], str(matched_term_it), "NA", "W", "NA", tag, hlepor)
                annotated_data.append(annotated_tuple)
                #print("[NO MATCH] No German equivalent found in hypothesis.")
                #print(matched_term_it)
                #print(doc_de)
                #print(terms_matcher)
                print()

        # hereafter, matches_de is/are the German match(es) in the hypothesis sentence from either the first search
        # or the search after compound splitting
        # if no matches_de, it has already been handled above and annotated as wrong/omitted
        if not matches_de:
            matcher_de.remove(concept_id)
            continue

        elif len(matches_de) == 1:  # if only one match in hypothesis, no "disambiguation" problem
            span = matches_de[0]
            start = span.start
            end = span.end
            match_id = span.label
            span_de = "%s-%s" % (start, end)
            matched_term_de = doc_de[start:end]  # get the matched term by slicing the doc

        elif len(matches_de) > 1:  # if more than one match in german hypothesis (for one match in IT)
            for i in range(len(matches_de)):
                whichMatch, num = check_overlap(matches_de, match_spans_de_hyp, i)
                if whichMatch:  # meaning the term has not yet been considered and annotated
                    span = matches_de[num]
                    start = span.start
                    end = span.end
                    match_id = span.label
                    span_de = "%s-%s" % (start, end)
                    matched_term_de = doc_de[start:end]  # get the matched term by slicing the doc
                    # add to set of already annotated terms, in order to avoid re-annotating in following iterations
                    match_spans_de_hyp.add((str(matched_term_de), span_de))
                    break

        #print("[MATCH] German equivalent found in hypothesis.")
        concept_id = nlp_it.vocab.strings[match_id]  # getting the concept ID

        matched_term_de = doc_hyp[start:end]  # get the matched term by slicing the doc
        matched_term_de_or = doc_hyp_or[start:end]

        # which term has been matched?
        # computing Levenshtein edit distance to match matched_term with term within the entry in the full TB
        lev_dist_IT = []
        lev_dist_DE = []
        # TODO: HERE THE COMPARISON MUST BE DONE WITH THE REFERENCE TERMBASE
        itTerms, deTerms = referenceTB[concept_id]  # getting German terms from full termbase using ID
        #  Italian term
        for itTerm, (status, statusOLD) in itTerms.items():
            edit_distance = distance(str(matched_term_it_or), itTerm)  # todo: move conversion to string up?
            lev_dist_IT.append((edit_distance, itTerm))
        lev_dist_IT.sort(key=operator.itemgetter(0))  # sorting by lowest Levenshtein distance
        match_it = lev_dist_IT[0]  # first tuple, lowest Levenshtein distance. tuples -> (levenshtein_dist, term)
        matchIT = match_it[1]  # ITALIAN MATCHED TERM
        #  German term
        for deTerm, (spr, status, statusOLD) in deTerms.items():
            edit_distance = distance(str(matched_term_de_or), deTerm)  # todo: move conversion to string up?
            lev_dist_DE.append((edit_distance, deTerm))
        lev_dist_DE.sort(key=operator.itemgetter(0))  # sorting by lowest Levenshtein distance
        match_de = lev_dist_DE[0]  # first tuple, lowest Levenshtein distance. tuples -> (levenshtein_dist, term)
        matchDE = match_de[1]  # GERMAN MATCHED TERM


        #  getting tags from full reference termbase and annotating
        #  first, I handle exceptions (tags that have to be assigned according to combination of other tags)
        #  ex: genormt; OLD;
        #  then, the remaining cases can be simply annotated with the tag in Termstatus
        # metadata for matched terms
        (status_it, old_it) = itTerms[matchIT]
        (spr, status_de, old_de) = deTerms[matchDE]
        tag = status_de
        CW = "C"

        #  assigning W tag (wrong) to terms with NST-S and NST-N status tags
        if tag == "NST-S" or tag == "NST-NS":
            CW = "W"
            
        #  handling terms with "OLD" tag
        if old_de == "OLD" and spr == "Südtirol":  # defensive; all OLD terms should already be from South Tyrol
            if old_it != "OLD":  # if German term is OLD and Italian was not
                tag = "OLD"  # assign OLD
                CW = "W"
            else:  # if Italian is OLD, too
                pass  # keep the tag already assigned

        #  computing hlepor score
        hlepor = str(float("{:.3f}".format(single_hlepor_score(ref, hyp))))
        hlepor = hlepor.replace(".", ",")  # localizing decimal number separator for Excel

        #  writing annotation row
        """it, de = id_terms[concept_id]
        concept_terms = ", ".join(it) + " = " + ", ".join(de)"""
        annotated_tuple = (id, src, ref, hyp, src_lemma, ref_lemma, hyp_lemma, concept_id, id_terms_full[concept_id],
                           str(matched_term_it), str(matched_term_de_or), CW, "|".join(spr), tag, hlepor)
        annotated_data.append(annotated_tuple)

        matcher_de.remove(concept_id)
        # removing current terminology patterns from German PhraseMatcher for next iterations
        # should errors be raised, re-instantiate an empty matcher_de here (as done above)

# print(identified_terms)  # todo: to convert to a dict to do counting with Counter
#print(matched_after_split)
#print(len(matched_after_split))

'''# printing matches after compound splitting nicely (for testing purposes)
for ((ITTERMS, DETERMS), ITSENT, DESENT) in matched_after_split:
    print(ITTERMS, "\t", DETERMS)
    print(ITSENT)
    print(DESENT)
    print()'''


#  counting each tag to compute term accuracy score
total = len(annotated_data)
counter_correct = 0
counter_wrong = 0
counter_NEO_S = 0
counter_NEO_NS = 0
counter_NST_S = 0
counter_NST_NS = 0
counter_OLD = 0
counter_CS = 0
counter_CNS = 0
counter_ANS = 0

for (id, src, ref, hyp, src_lemma, ref_lemma, hyp_lemma, concept_id, concept_terms,
     matched_term_it, matched_term_de_or, CW, spr, tag, hlepor) in annotated_data:
    if CW == "W":
        counter_wrong += 1
    elif CW == "C":
        counter_correct += 1
    if tag == "NEO-S":
        counter_NEO_S += 1
    if tag == "NEO-NS":
        counter_NEO_NS += 1
    elif tag == "NST-S":
        counter_NST_S += 1
    elif tag == "NST-NS":
        counter_NST_NS += 1
    elif tag == "OLD":
        counter_OLD += 1
    elif tag == "CS":
        counter_CS += 1
    elif tag == "CNS":
        counter_CNS += 1
    elif tag == "ANS":
        counter_ANS += 1


#  adding id to each row
final = []
idEval = 1
for (a, b, c, d, e, f, g, h, i, j, k, l, m, n, o) in annotated_data:
    final.append((idEval, a, b, c, d, e, f, g, h, i, j, k, l, m, n, o))
    idEval += 1

print()
print("===============================================================================================================")
print("Evaluated terms: ", total)
print("_______________________________________________________________________________________________________________")
print("Correct terms: ", counter_correct)
print("\tCorrect standardised/recommended terms: ", counter_CS)
print("\tCorrect non-standardised/non-recommended terms: ", counter_CNS)
print("\tAcceptable variant terms given a standardised/recommended term: ", counter_ANS)
print("_______________________________________________________________________________________________________________")
print("Wrong/omitted terms: ", counter_wrong)
print("\tNon-equivalent/omitted terms: ", counter_NEO_S + counter_NEO_NS)
print("\t\tNon-equivalent/omitted terms (given a standardised or recommended term): ", counter_NEO_S)
print("\t\tNon-equivalent/omitted terms (without a standardised or recommended term): ", counter_NEO_NS)
print("\tNon-South-Tyrol-specific terms: ", counter_NST_S + counter_NST_NS)
print("\t\tNon-South-Tyrol-specific terms (given a standardised or recommended term): ", counter_NST_S)
print("\t\tNon-South-Tyrol-specific terms (without a standardised or recommended term): ", counter_NST_NS)
print("\tOutdated terms: ", counter_OLD)
print("_______________________________________________________________________________________________________________")
print("LexTermEval score: ", (counter_correct / total) * 100)
print("===============================================================================================================")


#  exporting as TSV file
with open(output, "w", encoding="utf-8") as out:
    tsv_writer = csv.writer(out, delimiter='\t', lineterminator='\n')
    tsv_writer.writerow(
        ["ID", "sentenceID", "source", "reference", "hypothesis", "source_lemmatised", "reference_lemmatised",
         "hypothesis_lemmatised", "conceptID", "terms", "matched_term_source",
         "matched_term_hypothesis", "C/W", "Sprachgebrauch", "tag", "hLEPOR"])
    for (a, b, c, d, e, f, g, h, i, j, k, l, m, n, o, p) in final:
        tsv_writer.writerow([a, b, c, d, e, f, g, h, i, j, k, l, m, n, o, p])
