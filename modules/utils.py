"""Commonly used functions."""

import logging
import os

from STAPLERerror import STAPLERerror
from STAPLERerror import NotConfiguredError

# Define the config file path
CONFIG_FILE_PATH = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
CONFIG_FILE_PATH = os.path.split(CONFIG_FILE_PATH)[0]
CONFIG_FILE_PATH = os.path.join(CONFIG_FILE_PATH, 'config.txt')

# The following commands need not to be in config.txt
CONFIG_FILE_OMITTED_COMMANDS = set(['CUSTOM', 'bayenv2', 'vcf_sort'])

def parse_staplefile_command_line(command_line):
    """Parses command type and parameters from command line strings.

    Parameters:
    command_line: User-defined command line (in staplefile) for specific tool.

    Returns:
    command_type: The class of the tool specified in the command line.
    command_parameters: Parameters to be used with the tool.

    Raises:
    STAPLERerror: The command type user has defined is not supported by STAPLER.
    """
    import AvailableCommands

    command_line = command_line.split()
    try:
        command_type = AvailableCommands.commands[command_line[0]]
    except KeyError:
        raise STAPLERerror(
            'The following command type is not '
            'supported: {0}'.format(command_line[0]))
    command_parameters = ' '.join(command_line[1:])
    return command_type, command_parameters


def parse_table_2(handle):
    """Reads a tab delimited table of two columns into a dict name:value

    Parameters:
    handle: File in opened in a read mode

    Returns:
    d: Dict of name:value.

    Raises:
    STAPLERerror: File has wrong number of columns or a value on col 1 is mentioned
    twice.
    """
    d = {}
    for ln in handle:
        ln = ln.strip()
        if ln.startswith('#'):
            continue
        if not ln:
            continue
        ln = ln.split('\t')
        if len(ln) != 2:
            raise STAPLERerror('Expected 2 columns in file:\n{0}'
                               '\nfound: {1}'.format(handle, len(ln)))
        if ln[0] in d:
            raise STAPLERerror('Expected to find each row name only once when '
                               'reading file:\n{0}\nThis value was found twice:'
                               '\n{1}'.format(handle, ln[0]))

        d[ln[0]] = ln[1]
    return d


def read_value(file_path, name):
    """Open a file and returns the value of row with specific name.

    Parameters:
    file_path: Path to an existing file. parse_table_2 must be able to open
    and parse the file.
    name: Row name in the file.

    Raises:
    STAPLERerror: Unable to open or parse the file.
    """
    try:
        fl = open(file_path)
    except IOError as err:
        raise STAPLERerror('Unable to open file:\n{0}\nReason:\n{1}'.format(file_path, err))
    d = parse_table_2(fl)
    fl.close()

    try:
        return d[name]
    except KeyError:
        raise STAPLERerror('The following file does not contain row name {'
                           '0}\n{1}'.format(name, file_path))


def parse_table_multi(handle, key_col_name, value_col_name):
    """Reads a tab delimited table of n columns into a dict name:value

    Parameters:
    handle: File in opened in a read mode
    key_col_name: Name of a column to read as a key.
    value_col_name: Name of a column to read as a value.

    Returns:
    Dict of name:value.

    Raises:
    ValueError: File has wrong number of columns or a value on col 1 is
    mentioned twice.
    """
    d = {}
    i = 0
    for ln in handle:
        i += 1
        ln = ln.strip()
        if i == 1:
            ln = ln.strip('#')
            if '\t' not in ln:
                raise ValueError('File must have several columns:\n{0}'
                                 .format(handle))
            col_names = ln.split('\t')
            if key_col_name not in col_names:
                raise ValueError('{0} was not found from row names in file: {1}'
                                 .format(key_col_name, col_names))
            if value_col_name not in col_names:
                raise ValueError('{0} was not found from row names in file: {1}'
                                 .format(value_col_name, col_names))
            key_col = col_names.index(key_col_name)
            value_col = col_names.index(value_col_name)
            continue
        if ln.startswith('#'):
            continue
        if not ln:
            continue
        values = ln.split('\t')
        if len(values) != len(col_names):
            raise ValueError('Number of columns on the following row ({0}) '
                             'differs from the number of columns names '
                             '({1}):\n{2}'.format(len(values),
                                                  len(col_names),
                                                  ln))
        if key_col in d:
            raise ValueError('Expected to find each key name only once when '
                             'reading file! This value was found twice:'
                             '\n{0}'.format(key_col))
        d[values[key_col]] = values[value_col]
    return d


