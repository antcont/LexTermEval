'''
Lemmatiser for term list (id-italian terms-german terms) => TB_full.pkl
'''
import treetaggerwrapper
import pickle

input = r"...\TB_full.pkl"
output_lemmatised = r"...\TB_full_lemmatised.pkl"

tagger_it = treetaggerwrapper.TreeTagger(TAGLANG="it")
tagger_de = treetaggerwrapper.TreeTagger(TAGLANG="de")


def lemmatise(text, lang):
    if lang == "it":
        tagger = tagger_it
    elif lang == "de":
        tagger = tagger_de
    tags = tagger.tag_text(text)
    mytags = treetaggerwrapper.make_tags(tags, exclude_nottags=True)
    lemma_list = []
    for tag in mytags:
        lemma = tag.lemma
        if lemma == "essere|stare" or (lemma == "essere" and len(text.split(" ")) == 1):
            try:
                lemma = tag.word        # reverting to wordform instead of lemma
                print("Correcting lemmatisation error: ", tag.lemma, "->", tag.word)        #todo: remove after testing
            except AttributeError:
                # if NoTag, ignore
                continue
        try:
            lemma_list.append(lemma)
        except AttributeError:
            # if NoTag, ignore
            continue
    return " ".join(lemma_list)


with open(input, "rb") as inputText:
    tb = pickle.load(inputText)

len_tb = len(tb)
counter = 0
print("\n\n\n\n\n")


terms_lemmatised = {}
for id, (itTerms, deTerms) in tb.items():
    counter += 1
    terms_lemmatised[id] = ([lemmatise(x, "it") for x in itTerms], [lemmatise(x, "de") for x in deTerms])
    print("\r", "%i/%i" % (counter, len_tb), end="")

with open(output_lemmatised, "wb") as output:
    pickle.dump(terms_lemmatised, output)

