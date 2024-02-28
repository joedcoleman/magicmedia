import os
import tiktoken
from urllib.parse import urlparse

def is_url(path):
    try:
        result = urlparse(path)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False

def chunk_text_by_tokens(text, max_tokens_per_chunk, model_name='gpt-4'):
    """
    Chunks a given body of text into pieces with a maximum number of tokens.

    :param text: The input text to be chunked.
    :param max_tokens_per_chunk: The maximum number of tokens allowed per chunk.
    :param model_name: The name of the model to determine encoding (e.g., 'gpt-3.5-turbo').
    :return: A list of text chunks.
    """
    # Load the encoding for the specified model
    encoding = tiktoken.encoding_for_model(model_name)

    # Tokenize the input text
    tokens = encoding.encode(text)
    
    # Initialize variables for chunking
    chunks = []
    current_chunk = []

    # Iterate over the token IDs and create chunks
    token_count = 0
    for token_id in tokens:
        token_count += 1
        current_chunk.append(token_id)
        # Check if adding the next token would exceed the max token limit
        if token_count == max_tokens_per_chunk:
            # Decode the current chunk's tokens into a string
            chunk_text = encoding.decode(current_chunk)
            chunks.append(chunk_text)
            current_chunk = []
            token_count = 0

    # Add the last chunk if it has any tokens
    if current_chunk:
        chunk_text = encoding.decode(current_chunk)
        chunks.append(chunk_text)

    return chunks

def count_tokens(text, model_name='gpt-4'):
    """
    Counts the number of tokens in a given body of text.

    :param text: The input text to be tokenized.
    :param model_name: The name of the model to determine encoding (e.g., 'gpt-3.5-turbo').
    :return: The number of tokens in the text.
    """
    # Load the encoding for the specified model
    encoding = tiktoken.encoding_for_model(model_name)

    # Tokenize the input text
    tokens = encoding.encode(text)

    # Return the number of tokens
    return len(tokens)
