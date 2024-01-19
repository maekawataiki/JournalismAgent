colors = [
    "#FF5252",
    "#E040FB",
    "#536DFE",
    "#40C4FF",
    "#64FFDA",
    "#B2FF59",
    "#FFFF00",
    "#FFAB40",
]


def highlight(string, source):
    return f'<span class="c{source}">{"".join(string)}</span>'


def find_matches(output_tokens, search_tokens, split_by_word):
    """
    highlight output_tokens with matching search_tokens source
    """

    def create_ngram(string, n=2):
        delimiter = ['「', '」', '…', '　']
        if n == 1:
            return list(string)
        elif n == 2:
            double = list(zip(string[:-1], string[1:]))
            double = filter(
                (lambda x: not ((x[0] in delimiter) or (x[1] in delimiter))), double)
            return list(double)
        elif n == 3:
            triple = list(zip(string[:-2], string[1:-1], string[2:]))
            triple = filter((lambda x: not ((x[0] in delimiter) or (
                x[1] in delimiter) or (x[2] in delimiter))), triple)
            return list(triple)
        return []

    def create_ngrams(string, n=2):
        return create_ngram(string, n)

    
    # ngram: 1
    ngram_dict = {}
    for idx, search_token in enumerate(search_tokens):
        ngrams = create_ngrams(search_token, 1)
        for ngram in ngrams:
            if not ngram in ngram_dict:
                ngram_dict[ngram] = set()
            ngram_dict[ngram] = ngram_dict[ngram] | set([idx])
    
    # Match longest consecutive ngrams from single source and highlight
    spacer = " " if split_by_word else ""
    html = ""
    buffer = ()
    buffer_source = set()
    used_source = set()
    for token in output_tokens:
        if not token in ngram_dict:
            if buffer:
                source = list(buffer_source)[0]
                html += highlight(spacer.join(buffer), source) + spacer
                buffer = ()
                used_source |= set([source])
                buffer_source = set()
            html += token + spacer
        else:
            current_source = ngram_dict[token]
            if not buffer:
                buffer = [token]
                buffer_source = current_source
            else:
                # Check for overlap
                if buffer_source & current_source:
                    buffer.append(token)
                    buffer_source = buffer_source & current_source
                # No overlap, flush buffer
                else:
                    source = list(buffer_source)[0]
                    html += highlight(spacer.join(buffer), source) + spacer
                    buffer = [token]
                    used_source |= set([source])
                    buffer_source = current_source
    if buffer:
        html += highlight(spacer.join(buffer), list(buffer_source)[0])

    return html, used_source