def read_value_from_multi_table(file_path, name, key_col_name, value_col_name):
    """Open a file and returns the value of row with specific name.

    Parameters:
    file_path: Path to an existing file. parse_table_2 must be able to open
    and parse the file.
    name: Row name in the file.
    key_col_name: Name of the key column in the file.
    value_col_name: Name of the value column in the file.

    Raises:
    STAPLERerror: Unable to open or parse the file.
    """
    try:
        fl = open(file_path)
    except IOError as err:
        raise STAPLERerror('Unable to open file:\n{0}\nReason:\n{1}'.format(file_path, err))

    try:
        d = parse_table_multi(fl, key_col_name, value_col_name)
    except ValueError as ex:
        raise STAPLERerror('Problem when trying to open file:\n{0}\n{1}'
                           .format(file_path, str(ex)))
    finally:
        fl.close()
    try:
        return d[name]
    except KeyError:
        raise STAPLERerror('Could not find string "{0}" from file\n{1}'
                           '\nFound names are:\n{2}'.format(name, file_path,
                                                            '\n'.join(sorted(list(d.keys())))))


def get_config_file():
    """Returns the whole config file as string.

    Returns:
    config_lines: Command file contents.
    """
    try:
        with open(CONFIG_FILE_PATH, 'r') as content_file:
            config_file_string = content_file.read()
            config_file_string = config_file_string.replace('\r\n', '\n')
    except:
        raise STAPLERerror('Unable to open config file from path:\n{0}'
                           .format(CONFIG_FILE_PATH))

    return config_file_string



def parse_config(tool_name, key_col_name, value_col_name):
    """Parses the "execute" field for the given tool from installation config
    file.


    Parameters:
    tool_name: Tool name to search from file.

    Raises:
    STAPLERerror if config file does not exists.
    STAPLERerror if tool value can not be read from file.
    STAPLERerror if tool value was an empty string.

    Returns:
    String containing the user specified run command, None if no special
    command has been defined.
    """
    # Return None for the generic_base class, as it should not be in the
    # config file in any case

    try:
        run_command = read_value_from_multi_table(CONFIG_FILE_PATH,
                                                  tool_name,
                                                  key_col_name,
                                                  value_col_name)
    except STAPLERerror:
        print 'Error when reading installation configuration file for ' \
              'tool {0}'.format(tool_name)
        logging.error('Error when reading installation configuration file '
                      'for the tool {0}'.format(tool_name))
        raise

    if run_command == 'none':
        raise NotConfiguredError()
    if run_command == '':
        raise STAPLERerror('Error! Empty value for tool {0} was found from '
                           'installation configuration file !):\n{1}'.format(tool_name,
                                                                             CONFIG_FILE_PATH))

    return run_command


