import glob
import os
from tqdm import tqdm
from c64_diskmag_converter.diskmag import DiskmagC64


class Corpus:
    def __init__(self, corpus_name, corpus_path):
        if not os.path.exists(corpus_path):
            raise ValueError('The path to the corpus seems to be invalid')
        self.corpus_name = corpus_name
        self.corpus_path = corpus_path
        self.files = self.get_files()

    def get_files(self):
        file_paths = []
        pattern = '.d64'
        files = glob.glob(os.path.join(self.corpus_path, '**', f'*{pattern}'), recursive=True)
        file_paths.extend(files)
        return sorted(file_paths)

    def rename_files(self):
        pattern = '.d64'
        files = list(filter(lambda x: x.endswith(pattern), self.files))
        counts = {}
        for file in files:
            directory = os.path.dirname(file)
            counts[directory] = counts.get(directory, 0) + 1

        for directory, count in counts.items():
            if count > 1:
                dir_files = glob.glob(os.path.join(directory, '**', f'*{pattern}'), recursive=True)
                for i, file in enumerate(dir_files):
                    ext = os.path.splitext(os.path.basename(file))[1]
                    current_dir = os.path.basename(os.path.basename(os.path.dirname(file)))
                    new_base_filename = current_dir.lower().replace('.', '_').replace(' ', '_')
                    new_filename = f"{new_base_filename}_{i + 1}{ext}"
                    os.rename(file, os.path.join(directory, new_filename))
            else:
                dir_files = glob.glob(os.path.join(directory, '**', f'*{pattern}'), recursive=True)
                for file in dir_files:
                    ext = os.path.splitext(os.path.basename(file))[1]
                    current_dir = os.path.basename(os.path.basename(os.path.dirname(file)))
                    new_base_filename = current_dir.lower().replace('.', '_').replace(' ', '_')
                    new_filename = f'{new_base_filename}{ext}'
                    os.rename(file, os.path.join(directory, new_filename))

        self.files = self.get_files()

    def convert_files_to_tei(self, char_threshold: float):
        for disk_image in tqdm(self.files, unit='disk_images', desc=f'Converting disk images to TEI'):
            diskmag = DiskmagC64(disk_image)
            diskmag.convert_to_tei(char_threshold)
