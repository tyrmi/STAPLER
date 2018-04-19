import logging
import os

from GenericBase import GenericBase
from STAPLERerror import STAPLERerror
from STAPLERerror import VirtualIOError
import utils

import copy
import itertools
import logging
import os

from STAPLERerror import STAPLERerror
from STAPLERerror import VirtualIOError
import directory
import utils

class Picard_SuperClass(GenericBase):
    """Superclass for picard toolkit.

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

    name = 'Picard_SuperClass'

    def get_cmd(self):
        """Returns the final command line.

        Returns:
        final_cmd: List of command line produced by the object (line breaks not allowed within command lines!).
        """
        run_command = utils.parse_config(self.name, 'cmd_name', 'execute')
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
    hidden_mandatory_args = ['-INPUT', '-OUTPUT', '-RGLB', '-RGPL', '-RGPU', '-RGSM']
    user_mandatory_args = ['-RGLB', '-RGPL', '-RGPU', '-RGSM']
    remove_user_args = []
    user_optional_args = ['-SORT_ORDER', '-RGID', '-RGCN', '-RGDS', '-RGDT',
                          '-RGPI', '-VALIDATION_STRINGENCY', '-COMPRESSION_LEVEL',
                          '-MAX_RECORDS_IN_RAM', '-CREATE_INDEX',
                          '-CREATE_MD5_FILE', '-REFERENCE_SEQUENCE',
                          '-GA4GH_CLIENT_SECRETS']
    parallelizable = True
    help_description = '''
Tested with Picard 2.13.

This tool requires four specific fields to be defined in the input path:
RGLB
RGPL
RGPL
RGPU
RGSM

These (and other optional [see picard manual]) fields can be defined by using the 
STAPLER !value_table feature when you want to define a specific value for each file, e.g.:
-RGLB !value_table:path/to/my_RGLB_names.txt:name_of_id_column:name_of_RGLB_column
See STAPLER example directory on how to define a value_table
    '''

    def _select_IO(self, out_cmd, in_dir, out_dir):
        """Infers the input and output file paths.

        This method must keep the directory objects up to date of the file
        edits!

        Parameters:
        in_cmd: A dict containing the command line.
        in_dir: Input directory.
        out_dir: Output directory.

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
                    IO_files['-INPUT'] = os.path.join(in_dir.path, fl.name)
                    command_ids = [utils.infer_path_id(IO_files['-INPUT'])]
                    in_dir.use_file(fl.name, self.name)
                    output_name = fl.name
                    output_path = os.path.join(out_dir.path, output_name)
                    IO_files['-OUTPUT'] = output_path
                    file_names.add(output_name)
                    out_dir.add_file(output_name)
                    break
        if not IO_files:
            raise VirtualIOError('No more unused input files')
        out_cmd.update(IO_files)
        return out_cmd, command_ids


class Picard_CollectAlignmentSummaryMetrics(Picard_SuperClass):
    """Class for using CollectAlignmentSummaryMetrics_1.128 of picard toolkit.

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

    name = 'Picard_CollectAlignmentSummaryMetrics'
    #Accept all defined types:
    input_types = {'.sam', '.bam'}
    output_types = ['.out']
    hidden_mandatory_args = ['-INPUT', '-OUTPUT']
    user_mandatory_args = []
    remove_user_args = user_mandatory_args
    user_optional_args = ['-MAX_INSERT_SIZE', '-ADAPTER_SEQUENCE',
                          '-METRIC_ACCUMULATION_LEVEL', '-IS_BISULFITE_SEQUENCED',
                          '-ASSUME_SORTED', '-STOP_AFTER', '-VALIDATION_STRINGENCY',
                          '-COMPRESSION_LEVEL', '-MAX_RECORDS_IN_RAM',
                          '-CREATE_INDEX', '-CREATE_MD5_FILE',
                          '-REFERENCE_SEQUENCE', '-GA4GH_CLIENT_SECRETS']
    parallelizable = True
    help_description = '''
Tested with Picard 2.13.
    '''

    def _select_IO(self, out_cmd, in_dir, out_dir):
        """Infers the input and output file paths.

        This method must keep the directory objects up to date of the file
        edits!

        Parameters:
        in_cmd: A dict containing the command line.
        in_dir: Input directory.
        out_dir: Output directory.

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
                    IO_files['-INPUT'] = os.path.join(in_dir.path, fl.name)
                    command_ids = [utils.infer_path_id(IO_files['-INPUT'])]
                    in_dir.use_file(fl.name, self.name)
                    assert len(self.output_types) == 1, 'Several output ' \
                                                        'types, override ' \
                                                        'this method!'

                    output_name = utils.splitext(fl.name)[0] + \
                                  self.output_types[0]
                    output_path = os.path.join(out_dir.path, output_name)
                    IO_files['-OUTPUT'] = output_path
                    file_names.add(output_name)
                    out_dir.add_file(output_name)
                    break
        if not IO_files:
            raise VirtualIOError('No more unused input files')
        out_cmd.update(IO_files)
        return out_cmd, command_ids


