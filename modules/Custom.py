import copy
import itertools
import logging
import os

from GenericBase import GenericBase
from STAPLERerror import STAPLERerror
from STAPLERerror import VirtualIOError
import directory
import utils

class ANY_TOOL(GenericBase):
    """Class for generic command lines, omits user input checks.

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

    name = 'ANY_TOOL'
    #Accept all defined types:
    input_types = set([])
    output_types = []
    mandatory_args = ['-i', '-o']
    user_mandatory_args = ['--!INPUT_TYPE', '--!OUTPUT_TYPE', '--!TOOL_NAME']
    remove_user_args = user_mandatory_args
    optional_args = []
    parallelizable = True
    help_description = '''
This tool can be used to create command lines for software that is not
supported by STAPLER. Unlike other tools, this script has no
mandatory or optional parameters, which means that you can use any parameters
you would like. This tool also has no file type limitations, so any files can be
used as input. The output file will have the same name as the input file by
default. You may use the --!OUTPUT_TYPE to change this behaviour
(e.g. --!OUTPUT_TYPE txt). --!INPUT_TYPE parameter can be used in similar
fashion for setting input files. --!2tables may also become handy here.

By default the output command will have ANY_TOOl as the output
command name. This default string can be overridden by using the --!TOOL_NAME
option with a new string as a value (e.g. /path/my_script.py).
    '''

    def __init__(self, in_cmd, in_dir, out_dir):
        print 'Trying to initialize {0}'.format(self.name)
        logging.info('Trying to initialize {0} with user command:\n{1}'
                     .format(self.name, in_cmd))
        self.in_cmd = in_cmd
        self.parsed_in_cmd = self._cmd_parse(in_cmd)
        self.out_cmd = copy.deepcopy(self.parsed_in_cmd)
        self.out_cmd, self.file_names = self._select_IO(self.out_cmd,
                                                        in_dir,
                                                        out_dir)
        self._validate_user_input(self.out_cmd)
        self.input_types = self.out_cmd['--!INPUT_TYPE']
        self.output_types = self.out_cmd['--!OUTPUT_TYPE']
        self.name = self.out_cmd['--!TOOL_NAME']
        self._validate_final(self.out_cmd)
        self.id = self._parse_id(self.out_cmd)
        self.load_module = utils.parse_module(self.name,
                                              'cmd_name',
                                              'load_module')
        self.unload_module = utils.parse_module(self.name,
                                                'cmd_name',
                                                'unload_module')
        logging.info('Finished initializing {0} with user command:\n{1}'
                     .format(self.name, in_cmd))

    def _cmd_parse(self, cmd):
        """Turns a command line into argument-value pairs.

        The function expects that all arguments start with '-'!

        Args:
        cmd: A string containing the command line.

        Returns:
        parsed_cmd: A dict of argument-value pairs.

        Raises:
        STAPLERerror: The command line does not start with '-'
        """

        cmd = cmd.strip()

        if len(cmd) == 0:
            return {}

        if not cmd.startswith('-'):
            raise STAPLERerror("An argument does not start with '-':\n{0}".format(
                cmd))

        cmd = cmd.split(' -')
        parsed_cmd = {}
        i = 0
        for c in cmd:
            if not c:
                continue
            try:
                argument, value = c.split(' ', 1)
            except ValueError:
                argument = c.split(' ', 1)[0]
                value = ''
            if i > 0:
                argument = '-' + argument
            parsed_cmd[argument] = value
            i += 1
        return parsed_cmd

    def _validate_user_input(self, in_cmd):
        """Validates the input command of user.

        Arguments:
        in_cmd: String the user has input.

        Raises:
        STAPLERerror: Invalid format.
        """
        pass

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
            if '--!INPUT_TYPE' in self.parsed_in_cmd:
                if not fl_name.endswith(self.parsed_in_cmd['--!INPUT_TYPE']):
                    continue
            if self.name not in users:
                IO_files['-i'] = os.path.join(in_dir.path, fl_name)
                in_dir.use_file(fl_name, self.name)
                if '--!OUTPUT_TYPE' in self.parsed_in_cmd:
                    output_name = utils.splitext(fl_name)[0]
                    output_name += self.parsed_in_cmd['--!OUTPUT_TYPE']
                else:
                    output_name = fl_name
                output_path = os.path.join(out_dir.path, output_name)
                IO_files['-o'] = output_path
                file_names.add(output_name)
                out_dir.add_file(output_name)

        if not IO_files:
            raise VirtualIOError('No more unused input files')
        out_cmd.update(IO_files)
        return out_cmd, file_names

    def _user_override(self, parsed_in_cmd, out_cmd):
        """Overrides auto-inferred values with possible user inputs.

        Arguments:
        parsed_in_cmd: Parsed unmodified dict of user input.
        out_cmd: Dict of auto-inferred output commands.

        Returns:
        Output commands overridden with user inputs.
        """

        for arg, value in parsed_in_cmd.iteritems():
            if value.startswith('!2table'):
                new_value = self._parse_2table(value)
                out_cmd[arg] = new_value
        return out_cmd

    def _parse_2table(self, string):
        """Parses the 2table input.

        Proper format:
        !2table:path

        Arguments:
        string: 2table command.

        Raises:
        STAPLERerror: The 2table format is not correct.

        Returns:
        String read from user defined file.
        """
        if string.count(':') != 1:
            raise STAPLERerror('Invalid 2table format:\n{0}'.format(string))
        path = string.split(':')[1]
        return utils.read_value(path, self.id)

    def _validate_final(self, parsed_cmd):
        """Validates the final output command line.

        Raises STAPLERerror if validation is unsuccessful

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

    def _parse_id(self, parsed_cmd):
        """Returns the bare input file name (id)"""
        cmd = parsed_cmd[self.mandatory_args[0]]
        cmd = os.path.basename(cmd)
        return cmd.split('.', 1)[0]

    def get_cmd(self):
        """Returns the final command line.

        Returns:
        final_cmd: List of command line produced by the object (line breaks not allowed within command lines!).
        """
        if '--!TOOL_NAME' in self.out_cmd:
            run_command = self.out_cmd['--!TOOL_NAME']
        else:
            run_command = utils.parse_config(self.name, 'cmd_name', 'prefix')

        if run_command is None:
            final_cmd = [self.name]
        else:
            final_cmd = [run_command]

        for arg, val in self.out_cmd.iteritems():
            #Skip --!INPUT_TYPE, --!OUTPUT_TYPE, --!TOOL_NAME
            if arg in self.optional_args:
                continue
            final_cmd.append(arg + ' ' + val)
        return [' '.join(final_cmd)]

