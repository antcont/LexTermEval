"""

"""
import treetaggerwrapper
from HanTa import HanoverTagger as ht
import spacy
nlp = spacy.load("de_core_news_lg")



terms = r"C:\Users\anton\Documents\Documenti importanti\SSLMIT FORLI M.A. SPECIALIZED TRANSLATION 2019-2021\tesi\Evaluation (Automatic + Manual)\prove_terms_it-de.txt"
terms_lemma = r"C:\Users\anton\Documents\Documenti importanti\SSLMIT FORLI M.A. SPECIALIZED TRANSLATION 2019-2021\tesi\Evaluation (Automatic + Manual)\prove_terms_it-de_lemmatised_HanTa.txt"

tagger = ht.HanoverTagger('morphmodel_ger.pgz')


def lemmatise_it(text):
    tagger = treetaggerwrapper.TreeTagger(TAGLANG="it")
    tags = tagger.tag_text(text)
    mytags = treetaggerwrapper.make_tags(tags, allow_extra=True)
    lemma_list = []
    for tag in mytags:
        try:
            lemma_list.append(tag.lemma)
        except AttributeError:
            # if NoTag, ignore
            continue
    return " ".join(lemma_list)

def lemmatise_de(sent):
    """
    lemmatising using HanTa
    """
    doc = nlp(sent, disable=['parser', 'ner'])  # parse the text with SpaCy for tokenization
    lemmatised = []
    for word in doc:
        lemmatised.append(tagger.analyze(str(word))[0])  # lemmatising with HanTa
    lemmatised_sent = " ".join(lemmatised)
    return lemmatised_sent


#  importing list of it-de terms
with open(terms, "r", encoding="utf-8") as termList:
    termList_raw = termList.read().splitlines()
    termList = []
    for term_term in termList_raw:
        lemmas_it = lemmatise_it(term_term.split("\t")[0])
        lemmas_de = lemmatise_de(term_term.split("\t")[1])
        print(lemmas_de)
        termList.append("%s\t%s" % (lemmas_it, lemmas_de))


print(termList)

with open(terms_lemma, "w", encoding="utf-8") as lemmatised:
    lemmatised.write("\n".join(termList))





