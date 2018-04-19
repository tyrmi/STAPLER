import os

import directory
from STAPLERerror import STAPLERerror
from STAPLERerror import VirtualIOError
from GenericBase import GenericBase
import utils


class fastx_toolkit_generic_compressable(GenericBase):
    """Generic class with method for parsing fastx toolkit IO parameters.

    Only single type of output file is expected (but can be
    uncompressed or compressed if -z parameter is present).

    Attributes:
    name: Name of the function.
    input_type: Input types accepted by this application.
    _output_type: List of output types produced by the application.
    mandatory_args: Args the user be provided in in_cmd when initializing.
    optional_args: Args that may be part of the command line.
    in_cmd: Command entered by user.
    parsed_cmd: Final output command as option:value dict.
    id: Bare name of input file (without the possible ending)
    file_names: Names of output files

    Methods:
    _cmd_parse: Turns a command line into argument-value pairs.
    _validate: Classmethod for validating command lines.
    get_cmd: Method for getting the final cmd line string for output.
    _set_IO: Determines the output file name and type.
    _parse_id: Returns the bare input file name
    """

    def _select_IO(self, out_cmd, in_dir, out_dir):
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

        IO_files = {}
        file_names = set()
        for fl in in_dir.files:
            if self.name not in fl.users:
                if utils.splitext(fl.name)[-1] in self.input_types:
                    IO_files['-i'] = os.path.join(in_dir.path, fl.name)
                    command_ids = [utils.infer_path_id(IO_files['-i'])]
                    in_dir.use_file(fl.name, self.name)
                    assert len(self.output_types) < 2, 'Several output ' \
                                                       'types, override ' \
                                                       'this method!'
                    # If -z parameter is present in the input, output file will
                    # be compressed
                    if '-z' in out_cmd:
                        output_name = utils.splitext(fl.name)[0] + \
                                      self.output_types[0] + '.gz'
                    else:
                        output_name = utils.splitext(fl.name)[0] + \
                                      self.output_types[0]
                    output_path = os.path.join(out_dir.path, output_name)
                    IO_files['-o'] = output_path
                    file_names.add(output_name)
                    out_dir.add_file(output_name)
                    break
        if not IO_files:
            raise VirtualIOError('No more unused input files')
        out_cmd.update(IO_files)
        return out_cmd, command_ids


class fastx_toolkit_generic_compressable_fastx(GenericBase):
    """Generic class with method for parsing fastx toolkit IO parameters.

    Similar to fastx_toolkit_generic_compressable, but fasta or fastq output
    is expected (either can be compressed).
    Attributes:
    name: Name of the function.
    input_type: Input types accepted by this application.
    _output_type: List of output types produced by the application.
    mandatory_args: Args the user be provided in in_cmd when initializing.
    optional_args: Args that may be part of the command line.
    in_cmd: Command entered by user.
    parsed_cmd: Final output command as option:value dict.
    id: Bare name of input file (without the possible ending)
    file_names: Names of output files

    Methods:
    _cmd_parse: Turns a command line into argument-value pairs.
    _validate: Classmethod for validating command lines.
    get_cmd: Method for getting the final cmd line string for output.
    _set_IO: Determines the output file name and type.
    _parse_id: Returns the bare input file name
    """

    def _select_IO(self, out_cmd, in_dir, out_dir):
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

        IO_files = {}
        file_names = set()
        for fl in in_dir.files:
            if self.name not in fl.users:
                if utils.splitext(fl.name)[-1] in self.input_types:
                    IO_files['-i'] = os.path.join(in_dir.path, fl.name)
                    command_ids = [utils.infer_path_id(IO_files['-i'])]
                    in_dir.use_file(fl.name, self.name)

                    # Output filename extension is the same as input filename
                    # extension
                    output_file_extension = utils.splitext(IO_files['-i'])

                    # If -z parameter is present in the input, output file will
                    # be compressed
                    if '-z' in out_cmd:
                        output_name = utils.splitext(fl.name)[0] + \
                                      output_file_extension + '.gz'
                    else:
                        output_name = utils.splitext(fl.name)[0] + \
                                      output_file_extension
                    output_path = os.path.join(out_dir.path, output_name)
                    IO_files['-o'] = output_path
                    file_names.add(output_name)
                    out_dir.add_file(output_name)
                    break
        if not IO_files:
            raise VirtualIOError('No more unused input files')
        out_cmd.update(IO_files)
        return out_cmd, command_ids


