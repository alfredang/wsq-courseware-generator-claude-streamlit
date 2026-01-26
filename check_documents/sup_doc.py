import streamlit as st
from check_documents.gemini_processor import extract_entities
import os
import tempfile
from PIL import Image
import pandas as pd
import io
import gspread
from rapidfuzz import fuzz
from check_documents.acra_call import run_dataset_verifications, search_dataset_by_filters, search_dataset_by_query
from PyPDF2 import PdfReader, PdfWriter
import json
from typing import Dict, Any, Union
from oauth2client.service_account import ServiceAccountCredentials

# Optional imports - may not be available on all platforms
FITZ_AVAILABLE = False
try:
    import fitz  # PyMuPDF for PDF to image conversion
    FITZ_AVAILABLE = True
except ImportError:
    pass

# Note: Entity extraction now uses OpenRouter via gemini_processor.py
# The google.generativeai package is no longer required

# ------------------------------
# Helper Functions
# ------------------------------

def unlock_pdf(file_bytes: bytes, password: str) -> bytes:
    """
    Unlock the PDF using the provided password and return the decrypted bytes.
    Raises an exception if decryption fails.
    """
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name
    try:
        reader = PdfReader(tmp_path)
        if reader.is_encrypted:
            # decrypt returns an int (0 means failure, 1 means success)
            if reader.decrypt(password) == 0:
                raise Exception("File has not been decrypted (incorrect password?)")
        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)
        decrypted_buffer = io.BytesIO()
        writer.write(decrypted_buffer)
        decrypted_buffer.seek(0)
        return decrypted_buffer.read()
    finally:
        os.remove(tmp_path)

def convert_pdf_to_images(file_bytes: bytes) -> list:
    """
    Convert PDF bytes to a list of PIL images using PyMuPDF.
    """
    if not FITZ_AVAILABLE:
        st.warning("PDF to image conversion not available (PyMuPDF not installed)")
        return []
    try:
        doc = fitz.open("pdf", file_bytes)
        images = []
        for page in doc:
            pix = page.get_pixmap()
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            images.append(img)
        return images
    except Exception as e:
        st.error(f"Error converting PDF to images: {e}")
        return []

# ------------------------------
# GOOGLE SHEETS FUNCTIONS
# ------------------------------
# def get_google_sheet_data():
#     # Get the current working directory
#     current_dir = os.path.dirname(os.path.abspath(__file__))

#     # Construct the full path to the service account JSON file
#     service_account_path = os.path.join(current_dir, "ssg-api-calls-9d65ee02e639.json")
#     try:
#         # gc = gspread.service_account(filename="ssg-api-calls-9d65ee02e639.json")
#         gc = gspread.service_account(filename=service_account_path)        
#         spreadsheet = gc.open_by_key("14IjSXJ0pHG23evfULhrLJEFXXsegx3hBNJoNSgRcp1k")
#         worksheet = spreadsheet.worksheet("Detailed Data View")
#         data = worksheet.get_all_records()
#         return data
#     except Exception as e:
#         st.error("Error loading Google Sheet data: " + str(e))
#         return []

def get_google_sheet_data():
    # Get the current working directory
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # Construct the full path to the service account JSON file
    service_account_path = os.path.join(current_dir, "ssg-api-calls-9d65ee02e639.json")
    try:
        # Define the scope
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

        # Authenticate using the service account JSON file
        credentials = ServiceAccountCredentials.from_json_keyfile_name(service_account_path, scope)
        gc = gspread.authorize(credentials)
        
        spreadsheet = gc.open_by_key("14IjSXJ0pHG23evfULhrLJEFXXsegx3hBNJoNSgRcp1k")
        worksheet = spreadsheet.worksheet("Detailed Data View")
        
        # Get all values first to handle potential duplicate empty headers
        all_values = worksheet.get_all_values()
        if not all_values:
            return []
        
        # Get the header row and handle duplicates
        headers = all_values[0]
        cleaned_headers = []
        header_count = {}
        
        for header in headers:
            if header.strip() == '':
                # For empty headers, create a unique placeholder
                empty_count = header_count.get('empty', 0) + 1
                header_count['empty'] = empty_count
                cleaned_headers.append(f'empty_col_{empty_count}')
            else:
                # For non-empty headers, ensure uniqueness
                original_header = header.strip()
                if original_header in header_count:
                    header_count[original_header] += 1
                    cleaned_headers.append(f'{original_header}_{header_count[original_header]}')
                else:
                    header_count[original_header] = 1
                    cleaned_headers.append(original_header)
        
        # Convert to list of dictionaries
        data = []
        for row_values in all_values[1:]:  # Skip header row
            row_dict = {}
            for i, value in enumerate(row_values):
                if i < len(cleaned_headers):
                    row_dict[cleaned_headers[i]] = value
            data.append(row_dict)
        
        return data
    except Exception as e:
        st.error("Error loading Google Sheet data: " + str(e))
        return []

