'''
- Converting tb export file (MultitermXML) to dictionary
- converting and adding missing tags
- exporting as list of separated strings for re-use

Format:
dictionary with key=ID and value = bi-tuple of it-de,
with it-de each a dictionary with key=term and value = a tuple of (status termine, status Bistro Ita) for italian
and ([Sprachgebrauch], Termstatus, status Bistro DE) for German. If attribute not present, assign "NA" for now

Ex.


{
    '28629': ({'immunità di gregge': ('NA', 'NA'),
               'immunità di comunità': ('NA', 'NA'),
               'immunità di gruppo': ('NA', 'NA')},
              {'Herdenimmunität': (['Südtirol', 'AT', 'DE', 'CH'], 'CNS', 'NA'),
               'Herdenschutz': (['Südtirol', 'AT', 'DE', 'CH'], 'CNS', 'NA')})
}


export list of strings format:
\t = between ID, italian termgroup, german termgroup
||| = between single terms
|| = between term and attributes
| = between attributes
; = between single tags in Sprachgebrauch

'''

from lxml import etree

termbaseExport = r"C:\Users\anton\Documents\Documenti importanti\Eurac\tirocinio avanzato per tesi 2021\esporti Bluterm\esporto_Bistro_da_Bistrolocale13k.xml"

tree = etree.parse(termbaseExport)                 # parsing the TMX file
root = tree.getroot()
body = root.find("mtf")

#  building termbase data structure
termBase = {}
counter_noAA = 0

for conceptGrp in root.iter("conceptGrp"):         # iterating over each concept in the TB
    ID = conceptGrp.find("concept").text           # getting concept ID, which is in the <concept> child element
    #print(ID)
    languageGrp = conceptGrp.findall("languageGrp")
    languageGrpIT = languageGrp[0]      # the first language is Italian
    languageGrpDE = languageGrp[1]      # the second is German
    termIT_dict = {}
    for termGrp in languageGrpIT.findall("termGrp"):       # iterating over Italian terms in entry
        termIT = termGrp.find('term')
        termIT_text = termIT.text                 # getting the IT term
        statusTermine = "NA"
        statusBistroITA = "NA"
        termFields = termGrp.findall("descripGrp")
        for termfield in termFields:
            try:
                statusTermine = termfield.find('descrip[@type="Status termine"]').text      # getting Status termine
            except:
                pass
            try:
                statusBistroITA = termfield.find('descrip[@type="Status bistro ITA"]').text  # getting Status bistro DEU
            except:
                pass

        termIT_dict[termIT_text] = (statusTermine, statusBistroITA)

    termDE_dict = {}
    for termGrp in languageGrpDE.findall("termGrp"):
        termDE = termGrp.find('term')
        termDE_text = termDE.text               # getting the DE term
        sprachgebrauch = "NA"
        termStatus = "NA"
        statusBistroDEU = "NA"
        termFields = termGrp.findall("descripGrp")
        for termfield in termFields:
            try:
                sprachgebrauch = termfield.find('descrip[@type="Sprachgebrauch"]').text
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
                deStatus = "ANS_C"                                  # assign ANS_C tag
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
        # handling entries with no standardised/recommended terms;
        # also translation proposals (Übersetzungsvorschlag) fall in this group
        for de_term, (spr, deStatus, deStatusBistro) in termDE_dict.items():
            if "Südtirol" in spr and deStatus == "NA":         # South Tyrol terms
                deStatus = "CNS"                                    # assign CNS tag
            elif "Südtirol" not in spr:                        # terms from other legal systems
                deStatus = "NST-NS"                                 # assign NST-NS tag
            termDE_dict_new[de_term] = (spr, deStatus, deStatusBistro)

    # check len differences between old and modified dict
    if len(termDE_dict) != len(termDE_dict_new):
        print("Different lengths... ")
        print(termDE_dict)
        print(termDE_dict_new)

    # filtering out entries with no term with Sprachgebrauch="Südtirol" tag
    laender = set()
    for de_term, (spr, deStatus, deStatusBistro) in termDE_dict_new.items():
        for land in spr:
            laender.add(land)           # adding all Länders from Sprachgebrauch to a set
    if "Südtirol" not in laender:       # if entry does only contain non-South-Tyrol terms, discard
        counter_noAA += 1
        #print("Discarding entry because of missing South Tyrol terms.")
        #print(ID)       # printing ID to check
        continue    # discarding


    termBase[ID] = (termIT_dict, termDE_dict_new)       # adding entry to the final termbase dictionary


#  converting dict to list of strings for export
def dict2tb_string(dictTB):
    export_as_text = []
    for id, (italian, german) in dictTB.items():
        it_term_attr = []
        for it_term, (itStatus, itStatusBistro) in italian.items():
            it_term_attr.append("%s||%s|%s" % (it_term, itStatus, itStatusBistro))
        de_term_attr = []
        for de_term, (spr, deStatus, deStatusBistro) in german.items():
            de_term_attr.append("%s||%s|%s|%s" % (de_term, ";".join(spr), deStatus, deStatusBistro))
        export_as_text.append("%s\t%s\t%s" % (id, "|||".join(it_term_attr), "|||".join(de_term_attr)))
    print("Number of entries in TB: ", len(export_as_text))
    return "\n".join(export_as_text)

termbase_out = dict2tb_string(termBase)

#  exporting to txt file for re-use
with open("LexTB_full.txt", "w", encoding="utf-8") as txt:
    txt.write(termbase_out)


#  converting to list of id-termsIT-termsDE for Spacy's PhraseMatcher in LexTerm.py
#  todo: remember to lemmatise it before loading to LexTerm.py!
#  export_format: id(TABSEPARATOR)italianTerm(PIPESEPARATOR)italianTerm(TABSEPARATOR)germanTerm...

def dict2tb_string_reduced(dictTB):
    export_as_text = []
    for id, (italian, german) in dictTB.items():
        it_terms = []
        for it_term, (itStatus, itStatusBistro) in italian.items():
            it_terms.append(it_term)
        de_terms = []
        for de_term, (spr, deStatus, deStatusBistro) in german.items():
            de_terms.append(de_term)
        export_as_text.append("%s\t%s\t%s" % (id, "|".join(it_terms), "|".join(de_terms)))
    return "\n".join(export_as_text)

tb_PhraseMatcher = dict2tb_string_reduced(termBase)

#  exporting to txt file for re-use in LexTerm.py
with open("LexTB_id-terms.txt", "w", encoding="utf-8") as txt:
    txt.write(tb_PhraseMatcher)

#print(tb_PhraseMatcher)
#print(termBase)
print("Entries discarded (South Tyrol term missing): ", counter_noAA)
#print(termbase_out)


