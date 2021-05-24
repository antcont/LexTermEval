'''
script for sentence tokenization and detokenization (using the TreeTagger)
this is needed in order to have all sentences of the test set (non lemmatised vs lemmatised) with the same tokenization
in order to allow retrieving matched terms between non-lemmatised and lemmatised sentences using match span position

the script also creates the final test set file
id - src - ref - src_lemma - ref_lemma



'''
import treetaggerwrapper

input_totokenize = r"C:\Users\anton\Documents\Documenti importanti\SSLMIT FORLI M.A. SPECIALIZED TRANSLATION 2019-2021\tesi\Evaluation (Automatic + Manual)\testset+reference_2000_1 - Copia_todetokenize.txt"
input_lemmatised = r"C:\Users\anton\Documents\Documenti importanti\SSLMIT FORLI M.A. SPECIALIZED TRANSLATION 2019-2021\tesi\Evaluation (Automatic + Manual)\testset+reference_2000_1_lemmatised_TreeTagger.txt"
output_detokenized = r"C:\Users\anton\Documents\Documenti importanti\SSLMIT FORLI M.A. SPECIALIZED TRANSLATION 2019-2021\tesi\Evaluation (Automatic + Manual)\testset+reference_2000_1 - detokenized.txt"


def tokenize_detokenize(text, lang):
    tagger = treetaggerwrapper.TreeTagger(TAGLANG=lang)
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


with open(input_totokenize, "r", encoding="utf-8") as inputText:
    textLines = inputText.read().splitlines()

with open(input_lemmatised, "r", encoding="utf-8") as x:
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

#  check lengths
if not len(src) == len(ref) == len(src_lemma) == len(ref_lemma):
    print("An error occurred. Different sentence length between source and reference.")
    #exit()

output_list = []
for i in range(len(src)):
    output_list.append("%s\t%s\t%s\t%s\t%s" % (i, src[i], ref[i], src_lemma[i], ref_lemma[i]))
    print("%s\t%s\t%s\t%s\t%s" % (i, src[i], ref[i], src_lemma[i], ref_lemma[i]))

with open(output_detokenized, "w", encoding="utf-8") as out:
    out.write("\n".join(output_list))

print("Done.")