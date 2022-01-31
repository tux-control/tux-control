
class ConfigTxtParser(object):
    configuration = {}
    inline_comments = {}

    def __init__(self, config_path: str, ignore_missing_file: bool=True) -> None:
        self.config_path = config_path
        self.load(ignore_missing_file)

    def load(self, ignore_missing_file: bool=True):
        try:
            self._parse()
        except FileNotFoundError:
            if not ignore_missing_file:
                raise

    def _parse(self) -> None:
        with open(self.config_path, 'r') as file:
            line_num = 0
            for line in file:
                if line.strip().startswith('#') or '=' not in line:
                    self.configuration['?{}'.format(line_num)] = line
                    line_num += 1
                    continue

                if '#' in line:
                    to_parse, inline_comment = line.strip().split('#', 1)
                else:
                    to_parse = line.strip()
                    inline_comment = None

                key_raw, value_raw = to_parse.split('=', 1)

                if inline_comment:
                    self.inline_comments[key_raw.strip()] = inline_comment

                self.configuration[key_raw.strip()] = value_raw.strip()
                line_num += 1

    def save(self) -> None:
        with open(self.config_path, 'w') as file:
            for key, value in self.configuration.items():
                if key.startswith('?'):
                    file.write(value)
                elif key in self.inline_comments:
                    file.write('{}={} #{}\n'.format(key, value, self.inline_comments.get(key)))
                else:
                    file.write('{}={}\n'.format(key, value))

    def get(self, key: str, default: any=None):
        return self.configuration.get(key, default)

    def set(self, key, value):
        self.configuration[key] = value

    def remove(self, key):
        if key in self.configuration:
            del self.configuration[key]

    def __setitem__(self, key, value):
        self.configuration[key] = value