'''
Creating the test set for LexTermEval.py.
Source-reference-hypothesis sentences are kept both in lemmatised (for matching) and tokenized form.
this is needed in order to have all sentences of the test set (non lemmatised vs lemmatised) with the same tokenization
in order to allow retrieving matched terms between non-lemmatised and lemmatised sentences using match span position

Output: tab-separated test set file -->
id - src_tokenised - ref_tokenised - hyp_tokenised - src_lemma - ref_lemma - hyp_lemma

'''
import treetaggerwrapper

src = r"path\to\original\source\test-set"
ref = r"path\to\original\reference\set"
hyp = r"path\to\original\reference\set"
output_testset = r"path\to\output\testset\for\LexTermEval"

#  instantiating taggers for each language
tagger_it = treetaggerwrapper.TreeTagger(TAGLANG="it")
tagger_de = treetaggerwrapper.TreeTagger(TAGLANG="de")


def tokenize(text, lang):
    if lang == "it":
        tagger = tagger_it
    elif lang == "de":
        tagger = tagger_de
    tags = tagger.tag_text(text)
    mytags = treetaggerwrapper.make_tags(tags)
    tokenized_list = []
    for tag in mytags:
        try:
            tokenized_list.append(tag.word)
        except AttributeError:
            # if NoTag, ignore
            continue
    return " ".join(tokenized_list)


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


#  open data to tokenize and lemmatize
with open(src, "r", encoding="utf-8") as src_:
    src_t = src_.read().splitlines()
with open(ref, "r", encoding="utf-8") as ref_:
    ref_t = ref_.read().splitlines()
with open(hyp, "r", encoding="utf-8") as hyp_:
    hyp_t = hyp_.read().splitlines()


#  check lengths
if not len(src_t) == len(ref_t) == len(hyp_t):
    print("An error occurred. Different sentence length between source and reference.")
    exit()

#  tokenizing
tok_src = []
for line in src_t:
    tok_src.append(tokenize(line, "it"))

tok_ref = []
for line in ref_t:
    tok_ref.append(tokenize(line, "de"))

tok_hyp = []
for line in hyp_t:
    tok_hyp.append(tokenize(line, "de"))


# lemmatising
src_l = []
for line in src_t:
    src_l.append(lemmatise(line, "it"))

ref_l = []
for line in ref_t:
    ref_l.append(lemmatise(line, "de"))

hyp_l = []
for line in hyp_t:
    hyp_l.append(lemmatise(line, "de"))



#  writing test set output file
testset_out = []
for i in range(len(src_t)):
    row = "%s\t%s\t%s\t%s\t%s\t%s\t%s" % (i+1, tok_src[i], tok_ref[i], tok_hyp[i], src_l[i], ref_l[i],
                                          hyp_l[i])
    testset_out.append(row)
    #print(row)


with open(output_testset, "w", encoding="utf-8") as out:
    out.write("\n".join(testset_out))

print("Done.")