class fasta_formatter(GenericBase):
    """Class for using FASTX-toolkit command fasta_formatter.

    Attributes:
    name: Name of the function.
    input_type: Input types accepted by this application.
    _output_type: List of output types produced by the application.
    mandatory_args: Args the user be provided in in_cmd when initializing.
    optional_args: Args that may be part of the command line.
    in_cmd: Command entered by user.
    parsed_cmd: Final output command as option:value dict.
    id: Bare name of input file (without the possible ending)
    file_names: Names of output files

    Methods:
    _cmd_parse: Turns a command line into argument-value pairs.
    _validate: Classmethod for validating command lines.
    get_cmd: Method for getting the final cmd line string for output.
    _set_IO: Determines the output file name and type.
    _parse_id: Returns the bare input file name
    """

    name = 'fastx_toolkit_fasta_formatter'
    input_types = {'.fasta', '.fastq'}
    output_types = ['.fasta', '.fastq', '.tab']
    hidden_mandatory_args = ['-i', '-o']
    user_optional_args = ['-w', '-t', '-e']
    help_description = '''
Tested with fastx-tookit v. 0.0.14
'''

    def _select_IO(self, out_cmd, in_dir, out_dir):
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

        IO_files = {}
        file_names = set()
        for fl in in_dir.files:
            if self.name not in fl.users:
                if utils.splitext(fl.name)[-1] in self.input_types:
                    IO_files['-i'] = os.path.join(in_dir.path, fl.name)
                    command_ids = [utils.infer_path_id(IO_files['-i'])]
                    in_dir.use_file(fl.name, self.name)

                    # Output filename extension is the same as input filename
                    # extension, except when -t parameter is included the
                    # output format is .tab
                    if '-t' in out_cmd:
                        output_file_extension = '.tab'
                    else:
                        output_file_extension = utils.splitext(IO_files['-i'])

                    # If -z parameter is present in the input, output file will
                    # be compressed
                    if '-z' in out_cmd:
                        output_name = utils.splitext(fl.name)[0] + \
                                      output_file_extension + '.gz'
                    else:
                        output_name = utils.splitext(fl.name)[0] + \
                                      output_file_extension
                    output_path = os.path.join(out_dir.path, output_name)
                    IO_files['-o'] = output_path
                    file_names.add(output_name)
                    out_dir.add_file(output_name)
                    break
        if not IO_files:
            raise VirtualIOError('No more unused input files')
        out_cmd.update(IO_files)
        return out_cmd, command_ids


class fasta_nucleotide_changer(fastx_toolkit_generic_compressable_fastx):
    """Class for using FASTX-toolkit command fasta_nucleotide_changer.

    Attributes:
    name: Name of the function.
    input_type: Input types accepted by this application.
    _output_type: List of output types produced by the application.
    mandatory_args: Args the user be provided in in_cmd when initializing.
    optional_args: Args that may be part of the command line.
    in_cmd: Command entered by user.
    parsed_cmd: Final output command as option:value dict.
    id: Bare name of input file (without the possible ending)
    file_names: Names of output files

    Methods:
    _cmd_parse: Turns a command line into argument-value pairs.
    _validate: Classmethod for validating command lines.
    get_cmd: Method for getting the final cmd line string for output.
    _set_IO: Determines the output file name and type.
    _parse_id: Returns the bare input file name
    """

    name = 'fastx_toolkit_fasta_nucleotide_changer'
    input_types = {'.fasta', '.fastq'}
    output_types = ['.fasta', '.fastq']
    hidden_mandatory_args = ['-i', '-o']
    user_optional_args = ['-r', '-d', '-z', '-v']
    help_description = '''
Tested with fastx-tookit v. 0.0.14
'''



