# English RAG test report

Collection: `indian_law_en` | chat model: `qwen3:4b-instruct-2507-q4_K_M` | embeddings: `bge-m3` | top_k=6 | relevance cut-off (max cosine distance)=0.65

**9 of 22 cases passed every automatic check.**

| Id | Category | Question | Status | Best dist | Retrieval | Total latency | Verdict |
|---|---|---|---|---|---|---|---|
| E1 | Exact lookup | What does Article 21 of the Constitution say? | answered | 0.421 | 5.82s | 62.41s | PASS |
| E2 | Exact lookup | Explain Article 14 of the Constitution. | answered | 0.399 | 2.15s | 63.61s | **REVIEW** |
| E3 | Exact lookup | What is Section 103 of the BNS? | answered | 0.471 | 2.16s | 61.4s | PASS |
| E4 | Exact lookup | What does Section 63 of the Bharatiya Sakshya Adhiniyam provide? | answered | 0.39 | 2.18s | 122.25s | PASS |
| E5 | Exact lookup | What does Section 35 of the BNSS provide? | answered | 0.521 | 2.2s | 152.46s | **REVIEW** |
| E6 | Exact lookup | What is Section 66C of the IT Act? | answered | 0.404 | 2.17s | 44.87s | **REVIEW** |
| E7 | Exact lookup | What does Section 35 of the Consumer Protection Act say? | answered | 0.319 | 2.16s | 82.95s | **REVIEW** |
| E8 | Exact lookup (nonexistent) | What does Section 999 of the BNS say? | answered | 0.535 | 2.23s | 59.26s | **REVIEW** |
| S1 | Semantic | What is the punishment for theft? | answered | 0.348 | 2.21s | 64.96s | PASS |
| S2 | Semantic | What is the punishment for murder? | answered | 0.298 | 2.17s | 57.33s | PASS |
| S3 | Semantic | What is dowry death? | answered | 0.356 | 2.17s | 35.17s | PASS |
| S4 | Semantic | What is the punishment for cheating? | ERROR | -1 | 0s | -s | **REVIEW** |
| S5 | Semantic | What is the punishment for defamation? | answered | 0.346 | 5.52s | 89.84s | **REVIEW** |
| S6 | Semantic | Is stalking a crime? | answered | 0.317 | 2.2s | 47.49s | PASS |
| S7 | Semantic | What is the punishment for identity theft online? | answered | 0.275 | 2.21s | 26.18s | PASS |
| S8 | Semantic | What is the penalty for hacking a computer system? | answered | 0.31 | 2.17s | 83.68s | PASS |
| S9 | Semantic | What is the right to freedom of speech and expression? | answered | 0.394 | 2.21s | 57.61s | **REVIEW** |
| S10 | Semantic | What are the fundamental duties of citizens? | answered | 0.319 | 2.17s | 77.84s | **REVIEW** |
| S11 | Semantic | What is anticipatory bail? | answered | 0.489 | 2.19s | 43.91s | **REVIEW** |
| S12 | Semantic | When can the police arrest without a warrant? | ERROR | -1 | 0s | -s | **REVIEW** |
| S13 | Semantic | How do I file a complaint against a company for a defective product? | ERROR | -1 | 0s | -s | **REVIEW** |
| S14 | Semantic | What counts as an unfair trade practice? | ERROR | -1 | 0s | -s | **REVIEW** |

Latency of answered questions (seconds): median 62.41, min 26.18, max 152.46, n=18.

---

## E1: What does Article 21 of the Constitution say?

*Category:* Exact lookup | *status:* `answered` | *best distance:* 0.421 | *timings:* {'rewrite_s': 0.0, 'retrieval_s': 2.19, 'generation_s': 60.21, 'total_s': 62.41}

**Expected provisions:** ('constitution_en', '21')

**Retrieved chunks (top 6):**

| # | Chunk | Provision | Title | Distance | Match |
|---|---|---|---|---|---|
| 1 | `constitution_en:21:1` | The Constitution of India article 21 | Protection of life and personal liberty | 0.0 | exact |
| 2 | `constitution_en:366:3` | The Constitution of India article 366 | Definitions | 0.449 | semantic |
| 3 | `constitution_en:51a:1` | The Constitution of India article 51A | Fundamental duties | 0.451 | semantic |
| 4 | `constitution_en:19:1` | The Constitution of India article 19 | Protection of certain rights regarding freedom of speech, et | 0.459 | semantic |
| 5 | `constitution_en:81:1` | The Constitution of India article 81 | Composition of the House of the People | 0.461 | semantic |
| 6 | `constitution_en:305:1` | The Constitution of India article 305 | Saving of existing laws and laws providing for State monopol | 0.466 | semantic |

**Sources given to the model:** [1] The Constitution of India, Article 21 (Protection of life and personal liberty) (p.42, `constitution_en:21:1`); [2] The Constitution of India, Article 366 (Definitions) (p.256, `constitution_en:366:3`); [3] The Constitution of India, Article 51A (Fundamental duties) (p.56, `constitution_en:51a:1`); [4] The Constitution of India, Article 19 (Protection of certain rights regarding freedom of speech, etc) (p.40, `constitution_en:19:1`); [5] The Constitution of India, Article 19 (Protection of certain rights regarding freedom of speech, etc) (p.41, `constitution_en:19:2`); [6] The Constitution of India, Article 81 (Composition of the House of the People) (p.68, `constitution_en:81:1`); [7] The Constitution of India, Article 305 (Saving of existing laws and laws providing for State monopolies) (p.203, `constitution_en:305:1`)

**Generated answer:**

> Article 21 of the Constitution of India states:  
> "No person shall be deprived of his life or personal liberty except according to procedure established by law." [1]

**Verification:** refusal=False | errors=[] | warnings=[] | quotes checked=1

**Context:** 8645 of 10000 characters; included 7 chunks, excluded [('constitution_en:231:1', 'provision_cap'), ('constitution_en:21a:1', 'provision_cap'), ('constitution_en:341:1', 'provision_cap'), ('constitution_en:362:1', 'provision_cap'), ('constitution_en:31a:1', 'provision_cap'), ('constitution_en:371b:1', 'provision_cap'), ('constitution_en:363a:1', 'provision_cap'), ('constitution_en:seventhschedule:2', 'provision_cap')]

**Checks:** PASS status, PASS expected in retrieval top-10, PASS expected in sources given to model, PASS answer mentions expected words, PASS no forbidden claims, PASS has citation markers, PASS citations point to real sources, PASS no unverified section numbers, PASS cited source text verbatim in PDF, PASS every citation matched to its exact retrieved chunk, PASS disclaimer present

---

## E2: Explain Article 14 of the Constitution.

*Category:* Exact lookup | *status:* `answered` | *best distance:* 0.399 | *timings:* {'rewrite_s': 0.0, 'retrieval_s': 2.14, 'generation_s': 61.46, 'total_s': 63.61}

**Expected provisions:** ('constitution_en', '14')

**Retrieved chunks (top 6):**

