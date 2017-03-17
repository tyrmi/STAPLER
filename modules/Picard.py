import logging
import os

from GenericBase import GenericBase
from STAPLERerror import STAPLERerror
from STAPLERerror import VirtualIOError
import utils

class Picard_SuperClass(GenericBase):
    """Superclass for picard toolkit.

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

    name = 'Picard_SuperClass'

    def get_cmd(self):
        """Returns the final command line.

        Returns:
        final_cmd: List of command line produced by the object (line breaks not allowed within command lines!).
        """
        run_command = utils.parse_config(self.name, 'cmd_name', 'prefix')
        if run_command is None:
            final_cmd = [self.name]
        else:
            final_cmd = [run_command]
        for arg, val in self.out_cmd.iteritems():
            arg = arg.lstrip('-')
            final_cmd.append(arg + '=' + val)
        return [' '.join(final_cmd)]


class Picard_AddOrReplaceReadGroups(Picard_SuperClass):

    name = 'Picard_AddOrReplaceReadGroups'
    #Accept all defined types:
    input_types = {'.sam', '.bam'}
    output_types = ['.sam', '.bam']
    mandatory_args = ['-INPUT', '-OUTPUT', '-RGLB', '-RGPL', '-RGPU', '-RGSM']
    user_mandatory_args = ['-RGLB', '-RGPL', '-RGPU', '-RGSM']
    remove_user_args = []
    optional_args = ['-SORT_ORDER', '-RGID', '-RGCN', '-RGDS', '-RGDT',
                     '-RGPI', '-VALIDATION_STRINGENCY', '-COMPRESSION_LEVEL',
                     '-MAX_RECORDS_IN_RAM', '-CREATE_INDEX',
                     '-CREATE_MD5_FILE', '-REFERENCE_SEQUENCE',
                     '-GA4GH_CLIENT_SECRETS']
    parallelizable = True
    help_description = '''
This tool requires four specific fields to be defined in the input path:
RGLB
RGPL
RGPL
RGPU
RGSM

These (and other optional [see picard manual]) fields can be defined by:

1) Using the !2table (or !named_table) values if you wish to have a specific
value for each file, e.g.:
-RGLB !2table:path/to/my_RGLB_names.txt
The my_RGLB_names.txt should be a tab delimited list of file_substring:RGLB.

You do not need to create a !2table if the added value is the same for every
file in your project, e.g.:
-RGPL illumina
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
        out_cmd: Dict containing the output commands
        file_names: Names of the output files.

        Raises:
        VirtualIOError: No valid input file can be found.
        """

        IO_files = {}
        file_names = set()
        for fl_name, users in in_dir.files.iteritems():
            if self.name not in users:
                if utils.splitext(fl_name)[-1] in self.input_types:
                    IO_files['-INPUT'] = os.path.join(in_dir.path, fl_name)
                    in_dir.use_file(fl_name, self.name)
                    output_name = fl_name
                    output_path = os.path.join(out_dir.path, output_name)
                    IO_files['-OUTPUT'] = output_path
                    file_names.add(output_name)
                    out_dir.add_file(output_name)
                    break
        if not IO_files:
            raise VirtualIOError('No more unused input files')
        out_cmd.update(IO_files)
        return out_cmd, file_names


