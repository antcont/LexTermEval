"""
TODO: risolvere problema annotazione (v. output)... prima non c'era! Devo aver modificato qualcosa per sbaglio nelle
 ultime 2 ore
 - alcuni match poi non si riferiscono al termine italiano trovato ma alla entry del match precedente... com'è possibile
   es. ha cercato Landesgesetz, poi il termine italiano successivo è "essere",  e lui cerca in reference non il
   corrispondente di "essere", bensì Landesgesetz... perché???

TODO: create function for compound_splitting

TODO: possible reasons for duplicate rows and how to solve them
sentence 1: it contains 2 times "Artikel" and there are 8 total identical rows... why? should be 2
per evitare la doppia annotazione di un termine che compare due volte, devo impedire che alla prima iterazione lui trovi
due matches, devo limitarlo in qualche modo a uno, non so come... devo limitarlo anche nella ricerca di corrispondenti
in reference, e poi in hypothesis... forse posso instanziare un True/False e usare un while loop

- TODO: add limitation to 1-1 match (avoid 1-2 matches for sentences with more than one term from the same concept,
   or the same term repeated)



se uso la strategia del matches_de[0] potrebbe essere un problema; perché la prima volta becca il primo termine
all'interno della frase, ma se c'è un termine due volte, alla seconda volta non beccherà il secondo termine, ma di nuovo
il primo! come risolvo questa cosa? La risolvo così:
- annotare posizione termine annotato (ma dove, come?)
- inserire il matches_de[0] in un try-else o in un if/else: se c'è solo un match, okay. se ci sono più di un match,
  controllare se il match precedentemente considerato (considera sia id_frase che start-end) coincide con il primo.
  se non coincide, andare avanti; altrimenti, considerare il secondo match; altrimenti, il terzo match.
- una volta implementato tutto ciò, devo stare attento a se effettivamente il numero di righe nell'annotazione finale
  coincide fra i diversi test con diversi hypothesis
- rimane scoperto il caso in cui il secondo termine venga trovato solo dopo compound splitting e il primo no? perché
  non coinciderebbe più lo span


TODO: devo assicurarmi che per ogni match_it venga annotato solo un match_de, oltre a controllare che lo stesso
 non sia stato gia annotato. a sto punto devo veramente valutare se usare una strategia tipo match[0] etc.

Included lemmatisation of split compound terms (MUCH SLOWER; it allows to match 316 terms (vs. 305))
TODO: (only for final tests) re-add lemmatisation of compound words for evaluation
todo: when making CLI, insert argument for lemmatisation of compound words (it slows down the process heavily)

"""
from spacy import load as spacy_load
from spacy.lang.it import Italian
from spacy.lang.de import German
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
import pickle

#  (temporary) filepaths before adopting CLI
termListMatchRef = r"C:\Users\anton\Dropbox\Eurac_tesi\LexTermEval\TB_m_lemmatised.pkl"  # termlist with AA lemmatised terms only, for matching purposes
termListMatchHyp = r""      # TODO: lemmatise
termListEval = r"C:\Users\anton\Dropbox\Eurac_tesi\LexTermEval\TB_full.pkl"  # full termbase with all variants and tags
testSet = r"C:\Users\anton\Documents\Documenti importanti\SSLMIT FORLI M.A. SPECIALIZED TRANSLATION 2019-2021\tesi\Evaluation (Automatic + Manual)\testset+reference_2000_1 - detokenized+base+base_lemma.txt"
output = r"C:\Users\anton\Documents\Documenti importanti\SSLMIT FORLI M.A. SPECIALIZED TRANSLATION 2019-2021\tesi\Evaluation (Automatic + Manual)\testset+reference_2000_1 - detokenized+hyp3+hyp3_lemma.EXPERIMENT_09.06.2021_with reference.txt"


#  instantiating compound splitter
splitter = Splitter()



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
    Compound splitter for German sentences.
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
        if hyp_split[0] > thr:
            if lemma:
                split_text.append(lemmatise(hyp_split[1], "de"))  # lemmatising and appending first word of compound
                split_text.append(lemmatise(hyp_split[2], "de"))  # lemmatising and appending second element of compound
            else:  # if lemma == False
                split_text.append(hyp_split[1])  # appending first word of compound (faster, no lemmatisation)
                split_text.append(hyp_split[2])  # appending second element of compound (faster, no lemmatisation)
            print("Compound has been split: ", hyp_split)
        else:  # if score is under threshold, i.e., word is not a compound, append original unsplit token
            split_text.append(token.text)
    split_text = " ".join(split_text)  # sentence as string
    split_doc = nlp_de.make_doc(split_text)
    return split_doc





