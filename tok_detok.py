'''
script for sentence tokenization and detokenization (using the TreeTagger)
this is needed in order to have all sentences of the test set (non lemmatised vs lemmatised) with the same tokenization
in order to allow retrieving matched terms between non-lemmatised and lemmatised sentences using match span position

The script tokenizes and detokenizes the non-lemmatised sentences and creates the final test set file
id - src - ref - hyp - src_lemma - ref_lemma - hyp_lemma



'''
import treetaggerwrapper

src_totokenize = r"C:\Users\anton\Documents\Documenti importanti\SSLMIT FORLI M.A. SPECIALIZED TRANSLATION 2019-2021\tesi\Evaluation (Automatic + Manual)\Esperimento definitivo tesi\NEW_source_2000.txt"
ref_totokenize = r"C:\Users\anton\Documents\Documenti importanti\SSLMIT FORLI M.A. SPECIALIZED TRANSLATION 2019-2021\tesi\Evaluation (Automatic + Manual)\Esperimento definitivo tesi\NEW_reference_2000.txt"
hyp_totokenize = r"C:\Users\anton\Documents\Documenti importanti\SSLMIT FORLI M.A. SPECIALIZED TRANSLATION 2019-2021\tesi\Evaluation (Automatic + Manual)\Esperimento definitivo tesi\NEW_translated_2000_custom4a+termini.txt"
src_lemma = r"C:\Users\anton\Documents\Documenti importanti\SSLMIT FORLI M.A. SPECIALIZED TRANSLATION 2019-2021\tesi\Evaluation (Automatic + Manual)\Esperimento definitivo tesi\NEW_source_2000_lemmatised.txt"
ref_lemma = r"C:\Users\anton\Documents\Documenti importanti\SSLMIT FORLI M.A. SPECIALIZED TRANSLATION 2019-2021\tesi\Evaluation (Automatic + Manual)\Esperimento definitivo tesi\NEW_reference_2000_lemmatised.txt"
hyp_lemma = r"C:\Users\anton\Documents\Documenti importanti\SSLMIT FORLI M.A. SPECIALIZED TRANSLATION 2019-2021\tesi\Evaluation (Automatic + Manual)\Esperimento definitivo tesi\NEW_translated_2000_custom4a+termini_lemmatised.txt"
output_testset = r"C:\Users\anton\Documents\Documenti importanti\SSLMIT FORLI M.A. SPECIALIZED TRANSLATION 2019-2021\tesi\Evaluation (Automatic + Manual)\Esperimento definitivo tesi\NEW_testSet_custom4a+terminology_LexTermEval.txt"

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
    print(row)




'''with open(input_lemmatised, "r", encoding="utf-8") as x:
    textLemma =x.read().splitlines()

src = []
src_lemma = []
ref = []
ref_lemma = []

for line in textLines:
    (src_, ref_) = line.split("\t")
    src.append(tokenize_detokenize(src_, "it"))
    ref.append(tokenize_detokenize(ref_, "de"))

for line in textLemma:
    (srcL, refL) = line.split("\t")
    src_lemma.append(srcL)
    ref_lemma.append(refL)



output_list = []
for i in range(len(src)):
    output_list.append("%s\t%s\t%s\t%s\t%s" % (i, src[i], ref[i], src_lemma[i], ref_lemma[i]))
    print("%s\t%s\t%s\t%s\t%s" % (i, src[i], ref[i], src_lemma[i], ref_lemma[i]))

'''


with open(output_testset, "w", encoding="utf-8") as out:
    out.write("\n".join(testset_out))

print("Done.")