class Picard_CollectAlignmentSummaryMetrics(Picard_SuperClass):
    """Class for using CollectAlignmentSummaryMetrics of picard toolkit.

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

    name = 'Picard_CollectAlignmentSummaryMetrics'
    #Accept all defined types:
    input_types = {'.sam', '.bam'}
    output_types = ['.out']
    mandatory_args = ['-INPUT', '-OUTPUT']
    user_mandatory_args = []
    remove_user_args = user_mandatory_args
    optional_args = ['-REFERENCE_SEQUENCE', '-ASSUME_SORTED',
                     '-MAX_INSERT_SIZE', '-ADAPTER_SEQUENCE',
                     '-METRIC_ACCUMULATION_LEVEL', '-IS_BISULFITE_SEQUENCED',
                     '-STOP_AFTER', '-VALIDATION_STRINGENCY',
                     '-COMPRESSION_LEVEL',
                     '-MAX_RECORDS_IN_RAM', '-CREATE_INDEX',
                     '-CREATE_MD5_FILE', '-REFERENCE_SEQUENCE',
                     '-GA4GH_CLIENT_SECRETS']
    parallelizable = True
    help_description = '''
This version supports the syntax of older picard versions, up to v. 1.113 or
so. Unfortunately the exact version number is not known. If newer picard
version is used, use the Picard_CollectAlignmentSummaryMetrics_1.128 tool
instead.
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
        out_cmd: Dict containing the output commands
        file_names: Names of the output files.

        Raises:
        VirtualIOError: No valid input file can be found.
        """

        IO_files = {}
        file_names = set()
        for fl_name, users in in_dir.files.iteritems():
            if self.name not in users:
                if utils.splitext(fl_name)[-1] in self.input_types:
                    IO_files['-INPUT'] = os.path.join(in_dir.path, fl_name)
                    in_dir.use_file(fl_name, self.name)
                    assert len(self.output_types) == 1, 'Several output ' \
                                                        'types, override ' \
                                                        'this method!'

                    output_name = utils.splitext(fl_name)[0] + \
                                  self.output_types[0]
                    output_path = os.path.join(out_dir.path, output_name)
                    IO_files['-OUTPUT'] = output_path
                    file_names.add(output_name)
                    out_dir.add_file(output_name)
                    break
        if not IO_files:
            raise VirtualIOError('No more unused input files')
        out_cmd.update(IO_files)
        return out_cmd, file_names

class Picard_CollectAlignmentSummaryMetrics_1128(Picard_SuperClass):
    """Class for using CollectAlignmentSummaryMetrics_1.128 of picard toolkit.

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

    name = 'Picard_CollectAlignmentSummaryMetrics_1.128'
    #Accept all defined types:
    input_types = {'.sam', '.bam'}
    output_types = ['.out']
    mandatory_args = ['-INPUT', '-OUTPUT']
    user_mandatory_args = []
    remove_user_args = user_mandatory_args
    optional_args = ['-MAX_INSERT_SIZE', '-ADAPTER_SEQUENCE',
                     '-METRIC_ACCUMULATION_LEVEL', '-IS_BISULFITE_SEQUENCED',
                     '-ASSUME_SORTED', '-STOP_AFTER', '-VALIDATION_STRINGENCY',
                     '-COMPRESSION_LEVEL', '-MAX_RECORDS_IN_RAM',
                     '-CREATE_INDEX', '-CREATE_MD5_FILE',
                     '-REFERENCE_SEQUENCE', '-GA4GH_CLIENT_SECRETS']
    parallelizable = True
    help_description = '''
This version supports the syntax of newer picard versions, from v. 1.113 or
so onwards. Unfortunately the exact version number is not known. If an older
version of picard is used, use the Picard_CollectAlignmentSummaryMetrics
tool instead.
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
        out_cmd: Dict containing the output commands
        file_names: Names of the output files.

        Raises:
        VirtualIOError: No valid input file can be found.
        """

        IO_files = {}
        file_names = set()
        for fl_name, users in in_dir.files.iteritems():
            if self.name not in users:
                if utils.splitext(fl_name)[-1] in self.input_types:
                    IO_files['-INPUT'] = os.path.join(in_dir.path, fl_name)
                    in_dir.use_file(fl_name, self.name)
                    assert len(self.output_types) == 1, 'Several output ' \
                                                        'types, override ' \
                                                        'this method!'

                    output_name = utils.splitext(fl_name)[0] + \
                                  self.output_types[0]
                    output_path = os.path.join(out_dir.path, output_name)
                    IO_files['-OUTPUT'] = output_path
                    file_names.add(output_name)
                    out_dir.add_file(output_name)
                    break
        if not IO_files:
            raise VirtualIOError('No more unused input files')
        out_cmd.update(IO_files)
        return out_cmd, file_names