def parse_module(tool_name, key_col_name, value_col_name):
    """Parses the run command for the given tool from installation config file.

    Parameters:
    tool_name: Tool name to search from file.
    key_col_name: Name of the key column,
    value_col_name: Name of the value column.

    Raises:
    STAPLERerror if config file does not exists.
    STAPLERerror if tool value can not be read from file.
    STAPLERerror if tool value was an empty string.

    Returns:
    String containing the user specified run command, None if no special
    command has been defined.
    """
    # Return None for the generic_base class, as it should not be in the
    # config file in any case
    if tool_name == 'GenericBase': return None

    # Define the location of STAPLER.py file
    try:
        load_module = read_value_from_multi_table(CONFIG_FILE_PATH,
                                                  tool_name,
                                                  key_col_name,
                                                  value_col_name)
    except STAPLERerror:
        print 'Error when reading installation configuration file for ' \
              'tool {0}'.format(tool_name)
        logging.error('Error when reading installation configuration file '
                      'for the tool {0}'.format(tool_name))
        raise

    if '!+' in load_module:
        return load_module.split('!+')
    elif load_module == 'none':
        return []
    if load_module == '':
        raise STAPLERerror('Error! Empty value for tool {0} was found from '
                           'installation configuration file (use the value "none" '
                           'if you wish not define a special run command for '
                           'this tool!):\n{1}'
                           .format(tool_name, CONFIG_FILE_PATH))

    return [load_module]


def find_pairs(virtual_dir, pattern='_R?', user=None, file_formats=None,
               exclusion_iterable=None):
    """Finds pairs for paired end files within virtual directories.

    Parameters:
    virtual_dir: Virtual directory containing files.
    pattern: Pattern to look for from the files. Pair 1 should have 1 and
    pair 2 a 2 in place of ?.
    user: Name of the user. Files that are already used by the user are
    ignored.
    file_format: Files not in specified format are ignored.
    exclusion_iterable: Iterable of substrings. Files containing any of these
    items are omitted from output.

    Raises:
    STAPLERerror: If pattern does not contain exactly one "?".

    Returns: List of (file_1, file_2) tuples.
    """

    if pattern.count('?') != 1:
        raise STAPLERerror('Paired end pattern should contain one "?", current pattern:\n{0}'
                           .format(pattern))

    if user is None:
        user = []
    if file_formats is None:
        file_formats = []
    if exclusion_iterable is None:
        exclusion_iterable = []

    pairs = []
    read1_pattern = pattern.replace('?', '1')
    read2_pattern = pattern.replace('?', '2')
    files = virtual_dir.file_names.keys()
    for fl in files:
        #Exclude files that are in wrong format
        if file_formats:
            correct_format = False
            for f in file_formats:
                if fl.endswith(f):
                    correct_format = True
            if not correct_format: continue
        #Exclude file if it contains a specified substring
        if exclusion_iterable:
            cnt = False
            for substring in exclusion_iterable:
                if substring in fl:
                    cnt = True
                    break
            if cnt: continue
        if read1_pattern in fl:
            pair1_fl = fl
            pair2_fl = pair1_fl.replace(read1_pattern, read2_pattern)
            if not pair2_fl in files: continue
            if user:
                if user in virtual_dir.file_names[pair1_fl].users:
                    continue
                if user in virtual_dir.file_names[pair2_fl].users:
                    continue
            pairs.append((pair1_fl, pair2_fl))
    return pairs


def splitext(absolute_path):
    """"Similar to os.path.splitext, but includes two file extensions for compressed files

    gives .<ext>.gz extension for gzip compressed files
    gives .<ext>.bz2 extension for bz2 compressed files

    Parameters:
    file_name: name of the file

    Returns: a list of [basename, extension (empty string if no extension)]
    """
    splitexted_absolute_path = os.path.splitext(absolute_path)
    if splitexted_absolute_path[1] in ('.gz', '.bz2'):
        twice_splitexted_absolute_path = os.path.splitext(splitexted_absolute_path[0])
        if not twice_splitexted_absolute_path[1]: # i.e. <basename>.gz
            return splitexted_absolute_path
        else: # i.e. <basename>.<ext>.gz
            return [twice_splitexted_absolute_path[0],
                    twice_splitexted_absolute_path[1] + splitexted_absolute_path[1]]
    else:
        return os.path.splitext(absolute_path)


def infer_path_id(path):
    """Infers the ID of a directory or a file.

    Id is defined as the string preceding the first dot in the file basename.

    Parameters:
    path: an absolute or a relative path to a directory or a file

    Returns:
    id: the string preceding the first dot in the path string basename.
    """
    path = os.path.basename(path)
    return path.split('.', 1)[0]

