# document_parser.py

from docx import Document
import json
from docx.oxml.text.paragraph import CT_P
from docx.oxml.table import CT_Tbl
from docx.table import Table
from docx.text.paragraph import Paragraph
import re

def parse_document(input_docx, output_json):
    # Load the document
    doc = Document(input_docx)
    
    # Initialize containers
    data = {
        "Course_Proposal_Form": {}
    }
    
    # Function to parse tables with advanced duplication check
    def parse_table(table):
        rows = []
        for row in table.rows:
            # Process each cell and ensure unique content within the row
            cells = []
            for cell in row.cells:
                cell_text = cell.text.strip()
                if cell_text not in cells:
                    cells.append(cell_text)
            # Ensure unique rows within the table
            if cells not in rows:
                rows.append(cells)
        return rows

    # Function to add text and table content
    def add_content_to_section(section_name, content):
        if section_name not in data["Course_Proposal_Form"]:
            data["Course_Proposal_Form"][section_name] = []
        # Check for duplication before adding content
        if content not in data["Course_Proposal_Form"][section_name]:
            data["Course_Proposal_Form"][section_name].append(content)

    # Function to detect bullet points using regex
    def is_bullet_point(text):
        # Regex to match common bullet points (e.g., '•', '-', etc.)
        bullet_pattern = r"^[•\-\–●◦]\s+.*"
        return bool(re.match(bullet_pattern, text))

    # Function to add bullet points under a list
    def add_bullet_point(section_name, bullet_point_text):
        if section_name not in data["Course_Proposal_Form"]:
            data["Course_Proposal_Form"][section_name] = []
        if not data["Course_Proposal_Form"][section_name] or not isinstance(data["Course_Proposal_Form"][section_name][-1], dict) or 'bullet_points' not in data["Course_Proposal_Form"][section_name][-1]:
            data["Course_Proposal_Form"][section_name].append({"bullet_points": []})
        data["Course_Proposal_Form"][section_name][-1]["bullet_points"].append(bullet_point_text)

    # Variables to track the current section
    current_section = None

    # Iterate through the elements of the document
    for element in doc.element.body:
        if isinstance(element, CT_P):  # It's a paragraph
            para = Paragraph(element, doc)
            text = para.text.strip()

            # If the text indicates a new section, set current_section
            if text.startswith("Part") or text.startswith("LU"):
                current_section = text
            elif text:
                # Check if the paragraph is a bullet point using regex
                if is_bullet_point(text):
                    add_bullet_point(current_section, text)
                else:
                    add_content_to_section(current_section, text)
        elif isinstance(element, CT_Tbl):  # It's a table
            tbl = Table(element, doc)
            table_content = parse_table(tbl)
            if current_section:
                add_content_to_section(current_section, {"table": table_content})

    # Convert to JSON
    json_output = json.dumps(data, indent=4, ensure_ascii=False)

    # Save the JSON to a file in the current working directory
    with open(output_json, "w", encoding="utf-8") as json_file:
        json_file.write(json_output)

    print(f"{input_docx} JSON output saved to {output_json}")

# if __name__ == "__main__":
#     # Get input and output file paths from command-line arguments
#     if len(sys.argv) != 3:
#         print("Usage: python document_parser.py <input_docx> <output_json>")
#         sys.exit(1)
#     input_docx = sys.argv[1]
#     output_json = sys.argv[2]
#     parse_document(input_docx, output_json)
