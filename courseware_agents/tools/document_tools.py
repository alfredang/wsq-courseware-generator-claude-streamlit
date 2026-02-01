"""
Document Tools

Tool implementations for Document Agent - document verification and validation.

Author: Courseware Generator Team
Date: 26 January 2026
"""

import json


def extract_document_entities(
    file_path: str,
    custom_instructions: str = "Extract the name of the person, company, UEN, masked NRIC, and document date."
) -> str:
    """
    Extract named entities from a document using AI.

    Args:
        file_path: Path to the document (PDF or image)
        custom_instructions: Custom extraction instructions

    Returns:
        Extracted entities as JSON string
    """
    from check_documents.gemini_processor import extract_entities
    from PIL import Image
    import io

    file_extension = file_path.split(".")[-1].lower()

    if file_extension in ["png", "jpg", "jpeg"]:
        with open(file_path, "rb") as f:
            image_bytes = f.read()
        img = Image.open(io.BytesIO(image_bytes))
        result = extract_entities(img, custom_instructions, is_image=True)
        return json.dumps(result)

    elif file_extension == "pdf":
        from check_documents.sup_doc import convert_pdf_to_images

        with open(file_path, "rb") as f:
            pdf_bytes = f.read()

        images = convert_pdf_to_images(pdf_bytes)
        all_entities = {"entities": []}

        for img in images:
            result = extract_entities(img, custom_instructions, is_image=True)
            if "entities" in result:
                all_entities["entities"].extend(result["entities"])

        return json.dumps(all_entities)

    else:
        return json.dumps({"error": f"Unsupported file type: {file_extension}", "entities": []})


def verify_against_training_records(
    extracted_entities_json: str,
    threshold: float = 80.0
) -> str:
    """
    Verify extracted entities against training records.

    Args:
        extracted_entities_json: Entities as JSON string
        threshold: Minimum similarity score for match (0-100)

    Returns:
        Verification results as JSON string
    """
    from check_documents.sup_doc import (
        get_google_sheet_data,
        get_extracted_fields,
        find_best_match
    )

    extracted_entities = json.loads(extracted_entities_json)
    sheet_data = get_google_sheet_data()

    if not sheet_data:
        return json.dumps({
            "status": "error",
            "message": "Could not load training records"
        })

    extracted_fields_list = get_extracted_fields(extracted_entities)

    results = []
    for fields in extracted_fields_list:
        match, score = find_best_match(fields, sheet_data, threshold)

        result = {
            "extracted_name": fields.get("name", ""),
            "extracted_uen": fields.get("uen", ""),
            "extracted_company": fields.get("company", ""),
            "matched": match is not None,
            "match_score": score,
        }

        if match:
            result["matched_record"] = {
                "trainee_name": match.get("Trainee Name (as on government ID)", ""),
                "employer_uen": match.get("Employer UEN (mandatory if sponsorship type = employer)", ""),
            }

        results.append(result)

    return json.dumps({
        "status": "success",
        "verification_results": results,
        "total_records_checked": len(sheet_data)
    })


def verify_company_uen(uen: str) -> str:
    """
    Verify a company UEN against ACRA database.

    Args:
        uen: The UEN to verify

    Returns:
        ACRA verification results as JSON string
    """
    from check_documents.acra_call import search_dataset_by_query

    try:
        result = search_dataset_by_query(uen)
        return json.dumps({
            "status": "success",
            "uen": uen,
            "verification": result
        })
    except Exception as e:
        return json.dumps({
            "status": "error",
            "uen": uen,
            "message": str(e)
        })


def check_document_completeness(file_path: str) -> str:
    """
    Check if a document has all required sections/fields.

    Args:
        file_path: Path to the document

    Returns:
        Completeness check results as JSON string
    """
    entities_json = extract_document_entities(
        file_path,
        "Extract all key information: names, dates, company details, UEN, amounts, and any reference numbers."
    )
    entities = json.loads(entities_json)

    required_fields = ["PERSON", "COMPANY NAME", "DOCUMENT DATE"]
    found_fields = set()

    for entity in entities.get("entities", []):
        entity_type = entity.get("type", "").upper()
        for required in required_fields:
            if required in entity_type:
                found_fields.add(required)

    missing = [f for f in required_fields if f not in found_fields]

    return json.dumps({
        "status": "complete" if not missing else "incomplete",
        "found_fields": list(found_fields),
        "missing_fields": missing,
        "all_entities": entities.get("entities", []),
        "recommendation": "Document appears complete" if not missing else f"Missing: {', '.join(missing)}"
    })