def compute_similarity(a: str, b: str) -> float:
    return fuzz.ratio(a, b)

def find_best_match(extracted_fields: dict, sheet_data: list, threshold: float = 80) -> (dict, float):
    best_match = None
    best_score = 0
    extracted_name = extracted_fields.get("name", "").lower().strip()
    extracted_uen = extracted_fields.get("uen", "").lower().strip()
    for row in sheet_data:
        sheet_name = str(row.get("Trainee Name (as on government ID)", "")).lower().strip()
        sheet_uen = str(row.get("Employer UEN (mandatory if sponsorship type = employer)", "")).lower().strip()
        name_similarity = compute_similarity(extracted_name, sheet_name)
        if extracted_uen:
            uen_similarity = compute_similarity(extracted_uen, sheet_uen)
            avg_similarity = (0.6 * name_similarity) + (0.4 * uen_similarity)
        else:
            avg_similarity = name_similarity
        if avg_similarity > best_score:
            best_score = avg_similarity
            best_match = row
    if best_score >= threshold:
        return best_match, best_score
    else:
        return None, best_score

def get_extracted_fields(extracted_entities: dict) -> list:
    """
    Returns a list of dictionaries (one per individual) with:
      - name: Trainee name
      - nric: Masked NRIC (if any)
      - company: Company name
      - uen: Company UEN
    """
    names = []
    nrics = []
    company = ""
    uen = ""
    for entity in extracted_entities.get("entities", []):
        etype = entity.get("type", "").lower()
        value = entity.get("value", "")
        if "nric" in etype:
            nrics.append(value)
        elif ("person" in etype or ("name" in etype and "company" not in etype)):
            names.append(value)
        elif "company" in etype and not company:
            company = value
        elif "uen" in etype and not uen:
            uen = value
    num = max(len(names), len(nrics))
    result = []
    if num == 0:
        result.append({"name": "", "nric": "", "company": company, "uen": uen})
    else:
        for i in range(num):
            entry = {
                "name": names[i] if i < len(names) else "",
                "nric": nrics[i] if i < len(nrics) else "",
                "company": company,
                "uen": uen
            }
            result.append(entry)
    return result