| # | Chunk | Provision | Title | Distance | Match |
|---|---|---|---|---|---|
| 1 | `constitution_en:14:1` | The Constitution of India article 14 | Equality before law | 0.0 | exact |
| 2 | `constitution_en:seventhschedule:1` | The Constitution of India schedule Seventh Schedule |  | 0.424 | semantic |
| 3 | `constitution_en:31a:1` | The Constitution of India article 31A | Saving of laws providing for acquisition of estates, etc | 0.426 | semantic |
| 4 | `constitution_en:15:2` | The Constitution of India article 15 | Prohibition of discrimination on grounds of religion, race,  | 0.429 | semantic |
| 5 | `constitution_en:257a:1` | The Constitution of India article 257A | [Assistance to States by deployment of armed forces or other | 0.43 | semantic |
| 6 | `constitution_en:thirdschedule:4` | The Constitution of India schedule Third Schedule |  | 0.431 | semantic |

**Sources given to the model:** [1] The Constitution of India, Article 14 (Equality before law) (p.37, `constitution_en:14:1`); [2] The Constitution of India, Article 31A (Saving of laws providing for acquisition of estates, etc) (p.47, `constitution_en:31a:1`); [3] The Constitution of India, Article 15 (Prohibition of discrimination on grounds of religion, race, caste, sex or place of birth) (p.38, `constitution_en:15:2`); [4] The Constitution of India, Article 257A ([Assistance to States by deployment of armed forces or other forces of the Union.) (p.181, `constitution_en:257a:1`); [5] The Constitution of India, Article 51A (Fundamental duties) (p.56, `constitution_en:51a:1`); [6] The Constitution of India, Article 366 (Definitions) (p.255, `constitution_en:366:2`); [7] The Constitution of India, Article 366 (Definitions) (p.256, `constitution_en:366:3`)

**Generated answer:**

> Article 14 of the Constitution of India states:  
> "Equality before law.—The State shall not deny to any person equality before the law or the equal protection of the laws within the territory of India." [1]  
>
> This means that every individual, regardless of their background, must be treated equally by the law. The State is prohibited from denying any person the right to be treated equally before the law or to receive equal protection under the law within India. This principle ensures that no person is subjected to unequal treatment by the legal system.  
>
> The provision is fundamental and applies universally, forming a cornerstone of the legal system in India. It is not subject to exceptions or qualifications as stated in the text provided.  
>
> [1]

**Notes shown to the user:** Check: some sentences add explanation that does not appear in the cited sources. Rely on the source text.

**Verification:** refusal=False | errors=[] | warnings=['weak_support', 'weak_support', 'weak_support', 'weak_support'] | quotes checked=1

**Context:** 7713 of 10000 characters; included 7 chunks, excluded [('constitution_en:241:1', 'provision_cap'), ('constitution_en:240:2', 'provision_cap'), ('constitution_en:18:1', 'provision_cap'), ('constitution_en:4:1', 'provision_cap'), ('constitution_en:144a:1', 'provision_cap'), ('constitution_en:19:1', 'provision_cap'), ('constitution_en:seventhschedule:1', 'provision_cap'), ('constitution_en:thirdschedule:4', 'provision_cap')]

**Checks:** PASS status, PASS expected in retrieval top-10, PASS expected in sources given to model, PASS answer mentions expected words, PASS no forbidden claims, PASS has citation markers, PASS citations point to real sources, PASS no unverified section numbers, FAIL cited source text verbatim in PDF, PASS every citation matched to its exact retrieved chunk, PASS disclaimer present

---

## E3: What is Section 103 of the BNS?

*Category:* Exact lookup | *status:* `answered` | *best distance:* 0.471 | *timings:* {'rewrite_s': 0.0, 'retrieval_s': 2.1, 'generation_s': 59.29, 'total_s': 61.4}

**Expected provisions:** ('bns_en', '103')

**Retrieved chunks (top 6):**

| # | Chunk | Provision | Title | Distance | Match |
|---|---|---|---|---|---|
| 1 | `bns_en:103:1` | Bharatiya Nyaya Sanhita, 2023 section 103 | Punishment for murder | 0.0 | exact |
| 2 | `bnss_en:103:2` | Bharatiya Nagarik Suraksha Sanhita, 2023 section 103 | Persons in charge of closed place to allow search. | 0.471 | semantic |
| 3 | `bnss_en:thesecondschedule:34` | Bharatiya Nagarik Suraksha Sanhita, 2023 schedule The Second Schedule |  | 0.486 | semantic |
| 4 | `bnss_en:102:1` | Bharatiya Nagarik Suraksha Sanhita, 2023 section 102 | C.—General provisions relating to searches Direction, etc.,  | 0.486 | semantic |
| 5 | `bnss_en:509:1` | Bharatiya Nagarik Suraksha Sanhita, 2023 section 509 | Non- compliance with provisions of section 183 or section 31 | 0.493 | semantic |
| 6 | `bnss_en:33:1` | Bharatiya Nagarik Suraksha Sanhita, 2023 section 33 | Public to give information of certain offences. | 0.493 | semantic |

**Sources given to the model:** [1] Bharatiya Nyaya Sanhita, 2023, Section 103 (Punishment for murder) (p.47, `bns_en:103:1`); [2] Bharatiya Nagarik Suraksha Sanhita, 2023, Section 103 (Persons in charge of closed place to allow search.) (p.84, `bnss_en:103:1`); [3] Bharatiya Nagarik Suraksha Sanhita, 2023, Section 103 (Persons in charge of closed place to allow search.) (p.85, `bnss_en:103:2`); [4] Bharatiya Nagarik Suraksha Sanhita, 2023, Section 102 (C.—General provisions relating to searches Direction, etc., of search- warrants.) (p.84, `bnss_en:102:1`); [5] Bharatiya Nagarik Suraksha Sanhita, 2023, Section 509 (Non- compliance with provisions of section 183 or section 316.) (p.255, `bnss_en:509:1`); [6] Bharatiya Nagarik Suraksha Sanhita, 2023, Section 33 (Public to give information of certain offences.) (p.60, `bnss_en:33:1`); [7] Bharatiya Nagarik Suraksha Sanhita, 2023, Section 93 (Provisions of this Chapter generally applicable to summons and warrants of arrest.) (p.80, `bnss_en:93:1`)

**Generated answer:**

> Section 103 of the Bharatiya Nyaya Sanhita, 2023 is about the punishment for murder. 
>
> (1) Whoever commits murder shall be punished with death or imprisonment for life, and shall also be liable to fine. [1]  
> (2) When a group of five or more persons acting in concert commits murder on the ground of race, caste or community, sex, place of birth, language, personal belief or any other similar ground, each member of such group shall be punished with death or with imprisonment for life, and shall also be liable to fine. [1]
>
> Note: The provided sources indicate that Section 103 of the Bharatiya Nyaya Sanhita, 2023 deals exclusively with punishment for murder, as per the text on page 47 of bns_english.pdf. No other provisions in the sources relate to Section 103 of the BNS in a different context. The section does not mention any other offences or procedural matters. The content is fully contained in [1].

**Notes shown to the user:** Check: some sentences add explanation that does not appear in the cited sources. Rely on the source text.

**Verification:** refusal=False | errors=[] | warnings=['weak_support'] | quotes checked=0

**Context:** 5361 of 10000 characters; included 7 chunks, excluded [('bnss_en:1:1', 'provision_cap'), ('bnss_en:300:1', 'provision_cap'), ('bns_en:209:1', 'provision_cap'), ('bnss_en:393:1', 'provision_cap'), ('bnss_en:100:1', 'provision_cap'), ('bns_en:358:3', 'provision_cap'), ('bnss_en:220:1', 'provision_cap'), ('bnss_en:101:1', 'provision_cap')]

**Checks:** PASS status, PASS expected in retrieval top-10, PASS expected in sources given to model, PASS answer mentions expected words, PASS no forbidden claims, PASS has citation markers, PASS citations point to real sources, PASS no unverified section numbers, PASS cited source text verbatim in PDF, PASS every citation matched to its exact retrieved chunk, PASS disclaimer present

---

## E4: What does Section 63 of the Bharatiya Sakshya Adhiniyam provide?

*Category:* Exact lookup | *status:* `answered` | *best distance:* 0.39 | *timings:* {'rewrite_s': 0.0, 'retrieval_s': 2.18, 'generation_s': 120.05, 'total_s': 122.25}

**Expected provisions:** ('bsa_en', '63')

**Retrieved chunks (top 6):**

| # | Chunk | Provision | Title | Distance | Match |
|---|---|---|---|---|---|
| 1 | `bsa_en:63:1` | Bharatiya Sakshya Adhiniyam, 2023 section 63 |  | 0.0 | exact |
| 2 | `bsa_en:63:2` | Bharatiya Sakshya Adhiniyam, 2023 section 63 |  | 0.0 | exact |
| 3 | `bsa_en:63:3` | Bharatiya Sakshya Adhiniyam, 2023 section 63 |  | 0.0 | exact |
| 4 | `bsa_en:1:1` | Bharatiya Sakshya Adhiniyam, 2023 section 1 |  | 0.428 | semantic |
| 5 | `bnss_en:33:1` | Bharatiya Nagarik Suraksha Sanhita, 2023 section 33 | Public to give information of certain offences. | 0.439 | semantic |
| 6 | `bsa_en:165:1` | Bharatiya Sakshya Adhiniyam, 2023 section 165 |  | 0.455 | semantic |

**Sources given to the model:** [1] Bharatiya Sakshya Adhiniyam, 2023, Section 63 (p.29, `bsa_en:63:1`); [2] Bharatiya Sakshya Adhiniyam, 2023, Section 63 (p.30, `bsa_en:63:2`); [3] Bharatiya Sakshya Adhiniyam, 2023, Section 63 (p.30, `bsa_en:63:3`); [4] Bharatiya Sakshya Adhiniyam, 2023, Section 1 (p.8, `bsa_en:1:1`); [5] Bharatiya Nagarik Suraksha Sanhita, 2023, Section 33 (Public to give information of certain offences.) (p.60, `bnss_en:33:1`); [6] Bharatiya Sakshya Adhiniyam, 2023, Section 165 (p.51, `bsa_en:165:1`); [7] Bharatiya Nagarik Suraksha Sanhita, 2023, Section 173 (CHAPTER XIII INFORMATION TO THE POLICE AND THEIR POWERS TO INVESTIGATE Information in cognizable cases.) (p.116, `bnss_en:173:1`); [8] Bharatiya Sakshya Adhiniyam, 2023, Section 62 (p.29, `bsa_en:62:1`)

**Generated answer:**

> Section 63 of the Bharatiya Sakshya Adhiniyam, 2023 provides that an electronic record printed on paper or stored in any electronic form (referred to as "computer output") shall be deemed to be a document and admissible in judicial proceedings without further proof of the original, if certain conditions are satisfied. These conditions are specified in sub-section (2) and include:
>
> (a) The computer output was produced during a period when the computer or communication device was regularly used to create, store, or process information for an activity regularly carried on by the person in lawful control of the device;  
> (b) Information of the kind contained in the electronic record or derived from it was regularly fed into the computer in the ordinary course of that activity;  
> (c) Throughout the material part of the period, the computer or device was operating properly, or if not, the malfunction did not affect the accuracy or integrity of the electronic record; and  
> (d) The information in the electronic record reproduces or is derived from such regularly fed information in the ordinary course of the activity.  
>
> Additionally, where the function of creating, storing, or processing information was regularly performed by one or more computers or communication devices—whether in standalone mode, on a computer system, on a network, on a resource enabling information processing and storage, or through an intermediary—the computers used during that period shall be treated as constituting a single computer for the purposes of this section [1][3].
>
> In any proceeding, a certificate must be submitted with the electronic record at each instance of admission, identifying the record, describing its production, and providing particulars of any device involved. The certificate must deal with the conditions in sub-section (2) and be signed by a person in charge of the computer or communication device and an expert (whichever is appropriate), and such a certificate shall be sufficient evidence of the matters stated, to the best of the knowledge and belief of the person making it [1][3].
>
> For the purposes of this section, information is considered supplied to a computer if it is supplied in any appropriate form, directly or with human intervention or via appropriate equipment. A computer output is deemed produced by a computer or communication device whether it was produced directly or via appropriate equipment or other electronic means [1][3].
>
> Thus, Section 63 establishes the conditions under which electronic records, even when printed or stored in electronic form, are admissible as evidence in judicial proceedings, provided the specified conditions are met [1].

**Notes shown to the user:** Check: a statement is cited to a source that matches it only weakly (cited [1, 3]: 0.35; best match [2]).

**Verification:** refusal=False | errors=[] | warnings=['miscited_claim'] | quotes checked=0

**Context:** 9209 of 10000 characters; included 8 chunks, excluded [('bsa_en:60:1', 'budget'), ('bsa_en:115:1', 'budget'), ('bsa_en:64:1', 'budget'), ('bsa_en:61:1', 'provision_cap'), ('bsa_en:149:1', 'provision_cap'), ('bns_en:1:1', 'provision_cap'), ('bnss_en:1:1', 'provision_cap'), ('bnss_en:219:2', 'provision_cap')]

**Checks:** PASS status, PASS expected in retrieval top-10, PASS expected in sources given to model, PASS answer mentions expected words, PASS no forbidden claims, PASS has citation markers, PASS citations point to real sources, PASS no unverified section numbers, PASS cited source text verbatim in PDF, PASS every citation matched to its exact retrieved chunk, PASS disclaimer present

---

## E5: What does Section 35 of the BNSS provide?

*Category:* Exact lookup | *status:* `answered` | *best distance:* 0.521 | *timings:* {'rewrite_s': 0.0, 'retrieval_s': 2.17, 'generation_s': 150.28, 'total_s': 152.46}

**Expected provisions:** ('bnss_en', '35')

**Retrieved chunks (top 6):**

| # | Chunk | Provision | Title | Distance | Match |
|---|---|---|---|---|---|
| 1 | `bnss_en:35:1` | Bharatiya Nagarik Suraksha Sanhita, 2023 section 35 | CHAPTER V ARREST OF PERSONS When police may arrest without w | 0.0 | exact |
| 2 | `bnss_en:35:2` | Bharatiya Nagarik Suraksha Sanhita, 2023 section 35 | CHAPTER V ARREST OF PERSONS When police may arrest without w | 0.0 | exact |
| 3 | `bnss_en:35:3` | Bharatiya Nagarik Suraksha Sanhita, 2023 section 35 | CHAPTER V ARREST OF PERSONS When police may arrest without w | 0.0 | exact |
| 4 | `bnss_en:35:4` | Bharatiya Nagarik Suraksha Sanhita, 2023 section 35 | CHAPTER V ARREST OF PERSONS When police may arrest without w | 0.0 | exact |
| 5 | `bns_en:35:1` | Bharatiya Nyaya Sanhita, 2023 section 35 | Right of private defence of body and of property | 0.521 | semantic |
| 6 | `bsa_en:35:1` | Bharatiya Sakshya Adhiniyam, 2023 section 35 |  | 0.53 | semantic |

**Sources given to the model:** [1] Bharatiya Nagarik Suraksha Sanhita, 2023, Section 35 (CHAPTER V ARREST OF PERSONS When police may arrest without warrant.) (p.61, `bnss_en:35:1`); [2] Bharatiya Nagarik Suraksha Sanhita, 2023, Section 35 (CHAPTER V ARREST OF PERSONS When police may arrest without warrant.) (p.62, `bnss_en:35:2`); [3] Bharatiya Nagarik Suraksha Sanhita, 2023, Section 35 (CHAPTER V ARREST OF PERSONS When police may arrest without warrant.) (p.63, `bnss_en:35:3`); [4] Bharatiya Nagarik Suraksha Sanhita, 2023, Section 35 (CHAPTER V ARREST OF PERSONS When police may arrest without warrant.) (p.63, `bnss_en:35:4`); [5] Bharatiya Nyaya Sanhita, 2023, Section 35 (Right of private defence of body and of property) (p.28, `bns_en:35:1`); [6] Bharatiya Sakshya Adhiniyam, 2023, Section 35 (p.22, `bsa_en:35:1`); [7] Bharatiya Nagarik Suraksha Sanhita, 2023, Section 85 (Attachment of property of person absconding.) (p.77, `bnss_en:85:1`); [8] The Consumer Protection Act, 2019, Section 59 (p.26, `cp_en:59:1`)

**Generated answer:**

> Section 35 of the Bharatiya Nagarik Suraksha Sanhita, 2023 provides the circumstances under which a police officer may arrest a person without a warrant.  
>
> A police officer may arrest any person without a warrant if:  
> (a) the person commits, in the presence of a police officer, a cognizable offence; or  
> (b) against whom a reasonable complaint has been made, or credible information has been received, or a reasonable suspicion exists that he has committed a cognizable offence punishable with imprisonment for a term which may be less than seven years or which may extend to seven years whether with or without fine, if the following conditions are satisfied:  
> (i) the police officer has reason to believe on the basis of such complaint, information, or suspicion that such person has committed the said offence;  
> (ii) the police officer is satisfied that such arrest is necessary—  
> (a) to prevent such person from committing any further offence; or  
> (b) for proper investigation of the offence; or  
> (c) to prevent such person from causing the evidence of the offence to disappear or tampering with such evidence in any manner; or  
> (d) to prevent such person from making any inducement, threat or promise to any person acquainted with the facts of the case so as to dissuade him from disclosing such facts to the Court or to the police officer; or  
> (e) unless such person is arrested, his presence in the Court whenever required cannot be ensured, and the police officer shall record while making such arrest, his reasons in writing.  
> Provided that a police officer shall, in all cases where the arrest of a person is not required under the provisions of this sub-section, record the reasons in writing for not making the arrest; or  
> (c) against whom credible information has been received that he has committed a cognizable offence punishable with imprisonment for a term which may extend to more than seven years whether with or without fine or with death sentence and the police officer has reason to believe on the basis of that information that such person has committed the said offence; or  
> (d) who has been proclaimed as an offender either under this Sanhita or by order of the State Government; or  
> (e) in whose possession anything is found which may reasonably be suspected to be stolen property and who may reasonably be suspected of having committed an offence with reference to such thing; or  
> (f) who obstructs a police officer while in the execution of his duty, or who has escaped, or attempts to escape, from lawful custody; or  
> (g) who is reasonably suspected of being a deserter from any of the Armed Forces of the Union; or  
> (h) who has been concerned in, or against whom a reasonable complaint has been made, or credible information has been received, or a reasonable suspicion exists, of his having been concerned in, any act committed at any place out of India which, if committed in India, would have been punishable as an offence, and for which he is, under any law relating to extradition, or otherwise, liable to be apprehended or detained in custody in India; or  
> (i) who, being a released convict, commits a breach of any rule made under sub-section (5) of section 394; or  
> (j) for whose arrest any requisition, whether written or oral, has been received from another police officer, provided that the requisition specifies the person to be arrested and the offence

**Verification:** refusal=False | errors=[] | warnings=[] | quotes checked=0

**Context:** 9578 of 10000 characters; included 8 chunks, excluded [('constitution_en:338b:2', 'budget'), ('bnss_en:33:1', 'budget'), ('constitution_en:35:1', 'budget'), ('cp_en:35:1', 'budget'), ('bnss_en:42:1', 'budget'), ('constitution_en:338:2', 'budget'), ('bnss_en:369:1', 'budget'), ('cp_en:55:1', 'budget')]

**Checks:** PASS status, PASS expected in retrieval top-10, PASS expected in sources given to model, PASS answer mentions expected words, PASS no forbidden claims, FAIL has citation markers, PASS citations point to real sources, PASS no unverified section numbers, PASS cited source text verbatim in PDF, PASS every citation matched to its exact retrieved chunk, PASS disclaimer present

---

## E6: What is Section 66C of the IT Act?

*Category:* Exact lookup | *status:* `answered` | *best distance:* 0.404 | *timings:* {'rewrite_s': 0.0, 'retrieval_s': 2.15, 'generation_s': 42.72, 'total_s': 44.87}

**Expected provisions:** ('it_en', '66C')

**Retrieved chunks (top 6):**

| # | Chunk | Provision | Title | Distance | Match |
|---|---|---|---|---|---|
| 1 | `it_en:66c:1` | The Information Technology Act, 2000 section 66C | Punishment for identity theft | 0.0 | exact |
| 2 | `it_en:66f:1` | The Information Technology Act, 2000 section 66F | Punishment for cyber terrorism | 0.415 | semantic |
| 3 | `it_en:69b:1` | The Information Technology Act, 2000 section 69B | Power to authorise to monitor and collect traffic data or in | 0.441 | semantic |
| 4 | `it_en:70b:1` | The Information Technology Act, 2000 section 70B | Indian Computer Emergency Response Team to serve as national | 0.446 | semantic |
| 5 | `it_en:67c:1` | The Information Technology Act, 2000 section 67C | Preservation and retention of information by intermediaries | 0.453 | semantic |
| 6 | `it_en:66:1` | The Information Technology Act, 2000 section 66 | Computer related offences | 0.459 | semantic |

**Sources given to the model:** [1] The Information Technology Act, 2000, Section 66C (Punishment for identity theft) (p.24, `it_en:66c:1`); [2] The Information Technology Act, 2000, Section 66F (Punishment for cyber terrorism) (p.25, `it_en:66f:1`); [3] The Information Technology Act, 2000, Section 69B (Power to authorise to monitor and collect traffic data or information through any computer resource for cyber security) (p.27, `it_en:69b:1`); [4] The Information Technology Act, 2000, Section 70B (Indian Computer Emergency Response Team to serve as national agency for incident response) (p.28, `it_en:70b:1`); [5] The Information Technology Act, 2000, Section 70B (Indian Computer Emergency Response Team to serve as national agency for incident response) (p.28, `it_en:70b:2`); [6] The Information Technology Act, 2000, Section 67C (Preservation and retention of information by intermediaries) (p.26, `it_en:67c:1`); [7] The Information Technology Act, 2000, Section 66 (Computer related offences) (p.23, `it_en:66:1`)

**Generated answer:**

> Section 66C of the IT Act punishes whoever fraudulently or dishonestly makes use of the electronic signature, password, or any other unique identification feature of any other person. The person shall be punished with imprisonment of either description for a term which may extend to three years and shall also be liable to a fine which may extend to rupees one lakh. [1]

**Verification:** refusal=False | errors=[] | warnings=[] | quotes checked=0

**Context:** 6972 of 10000 characters; included 7 chunks, excluded [('it_en:66a:1', 'provision_cap'), ('it_en:65:1', 'provision_cap'), ('it_en:46:1', 'provision_cap'), ('it_en:66b:1', 'provision_cap'), ('it_en:52c:1', 'provision_cap'), ('it_en:69:1', 'provision_cap'), ('it_en:69a:1', 'provision_cap'), ('it_en:87:3', 'provision_cap')]

**Checks:** PASS status, PASS expected in retrieval top-10, PASS expected in sources given to model, FAIL answer mentions expected words, PASS no forbidden claims, PASS has citation markers, PASS citations point to real sources, PASS no unverified section numbers, PASS cited source text verbatim in PDF, PASS every citation matched to its exact retrieved chunk, PASS disclaimer present

---

## E7: What does Section 35 of the Consumer Protection Act say?

*Category:* Exact lookup | *status:* `answered` | *best distance:* 0.319 | *timings:* {'rewrite_s': 0.0, 'retrieval_s': 2.18, 'generation_s': 80.76, 'total_s': 82.95}

**Expected provisions:** ('cp_en', '35')

**Retrieved chunks (top 6):**

| # | Chunk | Provision | Title | Distance | Match |
|---|---|---|---|---|---|
| 1 | `cp_en:35:1` | The Consumer Protection Act, 2019 section 35 |  | 0.0 | exact |
| 2 | `cp_en:59:1` | The Consumer Protection Act, 2019 section 59 |  | 0.374 | semantic |
| 3 | `cp_en:49:1` | The Consumer Protection Act, 2019 section 49 |  | 0.375 | semantic |
| 4 | `cp_en:18:1` | The Consumer Protection Act, 2019 section 18 |  | 0.378 | semantic |
| 5 | `cp_en:39:1` | The Consumer Protection Act, 2019 section 39 |  | 0.382 | semantic |
| 6 | `cp_en:39:2` | The Consumer Protection Act, 2019 section 39 |  | 0.387 | semantic |

**Sources given to the model:** [1] The Consumer Protection Act, 2019, Section 35 (p.18, `cp_en:35:1`); [2] The Consumer Protection Act, 2019, Section 59 (p.26, `cp_en:59:1`); [3] The Consumer Protection Act, 2019, Section 49 (p.24, `cp_en:49:1`); [4] The Consumer Protection Act, 2019, Section 18 (p.13, `cp_en:18:1`); [5] The Consumer Protection Act, 2019, Section 39 (p.21, `cp_en:39:1`); [6] The Consumer Protection Act, 2019, Section 39 (p.22, `cp_en:39:2`); [7] The Consumer Protection Act, 2019, Section 2 (p.7, `cp_en:2:9`)

**Generated answer:**

> Section 35 of the Consumer Protection Act, 2019 states that a complaint relating to goods sold or delivered or agreed to be sold or delivered, or any service provided or agreed to be provided, may be filed with a District Commission by:
>
> (a) the consumer—  
> (i) to whom such goods are sold or delivered or agreed to be sold or delivered or such service is provided or agreed to be provided; or  
> (ii) who alleges unfair trade practice in respect of such goods or service;  
>
> (b) any recognised consumer association, whether the consumer to whom such goods are sold or delivered or agreed to be sold or delivered or such service is provided or agreed to be provided, or who alleges unfair trade practice in respect of such goods or service, is a member of such association or not;  
>
> (c) one or more consumers, where there are numerous consumers having the same interest, with the permission of the District Commission, on behalf of, or for the benefit of, all consumers so interested; or  
>
> (d) the Central Government, the Central Authority or the State Government, as the case may be:  
>
> Provided that the complaint under this sub-section may be filed electronically in such manner as may be prescribed.  
>
> Explanation.—For the purposes of this sub-section, "recognised consumer association" means any voluntary consumer association registered under any law for the time being in force.  
>
> Every complaint filed under sub-section (1) shall be accompanied with such fee and payable in such manner, including electronic form, as may be prescribed. [1]

**Verification:** refusal=False | errors=[] | warnings=[] | quotes checked=0

**Context:** 9211 of 10000 characters; included 7 chunks, excluded [('cp_en:38:2', 'provision_cap'), ('cp_en:34:1', 'provision_cap'), ('cp_en:1:1', 'provision_cap'), ('cp_en:10:1', 'provision_cap'), ('cp_en:2:1', 'budget'), ('cp_en:2:2', 'budget'), ('cp_en:2:3', 'budget'), ('cp_en:2:6', 'budget')]

**Checks:** PASS status, PASS expected in retrieval top-10, PASS expected in sources given to model, PASS answer mentions expected words, PASS no forbidden claims, PASS has citation markers, PASS citations point to real sources, PASS no unverified section numbers, FAIL cited source text verbatim in PDF, PASS every citation matched to its exact retrieved chunk, PASS disclaimer present

---

## E8: What does Section 999 of the BNS say?

*Category:* Exact lookup (nonexistent) | *status:* `answered` | *best distance:* 0.535 | *timings:* {'rewrite_s': 0.0, 'retrieval_s': 2.16, 'generation_s': 57.1, 'total_s': 59.26}

**Expected provisions:** (none: should be refused / handled)

**Retrieved chunks (top 6):**

| # | Chunk | Provision | Title | Distance | Match |
|---|---|---|---|---|---|
| 1 | `bnss_en:509:1` | Bharatiya Nagarik Suraksha Sanhita, 2023 section 509 | Non- compliance with provisions of section 183 or section 31 | 0.535 | semantic |
| 2 | `bnss_en:299:1` | Bharatiya Nagarik Suraksha Sanhita, 2023 section 299 | Statements of accused not to be used. | 0.54 | semantic |
| 3 | `bsa_en:119:2` | Bharatiya Sakshya Adhiniyam, 2023 section 119 |  | 0.55 | semantic |
| 4 | `bnss_en:119:1` | Bharatiya Nagarik Suraksha Sanhita, 2023 section 119 | Notice of forfeiture of property. | 0.553 | semantic |
| 5 | `bnss_en:500:1` | Bharatiya Nagarik Suraksha Sanhita, 2023 section 500 | Appeal against orders under section 498 or section 499. | 0.556 | semantic |
| 6 | `bnss_en:219:1` | Bharatiya Nagarik Suraksha Sanhita, 2023 section 219 | Prosecution for offences against marriage. | 0.558 | semantic |

**Sources given to the model:** [1] Bharatiya Nagarik Suraksha Sanhita, 2023, Section 509 (Non- compliance with provisions of section 183 or section 316.) (p.255, `bnss_en:509:1`); [2] Bharatiya Nagarik Suraksha Sanhita, 2023, Section 299 (Statements of accused not to be used.) (p.172, `bnss_en:299:1`); [3] Bharatiya Sakshya Adhiniyam, 2023, Section 119 (p.42, `bsa_en:119:2`); [4] Bharatiya Nagarik Suraksha Sanhita, 2023, Section 119 (Notice of forfeiture of property.) (p.92, `bnss_en:119:1`); [5] Bharatiya Nagarik Suraksha Sanhita, 2023, Section 500 (Appeal against orders under section 498 or section 499.) (p.252, `bnss_en:500:1`); [6] Bharatiya Nagarik Suraksha Sanhita, 2023, Section 219 (Prosecution for offences against marriage.) (p.141, `bnss_en:219:1`); [7] Bharatiya Nagarik Suraksha Sanhita, 2023, Section 219 (Prosecution for offences against marriage.) (p.142, `bnss_en:219:2`)

**Generated answer:**

> The available documents do not answer the question because there is no source provided that contains Section 999 of the Bharatiya Nagarik Suraksha Sanhita, 2023. All the cited sources cover different sections (e.g., 509, 299, 119, 500, 219), but none mention Section 999. Therefore, based on the provided sources, the content of Section 999 cannot be determined.

**Notes shown to the user:** Verification error: the answer mentions 999, which is not in the retrieved sources. Treat that reference as unverified.

**Verification:** refusal=True | errors=['unsupported_section_reference'] | warnings=[] | quotes checked=0

**Context:** 8215 of 10000 characters; included 7 chunks, excluded [('bns_en:209:1', 'provision_cap'), ('bnss_en:99:1', 'provision_cap'), ('bnss_en:151:1', 'provision_cap'), ('bns_en:309:1', 'provision_cap'), ('bsa_en:115:1', 'provision_cap'), ('bns_en:259:1', 'provision_cap'), ('bnss_en:399:1', 'provision_cap'), ('bnss_en:393:1', 'provision_cap')]

**Checks:** FAIL status, PASS expected in retrieval top-10, PASS expected in sources given to model, PASS answer mentions expected words, PASS no forbidden claims, FAIL has citation markers, PASS citations point to real sources, PASS no unverified section numbers, PASS cited source text verbatim in PDF, PASS every citation matched to its exact retrieved chunk, PASS disclaimer present

---

## S1: What is the punishment for theft?

*Category:* Semantic | *status:* `answered` | *best distance:* 0.348 | *timings:* {'rewrite_s': 0.0, 'retrieval_s': 2.19, 'generation_s': 62.76, 'total_s': 64.96}

**Expected provisions:** ('bns_en', '303')

**Retrieved chunks (top 6):**

| # | Chunk | Provision | Title | Distance | Match |
|---|---|---|---|---|---|
| 1 | `bns_en:303:5` | Bharatiya Nyaya Sanhita, 2023 section 303 | Theft | 0.348 | semantic |
| 2 | `bns_en:305:1` | Bharatiya Nyaya Sanhita, 2023 section 305 | Theft in a dwelling house, or means of transportation or pla | 0.366 | semantic |
| 3 | `bnss_en:thefirstschedule:43` | Bharatiya Nagarik Suraksha Sanhita, 2023 schedule The First Schedule |  | 0.373 | semantic |
| 4 | `bns_en:307:1` | Bharatiya Nyaya Sanhita, 2023 section 307 | Theft after preparation made for causing death, hurt or rest | 0.382 | semantic |
| 5 | `bnss_en:thefirstschedule:40` | Bharatiya Nagarik Suraksha Sanhita, 2023 schedule The First Schedule |  | 0.383 | semantic |
| 6 | `bns_en:306:1` | Bharatiya Nyaya Sanhita, 2023 section 306 | Theft by clerk or servant of property in possession of maste | 0.384 | semantic |

**Sources given to the model:** [1] Bharatiya Nyaya Sanhita, 2023, Section 303 (Theft) (p.89, `bns_en:303:5`); [2] Bharatiya Nyaya Sanhita, 2023, Section 305 (Theft in a dwelling house, or means of transportation or place of worship, etc) (p.89, `bns_en:305:1`); [3] Bharatiya Nyaya Sanhita, 2023, Section 307 (Theft after preparation made for causing death, hurt or restraint in order to committing of theft) (p.90, `bns_en:307:1`); [4] Bharatiya Nyaya Sanhita, 2023, Section 306 (Theft by clerk or servant of property in possession of master) (p.89, `bns_en:306:1`); [5] Bharatiya Nyaya Sanhita, 2023, Section 313 (Punishment for belonging to gang of robbers, etc) (p.92, `bns_en:313:1`); [6] Bharatiya Nyaya Sanhita, 2023, Section 134 (Assault or criminal force in attempt to commit theft of property carried by a person) (p.57, `bns_en:134:1`)

**Generated answer:**

> The punishment for theft depends on the circumstances of the offence.  
>
> For general theft, under Section 303, whoever commits theft shall be punished with imprisonment of either description for a term which may extend to three years, or with fine, or with both. In case of a second or subsequent conviction, the punishment shall be rigorous imprisonment for a term which shall not be less than one year but which may extend to five years, and with fine. [1]  
>
> If the theft occurs in a dwelling house, means of transportation, place of worship, or involves government or local authority property, the punishment is imprisonment of either description for a term which may extend to seven years, and a fine. [2]  
>
> If the theft is committed after preparation for causing death, hurt, or restraint, the punishment is rigorous imprisonment for a term which may extend to ten years, and a fine. [3]  
>
> If a clerk or servant commits theft of property in the possession of their master or employer, the punishment is imprisonment of either description for a term which may extend to seven years, and a fine. [4]  
>
> If a person belongs to a gang habitually engaged in theft or robbery (but not dacoits), the punishment is rigorous imprisonment for a term which may extend to seven years, and a fine. [5]  
>
> Additionally, if someone attempts to commit theft by assaulting or using criminal force on a person carrying property, the punishment is imprisonment of either description for a term which may extend to two years, or with fine, or with both. [6]  
>
> Note: The punishment for first-time theft where the value of stolen property is less than five thousand rupees and the property is restored, is community service. [1]  
>
> Thus, the punishment for theft varies based on the context, with minimum terms and maximum limits as specified in the relevant sections.

**Notes shown to the user:** Check: some sentences add explanation that does not appear in the cited sources. Rely on the source text.

**Verification:** refusal=False | errors=[] | warnings=['weak_support'] | quotes checked=0

**Context:** 3490 of 10000 characters; included 6 chunks, excluded [('bns_en:304:1', 'provision_cap'), ('bns_en:317:1', 'provision_cap'), ('bns_en:309:3', 'provision_cap'), ('bns_en:250:1', 'provision_cap'), ('bns_en:328:1', 'provision_cap'), ('bns_en:252:1', 'provision_cap'), ('bns_en:140:1', 'provision_cap'), ('it_en:66b:1', 'provision_cap')]

**Checks:** PASS status, PASS expected in retrieval top-10, PASS expected in sources given to model, PASS answer mentions expected words, PASS no forbidden claims, PASS has citation markers, PASS citations point to real sources, PASS no unverified section numbers, PASS cited source text verbatim in PDF, PASS every citation matched to its exact retrieved chunk, PASS disclaimer present

---

## S2: What is the punishment for murder?

*Category:* Semantic | *status:* `answered` | *best distance:* 0.298 | *timings:* {'rewrite_s': 0.0, 'retrieval_s': 2.12, 'generation_s': 55.2, 'total_s': 57.33}

**Expected provisions:** ('bns_en', '103')

**Retrieved chunks (top 6):**

| # | Chunk | Provision | Title | Distance | Match |
|---|---|---|---|---|---|
| 1 | `bns_en:103:1` | Bharatiya Nyaya Sanhita, 2023 section 103 | Punishment for murder | 0.298 | semantic |
| 2 | `bns_en:104:1` | Bharatiya Nyaya Sanhita, 2023 section 104 | Punishment for murder by life-convict | 0.323 | semantic |
| 3 | `bns_en:105:1` | Bharatiya Nyaya Sanhita, 2023 section 105 | Punishment for culpable homicide not amounting to murder | 0.359 | semantic |
| 4 | `bns_en:4:1` | Bharatiya Nyaya Sanhita, 2023 section 4 | Punishments | 0.391 | semantic |
| 5 | `bns_en:109:1` | Bharatiya Nyaya Sanhita, 2023 section 109 | Attempt to murder | 0.393 | semantic |
| 6 | `bns_en:55:1` | Bharatiya Nyaya Sanhita, 2023 section 55 | Abetment of offence punishable with death or imprisonment fo | 0.397 | semantic |

**Sources given to the model:** [1] Bharatiya Nyaya Sanhita, 2023, Section 103 (Punishment for murder) (p.47, `bns_en:103:1`); [2] Bharatiya Nyaya Sanhita, 2023, Section 104 (Punishment for murder by life-convict) (p.47, `bns_en:104:1`); [3] Bharatiya Nyaya Sanhita, 2023, Section 105 (Punishment for culpable homicide not amounting to murder) (p.47, `bns_en:105:1`); [4] Bharatiya Nyaya Sanhita, 2023, Section 4 (Punishments) (p.21, `bns_en:4:1`); [5] Bharatiya Nyaya Sanhita, 2023, Section 109 (Attempt to murder) (p.47, `bns_en:109:1`); [6] Bharatiya Nyaya Sanhita, 2023, Section 55 (Abetment of offence punishable with death or imprisonment for life) (p.33, `bns_en:55:1`)

**Generated answer:**

> The punishment for murder is death or imprisonment for life, and the offender shall also be liable to fine. [1]  
>
> Additionally, if a group of five or more persons acting in concert commits murder on the ground of race, caste or community, sex, place of birth, language, personal belief or any other similar ground, each member of such group shall be punished with death or with imprisonment for life, and shall also be liable to fine. [1][2]  
>
> This applies regardless of whether the offence is committed by a single person or a group, as long as the group consists of five or more persons acting in concert and the murder is motivated by one of the specified grounds.  
>
> Note: Section 104 applies specifically to a person who is already under sentence of imprisonment for life and commits murder, and in such case, the punishment is death or imprisonment for life (which means the remainder of that person’s natural life). [2]  
>
> However, the general punishment for murder, as stated in Section 103(1), remains death or imprisonment for life, with a fine. [1]  
>
> Thus, the primary punishment for murder is death or life imprisonment, with a fine. [1]

**Verification:** refusal=False | errors=[] | warnings=[] | quotes checked=0

**Context:** 4609 of 10000 characters; included 6 chunks, excluded [('bns_en:101:1', 'provision_cap'), ('bns_en:66:1', 'provision_cap'), ('bnss_en:474:1', 'provision_cap'), ('bns_en:71:1', 'provision_cap'), ('bns_en:110:1', 'provision_cap'), ('bnss_en:thefirstschedule:19', 'provision_cap'), ('bnss_en:thefirstschedule:38', 'provision_cap'), ('bnss_en:thefirstschedule:14', 'provision_cap')]

**Checks:** PASS status, PASS expected in retrieval top-10, PASS expected in sources given to model, PASS answer mentions expected words, PASS no forbidden claims, PASS has citation markers, PASS citations point to real sources, PASS no unverified section numbers, PASS cited source text verbatim in PDF, PASS every citation matched to its exact retrieved chunk, PASS disclaimer present

---

## S3: What is dowry death?

*Category:* Semantic | *status:* `answered` | *best distance:* 0.356 | *timings:* {'rewrite_s': 0.0, 'retrieval_s': 2.15, 'generation_s': 33.01, 'total_s': 35.17}

**Expected provisions:** ('bns_en', '80')

**Retrieved chunks (top 6):**

| # | Chunk | Provision | Title | Distance | Match |
|---|---|---|---|---|---|
| 1 | `bns_en:80:1` | Bharatiya Nyaya Sanhita, 2023 section 80 | Dowry death | 0.356 | semantic |
| 2 | `bsa_en:118:1` | Bharatiya Sakshya Adhiniyam, 2023 section 118 |  | 0.371 | semantic |
| 3 | `bns_en:315:1` | Bharatiya Nyaya Sanhita, 2023 section 315 | Dishonest misappropriation of property possessed by deceased | 0.559 | semantic |
| 4 | `bns_en:311:1` | Bharatiya Nyaya Sanhita, 2023 section 311 | Robbery, or dacoity, with attempt to cause death or grievous | 0.575 | semantic |
| 5 | `bns_en:25:1` | Bharatiya Nyaya Sanhita, 2023 section 25 | Act not intended and not known to be likely to cause death o | 0.577 | semantic |
| 6 | `bns_en:41:1` | Bharatiya Nyaya Sanhita, 2023 section 41 | When right of private defence of property extends to causing | 0.578 | semantic |

**Sources given to the model:** [1] Bharatiya Nyaya Sanhita, 2023, Section 80 (Dowry death) (p.41, `bns_en:80:1`); [2] Bharatiya Sakshya Adhiniyam, 2023, Section 118 (p.41, `bsa_en:118:1`); [3] Bharatiya Nyaya Sanhita, 2023, Section 315 (Dishonest misappropriation of property possessed by deceased person at the time of his death) (p.93, `bns_en:315:1`); [4] Bharatiya Nyaya Sanhita, 2023, Section 311 (Robbery, or dacoity, with attempt to cause death or grievous hurt) (p.92, `bns_en:311:1`); [5] Bharatiya Nyaya Sanhita, 2023, Section 25 (Act not intended and not known to be likely to cause death or grievous hurt, done by consent) (p.26, `bns_en:25:1`); [6] Bharatiya Nyaya Sanhita, 2023, Section 41 (When right of private defence of property extends to causing death) (p.29, `bns_en:41:1`)

**Generated answer:**

> Dowry death is the death of a woman caused by any burns or bodily injury or occurring otherwise than under normal circumstances within seven years of her marriage, if it is shown that soon before her death she was subjected to cruelty or harassment by her husband or any relative of her husband for, or in connection with, any demand for dowry [1].

**Verification:** refusal=False | errors=[] | warnings=[] | quotes checked=0

**Context:** 4260 of 10000 characters; included 6 chunks, excluded [('bns_en:106:1', 'provision_cap'), ('bns_en:101:1', 'provision_cap'), ('bns_en:101:6', 'provision_cap'), ('bns_en:90:1', 'provision_cap'), ('bns_en:310:1', 'provision_cap'), ('bns_en:251:1', 'provision_cap'), ('bns_en:338:1', 'provision_cap'), ('bns_en:100:1', 'provision_cap')]

**Checks:** PASS status, PASS expected in retrieval top-10, PASS expected in sources given to model, PASS answer mentions expected words, PASS no forbidden claims, PASS has citation markers, PASS citations point to real sources, PASS no unverified section numbers, PASS cited source text verbatim in PDF, PASS every citation matched to its exact retrieved chunk, PASS disclaimer present

---

## S4: What is the punishment for cheating?

*Category:* Semantic | *status:* `ERROR` | *best distance:* -1 | *timings:* {}

**Expected provisions:** ('bns_en', '318')

**Retrieved chunks (top 6):**

| # | Chunk | Provision | Title | Distance | Match |
|---|---|---|---|---|---|

**Sources given to the model:** none

**Generated answer:**

> ERROR: timed out

**Checks:** FAIL ran without error

---

## S5: What is the punishment for defamation?

*Category:* Semantic | *status:* `answered` | *best distance:* 0.346 | *timings:* {'rewrite_s': 0.0, 'retrieval_s': 2.12, 'generation_s': 87.7, 'total_s': 89.84}

**Expected provisions:** ('bns_en', '356')

**Retrieved chunks (top 6):**

| # | Chunk | Provision | Title | Distance | Match |
|---|---|---|---|---|---|
| 1 | `bns_en:356:9` | Bharatiya Nyaya Sanhita, 2023 section 356 | Defamation | 0.346 | semantic |
| 2 | `bns_en:356:1` | Bharatiya Nyaya Sanhita, 2023 section 356 | Defamation | 0.388 | semantic |
| 3 | `bns_en:298:1` | Bharatiya Nyaya Sanhita, 2023 section 298 | Injuring or defiling place of worship with intent to insult  | 0.413 | semantic |
| 4 | `bns_en:131:1` | Bharatiya Nyaya Sanhita, 2023 section 131 | Punishment for assault or criminal force otherwise than on g | 0.417 | semantic |
| 5 | `bns_en:299:1` | Bharatiya Nyaya Sanhita, 2023 section 299 | Deliberate and malicious acts, intended to outrage religious | 0.42 | semantic |
| 6 | `bns_en:356:7` | Bharatiya Nyaya Sanhita, 2023 section 356 | Defamation | 0.426 | semantic |

**Sources given to the model:** [1] Bharatiya Nyaya Sanhita, 2023, Section 356 (Defamation) (p.108, `bns_en:356:1`); [2] Bharatiya Nyaya Sanhita, 2023, Section 356 (Defamation) (p.108, `bns_en:356:3`); [3] Bharatiya Nyaya Sanhita, 2023, Section 356 (Defamation) (p.109, `bns_en:356:7`); [4] Bharatiya Nyaya Sanhita, 2023, Section 356 (Defamation) (p.110, `bns_en:356:8`); [5] Bharatiya Nyaya Sanhita, 2023, Section 356 (Defamation) (p.110, `bns_en:356:9`); [6] Bharatiya Nyaya Sanhita, 2023, Section 298 (Injuring or defiling place of worship with intent to insult religion of any class) (p.87, `bns_en:298:1`); [7] Bharatiya Nyaya Sanhita, 2023, Section 131 (Punishment for assault or criminal force otherwise than on grave provocation) (p.56, `bns_en:131:1`); [8] Bharatiya Nyaya Sanhita, 2023, Section 299 (Deliberate and malicious acts, intended to outrage religious feelings of any class by insulting its religion or religious beliefs) (p.87, `bns_en:299:1`); [9] Bharatiya Nagarik Suraksha Sanhita, 2023, Section 222 (Prosecution for defamation.) (p.142, `bnss_en:222:1`); [10] Bharatiya Nyaya Sanhita, 2023, Section 133 (Assault or criminal force with intent to dishonour person, otherwise than on grave provocation) (p.56, `bns_en:133:1`)

**Generated answer:**

> The punishment for defamation is simple imprisonment for a term which may extend to two years, or with fine, or with both. [1][2][3][4][5]
>
> Specifically, under Section 356(2) of the Bharatiya Nyaya Sanhita, 2023, whoever defames another shall be punished with simple imprisonment for a term which may extend to two years, or with fine, or with both. [1][5]
>
> Additionally, if someone prints or engraves defamatory matter knowing or having good reason to believe it is defamatory, or sells or offers for sale such matter knowing it contains defamatory content, they shall also face the same punishment: simple imprisonment for a term which may extend to two years, or with fine, or with both. [3][4]
>
> Note: The punishment under Section 356 does not apply in certain exceptions, such as when the imputation is made in good faith for the protection of interests or for public good, or when it relates to public proceedings or judicial conduct. [2][3][4] However, these exceptions do not negate the punishment in cases where defamation is established and not covered by exception. The punishment remains as stated above when defamation is proven and not exempted.

**Notes shown to the user:** Check: some sentences add explanation that does not appear in the cited sources. Rely on the source text.

**Verification:** refusal=False | errors=[] | warnings=['weak_support'] | quotes checked=0

**Context:** 9729 of 10000 characters; included 10 chunks, excluded [('bns_en:174:1', 'provision_cap'), ('it_en:67:1', 'provision_cap'), ('bns_en:355:1', 'provision_cap'), ('bns_en:4:1', 'provision_cap'), ('bns_en:356:2', 'budget'), ('bns_en:356:6', 'budget'), ('bnss_en:thefirstschedule:47', 'provision_cap'), ('bnss_en:thefirstschedule:48', 'provision_cap')]

**Checks:** PASS status, PASS expected in retrieval top-10, PASS expected in sources given to model, PASS answer mentions expected words, PASS no forbidden claims, PASS has citation markers, PASS citations point to real sources, PASS no unverified section numbers, FAIL cited source text verbatim in PDF, PASS every citation matched to its exact retrieved chunk, PASS disclaimer present

---

## S6: Is stalking a crime?

*Category:* Semantic | *status:* `answered` | *best distance:* 0.317 | *timings:* {'rewrite_s': 0.0, 'retrieval_s': 2.13, 'generation_s': 45.34, 'total_s': 47.49}

**Expected provisions:** ('bns_en', '78')

**Retrieved chunks (top 6):**

| # | Chunk | Provision | Title | Distance | Match |
|---|---|---|---|---|---|
| 1 | `bns_en:78:1` | Bharatiya Nyaya Sanhita, 2023 section 78 | Stalking | 0.317 | semantic |
| 2 | `bns_en:111:1` | Bharatiya Nyaya Sanhita, 2023 section 111 | Organised crime | 0.443 | semantic |
| 3 | `bnss_en:thefirstschedule:8` | Bharatiya Nagarik Suraksha Sanhita, 2023 schedule The First Schedule |  | 0.451 | semantic |
| 4 | `bnss_en:thefirstschedule:43` | Bharatiya Nagarik Suraksha Sanhita, 2023 schedule The First Schedule |  | 0.461 | semantic |
| 5 | `bns_en:249:1` | Bharatiya Nyaya Sanhita, 2023 section 249 | Harbouring offender | 0.463 | semantic |
| 6 | `bnss_en:201:1` | Bharatiya Nagarik Suraksha Sanhita, 2023 section 201 | Place of trial in case of certain offences. | 0.464 | semantic |

**Sources given to the model:** [1] Bharatiya Nyaya Sanhita, 2023, Section 78 (Stalking) (p.41, `bns_en:78:1`); [2] Bharatiya Nyaya Sanhita, 2023, Section 111 (Organised crime) (p.48, `bns_en:111:1`); [3] Bharatiya Nyaya Sanhita, 2023, Section 249 (Harbouring offender) (p.79, `bns_en:249:1`); [4] Bharatiya Nagarik Suraksha Sanhita, 2023, Section 201 (Place of trial in case of certain offences.) (p.134, `bnss_en:201:1`); [5] Bharatiya Nyaya Sanhita, 2023, Section 143 (Trafficking of person) (p.58, `bns_en:143:1`); [6] Bharatiya Nyaya Sanhita, 2023, Section 77 (Voyeurism) (p.40, `bns_en:77:1`)

**Generated answer:**

> Yes, stalking is a crime. [1]

**Verification:** refusal=False | errors=[] | warnings=[] | quotes checked=0

**Context:** 9688 of 10000 characters; included 6 chunks, excluded [('bnss_en:202:1', 'provision_cap'), ('bns_en:133:1', 'provision_cap'), ('bns_en:309:1', 'provision_cap'), ('bns_en:32:1', 'provision_cap'), ('bns_en:143:2', 'budget'), ('bnss_en:thefirstschedule:8', 'provision_cap'), ('bnss_en:thefirstschedule:43', 'provision_cap'), ('bnss_en:thefirstschedule:5', 'provision_cap')]

**Checks:** PASS status, PASS expected in retrieval top-10, PASS expected in sources given to model, PASS answer mentions expected words, PASS no forbidden claims, PASS has citation markers, PASS citations point to real sources, PASS no unverified section numbers, PASS cited source text verbatim in PDF, PASS every citation matched to its exact retrieved chunk, PASS disclaimer present

---

## S7: What is the punishment for identity theft online?

*Category:* Semantic | *status:* `answered` | *best distance:* 0.275 | *timings:* {'rewrite_s': 0.0, 'retrieval_s': 2.19, 'generation_s': 23.99, 'total_s': 26.18}

**Expected provisions:** ('it_en', '66C')

**Retrieved chunks (top 6):**

| # | Chunk | Provision | Title | Distance | Match |
|---|---|---|---|---|---|
| 1 | `it_en:66c:1` | The Information Technology Act, 2000 section 66C | Punishment for identity theft | 0.275 | semantic |
| 2 | `it_en:66d:1` | The Information Technology Act, 2000 section 66D | Punishment for cheating by personation by using computer res | 0.356 | semantic |
| 3 | `it_en:66b:1` | The Information Technology Act, 2000 section 66B | Punishment for dishonestly receiving stolen computer resourc | 0.388 | semantic |
| 4 | `it_en:66e:1` | The Information Technology Act, 2000 section 66E | Punishment for violation of privacy | 0.388 | semantic |
| 5 | `it_en:66:1` | The Information Technology Act, 2000 section 66 | Computer related offences | 0.388 | semantic |
| 6 | `it_en:66f:1` | The Information Technology Act, 2000 section 66F | Punishment for cyber terrorism | 0.39 | semantic |

**Sources given to the model:** [1] The Information Technology Act, 2000, Section 66C (Punishment for identity theft) (p.24, `it_en:66c:1`); [2] The Information Technology Act, 2000, Section 66D (Punishment for cheating by personation by using computer resource) (p.24, `it_en:66d:1`); [3] The Information Technology Act, 2000, Section 66B (Punishment for dishonestly receiving stolen computer resource or communication device) (p.24, `it_en:66b:1`); [4] The Information Technology Act, 2000, Section 66E (Punishment for violation of privacy) (p.24, `it_en:66e:1`); [5] The Information Technology Act, 2000, Section 66 (Computer related offences) (p.23, `it_en:66:1`); [6] The Information Technology Act, 2000, Section 66F (Punishment for cyber terrorism) (p.25, `it_en:66f:1`)

**Generated answer:**

> The punishment for identity theft online is imprisonment of either description for a term which may extend to three years and a fine which may extend to rupees one lakh. [1]

**Verification:** refusal=False | errors=[] | warnings=[] | quotes checked=0

**Context:** 4732 of 10000 characters; included 6 chunks, excluded [('it_en:67a:1', 'provision_cap'), ('it_en:71:1', 'provision_cap'), ('it_en:67:1', 'provision_cap'), ('it_en:66a:1', 'provision_cap'), ('it_en:84c:1', 'provision_cap'), ('it_en:72a:1', 'provision_cap'), ('it_en:67b:1', 'provision_cap'), ('it_en:74:1', 'provision_cap')]

**Checks:** PASS status, PASS expected in retrieval top-10, PASS expected in sources given to model, PASS answer mentions expected words, PASS no forbidden claims, PASS has citation markers, PASS citations point to real sources, PASS no unverified section numbers, PASS cited source text verbatim in PDF, PASS every citation matched to its exact retrieved chunk, PASS disclaimer present

---

## S8: What is the penalty for hacking a computer system?

*Category:* Semantic | *status:* `answered` | *best distance:* 0.31 | *timings:* {'rewrite_s': 0.0, 'retrieval_s': 2.16, 'generation_s': 81.51, 'total_s': 83.68}

**Expected provisions:** ('any', [('it_en', '66'), ('it_en', '43')])

**Retrieved chunks (top 6):**

| # | Chunk | Provision | Title | Distance | Match |
|---|---|---|---|---|---|
| 1 | `it_en:43:1` | The Information Technology Act, 2000 section 43 | Penalty and compensation] for damage to computer, computer s | 0.31 | semantic |
| 2 | `it_en:66f:1` | The Information Technology Act, 2000 section 66F | Punishment for cyber terrorism | 0.331 | semantic |
| 3 | `it_en:66c:1` | The Information Technology Act, 2000 section 66C | Punishment for identity theft | 0.348 | semantic |
| 4 | `it_en:65:1` | The Information Technology Act, 2000 section 65 | Tampering with computer source documents | 0.35 | semantic |
| 5 | `it_en:66:1` | The Information Technology Act, 2000 section 66 | Computer related offences | 0.351 | semantic |
| 6 | `it_en:66d:1` | The Information Technology Act, 2000 section 66D | Punishment for cheating by personation by using computer res | 0.353 | semantic |

**Sources given to the model:** [1] The Information Technology Act, 2000, Section 43 (Penalty and compensation] for damage to computer, computer system, etc) (p.18, `it_en:43:1`); [2] The Information Technology Act, 2000, Section 43 (Penalty and compensation] for damage to computer, computer system, etc) (p.19, `it_en:43:2`); [3] The Information Technology Act, 2000, Section 66F (Punishment for cyber terrorism) (p.25, `it_en:66f:1`); [4] The Information Technology Act, 2000, Section 66C (Punishment for identity theft) (p.24, `it_en:66c:1`); [5] The Information Technology Act, 2000, Section 65 (Tampering with computer source documents) (p.23, `it_en:65:1`); [6] The Information Technology Act, 2000, Section 66 (Computer related offences) (p.23, `it_en:66:1`); [7] The Information Technology Act, 2000, Section 66D (Punishment for cheating by personation by using computer resource) (p.24, `it_en:66d:1`)

