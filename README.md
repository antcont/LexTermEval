# LexTermEval
## Automatic legal terminology evaluation for South Tyrolean German

- `xml2dict.py`:   	Converting termbase (MultiTermXML export file) to python data structure for terminology evaluation (LexTermEval.py)

- `LexTermEval.py`:   Fine-grained automatic evaluation of legal terminology in MT output




Given a test set of source-reference sentence pairs, respective MT hypothesis sentences and a MultiTermXML export file:
- Termbase pre-processing
  - convert termbase (MultiTermXML export file) to python data structure (`xml2dict.py`)
  - lemmatise converted termbase data structures (`lemmatiser_termlist_TT.py`)
- Dataset pre-processing
  - lemmatise source-sentence-hypothesis sentences (`lemmatisation_TreeTagger.py`)
  - tokenize original source-sentence-hypothesis sentences and assemble testset for terminology evaluation (`tokenize.py`)
- Terminology evaluation
  - `LexTermEval.py`
- Evaluate LexTermEval precision
  - `precision_evaluation.py`
