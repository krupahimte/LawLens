# Index validation: collection `indian_law_en`

## Validation configuration

| Setting | Value |
|---|---|
| Collection validated | indian_law_en |
| Chroma directory | C:\Users\admin1\Desktop\India_law\chroma_db |
| Run at | 2026-11-06T14:41:20 |
| chromadb version | 1.5.9 |
| Embedding model | bge-m3 |
| ENABLE_HINDI | False |
| Active documents | bns_en, bnss_en, bsa_en, constitution_en, cp_en, it_en |
| Expected top section/article numbers | {"bns_en": 358, "bnss_en": 531, "bsa_en": 170, "cp_en": 107, "it_en": 94, "constitution_en": 395} |
| Known omitted numbers | {"constitution_en": [232, 238, 259, 272]} |
| Required metadata fields | doc_id, act_name, act_name_en, language, unit, section_number, page_start, page_end, part, text_source, chunk_kind |
| Chunk length bounds (characters) | 30..2500 |
| Expected vector dimension | 1024 |
| PDF spot-check | 60 random chunks, seed 7, first and last 50 characters, at most 2 misses tolerated |
| Processed files compared | C:\Users\admin1\Desktop\India_law\data\processed\<doc_id>.jsonl |

Total chunks: **2298**

## Checks

| Check | Result | Detail |
|---|---|---|
| chunk ids equal the processed files (nothing missing, nothing extra) | PASS | collection=2298 expected=2298 missing=0 extra=0 |
| chunk ids are unique | PASS |  |
| no Hindi chunks: every chunk has language=en | PASS | Counter({'en': 2298}) |
| no Devanagari characters in any chunk text | PASS |  |
| only English documents present | PASS | ['bns_en', 'bnss_en', 'bsa_en', 'constitution_en', 'cp_en', 'it_en'] |
| bns_en: every section/article 1..358 present | PASS | chunks=440 distinct numbers=358 missing=[] beyond=[] lettered=0 |
| bnss_en: every section/article 1..531 present | PASS | chunks=723 distinct numbers=531 missing=[] beyond=[] lettered=0 |
| bsa_en: every section/article 1..170 present | PASS | chunks=197 distinct numbers=170 missing=[] beyond=[] lettered=0 |
| cp_en: every section/article 1..107 present | PASS | chunks=134 distinct numbers=107 missing=[] beyond=[] lettered=0 |
| it_en: every section/article 1..94 present | PASS | chunks=136 distinct numbers=94 missing=[] beyond=[] lettered=31 |
| constitution_en: every section/article 1..395 present (known omitted: [232, 238, 259, 272]) | PASS | chunks=668 distinct numbers=391 missing=[] beyond=[] lettered=104 |
| required metadata present on every chunk | PASS | 0 incomplete [] |
| provenance fields correct (text_layer, not low quality, no OCR confidence) | PASS |  |
| chunk_kind is operative or illustration | PASS | Counter({'operative': 2246, 'illustration': 52}) |
| page ranges valid | PASS |  |
| chunk lengths sane (30..2500 characters) | **FAIL** | min=14 max=2183 |
| every vector has 1024 dimensions (BGE-M3) | PASS | {1024} |
| page numbers lie inside the PDFs | PASS | 0 out of range |
| random spot-check: 60 chunks' first and last 50 characters occur on the cited PDF pages | **FAIL** | 56/60 verbatim; failures: [('bns_en:125:1', True, False), ('bnss_en:471:1', False, True), ('bnss_en:403:1', False, True), ('constitution_en:257a:1', False, True)] |

## Coverage by document

| Document | Chunks | Distinct numbers | Expected top number | Missing | Beyond |
|---|---|---|---|---|---|
| bns_en | 440 | 358 | 358 | - | - |
| bnss_en | 723 | 531 | 531 | - | - |
| bsa_en | 197 | 170 | 170 | - | - |
| cp_en | 134 | 107 | 107 | - | - |
| it_en | 136 | 94 | 94 | - | - |
| constitution_en | 668 | 391 | 395 | - | - |