class Picard_CollectInsertSizeMetrics(Picard_SuperClass):
    """Class for using CollectInsertSizeMetrics of picard toolkit.

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

    name = 'Picard_CollectInsertSizeMetrics'
    #Accept all defined types:
    input_types = {'.sam', '.bam'}
    output_types = ['.out']
    hidden_mandatory_args = ['-INPUT', '-OUTPUT', '-HISTOGRAM_FILE']
    user_mandatory_args = []
    remove_user_args = []
    user_optional_args = ['-REFERENCE_SEQUENCE', '-DEVIATIONS',
                          '-HISTOGRAM_WIDTH', '-MINIMUM_PCT',
                          '-METRIC_ACCUMULATION_LEVEL', '-ASSUME_SORTED',
                          '-STOP_AFTER', '-VALIDATION_STRINGENCY',
                          '-COMPRESSION_LEVEL',
                          '-MAX_RECORDS_IN_RAM', '-CREATE_INDEX',
                          '-CREATE_MD5_FILE', '-REFERENCE_SEQUENCE',
                          '-GA4GH_CLIENT_SECRETS']
    parallelizable = True
    help_description = '''
Tested with Picard 2.13.
    '''

    def _select_IO(self, out_cmd, in_dir, out_dir):
        """Infers the input and output file paths.

        This method must keep the directory objects up to date of the file
        edits!

        Parameters:
        in_cmd: A dict containing the command line.
        in_dir: Input directory.
        out_dir: Output directory.

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
                    IO_files['-INPUT'] = os.path.join(in_dir.path, fl.name)
                    command_ids = [utils.infer_path_id(IO_files['-INPUT'])]
                    in_dir.use_file(fl.name, self.name)
                    assert len(self.output_types) == 1, 'Several output ' \
                                                        'types, override ' \
                                                        'this method!'

                    output_name = utils.splitext(fl.name)[0] + \
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
        return out_cmd, command_ids


class Picard_CollectWgsMetrics(Picard_SuperClass):
    """Class for using CollectWgsMetrics of picard toolkit.

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

    name = 'Picard_CollectWgsMetrics'
    #Accept all defined types:
    input_types = {'.sam', '.bam'}
    output_types = ['.out']
    hidden_mandatory_args = ['-INPUT', '-OUTPUT']
    user_mandatory_args = []
    remove_user_args = []
    user_optional_args = ['-MINIMUM_MAPPING_QUALITY', '-MINIMUM_BASE_QUALITY',
                          '-COVERAGE_CAP', '-STOP_AFTER', '-REFERENCE_SEQUENCE',
                          '-VALIDATION_STRINGENCY', '-COMPRESSION_LEVEL',
                          '-MAX_RECORDS_IN_RAM', '-CREATE_INDEX',
                          '-CREATE_MD5_FILE', '-REFERENCE_SEQUENCE',
                          '-GA4GH_CLIENT_SECRETS']
    parallelizable = True
    help_description = '''
Tested with Picard 2.13.
    '''

    def _select_IO(self, out_cmd, in_dir, out_dir):
        """Infers the input and output file paths.

        This method must keep the directory objects up to date of the file
        edits!

        Parameters:
        in_cmd: A dict containing the command line.
        in_dir: Input directory.
        out_dir: Output directory.

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
                    IO_files['-INPUT'] = os.path.join(in_dir.path, fl.name)
                    command_ids = [utils.infer_path_id(IO_files['-INPUT'])]
                    in_dir.use_file(fl.name, self.name)
                    assert len(self.output_types) == 1, 'Several output ' \
                                                        'types, override ' \
                                                        'this method!'

                    output_name = utils.splitext(fl.name)[0] + \
                                  self.output_types[0]
                    output_path = os.path.join(out_dir.path, output_name)
                    IO_files['-OUTPUT'] = output_path
                    file_names.add(output_name)
                    out_dir.add_file(output_name)
                    break
        if not IO_files:
            raise VirtualIOError('No more unused input files')
        out_cmd.update(IO_files)
        return out_cmd, command_ids


    def get_cmd(self):
        """Returns the final command line.

        Returns:
        final_cmd: List of command line produced by the object (line breaks not allowed within command lines!).
        """
        run_command = utils.parse_config(self.name, 'cmd_name', 'execute')
        final_cmd = [run_command]
        final_cmd.append(self.out_cmd['-i'])
        final_cmd.append(self.out_cmd['-i2'])
        final_cmd.append('>')
        final_cmd.append(self.out_cmd['-o'])
        return [' '.join(final_cmd)]

