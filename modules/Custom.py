import copy
import fnmatch
import itertools
import logging
import os

from GenericBase import GenericBase
from STAPLERerror import STAPLERerror
from STAPLERerror import VirtualIOError
import directory
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
This tool cannot be used by the end user.
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
        IO_files = {}

        # Parse elements
        IDd_IO_elements = {}
        input_elements = {}
        pair_elements = {}
        pair_identifier = []
        output_elements = {}
        for element in command_elements:
            # Find elements containing $INPUT, $PAIR1, $PAIR2 and $OUTPUT strings
            current_element_string = element
            if element.startswith('$INPUT'):
                unparsed_substring = element.replace('$INPUT', '')
                element_is_input = True
                element_is_pair1 = False
                element_is_pair2 = False
                element_is_output = False
            elif element.startswith('$PAIR1'):
                unparsed_substring = element.replace('$PAIR1', '')
                element_is_input = False
                element_is_pair1 = True
                element_is_pair2 = False
                element_is_output = False
            elif element.startswith('$PAIR2'):
                unparsed_substring = element.replace('$PAIR2', '')
                element_is_input = False
                element_is_pair1 = False
                element_is_pair2 = True
                element_is_output = False
            elif element.startswith('$OUTPUT'):
                unparsed_substring = element.replace('$OUTPUT', '')
                element_is_input = False
                element_is_pair1 = False
                element_is_pair2 = False
                element_is_output = True
            else:
                continue

            # Parse $INPUT parameter optional IO-file index
            input_identifier = None
            if element_is_input and unparsed_substring.startswith('{'):
                if unparsed_substring.count('{') != 1 or \
                                unparsed_substring.count('}') != 1:
                    raise STAPLERerror('Syntax for adding index to IO-keyword '
                                       'includes an integer within curly '
                                       'braces (e.g. $INPUT{1}). Please '
                                       'revise the command line: ' + command_string)
                input_identifier = unparsed_substring.split('{')[1].split('}')[0]
                try:
                    int(input_identifier)
                except ValueError:
                    raise STAPLERerror('Syntax for adding index to IO-keyword '
                                       'includes an integer within curly '
                                       'braces (e.g. $INPUT{1}). Please '
                                       'revise the command line: ' + command_string)
                IDd_IO_element = current_element_string.split('}')[0] + '}'
                if IDd_IO_element in IDd_IO_elements:
                    if current_element_string != IDd_IO_elements[IDd_IO_element]:
                        raise STAPLERerror('It is not allowed to define the same '
                                           'IO-keyword twice with different '
                                           'filename patterns (e.g. $INPUT{'
                                           '1}.fastq and $INPUT{1}.txt). '
                                           'Revise line: ' + command_string)
                    else:
                        # Element has been parsed already, no need to redo it
                        continue
                else:
                    IDd_IO_elements[IDd_IO_element] = current_element_string
                unparsed_substring = unparsed_substring.split('}')[1]

            # Parse $OUTPUT parameter optional IO-file identifier
            output_identifier = None
            if element_is_output and unparsed_substring.startswith('{'):
                output_identifier = unparsed_substring.split('{',1)[1].rsplit('}',1)[0]
                unparsed_substring = unparsed_substring.replace('{' + output_identifier + '}', '')

            # Parse the mandatory pair identifiers from $PAIR_N keywords
            current_pair_identifier = None
            if element_is_pair1 or element_is_pair2:
                if unparsed_substring.count('{') != 1 or \
                                unparsed_substring.count('}') != 1 or \
                        not unparsed_substring.startswith('{'):
                    raise STAPLERerror('Syntax for identifying paired '
                                       'end sequencing filepairs requires '
                                       'identifier strings for first and '
                                       'second pair keywords in curly braces. '
                                       'E.g. for fastq files with naming '
                                       'scheme file_R1.fq, '
                                       'file_2.fq ... the appropriate '
                                       'keywords are $PAIR1{_R1} and '
                                       '$PAIR2{_R2}). Please '
                                       'revise the command line: ' +
                                       command_string)
                # Extract the contents of curly braces
                current_pair_identifier = unparsed_substring.split('}')[0][1:]
                unparsed_substring = unparsed_substring.split('}')[1]

            # Parse the optional filename extension
            if unparsed_substring:
                if not unparsed_substring.startswith('.'):
                    raise STAPLERerror('Please revisit documentation for '
                                       'proper IO-keyword syntax.'
                                       'Cannot parse substring "{0}" '
                                       'of IO-keyword {1} on line: {'
                                       '2}'.format(unparsed_substring,
                                                   current_element_string,
                                                   command_string))

                file_extension = unparsed_substring
            else:
                file_extension = ''

            # Add the input and output parameters to an appropriate dictionary
            if element_is_input:
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
                                           'revise command line: ' +
                                           command_string)
                input_elements[current_element_string] = [input_identifier, file_extension]
            elif element_is_pair1 or element_is_pair2:
                pair_identifier.append(current_pair_identifier)
                pair_elements[current_element_string] = [pair_identifier, file_extension]
            elif element_is_output:
                output_elements[current_element_string] = [output_identifier, file_extension]
            else:
                assert False

        # Validate the number of inputs
        if not input_elements and not pair_elements:
            raise STAPLERerror('{0} command must have either one or more '
                               '$INPUT keywords or two $PAIR '
                               'keywords.'.format(self.name))
        if pair_elements and len(pair_elements) != 2:
            raise STAPLERerror('{0} command must have $PAIR_1 and $PAIR_2 '
                               'keywords. Please revise line: {1}'.format(self.name, command_string))
        if input_elements and pair_elements:
            raise STAPLERerror('{0} command can only contain $INPUT or $PAIR '
                               'keywords, but not both. Please revise line: '
                               '{1}'.format(self.name, command_string))
        if not output_elements:
            raise STAPLERerror('{0} command must have at least one $OUTPUT '
                               'keyword. Please revise line: {1}'.format(command_string))

        # For simplicity
        if not input_elements:
            input_elements = pair_elements

        # Find suitable input file from input directory
        IO_files = {}
        command_ids = []
        for input_element_string, input_element_params in input_elements.iteritems():
            for fl in in_dir.files:
                # Skip files that have been used as an input file already
                if self.name in fl.users: continue

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
                        in_dir.use_file(fl.name, self.name)
                        # Pair 2
                        IO_files[pair_element_string] = os.path.join(in_dir.path,
                                                                     putative_pair_name)
                        command_ids.append(utils.infer_path_id(IO_files[pair_element_string]))
                        in_dir.use_file(putative_pair_name, self.name)
                        break
                    else:
                        raise STAPLERerror('Unable to find a pair for file {0}, '
                                           'expected to find a pairt with name '
                                           '{1}'.format(fl.name, putative_pair_name))
                else: # Non-paired input
                    if not input_element_params[0]:
                        IO_files[input_element_string] = (os.path.join(in_dir.path, fl.name))
                    else:
                        IO_files[input_element_string] = os.path.join(in_dir.path, fl.name)
                    command_ids.append(utils.infer_path_id(fl.name))
                    in_dir.use_file(fl.name, self.name)
                    break
        if not IO_files:
            raise VirtualIOError('No more unused input files')

        # Parse output elements
        for output_element_string, output_element_params in output_elements.iteritems():
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

        output_cmd = []
        for element in command_elements:
            if element.startswith('$INPUT') or element.startswith('$PAIR'):
                output_cmd.append(IO_files[element])
            elif element.startswith('$OUTPUT'):
                output_cmd.append(IO_files[element])
            else:
                output_cmd.append(element)
        return output_cmd, command_ids


    def _user_override(self, out_cmd):
        """Overrides auto-inferred values with possible user inputs.

        Parameters:
        out_cmd: List of input string elements

        Returns:
        Output commands overridden with user inputs.
        """
        for i in xrange(len(out_cmd)):
            value = out_cmd[i]
            if value.startswith('!value_table'):
                out_cmd[i] = self._parse_value_table(value)
        return out_cmd


    def get_cmd(self):
        """Returns the final command line.

        Returns:
        final_cmd: List of command line produced by the object (line breaks not allowed within command lines!).
        """
        return [' '.join(self.out_cmd)]


