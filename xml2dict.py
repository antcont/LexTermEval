'''
xml2dict.py

- Converting termbase export file (MultitermXML) to dict for use in LexTermEval.py
- converting tags and adding missing tags
- exporting converted termbase with tags as "TB_full.pkl"
- exporting converted termbase without tags (id-termsIT-termsDE) for matching as "TB_m.pkl"


Format of "TB_full.pkl":
Dictionary with key = Bistro entry ID and value = bi-tuple of it-de,
with it-de each a dictionary with key=term and value = a tuple of (status termine, status Bistro Ita) for italian
and ([Sprachgebrauch], Termstatus, status Bistro DE) for German. If attribute not present, assign "NA" for now

Ex.:
{
    '28629': ({'immunità di gregge': ('NA', 'NA'),
               'immunità di comunità': ('NA', 'NA'),
               'immunità di gruppo': ('NA', 'NA')},
              {'Herdenimmunität': (['Südtirol', 'AT', 'DE', 'CH'], 'CNS', 'NA'),
               'Herdenschutz': (['Südtirol', 'AT', 'DE', 'CH'], 'CNS', 'NA')})
}
'''

from lxml import etree
import pickle

termbaseExport = r""  # path to MultiTerm export file (filtered with only needed tags)

blacklist = (   # set of IDs of terms to not be added to final termbase
    "14678",  # Sinn = senso
)


tree = etree.parse(termbaseExport)                 # parsing the XML file
root = tree.getroot()
body = root.find("mtf")

#  building termbase data structure
termBase = {}

#  counters for stats about the tb used for evaluation
counter_noAA = 0
counter_standardised_AA = 0
counter_italian_terms = 0
counter_AA_terms = 0
counter_german_terms = 0


