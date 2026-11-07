"""Language detection and the fixed bilingual texts (disclaimer, refusals, labels).

Fixed texts live here, in code, so safety-critical wording (disclaimer, 'not enough
information') is never left to the language model to improvise.
"""
import re

_DEVANAGARI = re.compile(r"[ऀ-ॿ]")
_LATIN = re.compile(r"[A-Za-z]")


def detect_language(text: str) -> str:
    """'hi' if Devanagari letters outnumber Latin letters, else 'en'."""
    hi, en = len(_DEVANAGARI.findall(text)), len(_LATIN.findall(text))
    return "hi" if hi > en else "en"


LANGUAGE_NAMES = {"en": "English", "hi": "Hindi"}

DISCLAIMER = {
    "en": ("This is general legal information drawn from the documents available to this system. "
           "It is not legal advice and may be incomplete or out of date. Please consult a qualified "
           "advocate for advice on your situation."),
    "hi": ("यह इस प्रणाली में उपलब्ध दस्तावेज़ों पर आधारित सामान्य कानूनी जानकारी है। यह कानूनी सलाह नहीं है और "
           "अधूरी या पुरानी हो सकती है। अपनी स्थिति के लिए कृपया किसी योग्य अधिवक्ता से परामर्श करें।"),
}

NOT_ENOUGH_INFO = {
    "en": ("I could not find enough information in the available legal documents to answer this reliably. "
           "Try rephrasing, naming the Act or section, or ask about the Constitution of India, BNS, BNSS, BSA, "
           "the IT Act 2000 or the Consumer Protection Act 2019."),
    "hi": ("उपलब्ध कानूनी दस्तावेज़ों में इस प्रश्न का भरोसेमंद उत्तर देने के लिए पर्याप्त जानकारी नहीं मिली। कृपया प्रश्न "
           "दूसरे शब्दों में पूछें, अधिनियम या धारा का नाम बताएँ, या भारत का संविधान, BNS, BNSS, BSA, आईटी अधिनियम 2000 "
           "अथवा उपभोक्ता संरक्षण अधिनियम 2019 के बारे में पूछें।"),
}

OCR_LIMITATION = {
    "en": ("The Hindi text of the relevant provision could not be read reliably from the scanned PDF, so I cannot "
           "quote it. Please open the cited page of the original document to read it."),
    "hi": ("संबंधित प्रावधान का हिंदी पाठ स्कैन की गई PDF से भरोसेमंद रूप से नहीं पढ़ा जा सका, इसलिए मैं उसे उद्धृत नहीं कर सकता। "
           "कृपया मूल दस्तावेज़ का उल्लिखित पृष्ठ स्वयं देखें।"),
}

OCR_NOTE = {
    "en": "Note: some cited Hindi text was machine-read (OCR) from a scan and may contain errors. Verify against the original PDF page.",
    "hi": "नोट: उद्धृत हिंदी पाठ का कुछ भाग स्कैन से मशीन द्वारा पढ़ा गया (OCR) है और उसमें त्रुटियाँ हो सकती हैं। मूल PDF पृष्ठ से मिलान करें।",
}

FALLBACK_LANGUAGE_NOTE = {
    "en": "Note: a reliable Hindi text was not available for some provisions, so the English source was used.",
    "hi": "नोट: कुछ प्रावधानों का भरोसेमंद हिंदी पाठ उपलब्ध नहीं था, इसलिए अंग्रेज़ी स्रोत का उपयोग किया गया।",
}

UNVERIFIED_REFERENCE_NOTE = {
    "en": "Warning: the answer mentions {refs}, which is not in the retrieved sources. Treat that reference as unverified.",
    "hi": "चेतावनी: उत्तर में {refs} का उल्लेख है, जो प्राप्त स्रोतों में नहीं है। इस संदर्भ को असत्यापित मानें।",
}

