# LexTermEval
## Automatic legal terminology evaluation for South Tyrolean German


Given a test set of source-reference sentence pairs, respective MT hypothesis sentences and a MultiTermXML export file:
- Termbase pre-processing
  - converting termbase (MultiTermXML export file) to python data structure for reference in terminology evaluation (`xml2dict.py`)
  - lemmatising converted termbase data structures (`lemmatiser_termlist_TT.py`)
- Dataset pre-processing
  - lemmatising source-sentence-hypothesis sentences (`lemmatisation_TreeTagger.py`)
  - tokenizing original source-sentence-hypothesis sentences and assembling testset for terminology evaluation (`tokenize.py`)
- Terminology evaluation
  - `LexTermEval.py`: fine-grained automatic evaluation of legal terminology in MT output
- Evaluating LexTermEval precision
  - `precision_evaluation.py`