**Generated answer:**

> The penalty for hacking a computer system depends on the specific act committed, as defined in the Information Technology Act, 2000.
>
> If a person accesses or secures access to a computer system without permission, downloads or copies data, introduces a computer contaminant, damages a computer system, disrupts access, or provides assistance to facilitate unauthorized access, they are liable to pay damages by way of compensation under Section 43 [1]. However, Section 43 does not specify a criminal penalty; it only mandates compensation.
>
> For criminal penalties, Section 66 of the Act applies if the act is done dishonestly or fraudulently and falls under the acts listed in Section 43. Under Section 66, such a person shall be punishable with imprisonment for a term which may extend to three years or with a fine which may extend to five lakh rupees, or with both [6].
>
> Additionally, if the hacking involves denial of access to authorized users or attempts to penetrate a computer resource without authorization, and such actions are likely to cause damage to property, disruption of essential services, or affect critical infrastructure, the act may constitute cyber terrorism under Section 66F. In that case, the offender may be punishable with imprisonment which may extend to life [3].
>
> Therefore, the penalty for hacking a computer system is:
>
> - Compensation under Section 43 [1], if damage occurs;
> - Imprisonment up to three years and/or a fine up to five lakh rupees under Section 66 [6], if the act is dishonest or fraudulent;
> - Imprisonment up to life under Section 66F [3], if the act constitutes cyber terrorism.
>
> Note: The term "hacking" is not explicitly defined in the sources, but the acts described in Section 43 and Section 66 cover unauthorized access, disruption, and damage to computer systems. The specific penalty depends on whether the act falls under a broader offence like cyber terrorism.