class Picard_CollectInsertSizeMetrics(Picard_SuperClass):
    """Class for using CollectInsertSizeMetrics of picard toolkit.

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

    name = 'Picard_CollectInsertSizeMetrics'
    #Accept all defined types:
    input_types = {'.sam', '.bam'}
    output_types = ['.out']
    mandatory_args = ['-INPUT', '-OUTPUT', '-HISTOGRAM_FILE']
    user_mandatory_args = []
    remove_user_args = []
    optional_args = ['-REFERENCE_SEQUENCE', '-DEVIATIONS',
                     '-HISTOGRAM_WIDTH', '-MINIMUM_PCT',
                     '-METRIC_ACCUMULATION_LEVEL', '-ASSUME_SORTED',
                     '-STOP_AFTER', '-VALIDATION_STRINGENCY',
                     '-COMPRESSION_LEVEL',
                     '-MAX_RECORDS_IN_RAM', '-CREATE_INDEX',
                     '-CREATE_MD5_FILE', '-REFERENCE_SEQUENCE',
                     '-GA4GH_CLIENT_SECRETS']
    parallelizable = True
    help_description = '''
Sorry no additional specific help available for this
tool :(

See the original tool manual for help!
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
        out_cmd: Dict containing the output commands
        file_names: Names of the output files.

        Raises:
        VirtualIOError: No valid input file can be found.
        """

        IO_files = {}
        file_names = set()
        for fl_name, users in in_dir.files.iteritems():
            if self.name not in users:
                if utils.splitext(fl_name)[-1] in self.input_types:
                    IO_files['-INPUT'] = os.path.join(in_dir.path, fl_name)
                    in_dir.use_file(fl_name, self.name)
                    assert len(self.output_types) == 1, 'Several output ' \
                                                        'types, override ' \
                                                        'this method!'

                    output_name = utils.splitext(fl_name)[0] + \
                                  self.output_types[0]
                    output_path = os.path.join(out_dir.path, output_name)
                    IO_files['-OUTPUT'] = output_path
                    histogram_file_path = os.path.join(out_dir.path,
                                                       output_name) + '.jpeg'
                    IO_files['-HISTOGRAM_FILE'] = histogram_file_path
                    file_names.add(output_name)
                    out_dir.add_file(output_name)
                    break
        if not IO_files:
            raise VirtualIOError('No more unused input files')
        out_cmd.update(IO_files)
        return out_cmd, file_names


class Picard_CollectWgsMetrics(Picard_SuperClass):
    """Class for using CollectWgsMetrics of picard toolkit.

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

    name = 'Picard_CollectWgsMetrics'
    #Accept all defined types:
    input_types = {'.sam', '.bam'}
    output_types = ['.out']
    mandatory_args = ['-INPUT', '-OUTPUT']
    user_mandatory_args = []
    remove_user_args = []
    optional_args = ['-MINIMUM_MAPPING_QUALITY', '-MINIMUM_BASE_QUALITY',
                     '-COVERAGE_CAP', '-STOP_AFTER', '-REFERENCE_SEQUENCE',
                     '-VALIDATION_STRINGENCY', '-COMPRESSION_LEVEL',
                     '-MAX_RECORDS_IN_RAM', '-CREATE_INDEX',
                     '-CREATE_MD5_FILE', '-REFERENCE_SEQUENCE',
                     '-GA4GH_CLIENT_SECRETS']
    parallelizable = True
    help_description = '''
Sorry no additional specific help available for this
tool :(

See the original tool manual for help!
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
        out_cmd: Dict containing the output commands
        file_names: Names of the output files.

        Raises:
        VirtualIOError: No valid input file can be found.
        """

        IO_files = {}
        file_names = set()
        for fl_name, users in in_dir.files.iteritems():
            if self.name not in users:
                if utils.splitext(fl_name)[-1] in self.input_types:
                    IO_files['-INPUT'] = os.path.join(in_dir.path, fl_name)
                    in_dir.use_file(fl_name, self.name)
                    assert len(self.output_types) == 1, 'Several output ' \
                                                        'types, override ' \
                                                        'this method!'

                    output_name = utils.splitext(fl_name)[0] + \
                                  self.output_types[0]
                    output_path = os.path.join(out_dir.path, output_name)
                    IO_files['-OUTPUT'] = output_path
                    file_names.add(output_name)
                    out_dir.add_file(output_name)
                    break
        if not IO_files:
            raise VirtualIOError('No more unused input files')
        out_cmd.update(IO_files)
        return out_cmd, file_names


