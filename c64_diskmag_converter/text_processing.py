import cbmcodecs2
from collections import Counter
import itertools
import more_itertools
import numpy as np
import os
import pandas as pd
import re
import regex
from scipy.stats import entropy


data_dir = os.path.join(os.path.dirname(__file__), 'data')
begin_trigrams = os.path.join(data_dir, 'beginning_trigrams.csv')
umlaut_trigrams = os.path.join(data_dir, 'umlaut_trigrams.csv')
BEGINNINGS = pd.read_csv(begin_trigrams, encoding='utf-8')
UMLAUT_TRIGRAMS = pd.read_csv(umlaut_trigrams, encoding='utf-8')
# Regular expression for detecting trigrams with german umlauts and eszett
UMLAUTS = list('äöüÄÖÜß')
DOUBLE_UMLAUTS = {'ae': 'ä', 'Ae': 'Ä', 'oe': 'ö', 'Oe': 'Ö', 'ue': 'ü', 'Ue': 'ü'}
FIND_DOUBLE_UMLAUTS = re.compile('|'.join([f"{key}(?!$)" for key in DOUBLE_UMLAUTS.keys()]))
# [@£\[\]↑;:]
FIND_UMLAUT_TRIGRAM = regex.compile(r'[a-zA-Z ]'
                                    r'([^\P{So}\N{CHECK MARK}\N{REPLACEMENT CHARACTER}]|[\uf110-\ufffc])'
                                    r'[a-zA-Z ,.:;\-"!?]')
UMLAUTS_lookup = {trigram: percentage for trigram, percentage in zip(UMLAUT_TRIGRAMS['trigram'], UMLAUT_TRIGRAMS['percentage'])}
# Regular expressions for detecting trigrams of line beginning
REPLACE_UNRECOGNIZED_CHARS = regex.compile(r'[\x00-\x08\x0b-\x1f]')
MATCH_BEGINNING_TRIGRAM = regex.compile(r'\p{Latin}[.,!?; ][\p{Latin} ]')
MATCH_2ND_BEGINNING_TRIGRAM = regex.compile(r'[ \p{Latin}]{3}')
BEGINNINGS_lookup = {trigram: percentage for trigram, percentage in zip(BEGINNINGS['trigram'], BEGINNINGS['percentage'])}
# Possible Commodore 64 encodings
ENCODING_MAPPING = {0: 'petscii_c64en_lc',
                    1: 'ascii',
                    2: 'screencode_c64_lc'}


def decode_text(binary_text: bytes, threshold: float):
    """
    The function converts the binary text to a string
    :param binary_text:
    :param threshold:
    :return:
    """
    if not isinstance(binary_text, bytes) or len(binary_text) == 0:
        return None, None, None, 'Nicht-binäre Datei'
    entr = check_entropy(binary_text)
    if entr >= 7:
        return entr, None, None, 'Komprimierte Datei/Assembler Code'

    texts = []
    sum_chars = []
    for encoding_index, encoding in ENCODING_MAPPING.items():
        if encoding_index == 0:
            decoded = binary_text.replace(b'\n\r', b'\r').replace(b'\r\n', b'\r').replace(b'\n', b'\r')
            decoded = decoded.decode(encoding='petscii_c64en_lc', errors='replace').replace('\r', '\n')
        else:
            decoded = binary_text.decode(encoding=encoding, errors='replace')
        decoded = REPLACE_UNRECOGNIZED_CHARS.sub('\N{REPLACEMENT CHARACTER}', decoded)
        decoded = decoded.replace(u'\xa0', ' ')
        texts.append(decoded)
        alpha_chars = sum(1 for character in decoded if character.isalpha())
        sum_chars.append(alpha_chars / len(decoded))
    best_encoding = np.argmax(np.array(sum_chars))
    if max(sum_chars) < threshold:
        return entr, None, None, 'Programmcode'
    else:
        text = texts[best_encoding]
        text, mapping = replace_custom_umlauts(text)
        text, best_line_length = insert_newlines(text)
        return entr, text, best_line_length, 'Textdokument'


def check_entropy(binary_text: bytes) -> int:
    """
    The function checks shannon's entropy of the binary file
    :param binary_text: Binary version of some diskmag program
    :return: Returns the entropy value
    """
    binary_text_size = len(binary_text)
    character_counts = Counter(binary_text)
    dist = np.array(list(character_counts.values())) / binary_text_size
    entropy_value = entropy(dist, base=2)
    return entropy_value


def replace_alt_umlauts(string: str) -> str:
    """
    The function takes a string and returns new string
    where alternative umlaut representations are replaced
    with german umlaut representations
    :param string: The string which should be processed by function
    :return: string with fixed umlauts
    """
    fixed_string = FIND_DOUBLE_UMLAUTS.sub(lambda match: DOUBLE_UMLAUTS[match.group(0)], string)
    return fixed_string


def replace_custom_umlauts(text: str):
    """
    :param text: string, where the umlauts were encoded with
    other characters
    :return: string with re-coded umlauts
    :author: Anton Ehrmanntraut
    """
    matches = list(FIND_UMLAUT_TRIGRAM.finditer(text))
    if not matches:
        return text, {}

    replacement_chars = set()
    trigrams = list()
    for m in matches:
        replacement_chars.add(m.group(1))
        trigrams.append(regex.sub(r'[,.:;\-"?!]', ' ', text[m.start(1) - 1:m.end(1) + 1]))

    num_replacement_chars = len(replacement_chars)
    if num_replacement_chars > 7:
        return text, {}

    mapping_logprobs = {}
    for mapping in itertools.permutations(UMLAUTS, r=len(replacement_chars)):
        trans = dict(zip(replacement_chars, mapping))
        score = 0
        translated_trigrams = (t.translate(str.maketrans(trans)) for t in trigrams)
        for t in translated_trigrams:
            prob = UMLAUTS_lookup.get(t, 0)
            if prob:
                score += np.log(prob)
            else:
                score += -50

        mapping_logprobs[mapping] = score

    best_mapping, best_logprob = max(mapping_logprobs.items(), key=lambda i: i[1])
    if best_logprob < -50 * len(trigrams) * 2 / 3:
        return text, {}

    trans = dict(zip(replacement_chars, best_mapping))
    substitutions = [(i, orig, trans[orig]) for i, orig in enumerate(text) if orig in trans.keys()]
    text = text.translate(str.maketrans(trans))
    return text, substitutions


def insert_newlines(text: str):
    """
    :param text: Takes a text which should be splitted into lines
    :return: Returns a text with inserted newlines
    :author: Anton Ehrmanntraut
    """
    logprobs = {}
    for col_len in range(40, 81):
        rows = [''.join(x) for x in more_itertools.chunked(text, n=col_len)]
        scores = []
        for prev_row, row in zip(itertools.chain([None], rows), rows):
            if prev_row is not None and prev_row.endswith('-'):
                continue
            trigram = row[:3]
            if MATCH_BEGINNING_TRIGRAM.fullmatch(trigram):
                scores.append(-100)
                continue
            if trigram == '   ' or not MATCH_2ND_BEGINNING_TRIGRAM.fullmatch(trigram):
                continue

            prob = BEGINNINGS_lookup.get(trigram, 0)
            if prob:
                scores.append(np.log(prob))
            else:
                scores.append(-100)
        if scores:
            logprobs[col_len] = np.mean(scores)
        else:
            continue

    if not logprobs:
        return text, 0
    best_col_len, logprob = max(logprobs.items(), key=lambda i: i[1])
    rows = [''.join(x) for x in more_itertools.chunked(text, n=best_col_len)]
    return '\n'.join(rows), best_col_len
