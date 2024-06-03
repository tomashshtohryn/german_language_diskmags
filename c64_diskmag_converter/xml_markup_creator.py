import json
from datetime import datetime
from lxml import etree
from c64_diskmag_converter.text_processing import *


def attach_header(root: etree.Element,
                  series: str,
                  issue: str,
                  principal: str,
                  record: pd.Series) -> etree.SubElement:
    """
    The function creates the TEI-Header element
    :param issue:
    :param root: the root element of the tree
    :param series: the title of the diskmag
    :param principal: the name of the editor
    :param record: the metadata of issue as dataframe
    :return: etree element <teiHeader>
    """
    header = etree.SubElement(root, 'teiHeader')
    filedesc = etree.SubElement(header, 'fileDesc')
    titlestmt = etree.SubElement(filedesc, 'titleStmt')
    title = etree.SubElement(titlestmt, 'title')
    title.text = issue
    principal_name = etree.SubElement(titlestmt, 'principal')
    principal_name.text = principal
    pubstmt = etree.SubElement(filedesc, 'publicationStmt')
    etree.SubElement(pubstmt, 'p').text = 'Erzeugt aus dem Abbild eines Diskettenmagazins'
    etree.SubElement(pubstmt, 'p').text = 'Nachnutzung eingeschränkt'
    sourcedesc = etree.SubElement(filedesc, 'sourceDesc')
    for index, row in record.iterrows():
        bibl = etree.SubElement(sourcedesc, 'bibl', type='diskmag')
        etree.SubElement(bibl, 'title', level='j').text = row['issue']
        etree.SubElement(bibl, 'series').text = series
        group = row['group']
        if isinstance(group, str):
            etree.SubElement(bibl, 'publisher').text = group
        release_date = row['release_converted']
        if isinstance(release_date, str):
            release_date_normalized = datetime.strptime(release_date, '%d.%m.%Y').strftime('%Y-%m-%d')
            etree.SubElement(bibl, 'date', when=release_date_normalized).text = release_date
        link = row['link']
        etree.SubElement(bibl, 'ref', target=link).text = row['source']
        download_links = row['download_links']
        if isinstance(download_links, str):
            for d in download_links.split(', '):
                etree.SubElement(bibl, 'ref', target=d)

    return header


def attach_front(parent: etree.Element, directory: list) -> etree.SubElement:
    """
    Attaches a front element to the text element
    :param parent:
    :param directory:
    :return:
    """
    front = etree.SubElement(parent, 'front')
    div = etree.SubElement(front, 'div', type='directory')
    toc = etree.SubElement(div, 'list')
    for index, entry in enumerate(directory):
        entry = entry.replace(u'\xa0', ' ')
        item = etree.SubElement(toc, 'item')
        item.text = entry
        if 1 <= index < len(directory) - 1:
            target = f"#file_{index}"  # Assuming the target format is 'file_index'
            item.set('corresp', target)

    return front


def attach_text_div(parent, metadata: TextMetaData) -> etree.SubElement:
    """

    :param parent:
    :param metadata:
    :return:
    """
    div = etree.SubElement(parent, 'div')
    div.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    div.set('{http://www.w3.org/XML/1998/namespace}id', f'file_{metadata.xml_id}')
    etree.SubElement(div, 'head').text = metadata.filename
    note_grp = etree.SubElement(div, 'noteGrp')
    etree.SubElement(note_grp, 'note', type='filename_extension').text = metadata.file_ext
    if metadata.filetype:
        etree.SubElement(note_grp, 'note', type='filetype').text = metadata.filetype
    if metadata.entropy is not None:
        etree.SubElement(note_grp, 'note', type='entropy').text = str(metadata.entropy)
    if metadata.encoding:
        etree.SubElement(note_grp, 'note', type='encoding').text = metadata.encoding
    if metadata.text:
        etree.SubElement(note_grp, 'note', type='line_length').text = str(metadata.col_length)
        if metadata.mapping:
            etree.SubElement(note_grp, 'note', type='umlaut_mapping').text = str(metadata.mapping)
        p = etree.SubElement(div, 'p', attrib={'rend': 'hidden'})
        text = metadata.text.split('\n')
        for i, line in enumerate(text, start=1):
            lb = etree.SubElement(p, 'lb', attrib={'n': str(i), 'break': 'yes'})
            if i != len(text):
                lb.tail = f'{line}\n{" " * 10}'
            else:
                lb.tail = f'{line}\n{" " * 8}'
    else:
        etree.SubElement(div, 'gap', reason='irrelevant')

    return div
