import requests
import json
from rapidfuzz import fuzz
import pandas as pd

# Constants for the ACRA affiliated dataset and non‑ACRA affiliated dataset
DATASET_ID = "d_3f960c10fed6145404ca7b821f263b87"  # ACRA
NON_ACRA_COMPANIES_DATASET = "d_b1d2b840ab9e993570c037b706b39bb8"  # Non‑ACRA
BASE_URL = "https://data.gov.sg/api/action/datastore_search"

def search_dataset_by_filters(filters: dict, limit: int = 1, resource_id: str = DATASET_ID):
    """
    Searches the dataset using the provided filters on the specified resource.
    Returns a list of matching records.
    """
    params = {
        "resource_id": resource_id,
        "filters": json.dumps(filters),
        "limit": limit
    }
    response = requests.get(BASE_URL, params=params)
    if response.status_code == 200:
        result = response.json().get("result", {})
        records = result.get("records", [])
        return records
    else:
        return []

def search_dataset_by_query(query: str, limit: int = 5, resource_id: str = DATASET_ID):
    """
    Performs a full-text search on the dataset using the query on the specified resource.
    Returns a list of matching records.
    """
    params = {
        "resource_id": resource_id,
        "q": query,
        "limit": limit
    }
    response = requests.get(BASE_URL, params=params)
    if response.status_code == 200:
        result = response.json().get("result", {})
        records = result.get("records", [])
        return records
    else:
        return []