**Notes shown to the user:** Check: some sentences add explanation that does not appear in the cited sources. Rely on the source text.

**Verification:** refusal=False | errors=[] | warnings=['weak_support', 'weak_support', 'weak_support'] | quotes checked=0

**Context:** 7047 of 10000 characters; included 7 chunks, excluded [('it_en:66b:1', 'provision_cap'), ('it_en:66a:1', 'provision_cap'), ('it_en:67a:1', 'provision_cap'), ('it_en:84c:1', 'provision_cap'), ('it_en:67:1', 'provision_cap'), ('it_en:72a:1', 'provision_cap'), ('it_en:74:1', 'provision_cap'), ('it_en:71:1', 'provision_cap')]

**Checks:** PASS status, PASS expected in retrieval top-10, PASS expected in sources given to model, PASS answer mentions expected words, PASS no forbidden claims, PASS has citation markers, PASS citations point to real sources, PASS no unverified section numbers, PASS cited source text verbatim in PDF, PASS every citation matched to its exact retrieved chunk, PASS disclaimer present

---

## S9: What is the right to freedom of speech and expression?

*Category:* Semantic | *status:* `answered` | *best distance:* 0.394 | *timings:* {'rewrite_s': 0.0, 'retrieval_s': 2.17, 'generation_s': 55.43, 'total_s': 57.61}

