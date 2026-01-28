# app.py
import streamlit as st
import os
import tempfile
from generate_cp.main import main
import asyncio
from generate_cp.utils.document_parser import parse_document
from company.company_manager import get_selected_company, show_company_info, get_company_template, apply_company_branding

# Initialize session state variables
if 'processing_done' not in st.session_state:
    st.session_state['processing_done'] = False
if 'output_docx' not in st.session_state:
    st.session_state['output_docx'] = None
if 'cv_output_files' not in st.session_state:
    st.session_state['cv_output_files'] = []
# Note: selected_model is set in app.py sidebar based on user selection and database defaults
# Do not set a hardcoded default here - let app.py handle model selection

def app():
    st.title("Generate CP")

    # Show current company info
    show_company_info()

    # Get selected company and templates
    selected_company = get_selected_company()
    cp_template_path = get_company_template("course_proposal")

    st.subheader("Course Proposal Type")
    cp_type_display = st.selectbox(
        "Select CP Type:",
        options=["Excel CP", "Docx CP"],
        index=0  # default: "Excel CP: New CP"
    )
    # Map display values to backend values
    cp_type_mapping = {
        "Excel CP": "New CP",
        "Docx CP": "Old CP"
    }
    st.session_state['cp_type'] = cp_type_mapping[cp_type_display]

    # Add a description of the page with improved styling
    st.markdown(
        """
        <style>
            .important-note {
                background-color: #f0f8ff;
                padding: 15px;
                border-radius: 10px;
                border-left: 6px solid #2196f3;
                font-size: 15px;
            }
            .header {
                font-size: 18px;
                font-weight: bold;
                color: #333;
                margin-top: 20px;
            }
            .section-title {
                font-size: 16px;
                font-weight: bold;
                margin-top: 10px;
            }
        </style>
        """,
        unsafe_allow_html=True
    )

    # Descriptive section
    uploaded_file = st.file_uploader("Upload a TSC DOCX file", type="docx", key='uploaded_file')

    if uploaded_file is not None:
        st.success(f"Uploaded file: {uploaded_file.name}")

        # 1) Save the uploaded file to a temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp_input:
            tmp_input.write(uploaded_file.getbuffer())
            input_tsc_path = tmp_input.name

        # 2) Process button
        if st.button("🚀 Process File"):
            # Optional: parse_document before the main pipeline if you want:
            # parse_document(input_tsc_path, "json_output/output_TSC_TEST.json")
            run_processing(input_tsc_path)
            st.session_state['processing_done'] = True

        # 3) Display download buttons after processing
        if st.session_state.get('processing_done'):
            st.subheader("Download Processed Files")
            
            # Get CP type to show relevant information
            cp_type = st.session_state.get('cp_type', "New CP")
            
            # Get file download data
            file_downloads = st.session_state.get('file_downloads', {})
            
            # Display CP Word document
            cp_docx = file_downloads.get('cp_docx')
            if cp_type == "Old CP":
                if cp_docx and os.path.exists(cp_docx['path']):
                    with open(cp_docx['path'], 'rb') as f:
                        data = f.read()
                    # Determine MIME type based on file extension
                    if cp_docx['name'].endswith('.docx'):
                        mime_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                    else:
                        mime_type = 'application/octet-stream'
                    
                    st.download_button(
                        label="📄 Download CP Document",
                        data=data,
                        file_name=cp_docx['name'],
                        mime=mime_type
                    )
            
            # Display Excel file for New CP
            if cp_type == "New CP":
                excel_file = file_downloads.get('excel')
                if excel_file and os.path.exists(excel_file['path']):
                    with open(excel_file['path'], 'rb') as f:
                        data = f.read()
                    # Determine MIME type based on file extension
                    if excel_file['name'].endswith('.xlsx'):
                        mime_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                    elif excel_file['name'].endswith('.xls'):
                        mime_type = 'application/vnd.ms-excel'
                    else:
                        mime_type = 'application/octet-stream'
                    
                    st.download_button(
                        label="📊 Download CP Excel",
                        data=data,
                        file_name=excel_file['name'],
                        mime=mime_type
                    )
                elif cp_type == "New CP":
                    st.warning("Excel file was not generated. This may be normal if processing was interrupted.")
            
            # Display CV validation documents
            cv_docs = file_downloads.get('cv_docs', [])
            if cv_docs:
                st.markdown("### Course Validation Documents")
                
                # Use columns to organize multiple download buttons
                cols = st.columns(min(3, len(cv_docs)))
                for idx, doc in enumerate(cv_docs):
                    if os.path.exists(doc['path']):
                        with open(doc['path'], 'rb') as f:
                            data = f.read()
                        
                        # Extract name from the filename (e.g. extract "Bernard" from "CP_validation_template_bernard_updated.docx")
                        file_base = os.path.basename(doc['name'])
                        validator_name = file_base.split('_')[3].capitalize()
                        
                        col_idx = idx % len(cols)
                        with cols[col_idx]:
                            # Determine MIME type based on file extension  
                            if doc['name'].endswith('.docx'):
                                mime_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                            elif doc['name'].endswith('.doc'):
                                mime_type = 'application/msword'
                            elif doc['name'].endswith('.xlsx'):
                                mime_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                            elif doc['name'].endswith('.xls'):
                                mime_type = 'application/vnd.ms-excel'
                            else:
                                mime_type = 'application/octet-stream'
                            
                            st.download_button(
                                label=f"📝 {validator_name}",
                                data=data,
                                file_name=doc['name'],
                                mime=mime_type
                            )