print("Loading data...")

with open(termListMatchRef, "rb") as termlistmatch:
    id_terms = pickle.load(termlistmatch)  # {id:([termsIT], [termsAA])}

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
# C/W, legal_system, tag)
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
    # filtering out overlaps, greedily.
    # "When spans overlap, the (first) longest span is preferred over shorter spans."
    # https://spacy.io/api/top-level#util.filter_spans
    # Same approach used by Farajian et al. (cfr. e-mail exchange with Farajian)

    # for match_id, start, end in matches_it:        # if as_spans=False and filter_spans() is not applied
    for span in matches_it:  # iterating over each single term match in the Italian source sentence
        start_it = span.start
        end_it = span.end
        match_id = span.label
        span_it = "%s-%s" % (start_it, end_it)
        concept_id = nlp_it.vocab.strings[match_id]  # getting the concept ID of the Italian matched term
        print(concept_id)
        matched_term_it = doc_it[start_it:end_it]  # getting the Italian matched term by slicing the doc
        matched_term_it_or = doc_it_or[start_it:end_it]  # matched term in the original Italian sentence
        print(matched_term_it, "\t", matched_term_it_or)

        #  now checking if the correspondent German term is in the reference sentence
        Ita, De = id_terms[concept_id]  # getting the DE equivalents using the concept ID of the IT matched term
        pattern_de = [nlp_de.make_doc(term) for term in De]  # converting DE term(s) from str to Doc
        matcher_de.add(concept_id, pattern_de)  # adding DE term(s) to the German PhraseMatcher (NB: only AA terms)
        doc_de = nlp_de.make_doc(ref_lemma)  # Str to Doc
        doc_de_or = nlp_de.make_doc(ref)  # Str to Doc
        matches_de = matcher_de(doc_de, as_spans=True)  # searching for term matches in the German reference sentence
        matches_de = filter_spans(matches_de)  # filtering overlapping matches (greedy)

        if not matches_de:  # if no match is found in the German reference sentence, I retry after splitting compounds
            doc_de = split_compounds(doc_de, 0.6, False) # splitting compounds and overwriting existing non-split doc_de

            # TODO: CHECK THE FOLLOWING: by doing so, I am overwriting the actual original non-lemmatised DE sentence,
            #  and, as a consequence, I am not annotating the actual term from the original sentence, but the lemmatised
            #  form. It's actually not a problem, but still, it is a small inconsistency. It is necessary if using the
            #  original form of the matched term to point to the reference termbase (not doing it would imply wrong
            #  spans and wrong (original) matched terms
            doc_de_or = doc_de

            # now re-trying to match on the German reference sentence with split compounds
            matches_de = matcher_de(doc_de, as_spans=True)  # checking for term matches in the German reference sentence
            matches_de = filter_spans(matches_de)  # filtering overlapping matches (greedy)

            if not matches_de:
                # if still no matches, the sentence is not annotated and therefore discarded from the test set
                print("[NO MATCH] German equivalent term absent in reference.")
                print(id_terms[concept_id])
                print(src, "\n", ref, "\n")

            else:  # if matches_de (meaning a match has been found but ONLY AFTER COMPOUND SPLITTING); for testing only
                # todo: remove "else" after testing!
                for span in matches_de:  # iterating over each single term match on the sentence
                    start = span.start
                    end = span.end
                    match_id = span.label
                    #concept_id = nlp_it.vocab.strings[match_id]
                    matched_after_split.append((id_terms[concept_id], src, ref))

        # hereafter, matches_de is/are the German match(es) in the reference sentence from either the first search
        # or the search after compound splitting
        if not matches_de:  # if no matches in reference sentence
            matcher_de.remove(concept_id)
            continue  # go the the next Italian match, therefore discarding the sentence from final test-set

        elif len(matches_de) == 1:  # if only one match in reference, no disambiguation problem
            span = matches_de[0]
            start = span.start
            end = span.end
            match_id = span.label
            span_de = "%s-%s" % (start, end)
            matched_term_de = doc_de[start:end]  # get the matched term by slicing the doc

        elif len(matches_de) > 1:  # if more than one match in German reference (for one match in IT)
            # here I am avoiding double annotation of a same term
            for i in range(len(matches_de)):
                whichMatch, num = check_overlap(matches_de, match_spans_de_ref, i)
                # checking if term is not already annotated (see "check_overlap" function defined at line 73)
                if whichMatch:  # meaning the term has not yet been considered
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
        matched_term_de_or = doc_de_or[start:end]
        print(matched_term_de, "\t", matched_term_de_or)

        identified_terms.append([concept_id, id_terms[concept_id]])  # todo: remove after testing?
        print(concept_id, "\t", id_terms[concept_id])
        print(src, "\n", ref, "\n")

        # now checking for matches in the German hypothesis sentence from the machine translation system
        # here I'm using the full termbase (with German terms from all legal systems, instead of only South Tyrol)

        matcher_de = PhraseMatcher(nlp_de.vocab, attr="LOWER")
        # RE-INSTANTIATING AN EMPTY GERMAN MATCHER INSTEAD OF REMOVING THE PATTERN FROM THE EXISTING MATCHER
        # because the following --> (matcher_de.remove(concept_id)) <-- raised an anomalous error
        # --> "Process finished with exit code -1073741819 (0xC0000005)"
        # probably due to a bug in SpaCy, very similar to this https://github.com/explosion/spaCy/issues/6148

        #  getting DE terms from the reference TB (containing all terms, not only South Tyrol)
        itTerms, deTerms = referenceTB[concept_id]  # getting entry through concept ID
        # getting German terms to be added to the PhraseMatcher and converting to Doc
        terms_matcher = [nlp_de.make_doc(term) for term, tags in deTerms.items()]
        matcher_de.add(concept_id, terms_matcher)  # adding all German term(s) to the German PhraseMatcher (full TB)

        doc_hyp = nlp_de.make_doc(hyp_lemma)  # Str to Doc
        doc_hyp_or = nlp_de.make_doc(hyp)  # Str to Doc
        matches_de = matcher_de(doc_hyp, as_spans=True)  # checking if DE term matches in German hyp sentence
        matches_de = filter_spans(matches_de)  # filtering overlapping matches (greedy)

        if not matches_de:
            # if no match is found in the German sentence, I retry after splitting compounds
            doc_de = split_compounds(doc_de, 0.6, False) # splitting compounds and overwriting existing non-split doc_de
            doc_de_or = doc_de

            # now retrying to match on German hypothesis sentence with split compounds
            matches_de = matcher_de(doc_hyp, as_spans=True)  # checking for DE term matches in German hyp sentence
            matches_de = filter_spans(matches_de)  # filtering overlapping matches (greedy)

            if not matches_de:
                # if still no matches... append to annotated data as wrong/omitted, 1. NEO: Non-equivalent term/omitted
                # (sentenceID, src, ref, hyp, src_l, ref_l, hyp_l, conceptID,
                # terminology_entry, src_term, hyp_term, C/W, legal_system, tag)
                annotated_tuple = (id, src, ref, hyp, src_lemma, ref_lemma, hyp_lemma, concept_id,
                                   id_terms[concept_id], str(matched_term_it), "NA", "W", "NA", "NEO")
                                    # "NA" because no term was found in hypothesis
                annotated_data.append(annotated_tuple)

        # hereafter, matches_de is/are the German match(es) in the hypothesis sentence from either the first search
        # or the search after compound splitting
        # if no matches_de, it has already been handled above and annotated as wrong/omitted
        if not matches_de:
            matcher_de.remove(concept_id)
            continue

        elif len(matches_de) == 1:  # if only one match in hypothesis, no disambiguation problem
            span = matches_de[0]
            start = span.start
            end = span.end
            match_id = span.label
            span_de = "%s-%s" % (start, end)
            matched_term_de = doc_de[start:end]  # get the matched term by slicing the doc

        elif len(matches_de) > 1:  # if more than one match in german hypothesis (for one match in IT)
            for i in range(len(matches_de)):
                whichMatch, num = check_overlap(matches_de, match_spans_de_hyp, i)
                if whichMatch:  # meaning the term has not yet been considered
                    span = matches_de[num]
                    start = span.start
                    end = span.end
                    match_id = span.label
                    span_de = "%s-%s" % (start, end)
                    matched_term_de = doc_de[start:end]  # get the matched term by slicing the doc
                    # add to set of already annotated terms, in order to avoid re-annotating in following iterations
                    match_spans_de_hyp.add((str(matched_term_de), span_de))
                    break

        print("[MATCH] German equivalent found in hypothesis.")
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
        if "NST" in status_de:
            CW = "W"

        #  removed, as ANS_C is no more annotated; ANS tag is already there
        """
        #  handling variants of standardised terms (according to status of Italian term)
        if status_de == "ANS_C":
            if status_it == "normato Alto Adige":
                # if matched term is not standardised (but there is a standardised German term
                # in the entry (ANS_C)), and the Italian matched term is standardised
                # assign ANS (acceptable term given a standardised/recommended term)
                tag = "ANS"
            else:  # if Italian term is NOT standardised
                tag = "CNS"   # correct non-standardised term"""

        #  handling terms with "OLD" tag
        if old_de == "OLD" and spr == "Südtirol":  # defensive; all OLD terms should already be from South Tyrol
            if old_it != "OLD":  # if German term is OLD and Italian was not
                tag = "OLD"  # assign OLD
                CW = "W"
            else:  # if Italian is OLD, too
                pass  # keep the tag already assigned

        #  writing annotation row
        """it, de = id_terms[concept_id]
        concept_terms = ", ".join(it) + " = " + ", ".join(de)"""
        annotated_tuple = (id, src, ref, hyp, src_lemma, ref_lemma, hyp_lemma, concept_id, id_terms[concept_id],
                           str(matched_term_it), str(matched_term_de_or), "C", "|".join(spr), tag)
        annotated_data.append(annotated_tuple)

        matcher_de.remove(concept_id)
        # removing current terminology patterns from German PhraseMatcher for next iterations
        # should errors be raised, re-instantiate an empty matcher_de here (as done above)

