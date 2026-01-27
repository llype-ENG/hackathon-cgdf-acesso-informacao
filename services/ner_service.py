#import spacy
#from googletrans import Translator  # ✅ importar Translator

# Inicializa tradutor
#translator = Translator()  # ✅ instancia Translator

# Carrega modelos SpaCy
#nlp_pt = spacy.load("pt_core_news_sm")
#nlp_en = spacy.load("en_core_web_sm")

#def extract_entities_dual(text_pt: str):
#    """
#    Extrai nomes e organizações usando SpaCy PT + SpaCy EN (via tradução)
#    """
#    # PT
#    doc_pt = nlp_pt(text_pt)
#    names = [ent.text for ent in doc_pt.ents if ent.label_ == "PER"]
#    orgs = [ent.text for ent in doc_pt.ents if ent.label_ == "ORG"]

    # EN
    #text_en = translator.translate(text_pt, src="pt", dest="en").text
    #doc_en = nlp_en(text_en)
    #names += [ent.text for ent in doc_en.ents if ent.label_ == "PERSON"]
    #orgs += [ent.text for ent in doc_en.ents if ent.label_ == "ORG"]

    #return list(set(names)), list(set(orgs))