class fastq_quality_boxplot_graph(GenericBase):
    """Class for using FASTX-toolkit command fastq_quality_boxplot_graph.

    Attributes:
    name: Name of the function.
    input_type: Input types accepted by this application.
    _output_type: List of output types produced by the application.
    mandatory_args: Args the user be provided in in_cmd when initializing.
    optional_args: Args that may be part of the command line.
    in_cmd: Command entered by user.
    parsed_cmd: Final output command as option:value dict.
    id: Bare name of input file (without the possible ending)
    file_names: Names of output files

    Methods:
    _cmd_parse: Turns a command line into argument-value pairs.
    _validate: Classmethod for validating command lines.
    get_cmd: Method for getting the final cmd line string for output.
    _set_IO: Determines the output file name and type.
    _parse_id: Returns the bare input file name
    """

    name = 'fastx_toolkit_fastq_quality_boxplot_graph.sh'
    input_types = {'.fastx_quality_stats'}
    output_types = ['.png']
    hidden_mandatory_args = ['-i', '-o']
    user_optional_args = []
    help_description = '''
Tested with fastx-tookit v. 0.0.14
'''

    def _format_cmd(self, cmd):
        """Determines the output file name and type.

        Also adds the -t argument which based on file name.

        Parameters:
        cmd: Parsed command line.

        Returns:
        cmd: Command line with -o set to point to a file in a dir instead a dir
        file_names: Name(s) of the files this command outputs
        """
        assert len(self.output_types) == 1, 'Many output types, override this function'
        file_name = cmd['-i']
        file_name = utils.splitext(file_name)[0] + self.output_types[0]
        cmd['-o'] = os.path.join(cmd['-o'], file_name)
        cmd['-t'] = file_name
        file_names = [os.path.basename(file_name)]
        return cmd, file_names


class fastq_quality_filter(fastx_toolkit_generic_compressable_fastx):
    """Class for using FASTX-toolkit command fastq_quality_filter.

    Attributes:
    name: Name of the function.
    input_type: Input types accepted by this application.
    _output_type: List of output types produced by the application.
    mandatory_args: Args the user be provided in in_cmd when initializing.
    optional_args: Args that may be part of the command line.
    in_cmd: Command entered by user.
    parsed_cmd: Final output command as option:value dict.
    id: Bare name of input file (without the possible ending)
    file_names: Names of output files

    Methods:
    _cmd_parse: Turns a command line into argument-value pairs.
    _validate: Classmethod for validating command lines.
    get_cmd: Method for getting the final cmd line string for output.
    _set_IO: Determines the output file name and type.
    _parse_id: Returns the bare input file name
    """

    name = 'fastx_toolkit_fastq_quality_filter'
    input_types = {'.fasta', '.fastq'}
    output_types = ['.fasta', '.fastq']
    hidden_mandatory_args = ['-i', '-o', '-q', '-p']
    user_optional_args = ['-v', '-z']
    help_description = '''
Tested with fastx-tookit v. 0.0.14
'''


