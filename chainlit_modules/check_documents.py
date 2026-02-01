"""
Check Documents Module - Chainlit

Handles document verification:
- Entity extraction (names, companies, UEN)
- Training records matching
- ACRA UEN verification

Author: Courseware Generator Team
Date: February 2026
"""

import sys
import os
import asyncio
import tempfile

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import chainlit as cl


async def on_start():
    """Called when Check Documents profile is selected."""
    cl.user_session.set("check_state", "awaiting_input")
    cl.user_session.set("documents", [])
    cl.user_session.set("extracted_data", {})


async def on_message(message: cl.Message):
    """Handle messages in Check Documents context."""
    state = cl.user_session.get("check_state", "awaiting_input")
    content = message.content.strip()

    if state == "awaiting_input":
        # Check if it's a UEN verification request
        uen_patterns = ["uen", "verify company", "check company"]
        if any(p in content.lower() for p in uen_patterns):
            # Extract potential UEN from message
            import re
            uen_match = re.search(r'\b\d{8,9}[A-Za-z]\b', content)
            if uen_match:
                await verify_uen(uen_match.group())
            else:
                await cl.Message(
                    content="Please provide the UEN to verify (e.g., 201912345A)."
                ).send()
        elif any(kw in content.lower() for kw in ["upload", "check", "verify", "document"]):
            await request_file_upload()
        else:
            await cl.Message(
                content="I can help you:\n\n"
                        "1. **Verify documents** - Upload PDFs or images to extract and verify entities\n"
                        "2. **Check UEN** - Verify a company's UEN against ACRA\n\n"
                        "Upload documents or provide a UEN to get started."
            ).send()

    elif state == "processing":
        await cl.Message(content="Document verification in progress. Please wait...").send()

    elif state == "completed":
        if any(kw in content.lower() for kw in ["another", "new", "again", "more"]):
            await on_start()
            await cl.Message(content="Ready to verify more documents.").send()
        else:
            await cl.Message(content="Verification complete. Say 'new' to check more documents.").send()


async def on_file_upload(files: list):
    """Handle file uploads."""
    if not files:
        return

    # Accept PDF and images
    valid_files = [f for f in files if f.name.lower().endswith(('.pdf', '.png', '.jpg', '.jpeg'))]

    if not valid_files:
        await cl.Message(
            content="Please upload documents in PDF or image format (.pdf, .png, .jpg)."
        ).send()
        return

    cl.user_session.set("documents", valid_files)

    file_list = "\n".join([f"- {f.name}" for f in valid_files])
    await cl.Message(content=f"Received {len(valid_files)} document(s):\n{file_list}").send()

    await process_documents(valid_files)


async def request_file_upload():
    """Request document upload."""
    files = await cl.AskFileMessage(
        content="Please upload documents to verify (PDF or images):",
        accept=["application/pdf", "image/png", "image/jpeg"],
        max_files=10,
        timeout=300
    ).send()

    if files:
        await on_file_upload(files)


async def process_documents(documents: list):
    """Process and verify documents."""
    cl.user_session.set("check_state", "processing")

    results = {}

    for doc in documents:
        async with cl.Step(name=f"Analyzing {doc.name}", type="tool") as step:
            step.input = "Extracting entities..."

            # Save file temporarily
            temp_dir = tempfile.mkdtemp()
            doc_path = os.path.join(temp_dir, doc.name)

            with open(doc_path, "wb") as f:
                f.write(doc.content)

            # Placeholder for entity extraction
            # Would use existing extraction code from check_documents/

            extracted = {
                "persons": [],
                "companies": [],
                "uens": [],
                "dates": [],
            }

            results[doc.name] = extracted
            step.output = f"Extracted entities from {doc.name}"

    cl.user_session.set("extracted_data", results)

    # Display results
    await cl.Message(
        content="Document verification integration in progress.\n\n"
                "The existing pipeline from `check_documents/` will be connected here.\n\n"
                "**Verification steps:**\n"
                "1. Extract entities (names, companies, UEN)\n"
                "2. Match against training records (Google Sheets)\n"
                "3. Verify UEN with ACRA\n"
                "4. Report findings"
    ).send()

    cl.user_session.set("check_state", "completed")


async def verify_uen(uen: str):
    """Verify a UEN against ACRA."""
    await cl.Message(content=f"Verifying UEN: **{uen}**...").send()

    async with cl.Step(name="ACRA Verification", type="tool") as step:
        step.input = f"Checking {uen} against ACRA database..."

        # Placeholder for ACRA verification
        # Would call existing ACRA verification code

        step.output = "Verification complete!"

    await cl.Message(
        content=f"UEN verification integration in progress.\n\n"
                f"**UEN:** {uen}\n\n"
                "The ACRA verification from `check_documents/` will be connected here."
    ).send()

    cl.user_session.set("check_state", "completed")
