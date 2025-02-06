---
jupyter:
  jupytext:
    text_representation:
      extension: .md
      format_name: markdown
      format_version: '1.3'
      jupytext_version: 1.16.2
  kernelspec:
    display_name: Python 3
    language: python
    name: python3
---

```python
import requests # type: ignore
import os
```

```python
def migration_questions(
        url_from: str, 
        url_to: str, 
        key_from: str, 
        key_to: str, 
        mapping_col: dict, 
        mapping_db: dict, 
        mapping_field: dict = None,
        id_snippet: dict = None,
        log: bool = False):
    """migration des questions Metabase de 'from' vers 'to'. 
    
    Seules sont migrées les questions présentes dans les collections 'from' définies dans mapping_col (keys).
    Les collections 'to' définies dans mapping_col (values) doivent exister.
    Mapping_db contient la correspondance des bases utilisées.
    Mapping_col contient la correspondance des collections d'appartenance des questions.
    Mapping_field contient la correspondance des id des champs utilisés par les variables.
    Les 'snippet' utilisés sont à créer au préalable dans 'to' (id_snippet contient le nom et l'id de chaque snippet).
    """
    api_card = '/api/card'
    template = { "name": "empty", 
                "cache_ttl": None, 
                "type": "question", 
                "dataset_query": {}, 
                "display": "table",
                "description": "empty", 
                "visualization_settings": {}, 
                "parameters": [], 
                "parameter_mappings": [],
                "archived": False,
                "enable_embedding": False,
                "embedding_params": None,
                "collection_id": None,
                "collection_position": None,
                "result_metadata": None}
    mapping_field = {} if not mapping_field else mapping_field
    id_snippet = {} if not id_snippet else id_snippet

    # liste des questions à copier
    response = requests.get(url_from + api_card,
                            headers={'x-api-key': key_from}).json()
    questions = [resp_js for resp_js in response]
    
    # copie des questions
    for question in questions:
        if question["collection_id"] in mapping_col :
            
            payload = template.copy()
            for item in ["name", "dataset_query", "display", "description", 
                         "visualization_settings", "parameters", "parameter_mappings"]:
                payload[item] = question[item]
                # payload["name"] = "test - " + payload["name"]
            payload["collection_id"] = mapping_col[question["collection_id"]]
            payload["dataset_query"]["database"] = mapping_db[question["dataset_query"]["database"]]
            if "native" in payload["dataset_query"] and "template-tags" in payload["dataset_query"]["native"]:
                template_tags = payload["dataset_query"]["native"]["template-tags"]
                for tag in template_tags:
                    if "dimension" in template_tags[tag]:
                        id_field = template_tags[tag]["dimension"][1]
                        new_id = mapping_field.get(id_field, id_field)
                        payload["dataset_query"]["native"]["template-tags"][tag]["dimension"][1] = new_id
                    elif "snippet-name" in template_tags[tag]:
                        new_id = id_snippet.get(template_tags[tag]["snippet-name"], template_tags[tag]["snippet-id"])
                        payload["dataset_query"]["native"]["template-tags"][tag]["snippet-id"] = new_id
            response = requests.post(url_to + api_card, headers={'x-api-key': key_to}, json=payload).json()
            if log:
                print(response)
```

```python
url_staging = os.getenv("URL_STAGING")
api_key_staging = os.getenv("API_KEY_STAGING")
api_key_local = os.getenv("API_KEY_LOCAL")
url_local = 'http://localhost:3000'

# collections sur staging
# 22 : questions bilan hebdo
# 18 : questions error-tracking
# 12 : questions open-data
# 20 : questions internes
# 17 : questions données dynamiques
mapping_col = {22: 9,  12: 11, 18: 10, 20: 12, 17: 13}
mapping_col = {12: 5}
# 2 : 
mapping_db = {2: 2}
# fields sur staging
# 515 : departement
# 530 : region
# 111 : operateur
# 77  : amenageur
# 104 : code_commune
# 125 : pdc
# 168 : station
mapping_field = {515: 283, 111: 329, 530: 365}
id_snippet = {"join city-dep-reg": 2,
              "join city-dep-reg-nat": 3,
              "join loc-city-dep-reg": 4,
              "join stat-loc-city-dep-reg": 1, 
              "join stat-loc-city-dep-reg_nat": 5}

migration_questions(url_staging, url_local, api_key_staging, api_key_local, 
                    mapping_col, mapping_db, mapping_field, id_snippet)
```