class fastq_quality_trimmer(fastx_toolkit_generic_compressable_fastx):
    """Class for using FASTX-toolkit command fastq_quality_trimmer.

    Attributes:
    name: Name of the function.
    input_type: Input types accepted by this application.
    _output_type: List of output types produced by the application.
    mandatory_args: Args the user be provided in in_cmd when initializing.
    optional_args: Args that may be part of the command line.
    in_cmd: Command entered by user.
    parsed_cmd: Final output command as option:value dict.
    id: Bare name of input file (without the possible ending)
    file_names: Names of output files

    Methods:
    _cmd_parse: Turns a command line into argument-value pairs.
    _validate: Classmethod for validating command lines.
    get_cmd: Method for getting the final cmd line string for output.
    _set_IO: Determines the output file name and type.
    _parse_id: Returns the bare input file name
    """

    name = 'fastx_toolkit_fastq_quality_trimmer'
    input_types = {'.fasta', '.fastq'}
    output_types = ['.fasta', '.fastq']
    hidden_mandatory_args = ['-i', '-o', '-t']
    user_optional_args = ['-l', '-v', '-Q']
    help_description = """
Tested with fastx-tookit v. 0.0.14
    """


class fastq_to_fasta(fastx_toolkit_generic_compressable):
    """Class for parallelizing fastq_to_fasta.

    Parameters:
    in_cmd: String containing a command line
    in_dir: Directory object containing input files
    out_dir: Directory object containing output files
    NOTICE! Keep the directory objects up to date about file edits!

    Attributes:
    name: Name of the function.
    input_type: Input types accepted by this application.
    output_types: List of output types produced by the application.
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

    name = 'fastx_toolkit_fastq_to_fasta'
    input_types = {'.fastq'}
    output_types = ['.fasta']
    hidden_mandatory_args = ['-i', '-o']
    user_mandatory_args = []
    remove_user_args = user_mandatory_args
    user_optional_args = ['-r', '-n', '-v', '-z']
    parallelizable = True
    help_description = '''
Tested with fastx-tookit v. 0.0.14
'''


class fastx_artifacts_filter(fastx_toolkit_generic_compressable_fastx):
    """Class for using FASTX-toolkit command fastx_artifacts_filter.

    Attributes:
    name: Name of the function.
    input_type: Input types accepted by this application.
    _output_type: List of output types produced by the application.
    mandatory_args: Args the user be provided in in_cmd when initializing.
    optional_args: Args that may be part of the command line.
    in_cmd: Command entered by user.
    parsed_cmd: Final output command as option:value dict.
    id: Bare name of input file (without the possible ending)
    file_names: Names of output files

    Methods:
    _cmd_parse: Turns a command line into argument-value pairs.
    _validate: Classmethod for validating command lines.
    get_cmd: Method for getting the final cmd line string for output.
    _set_IO: Determines the output file name and type.
    _parse_id: Returns the bare input file name
    """

    name = 'fastx_toolkit_fastx_artifacts_filter'
    input_types = {'.fasta', '.fastq'}
    output_types = ['.fasta', '.fastq']
    hidden_mandatory_args = ['-i', '-o']
    user_mandatory_args = []
    user_optional_args = ['-z']
    help_description = '''
Tested with fastx-tookit v. 0.0.14
'''


class fastx_clipper(fastx_toolkit_generic_compressable_fastx):
    """Class for using FASTX-toolkit command fastx_clipper.

    Attributes:
    name: Name of the function.
    input_type: Input types accepted by this application.
    _output_type: List of output types produced by the application.
    mandatory_args: Args the user be provided in in_cmd when initializing.
    optional_args: Args that may be part of the command line.
    in_cmd: Command entered by user.
    parsed_cmd: Final output command as option:value dict.
    id: Bare name of input file (without the possible ending)
    file_names: Names of output files

    Methods:
    _cmd_parse: Turns a command line into argument-value pairs.
    _validate: Classmethod for validating command lines.
    get_cmd: Method for getting the final cmd line string for output.
    _set_IO: Determines the output file name and type.
    _parse_id: Returns the bare input file name
    """

    name = 'fastx_toolkit_fastx_clipper'
    input_types = {'.fasta', '.fastq'}
    output_types = ['.fasta', '.fastq']
    hidden_mandatory_args = ['-i', '-o']
    user_optional_args = ['-a', '-l', '-d', '-c', '-C', '-k', '-n', '-v', '-z',
                          '-D']
    help_description = '''
Tested with fastx-tookit v. 0.0.14
'''


class fastx_collapser(fastx_toolkit_generic_compressable_fastx):
    """Class for using FASTX-toolkit command fastx_collapser.

    Attributes:
    name: Name of the function.
    input_type: Input types accepted by this application.
    _output_type: List of output types produced by the application.
    mandatory_args: Args the user be provided in in_cmd when initializing.
    optional_args: Args that may be part of the command line.
    in_cmd: Command entered by user.
    parsed_cmd: Final output command as option:value dict.
    id: Bare name of input file (without the possible ending)
    file_names: Names of output files

    Methods:
    _cmd_parse: Turns a command line into argument-value pairs.
    _validate: Classmethod for validating command lines.
    get_cmd: Method for getting the final cmd line string for output.
    _set_IO: Determines the output file name and type.
    _parse_id: Returns the bare input file name
    """

    name = 'fastx_toolkit_fastx_collapser'
    input_types = {'.fasta', '.fastq'}
    output_types = ['.fasta', '.fastq']
    hidden_mandatory_args = ['-i', '-o']
    user_mandatory_args = []
    user_optional_args = []
    help_description = '''
Tested with fastx-tookit v. 0.0.14
'''


class fastx_nucleotide_distribution_graph(fastq_quality_boxplot_graph):
    """Class for FASTX-toolkit command fastx_nucleotide_distribution_graph.

    Attributes:
    name: Name of the function.
    input_type: Input types accepted by this application.
    _output_type: List of output types produced by the application.
    mandatory_args: Args the user be provided in in_cmd when initializing.
    optional_args: Args that may be part of the command line.
    in_cmd: Command entered by user.
    parsed_cmd: Final output command as option:value dict.
    id: Bare name of input file (without the possible ending)
    file_names: Names of output files

    Methods:
    _cmd_parse: Turns a command line into argument-value pairs.
    _validate: Classmethod for validating command lines.
    get_cmd: Method for getting the final cmd line string for output.
    _set_IO: Determines the output file name and type.
    _parse_id: Returns the bare input file name
    """
    name = 'fastx_toolkit_fastx_nucleotide_distribution_graph.sh'


class fastx_quality_stats(GenericBase):
    """Class for using FASTX-toolkit command fastx_quality_stats.

    Attributes:
    name: Name of the function.
    input_type: Input types accepted by this application.
    _output_type: List of output types produced by the application. 
    mandatory_args: Args the user be provided in in_cmd when initializing.
    optional_args: Args that may be part of the command line.
    in_cmd: Command entered by user.
    parsed_cmd: Final output command as option:value dict.
    id: Bare name of input file (without the possible ending)
    file_names: Names of output files

    Methods:
    _cmd_parse: Turns a command line into argument-value pairs.
    _validate: Classmethod for validating command lines.
    get_cmd: Method for getting the final cmd line string for output.
    _set_IO: Determines the output file name and type.
    _parse_id: Returns the bare input file name
    """

    name = 'fastx_toolkit_fastx_quality_stats'
    input_types = {'.fasta', '.fastq'}
    output_types = ['.fastx_quality_stats']
    hidden_mandatory_args = ['-i', '-o']
    help_description = '''
Tested with fastx-tookit v. 0.0.14
'''


class fastx_renamer(fastx_toolkit_generic_compressable_fastx):
    """Class for using FASTX-toolkit command fastx_renamer.

    Attributes:
    name: Name of the function.
    input_type: Input types accepted by this application.
    _output_type: List of output types produced by the application.
    mandatory_args: Args the user be provided in in_cmd when initializing.
    optional_args: Args that may be part of the command line.
    in_cmd: Command entered by user.
    parsed_cmd: Final output command as option:value dict.
    id: Bare name of input file (without the possible ending)
    file_names: Names of output files

    Methods:
    _cmd_parse: Turns a command line into argument-value pairs.
    _validate: Classmethod for validating command lines.
    get_cmd: Method for getting the final cmd line string for output.
    _set_IO: Determines the output file name and type.
    _parse_id: Returns the bare input file name
    """

    name = 'fastx_toolkit_fastx_trimmer'
    input_types = {'.fasta', '.fastq'}
    output_types = ['.fasta', '.fastq']
    hidden_mandatory_args = ['-i', '-o']
    user_mandatory_args = ['-n']
    user_optional_args = ['-z']
    help_description = '''
Tested with fastx-tookit v. 0.0.14
'''


class fastx_reverse_complement(fastx_toolkit_generic_compressable_fastx):
    """Class for using FASTX-toolkit command fastx_reverse_complement.

    Attributes:
    name: Name of the function.
    input_type: Input types accepted by this application.
    _output_type: List of output types produced by the application.
    mandatory_args: Args the user be provided in in_cmd when initializing.
    optional_args: Args that may be part of the command line.
    in_cmd: Command entered by user.
    parsed_cmd: Final output command as option:value dict.
    id: Bare name of input file (without the possible ending)
    file_names: Names of output files

    Methods:
    _cmd_parse: Turns a command line into argument-value pairs.
    _validate: Classmethod for validating command lines.
    get_cmd: Method for getting the final cmd line string for output.
    _set_IO: Determines the output file name and type.
    _parse_id: Returns the bare input file name
    """

    name = 'fastx_toolkit_fastx_reverse_complement'
    input_types = {'.fasta', '.fastq'}
    output_types = ['.fasta', '.fastq']
    hidden_mandatory_args = ['-i', '-o']
    user_optional_args = ['-z']
    help_description = '''
Tested with fastx-tookit v. 0.0.14
'''


class fastx_trimmer(fastx_toolkit_generic_compressable_fastx):
    """Class for using FASTX-toolkit command fastx_trimmer.

    Attributes:
    name: Name of the function.
    input_type: Input types accepted by this application.
    _output_type: List of output types produced by the application. 
    mandatory_args: Args the user be provided in in_cmd when initializing.
    optional_args: Args that may be part of the command line.
    in_cmd: Command entered by user.
    parsed_cmd: Final output command as option:value dict.
    id: Bare name of input file (without the possible ending)
    file_names: Names of output files

    Methods:
    _cmd_parse: Turns a command line into argument-value pairs.
    _validate: Classmethod for validating command lines.
    get_cmd: Method for getting the final cmd line string for output.
    _set_IO: Determines the output file name and type.
    _parse_id: Returns the bare input file name
    """

    name = 'fastx_toolkit_fastx_trimmer'
    input_types = {'.fasta', '.fastq'}
    output_types = ['.fasta', '.fastq']
    hidden_mandatory_args = ['-i', '-o']
    user_optional_args = ['-f', '-l', '-z']
    help_description = '''
Tested with fastx-tookit v. 0.0.14
'''

    def _validate(self, parsed_cmd):
        """Validates the command line.

        Raises STAPLERerror if validation is unsuccessfull

        Args:
        parsed_cmd: Dict of arguments entered by user
        Raises:
        STAPLERerror if validation is unsuccessful
        """
        for ma in self.hidden_mandatory_args:
            if ma not in parsed_cmd:
                raise STAPLERerror('The command line does not contain '
                                   'all the mandatory arguments '
                                   '{0}:\n{1}'.format(self.hidden_mandatory_args,
                                                      ' '.join(parsed_cmd)))
        for cmd in parsed_cmd:
            if cmd not in self.hidden_mandatory_args and cmd not in self.user_optional_args:
                raise STAPLERerror('Unknown option: {0}\n'
                                   'on command line:\n{1}'.format(cmd, self.in_cmd))

