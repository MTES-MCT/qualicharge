"""Dashboard consent app JSON schemas.

JSON schemas:
- company_schema
- representative_schema
- control_authority_schema
"""

company_schema = {
    "type": "object",
    "properties": {
        "company_type": {"type": ["string", "null"], "maxLength": 255},
        "name": {"type": ["string", "null"], "maxLength": 255},
        "legal_form": {"type": ["string", "null"], "maxLength": 50},
        "trade_name": {"type": ["string", "null"], "maxLength": 255},
        "siret": {
            "type": ["string", "null"],
            "maxLength": 14,
            "pattern": "^[0-9]{14}$",
        },
        "naf": {
            "type": ["string", "null"],
            "maxLength": 5,
            "pattern": "^[0-9]{4}[A-Za-z]$",
        },
        "address": {
            "type": "object",
            "properties": {
                "line_1": {"type": ["string", "null"], "maxLength": 255},
                "line_2": {"type": ["string", "null"], "maxLength": 255},
                "zip_code": {
                    "type": ["string", "null"],
                    "maxLength": 5,
                    "pattern": "^[0-9]{5}$",
                },
                "city": {"type": ["string", "null"], "maxLength": 255},
            },
            "required": ["line_1", "zip_code", "city"],
        },
    },
    "required": [
        "company_type",
        "name",
        "legal_form",
        "trade_name",
        "siret",
        "naf",
        "address",
    ],
    "additionalProperties": False,
}

representative_schema = {
    "type": "object",
    "properties": {
        "firstname": {"type": ["string", "null"], "maxLength": 150},
        "lastname": {"type": ["string", "null"], "maxLength": 150},
        "email": {"type": ["string", "null"], "format": "email"},
        "phone": {"type": ["string", "null"], "maxLength": 20},
    },
    "required": ["firstname", "lastname", "email", "phone"],
    "additionalProperties": False,
}

control_authority_schema = {
    "type": "object",
    "properties": {
        "name": {"type": ["string", "null"], "maxLength": 255},
        "represented_by": {"type": ["string", "null"], "maxLength": 255},
        "email": {"type": ["string", "null"], "format": "email"},
        "address": {
            "type": "object",
            "properties": {
                "line_1": {"type": ["string", "null"], "maxLength": 255},
                "line_2": {"type": ["string", "null"], "maxLength": 255},
                "zip_code": {
                    "type": ["string", "null"],
                    "maxLength": 5,
                    "pattern": "^[0-9]{5}$",
                },
                "city": {"type": ["string", "null"], "maxLength": 255},
            },
            "required": ["line_1", "zip_code", "city"],
        },
    },
    "required": ["name", "represented_by", "email", "address"],
    "additionalProperties": False,
}
