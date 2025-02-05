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
import requests
import os
from urllib.parse import urljoin
from datetime import datetime

URL_QUALICHARGE = os.getenv("URL_QUALICHARGE")
API_KEY_QUALICHARGE = os.getenv("API_KEY_QUALICHARGE")
API_KEY_LOCAL =  os.getenv("API_KEY_LOCAL")
URL_LOCAL = 'http://localhost:3000'

ENV_LOCAL = [URL_LOCAL, API_KEY_LOCAL]
ENV_QUALI = [URL_QUALICHARGE, API_KEY_QUALICHARGE]

DB_STAGING = 2
DB_PROD = 4
```

```python
def migration_questions(
        url_from: str, 
        key_from: str, 
        url_to: str, 
        key_to: str, 
        db_to: int,
        mapping_col: dict, 
        mapping_field: dict,
        mapping_snip: dict,
        mapping_quest: dict|None = None,
        log: int = 0) -> dict:
    """migration des questions Metabase de 'from' vers 'to'. 
    
    La fonction retourne le mapping des id des questions.
    les questions sont migrées à parir des collections de 'from' vers celles de 'to'.
    Les dictionnaires mapping_xxx contiennent les id de 'from' (keys) et ceux de 'to' (values)
    Seules sont migrées les questions présentes dans les collections définies dans mapping_col.
    
    Mapping_db contient la correspondance des bases de données.
    Mapping_col contient la correspondance des collections des questions à migrer.
    Mapping_field contient la correspondance des id des champs (utilisés pour la migration des variables).
    Mapping_snip contient la correspondance des id des 'snippet'.
    Mapping_quest contient la correspondance des questions déja migrées (utiles unquement si les requêtes contiennent des includes '{{question}}')
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
    mapping_quest = mapping_quest or {}
    new_mapping_quest = mapping_quest.copy()

    # liste des questions
    questions = requests.get(urljoin(url_from, api_card),
                            headers={'x-api-key': key_from}).json()

    # copie des questions
    for question in questions:
        if question["collection_id"] not in mapping_col :
            continue
        tags = ["name", "dataset_query", "display", "description",
                "visualization_settings", "parameters", "parameter_mappings"]
        payload = template.copy() | dict(item for item in question.items() if item[0] in tags)
        payload["collection_id"] = mapping_col[question["collection_id"]]
        payload["dataset_query"]["database"] = db_to
        if "native" in payload["dataset_query"] and "template-tags" in payload["dataset_query"]["native"]:
            template_tags = payload["dataset_query"]["native"]["template-tags"]
            updated_tags = {}
            for tag in template_tags:
                match template_tags[tag]["type"]:
                    case "dimension": # variables
                        new_id = mapping_field[template_tags[tag]["dimension"][1]]
                        template_tags[tag]["dimension"][1] = new_id
                    case "snippet": 
                        new_id = mapping_snip[template_tags[tag]["snippet-id"]]
                        template_tags[tag]["snippet-id"] = new_id
                    case "card": # questions incluses
                        card_id = template_tags[tag]["card-id"]
                        new_id = mapping_quest[card_id]
                        template_tags[tag]["card-id"] = new_id
                        new_tag = template_tags[tag]["name"].replace(str(card_id), str(new_id), 1)
                        new_display_name = template_tags[tag]["name"].replace(str(card_id), str(new_id), 1)
                        template_tags[tag]["name"] = new_tag
                        template_tags[tag]["display-name"] = new_display_name
                        new_query = payload["dataset_query"]["native"]["query"].replace("#" + str(card_id), "#" + str(new_id), 1)
                        payload["dataset_query"]["native"]["query"] = new_query
                        updated_tags[tag] = new_tag
                    case _: ...
            for tag in updated_tags:
                template_tags[new_tag] = template_tags[tag]
                del template_tags[tag]
        
        new_quest_items = requests.post(urljoin(url_to, api_card), headers={'x-api-key': key_to}, json=payload).json()
        new_mapping_quest[question['id']] = new_quest_items["id"] if "id" in new_quest_items else None # id ?
        if log == 1:
            print(f"migrated question {question['id']} {new_mapping_quest[question['id']]} : {question['name']}")
        if log > 1:
            print(f"migrated question {question['id']} : {new_quest_items}")
    return new_mapping_quest
```

```python
def migration_collections(
        url_from: str, 
        key_from: str, 
        url_to: str, 
        key_to: str,
        list_from: list[int],
        log:int = 0) -> dict:
    """migration des collections Metabase de 'from' vers 'to'. 
    
    Les collections définies par leurs id dans list_from sont créées dans une collection "migration xxx" (xxx est la date).
    La collection créée est elle-même incluse dans une collection "migrated collections"
    La fonction retourne le mapping des id des collections.
    """
    api_col = '/api/collection'
    root_col_name = "migrated collections"
    migration_col_name = "migration " + datetime.now().isoformat(timespec='seconds')
    template = {
                "name": None,
                "description": None,
                "parent_id": None,
                "namespace": None,
                "authority_level": None
                }
    mapping_col = {}

    # root collection
    list_col = requests.get(urljoin(url_to, api_col), headers={'x-api-key': key_to}).json()
    root_col_id = None
    for collec in list_col:
        if collec['name'] == root_col_name:
             root_col_id = collec["id"]
             break
    if not root_col_id:
        payload = template.copy() | {"name": root_col_name}
        root_col_items = requests.post(urljoin(url_to, api_col), headers={'x-api-key': key_to}, json=payload).json()
        root_col_id = root_col_items["id"]
        if log >= 1:
            print("root migrated collection created")
    
    # 'migrated collections'
    payload = template.copy() | {"name": migration_col_name, "parent_id": root_col_id}
    migration_col_items = requests.post(urljoin(url_to, api_col), headers={'x-api-key': key_to}, json=payload).json()
    migration_col_id = migration_col_items["id"]

    # 'migration xxx' collections
    for col_id in list_from:
        col_items = requests.get(urljoin(url_from, api_col + "/" + str(col_id)), headers={'x-api-key': key_from}).json()
        tags = ["name", "description"]
        payload = template.copy() | dict(item for item in col_items.items() if item[0] in tags)
        payload["parent_id"] = migration_col_id
        new_col_items = requests.post(urljoin(url_to, api_col), headers={'x-api-key': key_to}, json=payload).json()
        mapping_col[col_id] = new_col_items["id"]
        if log == 1:
            print(f"migrated collection {col_id} - {new_col_items['id']} : {payload['name']}")
        if log > 1:
            print(f"migrated collection {col_id} : {new_col_items}")
    return mapping_col
```

```python
def mapping_fields(
        url_from: str, 
        key_from: str,
        url_to: str, 
        key_to: str,
        db_from: int,
        db_to: int) -> dict:
    """retourne la correspondance des id des champs de la base de données définie par 'mapping_db'."""
    api_db = '/api/database/'
    param = "?include=tables.fields"
    ext_from = api_db + str(db_from) + param
    ext_to = api_db + str(db_to) + param

    db_items_from = requests.get(urljoin(url_from, ext_from), headers={'x-api-key': key_from}).json()
    mapping_from = {table['name'] + '.' + field['name'] : field['id'] 
                    for table in db_items_from['tables'] 
                    for field in table['fields']}
    
    db_items_to = requests.get(urljoin(url_to, ext_to), headers={'x-api-key': key_to}).json()
    mapping_to = {table['name'] + '.' + field['name'] : field['id']
                  for table in db_items_to['tables'] 
                  for field in table['fields']}
    
    inv_mapping_from = {v: k for k,v in mapping_from.items()}
    return {id_from: mapping_to[inv_mapping_from[id_from]] 
            for id_from in inv_mapping_from 
            if inv_mapping_from[id_from] in mapping_to }
```

```python
def migration_snippets(
        url_from: str, 
        key_from: str, 
        url_to: str, 
        key_to: str,
        log:int = 0) -> dict:
    """migration des snippets Metabase de 'from' vers 'to'. 
    
    Si un snippet existe déjà, il n'est pas mis à jour.
    La fonction retourne le mapping des id des snippets.
    """
    api_snippet = '/api/native-query-snippet'
    template = {
                "name": "",
                "description": None,
                "collection_id": None,
                "content": ""}
    mapping_snip = {}

    # snippets to migrate
    snippets_from = requests.get(urljoin(url_from, api_snippet), headers={'x-api-key': key_from}).json()
    snippets_to = requests.get(urljoin(url_to, api_snippet), headers={'x-api-key': key_to}).json()
    names_to = {snippet['name']: snippet['id'] for snippet in snippets_to}

    # migrated snippets
    for snippet in snippets_from:
        if snippet['name'] in names_to:
            mapping_snip[snippet["id"]] = names_to[snippet['name']]
            continue
        tags = ["name", "content", "description"]
        payload = template.copy() | dict(item for item in snippet.items() if item[0] in tags)
        new_snip_items = requests.post(urljoin(url_to, api_snippet), headers={'x-api-key': key_to}, json=payload).json()
        
        mapping_snip[snippet["id"]] = new_snip_items["id"]
        if log == 1:
            print(f"migrated snippet {snippet['id']} - {new_snip_items['id']} : {payload['name']}")
        if log > 1:
            print(f"migrated collection {snippet['id']} : {new_snip_items['id']}")
    return mapping_snip
```

```python
env_from = ENV_QUALI
db_from = DB_STAGING

#env_to = ENV_QUALI
env_to = ENV_LOCAL
db_to = DB_STAGING

mapping_fld = mapping_fields(*env_from, *env_to, db_from, db_to)
mapping_snip = migration_snippets(*env_from, *env_to, log=1)

# migration préalable des questions réutilisées dans d'autres questions
list_col_first = [20]
mapping_col1 = migration_collections(*env_from, *env_to, list_col_first, log=1)
mapping_quest = migration_questions(*env_from, *env_to, db_to, mapping_col1, mapping_fld, mapping_snip, log=1)

# migration des autres questions
#list_col = [27, 28, 29, 30, 32] # collections philippe
list_col = [30] # test
mapping_col = migration_collections(*env_from, *env_to, list_col, log=1)
mapping_quest = migration_questions(*env_from, *env_to, db_to, mapping_col, mapping_fld, mapping_snip, 
                                    mapping_quest=mapping_quest, log=1)
```
