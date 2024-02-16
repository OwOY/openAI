import codecs


def read_file(file_path):
    with codecs.open(file_path, 'r', 'utf-8') as f:
        return f.read()