# Notes produced by answer verification. "Verification error" = deterministic evidence of a defect;
# "Check" = a heuristic warning that may be wrong. Warnings are deliberately worded as invitations to check.
VERIFICATION_NOTES = {
    "en": {
        "invalid_citation": "Verification error: the answer cited a source number that does not exist ({detail}); the marker was removed.",
        "unsupported_section_reference": "Verification error: the answer mentions {detail}, which is not in the retrieved sources. Treat that reference as unverified.",
        "quote_not_found": "Verification error: a quotation in this answer was not found in the sources. Do not rely on it.",
        "quote_altered_legal_term": "Verification error: a quotation differs from the source in a legal term ({detail}). Read the source text.",
        "unsupported_existence_claim": ("Verification error: the answer says a law or section does not exist. The documents can only show that it was "
                                        "not found in them, not that it does not exist. Do not rely on that statement."),
        "modal_changed": "Check: the answer may have changed 'shall' to 'may' (or the reverse) compared with the source ({detail}). Read the source wording.",
        "malformed_citation": "Check: the marker {detail} is not in the form [n], so the statement before it is not linked to a source.",
        "quote_not_exact": "Check: a quotation does not match the source word for word.",
        "quote_cited_to_wrong_source": "Check: a quotation appears in a different source from the one cited.",
        "threshold_qualifier_mismatch": "Check: a number or duration is worded differently from the source ({detail}).",
        "number_not_in_sources": "Check: a number or duration in the answer was not found in the sources ({detail}).",
        "miscited_claim": "Check: a statement is cited to a source that matches it only weakly ({detail}).",
        "weak_support": "Check: some sentences add explanation that does not appear in the cited sources. Rely on the source text.",
    },
    "hi": {
        "invalid_citation": "सत्यापन त्रुटि: उत्तर में ऐसे स्रोत की संख्या दी गई जो मौजूद नहीं है ({detail}); उसे हटा दिया गया।",
        "unsupported_section_reference": "सत्यापन त्रुटि: उत्तर में {detail} का उल्लेख है, जो प्राप्त स्रोतों में नहीं है। इसे असत्यापित मानें।",
        "quote_not_found": "सत्यापन त्रुटि: उत्तर का एक उद्धरण स्रोतों में नहीं मिला। उस पर भरोसा न करें।",
        "quote_altered_legal_term": "सत्यापन त्रुटि: एक उद्धरण स्रोत से किसी कानूनी शब्द में भिन्न है ({detail})। स्रोत पाठ पढ़ें।",
        "unsupported_existence_claim": ("सत्यापन त्रुटि: उत्तर कहता है कि कोई कानून या धारा मौजूद नहीं है। दस्तावेज़ केवल यह दिखा सकते हैं कि वह उनमें नहीं मिली, "
                                        "यह नहीं कि वह मौजूद ही नहीं है। इस कथन पर भरोसा न करें।"),
        "modal_changed": "जाँचें: उत्तर में स्रोत की तुलना में 'shall' को 'may' (या उलटा) बदला गया हो सकता है ({detail})। स्रोत का पाठ पढ़ें।",
        "malformed_citation": "जाँचें: चिह्न {detail} [n] रूप में नहीं है, इसलिए उससे पहले का कथन किसी स्रोत से जुड़ा नहीं है।",
        "quote_not_exact": "जाँचें: एक उद्धरण स्रोत से शब्दशः मेल नहीं खाता।",
        "quote_cited_to_wrong_source": "जाँचें: एक उद्धरण उद्धृत स्रोत के बजाय किसी अन्य स्रोत में है।",
        "threshold_qualifier_mismatch": "जाँचें: कोई संख्या या अवधि स्रोत से भिन्न शब्दों में लिखी है ({detail})।",
        "number_not_in_sources": "जाँचें: उत्तर की एक संख्या या अवधि स्रोतों में नहीं मिली ({detail})।",
        "miscited_claim": "जाँचें: एक कथन ऐसे स्रोत से उद्धृत है जो उससे केवल कमज़ोर रूप से मेल खाता है ({detail})।",
        "weak_support": "जाँचें: कुछ वाक्य ऐसी व्याख्या जोड़ते हैं जो उद्धृत स्रोतों में नहीं है। स्रोत पाठ पर भरोसा करें।",
    },
}

ANSWER_INCOMPLETE_NOTE = {
    "en": ("Incomplete answer: the reply was cut off before it finished (it reached the output length limit), so conditions, items or "
           "sentences may be missing. Do not treat it as a complete statement of the law; open the cited source pages or ask a narrower question."),
    "hi": ("अधूरा उत्तर: उत्तर पूरा होने से पहले ही कट गया (आउटपुट की लंबाई-सीमा पूरी हो गई), इसलिए कुछ शर्तें, बिंदु या वाक्य छूट सकते हैं। "
           "इसे कानून का पूर्ण कथन न मानें; उद्धृत स्रोतों के पृष्ठ देखें या प्रश्न को और सीमित करके पूछें।"),
}

PARTIAL_PROVISION_NOTE = {
    "en": "Only parts {parts} of {total} of {label} were available to the model, so anything listed from it may be incomplete. Open the original page for the full text.",
    "hi": "{label} के {total} भागों में से केवल भाग {parts} मॉडल को उपलब्ध थे, इसलिए उससे दी गई कोई भी सूची अधूरी हो सकती है। पूरे पाठ के लिए मूल पृष्ठ खोलें।",
}

HINDI_PAUSED = ("Hindi support is temporarily paused while the Hindi source documents are being verified. "
                "Please ask your question in English. / हिंदी समर्थन अभी अस्थायी रूप से बंद है; कृपया अंग्रेज़ी में पूछें।")

GREETING = {
    "en": ("Hello! I answer questions about Indian law using the Constitution of India, the BNS, BNSS, BSA, "
           "the IT Act 2000 and the Consumer Protection Act 2019, in English or Hindi. What would you like to know?"),
    "hi": ("नमस्ते! मैं भारत का संविधान, BNS, BNSS, BSA, आईटी अधिनियम 2000 और उपभोक्ता संरक्षण अधिनियम 2019 के आधार पर "
           "हिंदी या अंग्रेज़ी में कानूनी प्रश्नों के उत्तर देता हूँ। आप क्या जानना चाहते हैं?"),
}

GREETING_WORDS = {"hi", "hello", "hey", "namaste", "नमस्ते", "नमस्कार", "हेलो", "हैलो", "thanks", "thank you", "धन्यवाद"}


def is_greeting(text: str) -> bool:
    return text.strip().lower().strip("!.? ") in GREETING_WORDS
