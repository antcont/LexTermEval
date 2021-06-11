"""

"""
import treetaggerwrapper

input = r"C:\Users\anton\Documents\Documenti importanti\SSLMIT FORLI M.A. SPECIALIZED TRANSLATION 2019-2021\tesi\Evaluation (Automatic + Manual)\mmt_baseline_1.txt"
output_lemmatised = r"C:\Users\anton\Documents\Documenti importanti\SSLMIT FORLI M.A. SPECIALIZED TRANSLATION 2019-2021\tesi\Evaluation (Automatic + Manual)\mmt_baseline_1_lemmatised.txt"

tagger_it = treetaggerwrapper.TreeTagger(TAGLANG="it")
tagger_de = treetaggerwrapper.TreeTagger(TAGLANG="de")


def lemmatise_old(sent, lang):
    if lang == "it":
        tagger = tagger_it
    elif lang == "de":
        tagger = tagger_de
    tags = tagger.tag_text(sent)
    tags2 = treetaggerwrapper.make_tags(tags, allow_extra=True)
    lemmatised_sent = " ".join([item.lemma for item in tags2])
    return lemmatised_sent


def lemmatise(text, lang):
    if lang == "it":
        tagger = tagger_it
    elif lang == "de":
        tagger = tagger_de
    tags = tagger.tag_text(text)
    mytags = treetaggerwrapper.make_tags(tags, exclude_nottags=True)
    lemma_list = []
    for tag in mytags:
        try:
            lemma_list.append(tag.lemma)
        except AttributeError:
            # if NoTag, ignore
            continue
    return " ".join(lemma_list)


with open(input, "r", encoding="utf-8") as inputText:
    textLines = inputText.read().splitlines()

textLemma = []
for it_de in textLines:
    lemmas_de = lemmatise(it_de, "de")
    textLemma.append(lemmas_de)
with open(output_lemmatised, "w", encoding="utf-8") as lemmatised:
    lemmatised.write("\n".join(textLemma))

    """
    '''textLemma = []
    for it_de in textLines:
        lemmas_it = lemmatise((it_de.split("\t")[0]), "it")
        lemmas_de = lemmatise((it_de.split("\t")[1]), "de")
        textLemma.append("%s\t%s" % (lemmas_it, lemmas_de))'''
    it_de = []
    for biterm in textLines:
        it_de.append(tuple(biterm.split("\t")))  # creating list of tab-separated ID-ItTerms-DeTerms
    id_terms = {}
    for (id, termsIt, termsDe) in it_de:
        termsIt = [lemmatise(x, "it") for x in termsIt.split("|")]
        termsDe = [lemmatise(x, "de") for x in termsDe.split("|")]

        id_terms[id] = (termsIt, termsDe)



'''with open(output_lemmatised, "w", encoding="utf-8") as lemmatised:
    lemmatised.write("\n".join(textLemma))'''

export_as_text = []
for id, (it, de) in id_terms.items():
    it_terms = []
    de_terms = []
    for itterm in it:
        it_terms.append(itterm)
    for determ in de:
        de_terms.append(determ)
    export_as_text.append("%s\t%s\t%s" % (id, "|".join(it_terms), "|".join(de_terms)))

with open(output_lemmatised, "w", encoding="utf-8") as exp:
    exp.write("\n".join(export_as_text))
"""