class Picard_CompareSAMs(GenericBase):
    """Class for using CompareSAMs of picard toolkit.

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

    name = 'Picard_CompareSAMs'
    input_types = {'.sam'}
    output_types = ['.out']
    mandatory_args = ['-i', '-i2', '-o']
    user_mandatory_args = ['-i2']
    remove_user_args = []
    optional_args = ['-VALIDATION_STRINGENCY', '-COMPRESSION_LEVEL',
                     '-MAX_RECORDS_IN_RAM', '-CREATE_INDEX',
                     '-CREATE_MD5_FILE', '-REFERENCE_SEQUENCE',
                     '-GA4GH_CLIENT_SECRETS']
    parallelizable = True
    help_description = '''
The first set of sam files should be located in the previous folder
automatically pointed to by STAPLER script. The directory of the
second set (-i2) should be given by the user.
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
        out_cmd: Dict containing the output commands
        file_names: Names of the output files.

        Raises:
        VirtualIOError: No valid input file can be found.
        """
        i2_dir = self.parsed_in_cmd['-i2']
        IO_files = {}
        file_names = set()
        for fl_name, users in in_dir.files.iteritems():
            if self.name not in users:
                if utils.splitext(fl_name)[-1] in self.input_types:
                    IO_files['-i'] = os.path.join(in_dir.path, fl_name)
                    IO_files['-i2'] = os.path.join(i2_dir, fl_name)
                    in_dir.use_file(fl_name, self.name)
                    assert len(self.output_types) == 1, 'Several output ' \
                                                        'types, override ' \
                                                        'this method!'

                    output_name = utils.splitext(fl_name)[0] + \
                                  self.output_types[0]
                    output_path = os.path.join(out_dir.path, output_name)
                    IO_files['-o'] = output_path
                    file_names.add(output_name)
                    out_dir.add_file(output_name)
                    break
        if not IO_files:
            raise VirtualIOError('No more unused input files')
        out_cmd.update(IO_files)
        return out_cmd, file_names

    def get_cmd(self):
        """Returns the final command line.

        Returns:
        final_cmd: List of command line produced by the object (line breaks not allowed within command lines!).
        """
        run_command = utils.parse_config(self.name, 'cmd_name', 'prefix')
        if run_command is None:
            final_cmd = [self.name]
        else:
            final_cmd = [run_command]
        final_cmd.append(self.out_cmd['-i'])
        final_cmd.append(self.out_cmd['-i2'])
        final_cmd.append('>')
        final_cmd.append(self.out_cmd['-o'])
        return [' '.join(final_cmd)]

class Picard_MarkDuplicates(Picard_SuperClass):
    """Class for using MarkDuplicates of picard toolkit.

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

    name = 'Picard_MarkDuplicates'
    #Accept all defined types:
    input_types = {'.sam', '.bam'}
    output_types = ['.sam', '.bam']
    mandatory_args = ['-INPUT', '-OUTPUT', '-METRICS_FILE']
    user_mandatory_args = []
    remove_user_args = user_mandatory_args
    optional_args = ['-PROGRAM_RECORD_ID', '-PROGRAM_GROUP_VERSION',
                     '-PROGRAM_GROUP_COMMAND_LINE', '-PROGRAM_GROUP_NAME',
                     '-COMMENT', '-REMOVE_DUPLICATES', '-ASSUME_SORTED',
                     '-MAX_FILE_HANDLES_FOR_READ_ENDS_MAP',
                     '-SORTING_COLLECTION_SIZE_RATIO', '-READ_NAME_REGEX',
                     '-OPTICAL_DUPLICATE_PIXEL_DISTANCE',
                     '-VALIDATION_STRINGENCY', '-COMPRESSION_LEVEL',
                     '-MAX_RECORDS_IN_RAM', '-CREATE_INDEX',
                     '-CREATE_MD5_FILE', '-REFERENCE_SEQUENCE',
                     '-GA4GH_CLIENT_SECRETS']
    parallelizable = True
    help_description = '''
Nothing to say here.
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
        out_cmd: Dict containing the output commands
        file_names: Names of the output files.

        Raises:
        VirtualIOError: No valid input file can be found.
        """

        IO_files = {}
        file_names = set()
        for fl_name, users in in_dir.files.iteritems():
            if self.name not in users:
                if utils.splitext(fl_name)[-1] in self.input_types:
                    IO_files['-INPUT'] = os.path.join(in_dir.path, fl_name)
                    in_dir.use_file(fl_name, self.name)
                    output_name = fl_name
                    output_path = os.path.join(out_dir.path, output_name)
                    IO_files['-OUTPUT'] = output_path
                    metrics_path = os.path.splitext(output_path)[0] + \
                                   '.metrics'
                    IO_files['-METRICS_FILE'] = metrics_path
                    file_names.add(output_name)
                    out_dir.add_file(output_name)
                    break
        if not IO_files:
            raise VirtualIOError('No more unused input files')
        out_cmd.update(IO_files)
        return out_cmd, file_names


