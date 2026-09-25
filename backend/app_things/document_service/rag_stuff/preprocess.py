def markdown_to_chunks(markdown: str):
    lines = markdown.splitlines()

    chunks = []

    current = []
    headings = []

    for line in lines:
        if line.startswith("#"):
            if current:
                chunks.append(
                    {
                        "text": "\n".join(current).strip(),
                        "section": headings[-1] if headings else None,
                    }
                )

                current = []

            level = len(line) - len(line.lstrip("#"))
            title = line[level:].strip()

            headings = headings[: level - 1]
            headings.append(title)

        current.append(line)

    if current:
        chunks.append(
            {
                "text": "\n".join(current).strip(),
                "section": headings[-1] if headings else None,
            }
        )

    return [chunk for chunk in chunks if chunk["text"]]
