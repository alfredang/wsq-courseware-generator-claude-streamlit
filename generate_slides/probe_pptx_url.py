"""Probe NotebookLM artifact data to find PPTX download URL.

This script connects to NotebookLM, finds the most recent slide deck artifact,
and dumps the raw metadata to find the PPTX URL position.

Usage:
    uv run python -m generate_slides.probe_pptx_url [notebook_id]

If no notebook_id is provided, lists all notebooks and uses the most recent one
that has a completed slide deck.
"""
import asyncio
import json
import sys


async def probe():
    from notebooklm import NotebookLMClient

    client = await NotebookLMClient.from_storage()
    async with client:
        # Get notebook ID from command line or find one with slides
        notebook_id = sys.argv[1] if len(sys.argv) > 1 else None

        if not notebook_id:
            # List notebooks and find one with slides
            notebooks = await client.notebooks.list()
            print(f"Found {len(notebooks)} notebooks")
            for nb in notebooks[:10]:
                print(f"  - {nb.id}: {nb.title}")

            # Try each notebook to find one with slide decks
            for nb in notebooks:
                try:
                    raw = await client.artifacts._list_raw(nb.id)
                    for art in raw:
                        if isinstance(art, list) and len(art) > 4 and art[2] == 10:  # SLIDE_DECK = 10
                            notebook_id = nb.id
                            print(f"\nFound slide deck in: {nb.title} ({nb.id})")
                            break
                    if notebook_id:
                        break
                except Exception:
                    continue

        if not notebook_id:
            print("No notebooks with slide decks found.")
            return

        # Get raw artifact data
        raw = await client.artifacts._list_raw(notebook_id)
        print(f"\nRaw artifacts count: {len(raw)}")

        for art_i, art in enumerate(raw):
            if not isinstance(art, list) or len(art) <= 4:
                continue
            art_type = art[2]
            art_status = art[4]
            print(f"\n--- Artifact {art_i}: type={art_type}, status={art_status}, id={art[0]} ---")

            if art_type == 10:  # SLIDE_DECK
                print(f"  Total array length: {len(art)}")

                # Dump metadata at index 16
                if len(art) > 16:
                    metadata = art[16]
                    print(f"  art[16] type: {type(metadata).__name__}, length: {len(metadata) if isinstance(metadata, list) else 'N/A'}")

                    if isinstance(metadata, list):
                        for mi, item in enumerate(metadata):
                            item_str = str(item)
                            if len(item_str) > 200:
                                item_str = item_str[:200] + "..."
                            item_type = type(item).__name__
                            # Highlight URLs
                            is_url = isinstance(item, str) and item.startswith("http")
                            marker = " <<<< URL" if is_url else ""
                            print(f"  art[16][{mi}]: ({item_type}) {item_str}{marker}")

                # Also check other indices for URLs
                print(f"\n  Scanning ALL indices for URLs:")
                for idx in range(len(art)):
                    item = art[idx]
                    if isinstance(item, str) and item.startswith("http"):
                        print(f"  art[{idx}]: URL = {item[:150]}")
                    elif isinstance(item, list):
                        for sub_i, sub in enumerate(item):
                            if isinstance(sub, str) and sub.startswith("http"):
                                print(f"  art[{idx}][{sub_i}]: URL = {sub[:150]}")
                            elif isinstance(sub, list):
                                for sub2_i, sub2 in enumerate(sub):
                                    if isinstance(sub2, str) and sub2.startswith("http"):
                                        print(f"  art[{idx}][{sub_i}][{sub2_i}]: URL = {sub2[:150]}")
                                    elif isinstance(sub2, list):
                                        for sub3_i, sub3 in enumerate(sub2):
                                            if isinstance(sub3, str) and sub3.startswith("http"):
                                                print(f"  art[{idx}][{sub_i}][{sub2_i}][{sub3_i}]: URL = {sub3[:150]}")

                # Dump entire art[16] as JSON for analysis
                if len(art) > 16:
                    print(f"\n  Full art[16] JSON dump:")
                    try:
                        print(json.dumps(art[16], indent=2, default=str)[:3000])
                    except Exception as e:
                        print(f"  (could not JSON dump: {e})")

                # Check for .pptx in any string
                print(f"\n  Searching for 'pptx' or 'powerpoint' in all data:")
                art_str = json.dumps(art, default=str).lower()
                if "pptx" in art_str:
                    # Find position
                    pos = art_str.find("pptx")
                    print(f"  Found 'pptx' at char position {pos}: ...{art_str[max(0,pos-50):pos+100]}...")
                elif "powerpoint" in art_str:
                    pos = art_str.find("powerpoint")
                    print(f"  Found 'powerpoint' at char position {pos}: ...{art_str[max(0,pos-50):pos+100]}...")
                else:
                    print(f"  No 'pptx' or 'powerpoint' found in artifact data")


if __name__ == "__main__":
    asyncio.run(probe())
