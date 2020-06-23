import collections
import copy
import logging
import os

from STAPLERerror import STAPLERerror
from STAPLERerror import VirtualIOError
import utils



class Custom():
    """Custom command defined by user.

    Parameters:
    in_cmd: String containing a command line
    in_dir: Directory object containing input files
    out_dir: Directory object containing output files
    NOTICE! Keep the directory objects up to date about file edits!

    Attributes:
    name: Name of the function.
    input_type: Input types accepted by this application.
    output_types: List of output types produced by the application.
    require_output_dir: Bool for whether or not a new output directory is
    required as some tools output to input directory.
    mandatory_args: Args the user be provided in in_cmd when initializing.
    user_mandatory_args: Args the user must provide.
    remove_user_args: Args that will be removed from the final command.
    optional_args: Args that may be part of the command line.
    in_cmd: Command entered by user.
    parsed_cmd: Final output command as option:value dict.
    file_names: Names of output files.
    command_ids: File names of input file(s) with no file extensions.


    Methods:
    get_cmd: Method for getting the final cmd line string for output.
    """

    name = 'custom'
    input_types = set([])
    output_types = []
    require_output_dir = True
    mandatory_args = ['-i', '-o']
    user_mandatory_args = []
    remove_user_args = user_mandatory_args
    optional_args = []
    parallelizable = True
    help_description = '''
Special command for using any tool, details hidden from user.
'''

    def __init__(self, in_cmd, in_dir, out_dir):
        logging.info('Trying to initialize {0} with user command:\n{1}'
                     .format(self.name, in_cmd))
        self.command_string = in_cmd
        self.in_dir = in_dir
        self.out_dir = out_dir
        self.out_cmd, self.command_ids = self._select_IO(self.command_string,
                                                         in_dir,
                                                         out_dir)
        assert isinstance(self.command_ids, list)
        self.command_ids = sorted(self.command_ids)
        self.out_cmd = self._user_override(self.out_cmd)
        # Modules can not be loaded with this command
        self.load_module = []
        self.unload_module = []
        self.command_lines = self.get_cmd()
        logging.info('Finished initializing {0} with user command:\n{1}'
                     .format(self.name, in_cmd))


    def _select_IO(self, command_string, in_dir, out_dir):
        """Infers the input and output file paths.

        This method must keep the directory objects up to date of the file
        edits!

        Parameters:
        in_cmd: A dict containing the command line.
        in_dir: Input directory (instance of filetypes.Directory).
        out_dir: Output directory (instance of filetypes.Directory).

        Returns:
        out_cmd: Dict containing the output commands
        command_identifier: Input file name based identifier for the current command

        Raises:
        VirtualIOError: No valid input file can be found.
        """
        # Split the command line into elements
        command_elements = command_string.split()

        # Parse elements
        IDd_IO_elements = collections.OrderedDict()
        input_elements = collections.OrderedDict()
        all_input_elements = collections.OrderedDict()
        pair_elements = collections.OrderedDict()
        pair_identifier = []
        output_elements = collections.OrderedDict()
        all_IO_elements = collections.OrderedDict()
        i = -1
        for element in command_elements:
            i += 1
            # Find elements containing $INPUT, $PAIR_1, $PAIR_2 and $OUTPUT
            # strings
            current_element_string = element
            element_is_INPUT = False
            element_is_ALL_INPUTS = False
            element_is_PAIR1 = False
            element_is_PAIR2 = False
            element_is_OUTPUT = False
            if '$OUTPUT' in element:
                #masked_element = self._mask_curly_brace_contents(element)
                unparsed_substring = element.split('$OUTPUT', 1)
                element_is_OUTPUT = True
            elif '$NO_OUTPUT' in element:
                unparsed_substring = element.split('$NO_OUTPUT', 1)
                if ''.join(unparsed_substring):
                    raise STAPLERerror('$NO_OUTPUT should not be a '
                                       'substring, but as a standalone '
                                       'parameter separated with whitespace '
                                       'from other strings. Please revise '
                                       'line:\n{0}'.format(command_string))
                element_is_OUTPUT = True
            else:
                if '$INPUT' in element:
                    unparsed_substring = element.split('$INPUT')
                    element_is_INPUT = True
                if '$ALL_INPUTS' in element:
                    element_is_ALL_INPUTS = True
                    # $ALL_INPUTS can contain whitespaces within curly
                    # braces. Scan if this is the case and rejoin the strings
                    # split earlier to be contained within single element.
                    while (element.count('{') - element.count('}')) > 0:
                        try:
                            element = command_elements[i] + ' ' + command_elements[i+1]
                        except IndexError:
                            raise STAPLERerror('An unpaired curly brace '
                                               'detected on element {0} on '
                                               'line:\n{1}'.format(element,
                                                                   command_string))
                        command_elements[i] = element
                        del command_elements[i+1]
                    unparsed_substring = element.split('$ALL_INPUTS')
                    current_element_string = element
                if '$PAIR_1' in element:
                    unparsed_substring = element.split('$PAIR_1')
                    element_is_PAIR1 = True
                if '$PAIR_2' in element:
                    unparsed_substring = element.split('$PAIR_2')
                    element_is_PAIR2 = True


            # Check the numbers of input and output identifiers in single text element

            if sum([element_is_INPUT, element_is_PAIR1, element_is_PAIR2,
                    element_is_ALL_INPUTS, element_is_OUTPUT]) == 0: continue

            if '{' in unparsed_substring[1]:
                if not unparsed_substring[1].startswith('{'):
                    raise STAPLERerror('File extension definition should not '
                                       'precede curly braces as in element '
                                       '{0}. In input keywords the correct '
                                       'order is: keyword, curly braces, '
                                       'file extension. Please revise the '
                                       'command line:\n{1}'.format(element, command_string))

            if sum([element_is_INPUT, element_is_PAIR1, element_is_PAIR2, element_is_OUTPUT]) > 1:
                raise STAPLERerror('Command line element {0} contains multiple inputs or outputs. '
                                   'Please revise the command line:\n{1}'.format(element, command_string))

            if len(unparsed_substring) > 2:
                raise STAPLERerror('Command line element {0} contains multiple inputs or outputs. '
                                   'Please revise the command line:\n{1}'.format(element, command_string))

            # pre_substring allows text to precede input/output string e.g. INPUT_PATH=$INPUT, where pre_substring
            # would be "INPUT_PATH=" e.g. as in picard toolkit.
            pre_substring = unparsed_substring[0]
            unparsed_substring = unparsed_substring[1]

            # Parse $INPUT parameter optional IO-file index
            input_identifier = None
            if element_is_INPUT and unparsed_substring.startswith('{'):
                if unparsed_substring.count('{') != 1 or \
                                unparsed_substring.count('}') != 1:
                    raise STAPLERerror('Syntax for adding index to IO-keyword '
                                       'includes an integer within curly '
                                       'braces (e.g. $INPUT{1}). Please '
                                       'revise the command line:\n' + command_string)
                input_identifier = unparsed_substring.split('{')[1].split('}')[0]
                try:
                    int(input_identifier)
                except ValueError:
                    raise STAPLERerror('Syntax for adding index to IO-keyword '
                                       'includes an integer within curly '
                                       'braces (e.g. $INPUT{1}). Please '
                                       'revise the command line:\n' + command_string)
                IDd_IO_element = current_element_string.split('}')[0] + '}'
                if IDd_IO_element in IDd_IO_elements:
                    if current_element_string != IDd_IO_elements[IDd_IO_element]:
                        raise STAPLERerror('It is not allowed to define the same '
                                           'IO-keyword twice with different '
                                           'filename patterns (e.g. $INPUT{'
                                           '1}.fastq and $INPUT{1}.txt). '
                                           'Revise line:\n' + command_string)
                    else:
                        # Element has been parsed already, no need to redo it
                        continue
                else:
                    IDd_IO_elements[IDd_IO_element] = current_element_string
                unparsed_substring = unparsed_substring.split('}')[1]

            # Parse $ALL_INPUTS optional input variable prefix
            if element_is_ALL_INPUTS:
                input_variable_prefix = ''
                if unparsed_substring.startswith('{'):
                    if unparsed_substring.count('{') > 1 or unparsed_substring.count('}') > 1:
                        raise STAPLERerror('If not additional info is '
                                           'given for $ALL_INPUTS within curly '
                                           'braces, all acceptable input files '
                                           'will be by default listed one after '
                                           'another, '
                                           'e.g. /path/input_1 /path/input_2 ... '
                                           'If an input variable needs to '
                                           'explicitly defined (e.g. '
                                           'INPUT=/path/input_1 '
                                           'INPUT=/path/input_2) this information '
                                           'can be defined within curly braces: '
                                           '$ALL_INPUTS{INPUT=} Please revise '
                                           'the command line:\n' + command_string)
                    input_variable_prefix = unparsed_substring.split('{')[1].split('}')[0]
                    unparsed_substring = unparsed_substring.split('}')[1]



            # Parse $OUTPUT parameter optional IO-file identifier
            output_identifier = None
            if element_is_OUTPUT and unparsed_substring.startswith('{'):
                output_identifier = unparsed_substring.split('{',1)[1].rsplit('}',1)[0]
                unparsed_substring = unparsed_substring.replace('{' + output_identifier + '}', '')

            # Parse pair identifiers from $PAIR_N keywords
            current_pair_identifier = None
            if element_is_PAIR1 or element_is_PAIR2:
                if unparsed_substring.count('{') != 1 or unparsed_substring.count('}') != 1 or \
                        not unparsed_substring.startswith('{'):
                    # If no pair identifier is found, assume "_R1" and "_R2"
                    guessing_pair_id = True
                    if element_is_PAIR1:
                        current_pair_identifier = '_R1'
                    else:
                        current_pair_identifier = '_R2'
                else:
                    # Extract the contents of curly braces
                    guessing_pair_id = False
                    current_pair_identifier = unparsed_substring.split('}')[0][1:]
                    unparsed_substring = unparsed_substring.split('}')[1]

            # Parse the optional filename extension
            if unparsed_substring:
                if not unparsed_substring.startswith('.'):
                    raise STAPLERerror('Please revisit documentation for '
                                       'proper IO-keyword syntax.'
                                       'Cannot parse substring "{0}" '
                                       'of IO-keyword {1} on line:\n{2}'.format(unparsed_substring,
                                                   current_element_string,
                                                   command_string))

                file_extension = unparsed_substring
            else:
                file_extension = ''

            # Add the input and output parameters to an appropriate dictionary
            if element_is_INPUT:
                if current_element_string in input_elements:
                    if input_identifier is None:
                        raise STAPLERerror('By default the $INPUT parameter '
                                           'can be defined only once per '
                                           'command line. If you want to '
                                           'define multiple input files or '
                                           'use the same input files as a '
                                           'parameter several times you '
                                           'should add an identifier, '
                                           'e.g. $INPUT{1}, $INPUT{2}. Please '
                                           'revise command line:\n' +
                                           command_string)
                input_elements[current_element_string] = [input_identifier, file_extension, pre_substring]
            elif element_is_PAIR1 or element_is_PAIR2:
                pair_identifier.append(current_pair_identifier)
                pair_elements[current_element_string] = [pair_identifier, file_extension, pre_substring]
            elif element_is_ALL_INPUTS:
                all_input_elements[current_element_string] = [input_variable_prefix, file_extension, pre_substring]
            elif element_is_OUTPUT:
                output_elements[current_element_string] = [output_identifier, file_extension, pre_substring]
            else:
                assert False

        # Update all_IO_elements to contain all elements of IO subdicts
        all_IO_elements.update(input_elements)
        all_IO_elements.update(pair_elements)
        all_IO_elements.update(all_input_elements)
        all_input_file_extensions = set([e[1] for e in all_IO_elements.values()])
        if '' in all_input_elements: all_input_file_extensions = None
        all_IO_elements.update(output_elements)


        # Validate the number of inputs
        if not input_elements and not pair_elements and not all_input_elements:
            raise STAPLERerror('{0} command must have either one or more '
                               '$INPUT keywords or two $PAIR '
                               'keywords or a single $ALL_INPUTS.'.format(self.name))
        if pair_elements and len(pair_elements) != 2:
            raise STAPLERerror('{0} command must have $PAIR_1 and $PAIR_2 '
                               'keywords. Please revise line:\n{1}'.format(self.name, command_string))
        i = 0
        if input_elements: i += 1
        if pair_elements: i += 1
        if all_input_elements: i += 1
        if i > 1:
            raise STAPLERerror('{0} command can contain either $INPUT, '
                               '$PAIR or $ALL_INPUTS keywords, but any '
                               'combination of these. Please revise line: '
                               '{1}'.format(self.name, command_string))
        if not output_elements:
            raise STAPLERerror('{0} command must have at least one $OUTPUT '
                               'keyword. Please revise line:\n{1}'.format(
                self.name, command_string))
        if len(output_elements) > 1 and '$NO_OUTPUT' in output_elements:
            raise STAPLERerror('{0} command can contain only one $NO_OUTPUT '
                               'keyword. No other output keywords are '
                               'allowed. Please revise line:\n{1}'.format(self.name, command_string))

        # Input elements set to contain the input elements regardless if pair
        # or all inputs
        input_elements.update(pair_elements)
        input_elements.update(all_input_elements)


        # Find suitable input file from input directory
        IO_files = {}
        command_ids = []
        used_files_exist = False
        pairs_found = False
        all_ALL_INPUTS_file_path_strings = []
        for input_element_string, input_element_params in input_elements.iteritems():
            if pairs_found: break
            for fl in in_dir.unused_files(self.command_string, all_input_file_extensions):

                # Parse filename extension
                input_extension = utils.splitext(fl.name)[1]

                # Skip files that have incorrect file extension
                file_extension = input_element_params[1]


                if file_extension:
                    if file_extension != input_extension: continue
                # Find paired-end files
                if pair_elements:
                    # Go to next file if paired-end identifiers are not found
                    if input_element_params[0][0] not in fl.name and \
                                    input_element_params[0][1] not in fl.name:
                        found_one_pair = True
                        continue

                    # Infer putative pair name
                    if input_element_params[0][0] in fl.name:
                        putative_pair_name = fl.name.replace(
                            input_element_params[0][0],
                            input_element_params[0][1])
                    else:
                        putative_pair_name = fl.name.replace(
                            input_element_params[0][1],
                            input_element_params[0][0])

                    # Infer putative pair string. There are two items in
                    # pair_elements dict: the current element and the pair.
                    # Removing the current one leaves the pair element string.
                    pair_element = copy.deepcopy(pair_elements)
                    del pair_element[input_element_string]
                    pair_element_string = pair_element.keys()[0]

                    # Find the pair from input directory files
                    if putative_pair_name in in_dir.file_names:
                        # Pair 1
                        IO_files[input_element_string] = os.path.join(in_dir.path,fl.name)
                        command_ids.append(utils.infer_path_id(IO_files[input_element_string]))
                        in_dir.use_file(fl.name, self.command_string)
                        # Pair 2
                        IO_files[pair_element_string] = os.path.join(in_dir.path,
                                                                     putative_pair_name)
                        command_ids.append(utils.infer_path_id(IO_files[pair_element_string]))
                        in_dir.use_file(putative_pair_name, self.command_string)
                        pairs_found = True
                        break
                    else:
                        raise STAPLERerror('Unable to find a pair for file {0}, '
                                           'expected to find a pair with name '
                                           '{1}'.format(fl.name, putative_pair_name))
                elif all_input_elements:
                    if not input_element_string in IO_files:
                        IO_files[input_element_string] = os.path.join(in_dir.path,fl.name)
                    if not input_element_params[0]:
                        # No user set prefix for input files, will print
                        # whitespace delimited list of paths
                        all_ALL_INPUTS_file_path_strings.append(os.path.join(in_dir.path,fl.name))
                    else:
                        # Input variables will be delimited by whitespace
                        # plus the user defined string
                        all_ALL_INPUTS_file_path_strings.append(input_element_params[0] + os.path.join(in_dir.path, fl.name))
                    command_ids.append(utils.infer_path_id(fl.name))
                    in_dir.use_file(fl.name, self.command_string)
                else: # Non-paired input
                    if not input_element_params[0]:
                        IO_files[input_element_string] = (os.path.join(in_dir.path, fl.name))
                    else:
                        IO_files[input_element_string] = os.path.join(in_dir.path, fl.name)
                    command_ids.append(utils.infer_path_id(fl.name))
                    in_dir.use_file(fl.name, self.command_string)
                    break
        if not IO_files:
            if pair_elements:
                if not used_files_exist and guessing_pair_id:
                    raise STAPLERerror('Command line contains paired end '
                                       'input but no file pairs were found. '
                                       'Command line does not specify read '
                                       'pair identifiers so it was assumed '
                                       'first file pair contains string "_R1"'
                                       'and the second file pair string '
                                       '"_R2". If this is not the case define'
                                       'custom ids according to your file '
                                       'naming scheme, e.g. $PAIR_1{_P1} '
                                       '$PAIR_2{_P2}')
            raise VirtualIOError('No more unused input files')

        # Parse output elements
        for output_element_string, output_element_params in output_elements.iteritems():
            if output_element_string == '$NO_OUTPUT': continue
            # Output file name is based on specific user chosen input file name
            if output_element_params[0] is not None:
                if output_element_params[0] not in input_elements:
                    raise STAPLERerror('The $OUTPUT keyword have curly braces '
                                       'containing one of the defined $INPUT '
                                       'or $PAIR strings to indicate the '
                                       'input file name to use for output '
                                       'file name. The syntax for $OUTPUT '
                                       'keyword is: $OUTPUT{$INPUT{1}}. '
                                       'Please revise line: ' + command_string)
                output_path = IO_files[output_element_params[0]]
            else: # Choose output file name based on the "first" input file name
                output_path = IO_files[input_elements.keys()[0]]
                if isinstance(output_path, list):
                    output_path = output_path[0]

            # Set absolute path by replacing input file directory with output
            #  directory path
            output_path = output_path.replace(in_dir.path, out_dir.path)

            # Replace output path filename extension with user specified one
            if output_element_params[1]:
                output_path = output_path.replace(utils.splitext(output_path)[1],
                                                  output_element_params[1])
            IO_files[output_element_string] = output_path
            out_dir.add_file(os.path.split(output_path)[1])

            # If output is generated into the input file, mark the output file
            # used by the current command to prevent such files being considered
            # as input by the same command.
            if out_dir == in_dir:
                out_dir.use_file(os.path.split(output_path)[1], self.command_string)

        output_cmd = []
        for element in command_elements:
            if element == '$NO_OUTPUT': continue
            if element in all_input_elements:
                cmd_string = all_IO_elements[element][2]
                cmd_string += (' ' + all_IO_elements[element][2]).join(all_ALL_INPUTS_file_path_strings)
                output_cmd.append(cmd_string)
            elif element in all_IO_elements:
                output_cmd.append(all_IO_elements[element][2] + IO_files[element])
            else:
                output_cmd.append(element)
        return output_cmd, command_ids


    def _mask_curly_brace_contents(self, element_string):
        """Removes characters within curly braces.

        Parameters:
        element_string: string of characters

        Returns:
        string with characters removed within any encountered curly braces
        """
        masked_element = []
        brace_level = 0
        for c in element_string:
            if c == '{':
                brace_level += 1
                continue
            elif c == '}':
                brace_level -= 1
                continue
            if brace_level <= 0:
                masked_element.append(c)
        return ''.join(masked_element)


    def _user_override(self, out_cmd):
        """Overrides auto-inferred values with possible user inputs.

        Parameters:
        out_cmd: List of input string elements

        Returns:
        Output commands overridden with user inputs.
        """
        for i in xrange(len(out_cmd)):
            value = out_cmd[i]
            if value.startswith('$VALUE_TABLE'):
                out_cmd[i] = self._parse_value_table(value)
        return out_cmd


    def get_cmd(self):
        """Returns the final command line.

        Returns:
        final_cmd: List of command line produced by the object (line breaks not allowed within command lines!).
        """
        return [' '.join(self.out_cmd)]

class Custom_no_output(Custom):
    """Custom command defined by the user with $NO_OUTPUT argument"""
    require_output_dir = False