def app():
    # ------------------------------
    # STREAMLIT UI & PROCESSING
    # ------------------------------
    st.title("📄 Check Documents")

    custom_instructions = st.text_area(
        "✍️ Enter your custom instructions for entity extraction:",
        "Extract the name of the person this document belongs to, their company, company UEN (if available), masked NRIC, and the date of the document."
    )

    uploaded_files = st.file_uploader(
        "📂 Upload PDF or image files", 
        type=["pdf", "png", "jpg", "jpeg"], 
        accept_multiple_files=True
    )

    # Use session state to store unlocked file content and extracted data.
    if "unlocked_files" not in st.session_state:
        st.session_state.unlocked_files = {}
    if "extracted_data" not in st.session_state:
        st.session_state.extracted_data = {}
    if "sheet_data" not in st.session_state:
        st.session_state.sheet_data = get_google_sheet_data()

    # ------------------------------
    # Step 1: Preprocess Files (Unlock and Convert PDFs)
    # ------------------------------
    if uploaded_files:
        for uploaded_file in uploaded_files:
            file_extension = uploaded_file.name.split(".")[-1].lower()
            # Skip if already processed.
            if uploaded_file.name in st.session_state.unlocked_files:
                continue
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_extension}") as temp_file:
                temp_file.write(uploaded_file.getvalue())
                temp_file_path = temp_file.name

            file_bytes = None
            if file_extension == "pdf":
                try:
                    reader = PdfReader(temp_file_path)
                    if reader.is_encrypted:
                        password_key = f"password_{uploaded_file.name}"
                        # Only show form if we haven't already stored a password.
                        if not st.session_state.get(password_key, ""):
                            with st.form(key=f"form_{uploaded_file.name}"):
                                password = st.text_input(f"Enter password for {uploaded_file.name}:", type="password")
                                submitted = st.form_submit_button("Unlock")
                                if submitted and password:
                                    st.session_state[password_key] = password
                        # If password is stored, try to unlock.
                        if st.session_state.get(password_key, ""):
                            try:
                                file_bytes = unlock_pdf(uploaded_file.getvalue(), st.session_state[password_key])
                                st.success(f"{uploaded_file.name} unlocked successfully.")
                            except Exception as de:
                                st.error(f"Error unlocking {uploaded_file.name}: {de}")
                                os.remove(temp_file_path)
                                continue  # Skip processing if unlocking fails.
                        else:
                            st.warning(f"{uploaded_file.name} is password-protected. Please submit the password to unlock.")
                            os.remove(temp_file_path)
                            continue  # Skip until a password is provided.
                    else:
                        with open(temp_file_path, "rb") as f:
                            file_bytes = f.read()
                except Exception as e:
                    st.error(f"❌ Error processing PDF {uploaded_file.name}: {e}")
            elif file_extension in ["png", "jpg", "jpeg"]:
                try:
                    image = Image.open(temp_file_path)
                    img_byte_arr = io.BytesIO()
                    image.save(img_byte_arr, format=image.format)
                    file_bytes = img_byte_arr.getvalue()
                except Exception as e:
                    st.error(f"❌ Error processing image {uploaded_file.name}: {e}")
            os.remove(temp_file_path)
            if file_bytes:
                if file_extension == "pdf":
                    try:
                        # Convert PDF bytes to a list of PIL images using PyMuPDF.
                        pages = convert_pdf_to_images(file_bytes)
                        if pages:
                            st.session_state.unlocked_files[uploaded_file.name] = pages
                            st.success(f"{uploaded_file.name} converted to {len(pages)} page(s).")
                        else:
                            st.error(f"❌ No pages extracted from {uploaded_file.name}.")
                    except Exception as e:
                        st.error(f"❌ Error converting PDF {uploaded_file.name} to images: {e}")
                else:
                    try:
                        image = Image.open(io.BytesIO(file_bytes))
                        st.session_state.unlocked_files[uploaded_file.name] = image
                    except Exception as e:
                        st.error(f"❌ Error loading image {uploaded_file.name}: {e}")
            else:
                st.warning(f"⚠️ No readable content for {uploaded_file.name}.")

    # ------------------------------
    # Step 2: Process Entity Extraction
    # ------------------------------
    if st.session_state.unlocked_files and st.button("🚀 Process Documents"):
        for filename, file_content in st.session_state.unlocked_files.items():
            st.info(f"Processing entities for {filename}...")
            # If the file content is a list (i.e. PDF pages), process each page.
            if isinstance(file_content, list):
                page_results = []
                for i, page in enumerate(file_content, start=1):
                    # Pass the PIL image object to extract_entities; since it's already an image, set is_image=False.
                    result = extract_entities(page, custom_instructions, is_image=False)
                    page_results.append(result)
                st.session_state.extracted_data[filename] = page_results
            else:
                result = extract_entities(file_content, custom_instructions, is_image=False)
                st.session_state.extracted_data[filename] = result
        st.success("Entity extraction completed.")

    # ------------------------------
    # Step 3: Display Results
    # ------------------------------
    if st.session_state.extracted_data:
        st.subheader("📂 View Results by File:")
        file_names = list(st.session_state.extracted_data.keys())
        tabs = st.tabs(file_names)
        for tab, file_name in zip(tabs, file_names):
            with tab:
                extracted_data = st.session_state.extracted_data[file_name]
                if isinstance(extracted_data, list):
                    st.markdown(f"**{file_name} contains {len(extracted_data)} page(s):**")
                    page_tabs = st.tabs([f"Page {i+1}" for i in range(len(extracted_data))])
                    for p_tab, page_result in zip(page_tabs, extracted_data):
                        with p_tab:
                            with st.expander("📜 View Raw JSON Data (Page)"):
                                st.json(page_result)
                            st.subheader("Extracted Entities")
                            if page_result.get("entities"):
                                df = pd.DataFrame(page_result["entities"])
                                st.dataframe(df)
                            else:
                                st.warning("⚠️ No entities found on this page.")
                else:
                    with st.expander(f"📜 View Raw JSON Data ({file_name})"):
                        st.json(extracted_data)
                    st.subheader(f"Extracted Entities from {file_name}")
                    if extracted_data.get("entities"):
                        df = pd.DataFrame(extracted_data["entities"])
                        st.dataframe(df)
                    else:
                        st.warning("⚠️ No entities found. Consider modifying the extraction instructions.")
                
                st.markdown("---")
                st.subheader("🔎 Google Sheets Matching")
                extracted_fields_list = get_extracted_fields(extracted_data if not isinstance(extracted_data, list) else extracted_data[0])
                
                box_style = """
                    <style>
                        .custom-box {
                            border: 2px solid #ddd; 
                            border-radius: 8px; 
                            padding: 15px; 
                            margin: 10px 0; 
                            background-color: #f9f9f9;
                            box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.1);
                        }
                        .custom-box h3 {
                            margin-top: 0;
                            color: #333;
                            font-size: 18px;
                        }
                    </style>
                """
                st.markdown(box_style, unsafe_allow_html=True)
                
                for idx, person in enumerate(extracted_fields_list, start=1):
                    st.markdown(f"**Person {idx}:**")
                    st.markdown(
                        """
                        <div class="custom-box">
                            <h3>📄 Extracted Document Data</h3>
                            <p><strong>Name:</strong> {name}</p>
                            <p><strong>Masked NRIC:</strong> {nric}</p>
                            <p><strong>UEN:</strong> {uen}</p>
                            <p><strong>Company:</strong> {company}</p>
                        </div>
                        """.format(
                            name=person.get("name", "N/A"),
                            nric=person.get("nric", "N/A"),
                            uen=person.get("uen", "N/A"),
                            company=person.get("company", "N/A")
                        ),
                        unsafe_allow_html=True,
                    )
                    best_match, score = find_best_match(person, st.session_state.sheet_data, threshold=80)
                    if best_match:
                        st.markdown(
                            """
                            <div class="custom-box">
                                <h3>🔎 Best Google Sheets Match (Similarity: {score:.2f}%)</h3>
                                <p><strong>Trainee Name:</strong> {trainee}</p>
                                <p><strong>Trainee ID (NRIC):</strong> {nric_sheet}</p>  
                                <p><strong>Employer UEN:</strong> {employer}</p>                                                  
                                <p><strong>Sponsorship Type:</strong> {sponsorship}</p>
                            </div>
                            """.format(
                                score=score,
                                trainee=best_match.get("Trainee Name (as on government ID)", "N/A"),
                                sponsorship=best_match.get("Sponsorship Type *", "N/A"),
                                employer=best_match.get("Employer UEN (mandatory if sponsorship type = employer)", "N/A"),
                                nric_sheet=best_match.get("Trainee ID *", "N/A")
                            ),
                            unsafe_allow_html=True,
                        )
                        with st.expander("📜 View Google Sheets Row Data"):
                            st.json(best_match)
                    else:
                        st.markdown(
                            """
                            <div class="custom-box">
                                <h3>🔎 Best Google Sheets Match</h3>
                                <p><strong>No matching row found</strong></p>
                                <p>Best average similarity: {score:.2f}%</p>
                            </div>
                            """.format(score=score),
                            unsafe_allow_html=True,
                        )
                
                st.markdown("---")
                st.subheader("ACRA Data API Verification")
                verification_dfs = []
                for person in extracted_fields_list:
                    match, score = find_best_match(person, st.session_state.sheet_data, threshold=80)
                    if match:
                        verification_df = run_dataset_verifications(person, match, similarity_threshold=80)
                        # Keep only desired columns:
                        verification_df = verification_df[["Verification Type", "Dataset Value", "Input Value", "Dataset"]]
                        verification_dfs.append(verification_df)
                if verification_dfs:
                    df_combined = pd.concat(verification_dfs, ignore_index=True)
                    def highlight_cell(val):
                        return 'background-color: lightgreen' if val != "N/A" else ''
                    styled_df = df_combined.style.applymap(highlight_cell, subset=["Dataset Value"])
                    st.dataframe(styled_df, use_container_width=True)
                else:
                    st.markdown("**No Google Sheet match available to run combined dataset verification.**")