for conceptGrp in root.iter("conceptGrp"):         # iterating over each concept in the TB
    ID = conceptGrp.find("concept").text           # getting concept ID from the <concept> child element
    if ID in blacklist:
        continue      # discarding blacklisted terms
    languageGrp = conceptGrp.findall("languageGrp")
    languageGrpIT = languageGrp[0]      # the first language is Italian
    languageGrpDE = languageGrp[1]      # the second is German
    termIT_dict = {}
    for termGrp in languageGrpIT.findall("termGrp"):       # iterating over Italian terms in entry
        termIT = termGrp.find('term')
        termIT_text = termIT.text                 # getting the IT term
        if len(termIT_text) == 1:
            continue                    # removing terms composed by only one letter (ex. "e" in 27507)
        statusTermine = "NA"
        statusBistroITA = "NA"
        termFields = termGrp.findall("descripGrp")
        for termfield in termFields:
            try:
                statusTermine = termfield.find('descrip[@type="Status termine"]').text      # getting Status termine
            except:
                pass
            try:
                statusBistroITA = termfield.find('descrip[@type="Status bistro ITA"]').text  # getting Status bistro ITA
            except:
                pass

        termIT_dict[termIT_text] = (statusTermine, statusBistroITA)


    termDE_dict = {}
    for termGrp in languageGrpDE.findall("termGrp"):
        termDE = termGrp.find('term')
        termDE_text = termDE.text               # getting the DE term
        if termDE_text == "landes…":
            termDE_text = "landes"      # "correcting" entry "provinciale" = "landes..."/"provinzial"
        sprachgebrauch = "NA"
        termStatus = "NA"
        statusBistroDEU = "NA"
        termFields = termGrp.findall("descripGrp")
        for termfield in termFields:
            try:
                sprachgebrauch = termfield.find('descrip[@type="Sprachgebrauch"]').text  # getting Sprachgebrauch
                try:
                    sprachgebrauch = sprachgebrauch.split("|")
                except:
                    pass
            except:
                pass
            try:
                termStatus = termfield.find('descrip[@type="Termstatus"]').text     # getting Termstatus
            except:
                pass
            try:
                statusBistroDEU = termfield.find('descrip[@type="Status bistro DEU"]').text  # getting Status bistro DEU
            except:
                pass

        if termStatus == "Südtirol genormt":
            counter_standardised_AA += 1
        termDE_dict[termDE_text] = (sprachgebrauch, termStatus, statusBistroDEU)

    termDE_dict_new = {}
    # adding missing tags according to Termstatus tag (genormt, empfohlen, Übersetzungsvorschlag, NA)
    status = set()
    for de_term, (spr, deStatus, deStatusBistro) in termDE_dict.items():
        status.add(deStatus)

    if "Südtirol genormt" in status:                             # handling entries with standardised terms
        for de_term, (spr, deStatus, deStatusBistro) in termDE_dict.items():
            if "Südtirol" in spr and deStatus == "Südtirol genormt":           # South Tyrol standardised terms
                deStatus = "CS"                                     # overwrite "Südtirol genormt" with CS tag
            elif "Südtirol" in spr and deStatus == "NA":           # South Tyrol variants of standardised terms
                deStatus = "ANS"                                    # assign ANS tag
            elif "Südtirol" not in spr:                            # terms from other legal systems
                deStatus = "NST-S"                                  # assing NST-S tag
            termDE_dict_new[de_term] = (spr, deStatus, deStatusBistro)

    elif "in Südtirol empfohlen" in status:                    # handling entries with recommended terms
        for de_term, (spr, deStatus, deStatusBistro) in termDE_dict.items():
            if "Südtirol" in spr and deStatus == "in Südtirol empfohlen":       # South Tyrol recommended terms
                deStatus = "CS"                                     # overwrite "in Südtirol empfohlen" with CS tag
            elif "Südtirol" in spr and deStatus == "NA":         # South Tyrol variants of recommended terms
                deStatus = "ANS"                                    # assign ANS tag
            elif "Südtirol" not in spr:                        # terms from other legal systems
                deStatus = "NST-S"                                  # assign NST-S tag
            termDE_dict_new[de_term] = (spr, deStatus, deStatusBistro)

    else:
        # handling entries with NO standardised/recommended terms;
        # also translation proposals (Übersetzungsvorschlag) fall in this group
        for de_term, (spr, deStatus, deStatusBistro) in termDE_dict.items():
            if "Südtirol" in spr and deStatus == "NA":         # South Tyrol terms
                deStatus = "CNS"                                    # assign CNS tag
            elif "Südtirol" not in spr:                        # terms from other legal systems
                deStatus = "NST-NS"                                 # assign NST-NS tag
            termDE_dict_new[de_term] = (spr, deStatus, deStatusBistro)


    # defensive: check len differences between old and modified dict
    if len(termDE_dict) != len(termDE_dict_new):
        print("Different lengths...!")
        print(termDE_dict)
        print(termDE_dict_new)

    # filtering out entries with no terms with Sprachgebrauch="Südtirol" tag
    laender = set()
    for de_term, (spr, deStatus, deStatusBistro) in termDE_dict_new.items():
        for land in spr:
            laender.add(land)           # adding all Länders from Sprachgebrauch to a set
    if "Südtirol" not in laender:       # if entry does only contain non-South-Tyrol terms, discard
        counter_noAA += 1
        continue    # discarding

    termBase[ID] = (termIT_dict, termDE_dict_new)       # adding entry to the final termbase dictionary


#  counting Italian and German terms
for id, (it, de) in termBase.items():
    for it_term in it.items():
        counter_italian_terms += 1
    for de_term in de.items():
        counter_german_terms += 1


#  exporting full TB with tags as "TB_full.pkl" to be used in LexTermEval.py
with open(r"TB_full.pkl", "wb") as file:
    pickle.dump(termBase, file)


#  converting to reduced TB (id-termsIT-termsDE) for matching purposes (only AA terms)
#  {id:([termsIT], [termsAA])}
TB_PhraseMatcher = {}
for id, (italian, german) in termBase.items():
    it_terms = []
    for it_term, (itStatus, itStatusBistro) in italian.items():
        it_terms.append(it_term)
    de_terms = []
    for de_term, (spr, deStatus, deStatusBistro) in german.items():
        if "Südtirol" in spr:
            de_terms.append(de_term)        # appending only South Tyrol terms
            counter_AA_terms += 1
    TB_PhraseMatcher[id] = (it_terms, de_terms)


#  export as "TB_m.pkl"
with open(r"TB_m.pkl", "wb") as file:
    pickle.dump(TB_PhraseMatcher, file)


print("Total entries in TB: ", len(termBase))
print("Total Italian terms in TB: ", counter_italian_terms)
print("Total South Tyrolean German terms in TB: ", counter_AA_terms)
print("Total German terms in TB: ", counter_german_terms)
print("Total terms in TB: ", counter_italian_terms + counter_german_terms)
print("Entries discarded (South Tyrol term missing): ", counter_noAA)