**Expected provisions:** ('constitution_en', '19')

**Retrieved chunks (top 6):**

| # | Chunk | Provision | Title | Distance | Match |
|---|---|---|---|---|---|
| 1 | `constitution_en:19:1` | The Constitution of India article 19 | Protection of certain rights regarding freedom of speech, et | 0.394 | semantic |
| 2 | `constitution_en:105:1` | The Constitution of India article 105 | Powers, privileges, etc., of the Houses of Parliament and of | 0.467 | semantic |
| 3 | `constitution_en:194:1` | The Constitution of India article 194 | Powers, privileges, etc., of the Houses of Legislatures and  | 0.477 | semantic |
| 4 | `constitution_en:25:1` | The Constitution of India article 25 | Freedom of conscience and free profession, practice and prop | 0.49 | semantic |
| 5 | `constitution_en:86:1` | The Constitution of India article 86 | Right of President to address and send messages to Houses | 0.506 | semantic |
| 6 | `constitution_en:19:2` | The Constitution of India article 19 | Protection of certain rights regarding freedom of speech, et | 0.51 | semantic |

**Sources given to the model:** [1] The Constitution of India, Article 19 (Protection of certain rights regarding freedom of speech, etc) (p.40, `constitution_en:19:1`); [2] The Constitution of India, Article 19 (Protection of certain rights regarding freedom of speech, etc) (p.41, `constitution_en:19:2`); [3] The Constitution of India, Article 105 (Powers, privileges, etc., of the Houses of Parliament and of the members and committees thereof) (p.78, `constitution_en:105:1`); [4] The Constitution of India, Article 194 (Powers, privileges, etc., of the Houses of Legislatures and of the members and committees thereof) (p.118, `constitution_en:194:1`); [5] The Constitution of India, Article 25 (Freedom of conscience and free profession, practice and propagation of religion) (p.45, `constitution_en:25:1`); [6] The Constitution of India, Article 86 (Right of President to address and send messages to Houses) (p.71, `constitution_en:86:1`); [7] The Constitution of India, Article 361A (Protection of publication of proceedings of Parliament and State Legislatures) (p.251, `constitution_en:361a:1`)

