'''
script for sentence tokenization and detokenization (using the TreeTagger)
this is needed in order to have all sentences of the test set (non lemmatised vs lemmatised) with the same tokenization
in order to allow retrieving matched terms between non-lemmatised and lemmatised sentences using match span position

The script tokenizes and detokenizes the non-lemmatised sentences and creates the final test set file
id - src - ref - hyp - src_lemma - ref_lemma - hyp_lemma

'''
import treetaggerwrapper

src_totokenize = r"path\to\original\source\test-set"
ref_totokenize = r"path\to\original\reference\set"
hyp_totokenize = r"path\to\original\reference\set"
src_lemma = r"path\to\lemmatised\source\test-set"
ref_lemma = r"path\to\lemmatised\reference\set"
hyp_lemma = r"path\to\lemmatised\reference\set"
output_testset = r"path\to\output\testset\for\LexTermEval"

#  instantiating taggers for each language
tagger_it = treetaggerwrapper.TreeTagger(TAGLANG="it")
tagger_de = treetaggerwrapper.TreeTagger(TAGLANG="de")


def tokenize_detokenize(text, lang):
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


#  data to tokenize/detokenize
with open(src_totokenize, "r", encoding="utf-8") as src_tok:
    src_t = src_tok.read().splitlines()
with open(ref_totokenize, "r", encoding="utf-8") as ref_tok:
    ref_t = ref_tok.read().splitlines()
with open(hyp_totokenize, "r", encoding="utf-8") as hyp_tok:
    hyp_t = hyp_tok.read().splitlines()

#  lemmmatised data to append to test set
with open(src_lemma, "r", encoding="utf-8") as src_lemma:
    src_l = src_lemma.read().splitlines()
with open(ref_lemma, "r", encoding="utf-8") as ref_lemma:
    ref_l = ref_lemma.read().splitlines()
with open(hyp_lemma, "r", encoding="utf-8") as hyp_lemma:
    hyp_l = hyp_lemma.read().splitlines()


#  tokenizing / detokenizing
detok_src = []
for line in src_t:
    detok_src.append(tokenize_detokenize(line, "it"))

detok_ref = []
for line in ref_t:
    detok_ref.append(tokenize_detokenize(line, "de"))

detok_hyp = []
for line in hyp_t:
    detok_hyp.append(tokenize_detokenize(line, "de"))

#  check lengths
if not len(src_l) == len(ref_l) == len(hyp_l) == len(detok_src) == len(detok_ref) == len(detok_hyp):
    print("An error occurred. Different sentence length between source and reference.")
    exit()


#  writing test set output file
testset_out = []
for i in range(len(src_t)):
    row = "%s\t%s\t%s\t%s\t%s\t%s\t%s" % (i+1, detok_src[i], detok_ref[i], detok_hyp[i], src_l[i], ref_l[i],
                                          hyp_l[i])
    testset_out.append(row)
    #print(row)


with open(output_testset, "w", encoding="utf-8") as out:
    out.write("\n".join(testset_out))

print("Done.")