class Picard_MergeSamFiles(Picard_SuperClass):
    name = 'Picard_MergeSamFiles'
    #Accept all defined types:
    input_types = {'.sam', '.bam'}
    output_types = ['.sam', '.bam']
    mandatory_args = ['-INPUT', '-OUTPUT']
    user_mandatory_args = ['-!PATH_TO_FILE_SETS_FILE']
    remove_user_args = user_mandatory_args
    optional_args = ['-SORT_ORDER', '-ASSUME_SORTED',
                     '-MERGE_SEQUENCE_DICTIONARIES', '-USE_THREADING',
                     '-COMMENT', '-VALIDATION_STRINGENCY',
                     '-COMPRESSION_LEVEL',
                     '-MAX_RECORDS_IN_RAM', '-CREATE_INDEX',
                     '-CREATE_MD5_FILE', '-REFERENCE_SEQUENCE',
                     '-GA4GH_CLIENT_SECRETS']
    parallelizable = True
    help_description = '''
The -!PATH_TO_FILE_SETS_FILE argument takes a path to an input file as a
value. The input file should consist lines, of which each contains a tab
delimited list of input file name substrings. In practice this means that for
each substring the script iterates over the files in the (automatically
inferred) input directory and selects all files in which the substring is
found. Notice that the input strings are case sensitive!
Let us assume that you have the following files in the input directory:
pop_1_sample_1.bam
pop_1_sample_2.bam
pop_1_sample_3.bam
pop_2_sample_1.bam
pop_2_sample_2.bam
pop_2_sample_3.bam

If you wish to combine the files of each population into two corresponding
files, you should add the following strings into the input file:
pop_1
pop_2

The resulting output files have the name of the first included file
(pop_1_sample_1.bam and pop_2_sample_1.bam in this case).

The above input file would result in identical command lines as the following
input file:
pop_1_sample_1.bam  pop_1_sample_2.bam  pop_1_sample_3.bam
pop_2_sample_1.bam  pop_2_sample_2.bam  pop_2_sample_3.bam

NOTICE! Each input .bam/.sam file can only be part of one output file. An
error is raised if the same file is included in several output files.
    '''

    def _select_IO(self, out_cmd, in_dir, out_dir):
        """Returns a dict containing the proper IO commands.

        This method must keep the directory objects up to date of the file
        edits!

        Arguments:
        in_cmd: A dict containing the command line.
        in_dir: Input directory (instance of filetypes.Directory).
        out_dir: Output directory (instance of filetypes.Directory).

        Returns:
        out_cmd: Dict containing the output commands
        file_names: Names of the output files.

        Raises:
        VirtualIOError: No valid input file can be found.
        """
        user_defined_substrings = self._parse_user_file_sets(out_cmd['-!PATH_TO_FILE_SETS_FILE'])
        substring_corresponding_files = self._create_file_set(out_cmd,
                                                             in_dir,
                                                             user_defined_substrings)

        #Create the input set
        IO_files = {}
        file_names = set()
        input_path_list = []
        for fl in substring_corresponding_files:
            in_dir.use_file(fl, self.name)
            input_fl_path = in_dir.get_absolute_file_path(fl)
            input_path_list.append(input_fl_path)
            if len(input_path_list) == 1:
                IO_files['-OUTPUT'] = os.path.join(out_dir.path, fl)
                file_names.add(fl)
                out_dir.add_file(fl)
        IO_files['-INPUT'] = input_path_list
        out_cmd.update(IO_files)
        return out_cmd, file_names

    def _parse_user_file_sets(self, path):
        """Reads the user defined file sets from file.

        Arguments:
        path: Path to file defining the file sets.

        Returns:
        List, where each value contains a set (list) of sam/bam file
        identifiers (substrings) to combine.

        Raises:
        STAPLERerror if file can not be parsed.
        """
        try:
            handle = open(path)
        except IOError as err:
            raise STAPLERerror('Can not open file:\n{0}\nReason\n{1}'.format(path,
                                                                             str(err)))
        sets = []
        used_files = []
        for line in handle:
            line = line.strip()
            if not line: continue
            if line.startswith('#'): continue

            if '\t' in line:
                line = line.split('\t')
            else:
                line = [line]
            sets.append(line)

            #Check that the same id is not used more than once:
            for file_id in line:
                if file_id in used_files:
                    logging.error('The file id "{0}" has already been '
                                  'defined previously! File:\n{1}'
                                  .format(file_id,
                                          path))
                else:
                    used_files.append(file_id)
        handle.close()

        if not sets:
            raise STAPLERerror('No file sets found from file:\n{0}'
                               .format(path))

        return sets

    def _create_file_set(self, out_cmd, in_dir, file_set_ids):
        #Find corresponding files for each user defined id
        used_files = set()
        for id_set in file_set_ids:
            if not id_set:
                raise STAPLERerror('An empty id set found. Revise the set file:'
                              '\n{0}'.format(out_cmd['-!PATH_TO_FILE_SETS_FILE']))
            files_for_current_set = []
            for file_id in id_set:
                for current_file, users in in_dir.files.iteritems():
                    if file_id in current_file:
                        if utils.splitext(current_file)[-1] in \
                                self.input_types:
                            files_for_current_set.append(current_file)
                            if current_file in used_files:
                                raise STAPLERerror('The input file {0} has already '
                                              'been used before! Revise the '
                                              'set file:\n{1}'.format(current_file,
                                                                      out_cmd[
                                                                          '-!PATH_TO_FILE_SETS_FILE']))
                            used_files.add(current_file)

            #Make sure that all the files of the current set are used/unused
            for fl in files_for_current_set:
                used_files_found = False
                unused_files_found = False
                if self.name in in_dir.files[fl]:
                    used_files_found = True
                else:
                    unused_files_found = True
            if not files_for_current_set:
                raise STAPLERerror('Unable associate any file with the following '
                              'set:\n{0}\n\nOnly the following files '
                              'are available in the input '
                              'directory:\n{1}'.format(id_set,
                                                       in_dir.files.keys()))
            if used_files_found and unused_files_found:
                raise STAPLERerror('One or several of the files in the current set '
                              'have been used in a previous set. Revise the '
                              'file:\n{0}\nCurrent set ids:\n{1}\n'
                              'Corresponding files:\n{2}'
                                   .format(out_cmd['-!PATH_TO_FILE_SETS_FILE'],
                                      str(id_set),
                                      str(files_for_current_set)))
            elif unused_files_found:
                break

        #The last used defined set has already been created
        if used_files_found:
            raise VirtualIOError('No more unused input files')

        logging.info('Current id set:\n{0}'.format(str(id_set)))
        logging.info('Corresponding files:\n{0}'.format(str(files_for_current_set)))

        return files_for_current_set

    def get_cmd(self):
        """Returns the final command line.

        Returns:
        final_cmd: List of command line produced by the object (line breaks not allowed within command lines!).
        """
        run_command = utils.parse_config(self.name, 'cmd_name', 'prefix')
        if run_command is None:
            final_cmd = [self.name]
        else:
            final_cmd = [run_command]
        for arg, val in self.out_cmd.iteritems():
            arg = arg.lstrip('-')

            if arg == 'INPUT':
                #Input value is a list here
                for v in val:
                    final_cmd.append(arg + '=' + v)
            else:
                final_cmd.append(arg + '=' + val)
        return [' '.join(final_cmd)]

    def _parse_id(self, parsed_cmd):
        """Returns the bare input file name (id)"""
        cmd = parsed_cmd[self.mandatory_args[0]]
        #In this command the input consists of several bam/sam files, so the
        # cmd is a list of strings instead of a string:
        cmd = cmd[0]
        cmd = os.path.basename(cmd)
        return cmd.split('.', 1)[0]