**Generated answer:**

> The right to freedom of speech and expression is a fundamental right conferred upon all citizens under Article 19(1)(a) of the Constitution of India. It includes the right to express one's views and opinions freely, without interference by the state, subject to reasonable restrictions in the interests of the sovereignty and integrity of India, the security of the State, friendly relations with foreign States, public order, decency or morality, or in relation to contempt of court, defamation, or incitement to an offence. [1]

**Verification:** refusal=False | errors=[] | warnings=[] | quotes checked=0

**Context:** 8550 of 10000 characters; included 7 chunks, excluded [('constitution_en:177:1', 'provision_cap'), ('constitution_en:29:1', 'provision_cap'), ('constitution_en:21:1', 'provision_cap'), ('bns_en:353:1', 'provision_cap'), ('bns_en:36:1', 'provision_cap'), ('constitution_en:88:1', 'provision_cap'), ('constitution_en:350:1', 'provision_cap'), ('constitution_en:30:1', 'provision_cap')]

**Checks:** PASS status, PASS expected in retrieval top-10, PASS expected in sources given to model, PASS answer mentions expected words, PASS no forbidden claims, PASS has citation markers, PASS citations point to real sources, PASS no unverified section numbers, FAIL cited source text verbatim in PDF, PASS every citation matched to its exact retrieved chunk, PASS disclaimer present

