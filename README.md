# LexTermEval
## Automatic legal terminology evaluation for South Tyrolean German


Given a test set of source-reference sentence pairs, respective MT hypothesis sentences and a MultiTermXML export file:
- Termbase pre-processing
  - converting termbase (MultiTermXML export file) to python data structure for reference in terminology evaluation (`xml2dict.py`)
- Dataset pre-processing
  - pre-processing the dataset and creating final testset file (`create-testset.py`)
- Terminology evaluation
  - fine-grained automatic evaluation of legal terminology in MT output `LexTermEval.py`
- Evaluating LexTermEval precision
  - creating a tab-separated file for manual evaluation of LexTermEval precision `precision_evaluation.py`
