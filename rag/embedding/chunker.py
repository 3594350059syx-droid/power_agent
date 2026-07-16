from langchain_text_splitters import RecursiveCharacterTextSplitter


def split_text(
    text: str,
    chunk_size: int = 300,
    chunk_overlap: int = 50
):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=[
            "\n\n",
            "\n",
            "。",
            "！",
            "？",
            "；",
            "，",
            " "
        ]
    )
    chunks = splitter.split_text(text)
    return chunks