---

## S10: What are the fundamental duties of citizens?

*Category:* Semantic | *status:* `answered` | *best distance:* 0.319 | *timings:* {'rewrite_s': 0.0, 'retrieval_s': 2.2, 'generation_s': 75.62, 'total_s': 77.84}

**Expected provisions:** ('constitution_en', '51A')

**Retrieved chunks (top 6):**

| # | Chunk | Provision | Title | Distance | Match |
|---|---|---|---|---|---|
| 1 | `constitution_en:51a:1` | The Constitution of India article 51A | Fundamental duties | 0.319 | semantic |
| 2 | `constitution_en:47:1` | The Constitution of India article 47 | Duty of the State to raise the level of nutrition and the st | 0.46 | semantic |
| 3 | `constitution_en:10:1` | The Constitution of India article 10 | Continuance of the rights of citizenship | 0.486 | semantic |
| 4 | `constitution_en:366:2` | The Constitution of India article 366 | Definitions | 0.487 | semantic |
| 5 | `constitution_en:seventhschedule:5` | The Constitution of India schedule Seventh Schedule |  | 0.491 | semantic |
| 6 | `constitution_en:320:1` | The Constitution of India article 320 | Functions of Public Service Commissions | 0.494 | semantic |

**Sources given to the model:** [1] The Constitution of India, Article 51A (Fundamental duties) (p.56, `constitution_en:51a:1`); [2] The Constitution of India, Article 47 (Duty of the State to raise the level of nutrition and the standard of living and to improve public health) (p.54, `constitution_en:47:1`); [3] The Constitution of India, Article 10 (Continuance of the rights of citizenship) (p.36, `constitution_en:10:1`); [4] The Constitution of India, Article 366 (Definitions) (p.255, `constitution_en:366:2`); [5] The Constitution of India, Article 320 (Functions of Public Service Commissions) (p.211, `constitution_en:320:1`); [6] The Constitution of India, Article 15 (Prohibition of discrimination on grounds of religion, race, caste, sex or place of birth) (p.37, `constitution_en:15:1`)

