import logfire


def chunk_text(text: str, chunk_size: int = 1500) -> list[str]:
    """
    Simple semantic-ish chunker that splits by paragraphs.
    Ensures chunks do not exceed the specified size.
    """

    with logfire.span("✂️ Text Chunking", text_lenght=len(text)):
        if not text.strip():
            return []

        paragraphs = text.split("\n\n")
        chunks = []
        current_chunks = ""

        for p in paragraphs:
            if len(current_chunks) + len(p) < chunk_size:
                current_chunks += p + "\n\n"
            else:
                if current_chunks.strip():
                    chunks.append(current_chunks.strip())
                current_chunks = p + "\n\n"

        if current_chunks.strip():
            chunks.append(current_chunks.strip())

        valid_chunks = [c for c in chunks if c.strip()]
        logfire.info(f"✅ Generated {len(valid_chunks)} chunks")
        return valid_chunks


# from typing import List

# def chunk_text(
#     text: str,
#     chunk_size: int = 1500,
#     overlap: int = 200
# ) -> List[str]:
#     """
#     Splits text into chunks with overlapping content.
#     """

#     with logfire.span("✂️ Text Chunking", text_length=len(text)):
#         if not text.strip():
#             return []

#         paragraphs = text.split("\n\n")
#         chunks = []
#         current_chunk = ""

#         for p in paragraphs:
#             if len(current_chunk) + len(p) + 2 <= chunk_size:
#                 current_chunk += p + "\n\n"
#             else:
#                 if current_chunk.strip():
#                     chunks.append(current_chunk.strip())

#                 # Keep the last 'overlap' characters
#                 previous_text = current_chunk[-overlap:] if overlap else ""

#                 current_chunk = previous_text + "\n\n" + p + "\n\n"

#         if current_chunk.strip():
#             chunks.append(current_chunk.strip())

#         logfire.info(f"✅ Generated {len(chunks)} chunks")
#         return chunks
