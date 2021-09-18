"""
Treetagger lemmatiser
"""
import treetaggerwrapper

input = r""
output_lemmatised = r""

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
for text in textLines:
    lemmatised_text = lemmatise(text, "de")
    textLemma.append(lemmatised_text)
with open(output_lemmatised, "w", encoding="utf-8") as lemmatised:
    lemmatised.write("\n".join(textLemma))