**Generated answer:**

> The fundamental duties of citizens are as follows:
>
> (a) to abide by the Constitution and respect its ideals and institutions, the National Flag and the National Anthem; [1]  
> (b) to cherish and follow the noble ideals which inspired our national struggle for freedom; [1]  
> (c) to uphold and protect the sovereignty, unity and integrity of India; [1]  
> (d) to defend the country and render national service when called upon to do so; [1]  
> (e) to promote harmony and the spirit of common brotherhood amongst all the people of India transcending religious, linguistic and regional or sectional diversities; to renounce practices derogatory to the dignity of women; [1]  
> (f) to value and preserve the rich heritage of our composite culture; [1]  
> (g) to protect and improve the natural environment including forests, lakes, rivers and wild life, and to have compassion for living creatures; [1]  
> (h) to develop the scientific temper, humanism and the spirit of inquiry and reform; [1]  
> (i) to safeguard public property and to abjure violence; [1]  
> (j) to strive towards excellence in all spheres of individual and collective activity so that the nation constantly rises to higher levels of endeavour and achievement; [1]  
> (k) who is a parent or guardian to provide opportunities for education to his child or, as the case may be, ward between the age of six and fourteen years. [1]
>
> These duties are enshrined in Article 51A of the Constitution of India. [1]

**Verification:** refusal=False | errors=[] | warnings=[] | quotes checked=0

**Context:** 7625 of 10000 characters; included 6 chunks, excluded [('constitution_en:5:1', 'provision_cap'), ('constitution_en:39:1', 'provision_cap'), ('constitution_en:78:1', 'provision_cap'), ('constitution_en:8:1', 'provision_cap'), ('constitution_en:11:1', 'provision_cap'), ('constitution_en:375:1', 'provision_cap'), ('constitution_en:seventhschedule:5', 'provision_cap'), ('constitution_en:seventhschedule:10', 'provision_cap')]

**Checks:** PASS status, PASS expected in retrieval top-10, PASS expected in sources given to model, FAIL answer mentions expected words, PASS no forbidden claims, PASS has citation markers, PASS citations point to real sources, PASS no unverified section numbers, FAIL cited source text verbatim in PDF, PASS every citation matched to its exact retrieved chunk, PASS disclaimer present

---

## S11: What is anticipatory bail?

*Category:* Semantic | *status:* `answered` | *best distance:* 0.489 | *timings:* {'rewrite_s': 0.0, 'retrieval_s': 2.14, 'generation_s': 41.77, 'total_s': 43.91}

**Expected provisions:** ('bnss_en', '482')

**Retrieved chunks (top 6):**

| # | Chunk | Provision | Title | Distance | Match |
|---|---|---|---|---|---|
| 1 | `bnss_en:thefirstschedule:38` | Bharatiya Nagarik Suraksha Sanhita, 2023 schedule The First Schedule |  | 0.489 | semantic |
| 2 | `bnss_en:2:1` | Bharatiya Nagarik Suraksha Sanhita, 2023 section 2 | Definitions. | 0.489 | semantic |
| 3 | `bnss_en:thefirstschedule:33` | Bharatiya Nagarik Suraksha Sanhita, 2023 schedule The First Schedule |  | 0.503 | semantic |
| 4 | `bnss_en:thefirstschedule:39` | Bharatiya Nagarik Suraksha Sanhita, 2023 schedule The First Schedule |  | 0.508 | semantic |
| 5 | `bnss_en:thefirstschedule:37` | Bharatiya Nagarik Suraksha Sanhita, 2023 schedule The First Schedule |  | 0.511 | semantic |
| 6 | `bnss_en:483:1` | Bharatiya Nagarik Suraksha Sanhita, 2023 section 483 | Special powers of High Court or Court of Session regarding b | 0.512 | semantic |

**Sources given to the model:** [1] Bharatiya Nagarik Suraksha Sanhita, 2023, Section 2 (Definitions.) (p.46, `bnss_en:2:1`); [2] Bharatiya Nagarik Suraksha Sanhita, 2023, Section 483 (Special powers of High Court or Court of Session regarding bail.) (p.247, `bnss_en:483:1`); [3] Bharatiya Nagarik Suraksha Sanhita, 2023, Section 485 (Bond of accused and sureties.) (p.247, `bnss_en:485:1`); [4] Bharatiya Nagarik Suraksha Sanhita, 2023, Section 488 (Power to order sufficient bail when that first taken is insufficient.) (p.248, `bnss_en:488:1`); [5] Bharatiya Nyaya Sanhita, 2023, Section 269 (Failure by person released on bail bond or bond to appear in Court) (p.83, `bns_en:269:1`); [6] Bharatiya Nagarik Suraksha Sanhita, 2023, Section 478 (CHAPTER XXXV PROVISIONS AS TO BAIL AND BONDS In what cases bail to be taken.) (p.243, `bnss_en:478:1`)

**Generated answer:**

> The available documents do not answer the question. None of the provided sources define or mention "anticipatory bail."

**Verification:** refusal=True | errors=[] | warnings=[] | quotes checked=0

**Context:** 7400 of 10000 characters; included 6 chunks, excluded [('bnss_en:481:1', 'provision_cap'), ('bnss_en:480:1', 'provision_cap'), ('bnss_en:thefirstschedule:38', 'provision_cap'), ('bnss_en:thefirstschedule:33', 'provision_cap'), ('bnss_en:thefirstschedule:39', 'provision_cap'), ('bnss_en:thefirstschedule:37', 'provision_cap'), ('bnss_en:thefirstschedule:19', 'provision_cap'), ('bnss_en:thefirstschedule:18', 'provision_cap')]

**Checks:** PASS status, FAIL expected in retrieval top-10, FAIL expected in sources given to model, PASS answer mentions expected words, PASS no forbidden claims, FAIL has citation markers, PASS citations point to real sources, PASS no unverified section numbers, FAIL cited source text verbatim in PDF, PASS every citation matched to its exact retrieved chunk, PASS disclaimer present

*Missing from retrieval:* ['bnss_en:482'] | *missing from sources:* ['bnss_en:482']

---

## S12: When can the police arrest without a warrant?

*Category:* Semantic | *status:* `ERROR` | *best distance:* -1 | *timings:* {}

**Expected provisions:** ('bnss_en', '35')

**Retrieved chunks (top 6):**

| # | Chunk | Provision | Title | Distance | Match |
|---|---|---|---|---|---|

**Sources given to the model:** none

**Generated answer:**

> ERROR: timed out

**Checks:** FAIL ran without error

---

## S13: How do I file a complaint against a company for a defective product?

*Category:* Semantic | *status:* `ERROR` | *best distance:* -1 | *timings:* {}

**Expected provisions:** ('any', [('cp_en', '35'), ('cp_en', '2'), ('cp_en', '34')])

**Retrieved chunks (top 6):**

| # | Chunk | Provision | Title | Distance | Match |
|---|---|---|---|---|---|

**Sources given to the model:** none

**Generated answer:**

> ERROR: Server error '500 Internal Server Error' for url 'http://localhost:11434/api/embed'
> For more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/500

**Checks:** FAIL ran without error

---

## S14: What counts as an unfair trade practice?

*Category:* Semantic | *status:* `ERROR` | *best distance:* -1 | *timings:* {}

**Expected provisions:** ('cp_en', '2')

**Retrieved chunks (top 6):**

| # | Chunk | Provision | Title | Distance | Match |
|---|---|---|---|---|---|

**Sources given to the model:** none

**Generated answer:**

> ERROR: timed out

**Checks:** FAIL ran without error

---