class Picard_MarkDuplicates(Picard_SuperClass):
    """Class for using MarkDuplicates of picard toolkit.

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

    name = 'Picard_MarkDuplicates'
    #Accept all defined types:
    input_types = {'.sam', '.bam'}
    output_types = ['.sam', '.bam']
    hidden_mandatory_args = ['-INPUT', '-OUTPUT', '-METRICS_FILE']
    user_mandatory_args = []
    remove_user_args = user_mandatory_args
    user_optional_args = ['-PROGRAM_RECORD_ID', '-PROGRAM_GROUP_VERSION',
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
Tested with Picard 2.13.
    '''

    def _select_IO(self, out_cmd, in_dir, out_dir):
        """Infers the input and output file paths.

        This method must keep the directory objects up to date of the file
        edits!

        Parameters:
        in_cmd: A dict containing the command line.
        in_dir: Input directory.
        out_dir: Output directory.

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
                    IO_files['-INPUT'] = os.path.join(in_dir.path, fl.name)
                    command_ids = [utils.infer_path_id(IO_files['-INPUT'])]
                    in_dir.use_file(fl.name, self.name)
                    output_name = fl.name
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
        return out_cmd, command_ids


class Picard_SamFormatConverter(Picard_SuperClass):

    name = 'Picard_SamFormatConverter'
    #Accept all defined types:
    input_types = {'.sam', '.bam'}
    output_types = ['.sam', '.bam']
    hidden_mandatory_args = ['-INPUT', '-OUTPUT']
    user_mandatory_args = ['-!in_type', '-!out_type']
    remove_user_args = user_mandatory_args
    user_optional_args = ['-VERBOSITY', '-QUIET', '-VALIDATION_STRINGENCY',
                          '-COMPRESSION_LEVEL',
                          '-MAX_RECORDS_IN_RAM', '-CREATE_INDEX',
                          '-CREATE_MD5_FILE', '-VALIDATION_STRINGENCY',
                          '-COMPRESSION_LEVEL',
                          '-MAX_RECORDS_IN_RAM', '-CREATE_INDEX',
                          '-CREATE_MD5_FILE', '-REFERENCE_SEQUENCE',
                          '-GA4GH_CLIENT_SECRETS']
    parallelizable = True
    help_description = '''
Tested with Picard 2.13.

The -!in_type and -!out_type parameters are required to define the input and
output formats. Allowed values are ".sam" and ".bam".
    '''

    def _select_IO(self, out_cmd, in_dir, out_dir):
        """Infers the input and output file paths.

        This method must keep the directory objects up to date of the file
        edits!

        Parameters:
        in_cmd: A dict containing the command line.
        in_dir: Input directory.
        out_dir: Output directory.

        Returns:
        out_cmd: Dict containing the output commands
        command_identifier: Input file name based identifier for the current command

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
        for fl in in_dir.files:
            if self.name not in fl.users:
                if utils.splitext(fl.name)[1] in self.input_types and utils.splitext(fl.name)[1] == out_cmd['-!in_type']:
                    IO_files['-INPUT'] = os.path.join(in_dir.path, fl.name)
                    command_ids = [utils.infer_path_id(IO_files['-INPUT'])]
                    in_dir.use_file(fl.name, self.name)
                    output_name = (utils.splitext(fl.name)[0] +
                                   out_cmd['-!out_type'])
                    output_path = os.path.join(out_dir.path, output_name)
                    IO_files['-OUTPUT'] = output_path
                    file_names.add(output_name)
                    out_dir.add_file(output_name)
                    break
        if not IO_files:
            raise VirtualIOError('No more unused input files')
        out_cmd.update(IO_files)
        return out_cmd, command_ids


class Picard_SortSam(Picard_SuperClass):
    """Class for using SortSam of picard toolkit.

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

    name = 'Picard_SortSam'
    #Accept all defined types:
    input_types = {'.sam', '.bam'}
    output_types = ['.sam', '.bam']
    hidden_mandatory_args = ['-INPUT', '-OUTPUT', '-SORT_ORDER']
    user_mandatory_args = ['-SORT_ORDER']
    remove_user_args = []
    user_optional_args = ['-VALIDATION_STRINGENCY', '-COMPRESSION_LEVEL',
                          '-MAX_RECORDS_IN_RAM', '-CREATE_INDEX',
                          '-CREATE_MD5_FILE', '-REFERENCE_SEQUENCE',
                          '-GA4GH_CLIENT_SECRETS']
    parallelizable = True
    help_description = '''
Tested with Picard 2.13.
    '''

    def _select_IO(self, out_cmd, in_dir, out_dir):
        """Infers the input and output file paths.

        This method must keep the directory objects up to date of the file
        edits!

        Parameters:
        in_cmd: A dict containing the command line.
        in_dir: Input directory.
        out_dir: Output directory.

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
                current_file_extension = utils.splitext(fl.name)[1]
                if current_file_extension in self.input_types:
                    IO_files['-INPUT'] = os.path.join(in_dir.path, fl.name)
                    command_ids = [utils.infer_path_id(IO_files['-INPUT'])]
                    in_dir.use_file(fl.name, self.name)
                    output_path = os.path.join(out_dir.path, fl.name)
                    IO_files['-OUTPUT'] = output_path
                    file_names.add(fl.name)
                    out_dir.add_file(fl.name)
                    break
        if not IO_files:
            raise VirtualIOError('No more unused input files')
        out_cmd.update(IO_files)
        return out_cmd, command_ids