class Picard_SamFormatConverter(Picard_SuperClass):

    name = 'Picard_SamFormatConverter'
    #Accept all defined types:
    input_types = {'.sam', '.bam'}
    output_types = ['.sam', '.bam']
    mandatory_args = ['-INPUT', '-OUTPUT']
    user_mandatory_args = ['-!in_type', '-!out_type']
    remove_user_args = user_mandatory_args
    optional_args = ['-VERBOSITY', '-QUIET', '-VALIDATION_STRINGENCY',
                     '-COMPRESSION_LEVEL',
                     '-MAX_RECORDS_IN_RAM', '-CREATE_INDEX',
                     '-CREATE_MD5_FILE', '-VALIDATION_STRINGENCY',
                     '-COMPRESSION_LEVEL',
                     '-MAX_RECORDS_IN_RAM', '-CREATE_INDEX',
                     '-CREATE_MD5_FILE', '-REFERENCE_SEQUENCE',
                     '-GA4GH_CLIENT_SECRETS']
    parallelizable = True
    help_description = '''
The -!in_type and -!out_type parameters are needed to define the input and
output formats. Allowed values are ".sam" and ".bam".
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
        out_cmd: Dict containing the output commands
        file_names: Names of the output files.

        Raises:
        VirtualIOError: No valid input file can be found.
        """
        #Check user input
        if out_cmd['-!in_type'] not in {'.sam', '.bam'}:
            raise STAPLERerror('Valid values for -!in_type are ".sam" and '
                          '".bam"! The current value was:\n{0}'
                               .format(out_cmd['-!in_type']))
        if out_cmd['-!out_type'] not in {'.sam', '.bam'}:
            raise STAPLERerror('Valid values for -!out_type are ".sam" and '
                          '".bam"! The current value was:'
                               .format(out_cmd['-!out_type']))
        IO_files = {}
        file_names = set()
        for fl_name, users in in_dir.files.iteritems():
            if self.name not in users:
                if utils.splitext(fl_name)[1] in self.input_types and utils.splitext(fl_name)[1] == out_cmd['-!in_type']:
                    IO_files['-INPUT'] = os.path.join(in_dir.path, fl_name)
                    in_dir.use_file(fl_name, self.name)
                    output_name = (utils.splitext(fl_name)[0] +
                                   out_cmd['-!out_type'])
                    output_path = os.path.join(out_dir.path, output_name)
                    IO_files['-OUTPUT'] = output_path
                    file_names.add(output_name)
                    out_dir.add_file(output_name)
                    break
        if not IO_files:
            raise VirtualIOError('No more unused input files')
        out_cmd.update(IO_files)
        return out_cmd, file_names


class Picard_SortSam(Picard_SuperClass):
    """Class for using SortSam of picard toolkit.

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

    name = 'Picard_SortSam'
    #Accept all defined types:
    input_types = {'.sam', '.bam'}
    output_types = ['.sam', '.bam']
    mandatory_args = ['-INPUT', '-OUTPUT', '-SORT_ORDER']
    user_mandatory_args = ['-SORT_ORDER']
    remove_user_args = []
    optional_args = ['-VALIDATION_STRINGENCY', '-COMPRESSION_LEVEL',
                     '-MAX_RECORDS_IN_RAM', '-CREATE_INDEX',
                     '-CREATE_MD5_FILE', '-REFERENCE_SEQUENCE',
                     '-GA4GH_CLIENT_SECRETS']
    parallelizable = True
    help_description = '''
No additional help, sorry. See the official Picard manual.
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
        out_cmd: Dict containing the output commands
        file_names: Names of the output files.

        Raises:
        VirtualIOError: No valid input file can be found.
        """

        IO_files = {}
        file_names = set()
        for fl_name, users in in_dir.files.iteritems():
            if self.name not in users:
                current_file_extension = utils.splitext(fl_name)[1]
                if current_file_extension in self.input_types:
                    IO_files['-INPUT'] = os.path.join(in_dir.path, fl_name)
                    in_dir.use_file(fl_name, self.name)
                    output_path = os.path.join(out_dir.path, fl_name)
                    IO_files['-OUTPUT'] = output_path
                    file_names.add(fl_name)
                    out_dir.add_file(fl_name)
                    break
        if not IO_files:
            raise VirtualIOError('No more unused input files')
        out_cmd.update(IO_files)
        return out_cmd, file_names