def run_dataset_verifications(extracted_fields: dict, google_sheet_row: dict, similarity_threshold: float = 80) -> pd.DataFrame:
    """
    Runs three verification rules against both the ACRA and non‑ACRA datasets:
    
      Rule 1: If extracted_fields has a company name, perform a full‑text query on "entity_name" and return the UEN.
      Rule 2: If extracted_fields has a UEN, search using a filter on "uen" and return the company name.
      Rule 3: If the Google Sheet row has a UEN, search using a filter on "uen" and return the company name.
    
    For each rule, both datasets are queried and two rows (one per dataset) are added.
    
    Returns a pandas DataFrame with only the following columns:
      - Verification Type
      - Input Value
      - Dataset (ACRA or Non‑ACRA)
      - Dataset Value
    """
    results = []
    
    # --- Rule 1: Extracted Company Name -> search on "entity_name" ---
    extracted_company = extracted_fields.get("company", "").strip()
    if extracted_company:
        # Query ACRA dataset:
        records_acra = search_dataset_by_query(extracted_company, limit=5, resource_id=DATASET_ID)
        best_similarity_acra = 0
        best_record_acra = None
        for rec in records_acra:
            entity_name = rec.get("entity_name", "")
            sim = fuzz.ratio(extracted_company.lower(), entity_name.lower())
            if sim > best_similarity_acra:
                best_similarity_acra = sim
                best_record_acra = rec
        if best_record_acra and best_similarity_acra >= similarity_threshold:
            dataset_value_acra = best_record_acra.get("uen", "N/A")
        else:
            dataset_value_acra = "N/A"
        results.append({
            "Verification Type": "Extracted Company -> Dataset UEN (ACRA)",
            "Input Value": extracted_company,
            "Dataset": "ACRA",
            "Dataset Value": dataset_value_acra
        })
        
        # Query Non‑ACRA dataset:
        records_non_acra = search_dataset_by_query(extracted_company, limit=5, resource_id=NON_ACRA_COMPANIES_DATASET)
        best_similarity_non_acra = 0
        best_record_non_acra = None
        for rec in records_non_acra:
            entity_name = rec.get("entity_name", "")
            sim = fuzz.ratio(extracted_company.lower(), entity_name.lower())
            if sim > best_similarity_non_acra:
                best_similarity_non_acra = sim
                best_record_non_acra = rec
        if best_record_non_acra and best_similarity_non_acra >= similarity_threshold:
            dataset_value_non_acra = best_record_non_acra.get("uen", "N/A")
        else:
            dataset_value_non_acra = "N/A"
        results.append({
            "Verification Type": "Extracted Company -> Dataset UEN (Non‑ACRA)",
            "Input Value": extracted_company,
            "Dataset": "Non‑ACRA",
            "Dataset Value": dataset_value_non_acra
        })
    else:
        results.append({
            "Verification Type": "Extracted Company -> Dataset UEN (ACRA)",
            "Input Value": "N/A",
            "Dataset": "ACRA",
            "Dataset Value": "N/A"
        })
        results.append({
            "Verification Type": "Extracted Company -> Dataset UEN (Non‑ACRA)",
            "Input Value": "N/A",
            "Dataset": "Non‑ACRA",
            "Dataset Value": "N/A"
        })
        
    # --- Rule 2: Extracted UEN -> search on "uen" ---
    extracted_uen = extracted_fields.get("uen", "").strip()
    if extracted_uen:
        # Query ACRA dataset:
        records_acra = search_dataset_by_filters({"uen": extracted_uen}, limit=1, resource_id=DATASET_ID)
        if records_acra:
            dataset_value_acra = records_acra[0].get("entity_name", "N/A")
        else:
            dataset_value_acra = "N/A"
        results.append({
            "Verification Type": "Extracted UEN -> Dataset Company (ACRA)",
            "Input Value": extracted_uen,
            "Dataset": "ACRA",
            "Dataset Value": dataset_value_acra
        })
        
        # Query Non‑ACRA dataset:
        records_non_acra = search_dataset_by_filters({"uen": extracted_uen}, limit=1, resource_id=NON_ACRA_COMPANIES_DATASET)
        if records_non_acra:
            dataset_value_non_acra = records_non_acra[0].get("entity_name", "N/A")
        else:
            dataset_value_non_acra = "N/A"
        results.append({
            "Verification Type": "Extracted UEN -> Dataset Company (Non‑ACRA)",
            "Input Value": extracted_uen,
            "Dataset": "Non‑ACRA",
            "Dataset Value": dataset_value_non_acra
        })
    else:
        results.append({
            "Verification Type": "Extracted UEN -> Dataset Company (ACRA)",
            "Input Value": "N/A",
            "Dataset": "ACRA",
            "Dataset Value": "N/A"
        })
        results.append({
            "Verification Type": "Extracted UEN -> Dataset Company (Non‑ACRA)",
            "Input Value": "N/A",
            "Dataset": "Non‑ACRA",
            "Dataset Value": "N/A"
        })
        
    # --- Rule 3: Google Sheet row UEN -> search on "uen" ---
    google_sheet_uen = str(google_sheet_row.get("Employer UEN (mandatory if sponsorship type = employer)", "")).strip()
    if google_sheet_uen:
        # Query ACRA dataset:
        records_acra = search_dataset_by_filters({"uen": google_sheet_uen}, limit=1, resource_id=DATASET_ID)
        if records_acra:
            dataset_value_acra = records_acra[0].get("entity_name", "N/A")
        else:
            dataset_value_acra = "N/A"
        results.append({
            "Verification Type": "Google Sheet UEN -> Dataset Company (ACRA)",
            "Input Value": google_sheet_uen,
            "Dataset": "ACRA",
            "Dataset Value": dataset_value_acra
        })
        
        # Query Non‑ACRA dataset:
        records_non_acra = search_dataset_by_filters({"uen": google_sheet_uen}, limit=1, resource_id=NON_ACRA_COMPANIES_DATASET)
        if records_non_acra:
            dataset_value_non_acra = records_non_acra[0].get("entity_name", "N/A")
        else:
            dataset_value_non_acra = "N/A"
        results.append({
            "Verification Type": "Google Sheet UEN -> Dataset Company (Non‑ACRA)",
            "Input Value": google_sheet_uen,
            "Dataset": "Non‑ACRA",
            "Dataset Value": dataset_value_non_acra
        })
    else:
        results.append({
            "Verification Type": "Google Sheet UEN -> Dataset Company (ACRA)",
            "Input Value": "N/A",
            "Dataset": "ACRA",
            "Dataset Value": "N/A"
        })
        results.append({
            "Verification Type": "Google Sheet UEN -> Dataset Company (Non‑ACRA)",
            "Input Value": "N/A",
            "Dataset": "Non‑ACRA",
            "Dataset Value": "N/A"
        })
    
    # Return a DataFrame with only the desired columns.
    df = pd.DataFrame(results)
    # Ensure columns are in order: Verification Type, Input Value, Dataset, Dataset Value.
    df = df[["Verification Type", "Input Value", "Dataset", "Dataset Value"]]
    return df