# print(identified_terms)  # todo (later if needed): need to convert to a dict to do counting with Counter
# print(matched_after_split)

# printing matches after compound splitting nicely
"""for ((ITTERMS, DETERMS), ITSENT, DESENT) in matched_after_split:
    print(ITTERMS, "\t", DETERMS)
    print(ITSENT)
    print(DESENT)
    print()"""

# print(annotated_data)


#  temporarily removed, because todo: find the cause of duplicate rows and solve it there, instead of deduplicating
'''
print(len(annotated_data))   # before deduplication
#  deduplication
#  temporarily convert to strings in order to deduplicate, then reconvert to list of tuples
annotated_data = ["\t".join(row) for row in annotated_data]
annotated_data = list(set(annotated_data))
annotated_data = [row.split("\t") for row in annotated_data]
annotated_data = [(int(a), b, c, d, e, f, g, h, i, j, k, l, m, n) for (a, b, c, d, e, f, g, h, i, j, k, l, m, n)
                  in annotated_data]        # need to convert sentenceID to integer for sorting
#  re-order by sentenceID
annotated_data.sort(key=lambda x: x[0])
'''

#  counting each tag to compute LexTermEval
total = len(annotated_data)
counter_correct = 0
counter_wrong = 0

for (id, src, ref, hyp, src_lemma, ref_lemma, hyp_lemma, concept_id, concept_terms,
     matched_term_it, matched_term_de_or, CW, spr, tag) in annotated_data:
    if CW == "W":
        counter_wrong += 1
    elif CW == "C":
        counter_correct += 1

#  adding id to each row
final = []
idEval = 1
for (a, b, c, d, e, f, g, h, i, j, k, l, m, n) in annotated_data:
    final.append((idEval, a, b, c, d, e, f, g, h, i, j, k, l, m, n))
    idEval += 1

print("Evaluated terms: ", total)
print("Correct terms: ", counter_correct)
print("Wrong/omitted terms: ", counter_wrong)
print("LexTermEval score: ", (counter_correct / total) * 100)

#  exporting as TSV file
with open(output, "w", encoding="utf-8") as out:
    tsv_writer = csv.writer(out, delimiter='\t', lineterminator='\n')
    tsv_writer.writerow(
        ["ID", "sentenceID", "source", "reference", "hypothesis", "source_lemmatised", "reference_lemmatised",
         "hypothesis_lemmatised", "conceptID", "terms", "matched_term_source",
         "matched_term_hypothesis", "C/W", "Sprachgebrauch", "tag"])
    for (a, b, c, d, e, f, g, h, i, j, k, l, m, n, o) in final:
        tsv_writer.writerow([a, b, c, d, e, f, g, h, i, j, k, l, m, n, o])

print("Done.")