def run_processing(input_file: str):
    """
    1. Runs your main pipeline, which writes docs to 'output_docs/' 
    2. Copies those docs into NamedTemporaryFiles and stores them in session state.
    """
    st.info("Running pipeline (this might take some time) ...")
    
    # Get CP type from session state
    cp_type = st.session_state.get('cp_type', "New CP")

    # 1) Run the pipeline (async), passing the TSC doc path
    asyncio.run(main(input_file))

    # 2) Now copy the relevant docx files from 'output_docs' to NamedTemporaryFiles
    # Common files for both CP types
    cp_doc_path = "generate_cp/output_docs/CP_output.docx"
    cv_doc_paths = [
        "generate_cp/output_docs/CP_validation_template_bernard_updated.docx",
        "generate_cp/output_docs/CP_validation_template_dwight_updated.docx",
        "generate_cp/output_docs/CP_validation_template_ferris_updated.docx",
    ]
    
    # Excel file - only for "New CP"
    excel_path = "generate_cp/output_docs/CP_template_metadata_preserved.xlsx"
    
    # Store file info based on CP type
    st.session_state['file_downloads'] = {
        'cp_docx': None,
        'cv_docs': [],
        'excel': None
    }

    # Copy CP doc into tempfile
    if os.path.exists(cp_doc_path):
        with open(cp_doc_path, 'rb') as infile, tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as outfile:
            outfile.write(infile.read())
            st.session_state['file_downloads']['cp_docx'] = {
                'path': outfile.name,
                'name': "CP_output.docx"
            }

    # Copy CV docs
    for doc_path in cv_doc_paths:
        if os.path.exists(doc_path):
            with open(doc_path, 'rb') as infile, tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as outfile:
                outfile.write(infile.read())
                desired_name = os.path.basename(doc_path)
                st.session_state['file_downloads']['cv_docs'].append({
                    'path': outfile.name,
                    'name': desired_name
                })

    # Copy Excel file - only for New CP
    if cp_type == "New CP" and os.path.exists(excel_path):
        with open(excel_path, 'rb') as infile, tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as outfile:
            outfile.write(infile.read())
            st.session_state['file_downloads']['excel'] = {
                'path': outfile.name,
                'name': "CP_Excel_output.xlsx"
            }

    st.success("Processing complete. Download your files below!")


if __name__ == "__main__":
    app()
