import os

import directory
from STAPLERerror import STAPLERerror
from STAPLERerror import VirtualIOError
from GenericBase import GenericBase
import utils


class FASTX_toolkit(GenericBase):
    """Class for creating FASTX-toolkit commands.

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


class fastx_quality_stats(FASTX_toolkit):
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

    name = 'fastx_quality_stats'
    input_types = {'.fasta', '.fastq'}
    output_types = ['.fastx_quality_stats']
    mandatory_args = ['-i', '-o']
    optional_args = ['-Q']
    help_description = '''
Tested with fastx-tookit v. 0.0.13
'''


class fastq_quality_boxplot_graph(FASTX_toolkit):
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

    name = 'fastq_quality_boxplot_graph.sh'
    input_types = {'.fastx_quality_stats'}
    output_types = ['.png']
    mandatory_args = ['-i', '-o']
    optional_args = []
    help_description = '''
Tested with fastx-tookit v. 0.0.13
'''

    def _format_cmd(self, cmd):
        """Determines the output file name and type.

        Also adds the -t argument which based on file name.

        Arguments:
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
    name = 'fastx_nucleotide_distribution_graph.sh'


class fastx_trimmer(FASTX_toolkit):
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

    name = 'fastx_trimmer'
    input_types = {'.fasta', '.fastq'}
    output_types = ['.fastq']
    mandatory_args = ['-i', '-o']
    optional_args = ['-f', '-l', '-Q', '-t']
    help_description = '''
Tested with fastx-tookit v. 0.0.13
'''
    
    def _validate(self, parsed_cmd):
        """Validates the command line.

        Raises STAPLERerror if validation is unsuccessfull

        Args:
        parsed_cmd: Dict of arguments entered by user
        Raises:
        STAPLERerror if validation is unsuccessful
        """
        for ma in self.mandatory_args:
            if ma not in parsed_cmd:
                raise STAPLERerror('The command line does not contain '
                                 'all the mandatory arguments '
                                 '{0}:\n{1}'.format(self.mandatory_args,
                                                    ' '.join(parsed_cmd)))
        for cmd in parsed_cmd:
            if cmd not in self.mandatory_args and cmd not in self.optional_args:
                raise STAPLERerror('Unknown option: {0}\n'
                                 'on command line:\n{1}'.format(cmd, self.in_cmd))


class fastq_quality_filter(FASTX_toolkit):
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

    name = 'fastq_quality_filter'
    input_types = {'.fasta', '.fastq'}
    output_types = ['.fastq']
    mandatory_args = ['-i', '-o', '-q', '-p']
    optional_args = ['-v', '-Q']
    help_description = '''
Tested with fastx-tookit v. 0.0.13
'''

class fastq_quality_trimmer(FASTX_toolkit):
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

    name = 'fastq_quality_trimmer'
    input_types = {'.fasta', '.fastq'}
    output_types = ['.fastq']
    mandatory_args = ['-i', '-o', '-t']
    optional_args = ['-l', '-v', '-Q']
    help_description = """
Tested with fastx-tookit v. 0.0.13

Information on this tool is hard to come by for some reason (no mention of
this in fastx-toolkit pages?). Here are the explanations for the available
arguments:

   [-h]         = This helpful help screen.
   [-t N]       = Quality threshold - nucleotides with lower
                  quality will be trimmed (from the end of the sequence).
   [-l N]       = Minimum length - sequences shorter than this (after trimming)
                  will be discarded. Default = 0 = no minimum length.
   [-z]         = Compress output with GZIP.
   [-i INFILE]  = FASTQ input file. default is STDIN.
   [-o OUTFILE] = FASTQ output file. default is STDOUT.
   [-v]         = Verbose - report number of sequences.
                  If [-o] is specified,  report will be printed to STDOUT.
                  If [-o] is not specified (and output goes to STDOUT),
                  report will be printed to STDERR.
    """


class fastq_to_fasta(GenericBase):
    """Class for parallelizing fastq_to_fasta.

    Arguments:
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
    id: Bare name of input file (without the possible ending).


    Methods:
    get_cmd: Method for getting the final cmd line string for output.
    """

    name = 'fastq_to_fasta'
    input_types = {'.fastq'}
    output_types = ['.fasta']
    mandatory_args = ['-i', '-o']
    user_mandatory_args = []
    remove_user_args = user_mandatory_args
    optional_args = ['-r', '-n', '-v', '-Q']
    parallelizable = True
    help_description = '''
Tested with fastx-tookit v. 0.0.13
'''


class fastx_barcode_splitter(FASTX_toolkit):
    """Class for using FASTX-toolkit command fastx_barcode_splitter.
    """

    name = 'fastx_barcode_splitter'
    input_types = {'.fasta', '.fastq'}
    output_types = ['.fastq']
    mandatory_args = ['--bcfile', '--prefix']
    optional_args = ['--bol', '--eol', '--mismatches', '--exact',
                     '--partial', '--quiet']
    parallelizable = False
    help_description = '''
Tested with fastx-tookit v. 0.0.13
'''

    def _select_IO(self, out_cmd, in_dir, out_dir):
        """Returns a dict containing the proper IO commands.

        This method must keep the directory objects up to date of the file
        edits!

        Arguments:
        in_cmd: A dict containing the command line.
        in_dir: Input directory.
        out_dir: Output directory.

        Returns:
        out_cmd: Dict containing the output commands.
        file_names: Names of the output files.

        Raises:
        VirtualIOError: No valid input file can be found.
        """

        IO_files = {}
        file_names = set()
        for fl_name, users in in_dir.files.iteritems():
            if self.name not in users:
                if utils.splitext(fl_name)[-1] in self.input_types:
                    IO_files['-i'] = os.path.join(in_dir.path, fl_name)
                    in_dir.use_file(fl_name, self.name)
                    assert len(self.output_types) == 1, 'Several output ' \
                                                        'types, override ' \
                                                        'this method!'

                    output_name = utils.splitext(fl_name)[0] + \
                                  self.output_types[0]
                    output_path = os.path.join(out_dir.path, output_name)
                    IO_files['-'] = output_path
                    file_names.add(output_name)
                    out_dir.add_file(output_name)
                    break
        if not IO_files:
            raise VirtualIOError('No more unused input files')
        out_cmd.update(IO_files)
        return out_cmd, file_names

