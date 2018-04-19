import copy
import itertools
import logging
import os
import subprocess

from STAPLERerror import STAPLERerror
from STAPLERerror import VirtualIOError
from STAPLERerror import NotConfiguredError
import utils


class GenericBase():
    """Superclass for STAPLER input classes.

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

    name = 'GenericBase'
    input_types = set([])
    output_types = []
    require_output_dir = True
    hidden_mandatory_args = ['-i', '-o']
    hidden_optional_args = []
    user_mandatory_args = []
    user_optional_args = []
    remove_user_args = user_mandatory_args
    parallelizable = True
    help_description = '''
This tool cannot be used by the end user.
'''

    def __init__(self, in_cmd, in_dir, out_dir):
        logging.info('Trying to initialize {0} with user command:\n{1}'
                     .format(self.name, in_cmd))
        self.in_cmd = in_cmd
        self.in_dir = in_dir
        self.out_dir = out_dir
        self.parsed_in_cmd = self._cmd_parse(in_cmd)
        self.out_cmd = copy.deepcopy(self.parsed_in_cmd)
        self._validate_user_input(self.out_cmd)
        self.out_cmd, self.command_ids = self._select_IO(self.out_cmd,
                                                         in_dir,
                                                         out_dir)
        assert isinstance(self.command_ids, list)
        self.command_ids = sorted(self.command_ids)
        #id is defined twice in __init__ since it must be available for
        # _user_override but it may also change in _user_override
        self.out_cmd = self._user_override(self.parsed_in_cmd, self.out_cmd)
        self.out_cmd = self._remove_user_arguments(self.out_cmd)
        self._validate_STAPLER_output_parameters(self.out_cmd)
        self.run_command = self.run_command_config()
        self.load_module = self.load_module_config()
        self.unload_module = self.unload_module_config()
        self.command_lines = self.get_cmd()
        logging.info('Finished initializing {0} with user command:\n{1}'
                     .format(self.name, in_cmd))

    def _cmd_parse(self, cmd):
        """Turns a command line into argument-value pairs.

        The function expects that all arguments start with '-'! It is OK for
        an argument not to have a value.

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
            parsed_cmd[argument] = value.strip()
            i += 1
        return parsed_cmd

    def _validate_user_input(self, in_cmd):
        """Ensures the user has included all mandatory arguments.

        Parameters:
        in_cmd: String the user has input.

        Raises:
        STAPLERerror: Invalid format.
        """

        for m_cmd in self.user_mandatory_args:
            if m_cmd not in in_cmd:
                raise STAPLERerror('{0} command needs the following argument: {1}'
                                   .format(self.name, m_cmd))
            if not in_cmd[m_cmd]:
                raise STAPLERerror('{0} command needs the following argument to have a value: {1}'
                                   .format(self.name, m_cmd))

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

    def _user_override(self, parsed_in_cmd, out_cmd):
        """Overrides auto-inferred values with possible user inputs.

        Parameters:
        parsed_in_cmd: Parsed unmodified dict of user input.
        out_cmd: Dict of auto-inferred output commands.

        Returns:
        Output commands overridden with user inputs.
        """

        for arg, value in parsed_in_cmd.iteritems():
            if value.startswith('!value_table'):
                new_value = self._parse_value_table(value)
                out_cmd[arg] = new_value
        return out_cmd

    def _parse_value_table(self, string):
        """Parses the !value_table input.

        Proper format:
        !value_table:path:column_name_1:column_name_2

        Parameters:
        string: !value_table command.

        Raises:
        STAPLERerror: The !value_table format is not correct.

        Returns:
        String read from user defined file.
        """
        if string.count(':') != 3:
            raise STAPLERerror('Invalid !value_table format:\n{'
                               '0}\nProper format for value table looks like '
                               'this:\npath/to/value_table_file.txt:id_name_column:value_column.'.format(string))
        path = string.split(':')[1]
        column_name_1 = string.split(':')[2]
        column_name_2 = string.split(':')[3]
        return utils.read_value_from_multi_table(path,
                                                 self.command_ids[0],
                                                 column_name_1,
                                                 column_name_2)

    def _remove_user_arguments(self, out_cmd):
        """Removes the specified arguments from final command line.

        Parameters:
        out_cmd: Dict containing the output commands
        Returns:
        Output commands
        """
        for cmd in self.remove_user_args:
            try:
                del out_cmd[cmd]
            except KeyError:
                pass
        return out_cmd

    def _validate_STAPLER_output_parameters(self, parsed_cmd):
        """Validates the final output command line.

        Raises STAPLERerror if validation is unsuccessful

        Args:
        parsed_cmd: Dict of arguments entered by user
        Raises:
        STAPLERerror if validation is unsuccessful
        """

        for ma in self.hidden_mandatory_args:
            assert ma in parsed_cmd, 'The command line does not contain all ' \
                                     'the mandatory arguments {0}: ' \
                                     '\n{1}'.format(self.hidden_mandatory_args,
                                                    ' '.join(parsed_cmd))
        for cmd in parsed_cmd:
            if (cmd not in self.hidden_mandatory_args and
                        cmd not in self.hidden_optional_args and
                        cmd not in self.user_mandatory_args and
                        cmd not in self.user_optional_args):
                logging.warning('Unknown option:\n{0}\n'
                                'on command line:\n{1}'.format(cmd, self.in_cmd))

    @classmethod
    def validate_tool_config(cls):
        """Checks if the current tool can be run as defined in config.txt

        """

        # Command is not defined
        try:
            cls.run_command_config()
        except NotConfiguredError:
            return ['NONE', 'NONE', 'NONE']

        devnull = open(os.devnull, 'wb')
        module_unloading_test = '-   '
        command_run_test = '-   '

        # Test if loading modules works
        if cls.load_module_config():
            try:
                subprocess.check_call(' && '.join(cls.load_module_config()),
                                      shell=True,
                                      stdout=devnull,
                                      stderr=devnull)
                module_loading_test = 'OK  '
            except subprocess.CalledProcessError:
                module_loading_test = 'FAIL'
                return [command_run_test, module_loading_test, module_unloading_test]
        else:
            module_loading_test = 'OK  '

        # Test if loading modules and then unloading them works
        if cls.unload_module_config():
            try:
                subprocess.check_call(' && '.join(cls.load_module_config() + cls.unload_module_config()),
                                      shell=True,
                                      stdout=devnull,
                                      stderr=devnull)
                module_unloading_test = 'OK  '
            except subprocess.CalledProcessError:
                module_unloading_test = 'FAIL'
        else:
            module_unloading_test = 'OK  '

        # Test if loading modules, and then running the command fails
        run_command_with_command_v = 'command -v {0}'.format(cls.run_command_config())
        try:
            if cls.load_module_config():
                subprocess.check_call(' && '.join(cls.load_module_config() + [run_command_with_command_v]),
                                      shell=True,
                                      stdout=devnull,
                                      stderr=devnull)
            else:
                subprocess.check_call(run_command_with_command_v,
                                      shell=True,
                                      stdout=devnull,
                                      stderr=devnull)
            command_run_test = 'OK  '
        except subprocess.CalledProcessError:
            command_run_test = 'FAIL'

        return [command_run_test, module_loading_test, module_unloading_test]


    @classmethod
    def run_command_config(cls):
        return utils.parse_config(cls.name, 'cmd_name', 'execute')

    @classmethod
    def load_module_config(cls):
        return utils.parse_module(cls.name, 'cmd_name', 'load_module')

    @classmethod
    def unload_module_config(cls):
        return utils.parse_module(cls.name, 'cmd_name', 'unload_module')


    def get_cmd(self):
        """Returns the final command line.

        Returns:
        final_cmd: List of command line produced by the object (line breaks not allowed within command lines!).
        """
        run_command = self.run_command
        final_cmd = [run_command]
        for arg, val in self.out_cmd.iteritems():
            final_cmd.append(arg + ' ' + val)
        return [' '.join(final_cmd)]
