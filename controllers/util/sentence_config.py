def extract_fields_from_text(text: str) -> dict:
    return {
        "case_info": {
            "case_type": "",          # Regex o NLP posterior
            "court": "",
            "date_filed": "",
            "date_resolved": "",
            "resolution_type": "",
        },
        "case_outcome": {
            "outcome_details": ""
        },
        "reasons": [],
        "rights_and_laws_referenced": []
    }