class baitron(GenericBase):
    """Class for baitron.py.

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

    name = 'baitron'
    #Accept all defined types:
    input_types = set(['.coverageBed_out'])
    output_types = ['.baitron_out']
    mandatory_args = ['-i', '-o']
    user_mandatory_args = ['-b', '-c', '-d', '-p']
    remove_user_args = []
    optional_args = ['-t']
    parallelizable = True
    help_description = '''
This script works for .coverageBed_out files created with bedtools coverageBed
tool.
    '''

class baits_from_blast_selectomatic(GenericBase):
    """Class for parallelization of baits_from_blast_selectomatic.py.

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

    name = 'baits_from_blast_selectomatic'
    #Accept all defined types:
    input_types = {'.xml'}
    output_types = ['.bfbs']
    mandatory_args = ['-i', '-o', '-m', '-n', '-s', '-t']
    user_mandatory_args = ['-m', '-n', '-s', '-t']
    remove_user_args = []
    optional_args = []
    parallelizable = True
    help_description = '''
Tested with version 15.09.14.

The custom output format files have the following file name extension:
.bfbs
    '''


class MAD_MAX(GenericBase):
    """Class for generic command lines for MAD_MAX.py.

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

    name = 'generic_command'
    input_types = set(['.coverageBed_out'])
    output_types = ['.bed']
    mandatory_args = ['-i', '-o']
    user_mandatory_args = []
    remove_user_args = user_mandatory_args
    optional_args = ['-b', '-m', '-z']
    parallelizable = True
    help_description = '''
Tested with MAD_MAX v.16.03.11.
    '''

class ParalogAreaBEDmatic(GenericBase):
    name = 'ParalogAreaBEDmatic'
    #Accept all defined types:
    input_types = set(['.vcf'])
    output_types = ['.bed']
    mandatory_args = ['-i', '-o']
    user_mandatory_args = ['-r', '-g']
    remove_user_args = []
    optional_args = []
    parallelizable = True
    help_description = '''
Tested with ParalogAreaBEDmatic v. 15.12.16.
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
                    IO_files['-o'] = output_path
                    file_names.add(output_name)
                    out_dir.add_file(output_name)
                    break
        if not IO_files:
            raise VirtualIOError('No more unused input files')
        out_cmd.update(IO_files)
        return out_cmd, file_names


class variant_density_filter(GenericBase):
    """Class for parallelization of variant_density_filter.py.

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

    name = 'variant_density_filter'
    #Accept all defined types:
    input_types = {'.vcf'}
    output_types = ['.vcf']
    mandatory_args = ['-i', '-o', '-s', '-m']
    user_mandatory_args = ['-s', '-m']
    remove_user_args = []
    optional_args = ['-r']
    parallelizable = True
    help_description = '''
Tested with version 15.08.21.

Sorry no additional specific help available for this
tool :(

See the original tool manual for help!
    '''