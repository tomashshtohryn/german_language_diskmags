from c64_diskmag_converter import *
from c64_diskmag_converter import *
from d64 import DiskImage
import pandas as pd
from pathlib import Path
import re

data_dir = os.path.join(os.path.dirname(__file__), 'data')
issues = os.path.join(data_dir, 'c64_diskmag_issues.csv')
FIND_FILETYPES = re.compile(r'\b(PRG|DEL|SEQ|USR|REL)\b')
ISSUES = pd.read_csv(issues, encoding='utf-8')


class DiskmagC64:
    def __init__(self, diskmag_path: str):
        self.path = Path(diskmag_path)
        self.image = DiskImage(self.path)
        self.filename = self.path.stem
        self.diskmag = self.path.parent.parent.name
        self.issue = self.path.parent.name
        self.record = ISSUES[ISSUES['issue_normalized'] == self.issue]
        self.contents = self.get_contents()
        self.directory = self.get_directory()
        self.is_partial = self.check_d64_files_in_parent()
        if self.is_partial:
            self.image_number = int(self.filename[-1])
        else:
            self.image_number = None

    def check_d64_files_in_parent(self):
        parent_dir = self.path.parent
        d64_files = list(parent_dir.glob('*.d64'))
        return len(d64_files) > 1

    def get_directory(self):
        try:
            with self.image as disk_image:
                directory = []
                for file in disk_image.directory():
                    try:
                        directory.append(file)
                    except Exception as e:
                        directory.append(None)
                return directory
        except (FileNotFoundError, ValueError) as e:
            return None

    def get_contents(self):
        if not self.directory:
            return None
        try:
            directory = self.directory[1:-1]
            with self.image as disk_image:
                for index, entry in enumerate(disk_image.glob(b'*')):
                    try:
                        filename = entry.name.decode(encoding='petscii_c64en_lc', errors='replace')
                        directory_entry = directory[index]
                        if not directory_entry:
                            file_ext = 'Unknown'
                        else:
                            file_ext = FIND_FILETYPES.findall(directory_entry)[0]
                        content = disk_image.path(entry.name)
                        content = content.open().read()
                        if file_ext == 'PRG':
                            content = content[2:]
                        yield filename, file_ext, content
                    except (ValueError, AttributeError):
                        yield filename, file_ext, None
        except (FileNotFoundError, ValueError):
            return None

    def convert_to_tei(self, char_threshold: float):
        tei_path = self.path.parent / f'{self.filename}.xml'
        if not self.directory:
            return f'Error while creating tei file {tei_path}'
        try:
            with open(tei_path, 'wb') as xml_file:
                root = etree.Element('TEI', xmlns='http://www.tei-c.org/ns/1.0')
                attach_header(root, self.image_number, self.diskmag, self.issue, 'Tomash Shtohryn', self.record)
                text_elem = etree.SubElement(root, 'text')
                attach_front(text_elem, self.directory)
                body = etree.SubElement(text_elem, 'body')
                for index, entry in enumerate(self.contents):
                    xml_id = index + 1
                    filename, file_ext, content = entry
                    metadata = TextMetaData.from_binary(filename=filename,
                                                        xml_id=xml_id,
                                                        file_ext=file_ext,
                                                        content=content,
                                                        char_threshold=char_threshold)
                    attach_text_div(body, metadata)
                tree = etree.ElementTree(root)
                etree.indent(tree)
                xml_content = etree.tostring(tree,
                                             pretty_print=True,
                                             xml_declaration=True,
                                             encoding='UTF-8',
                                             method='xml')
                xml_file.write(xml_content)
        except Exception as e:
            print(e, tei_path)
            os.remove(tei_path)
            return f'Error accessing disk image: {str(e)}'
