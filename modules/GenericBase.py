import copy
import itertools
import logging
import os

from STAPLERerror import STAPLERerror
from STAPLERerror import VirtualIOError
import directory
import utils


class GenericBase():
    """Superclass for STAPLER input classes.

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
    input_types = set([])
    output_types = []
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
        self.in_cmd = in_cmd
        self.out_dir = out_dir
        self.parsed_in_cmd = self._cmd_parse(in_cmd)
        self.out_cmd = copy.deepcopy(self.parsed_in_cmd)
        self._validate_user_input(self.out_cmd)
        self.out_cmd, self.file_names = self._select_IO(self.out_cmd,
                                                        in_dir,
                                                        out_dir)
        #id is defined twice in __init__ since it must be available for
        # _user_override but it may also change in _user_override
        self.id = self._parse_id(self.out_cmd)
        self.out_cmd = self._user_override(self.parsed_in_cmd, self.out_cmd)
        self.out_cmd = self._remove_user_arguments(self.out_cmd)
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
        """Validates the input command of user.

        Arguments:
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
            elif value.startswith('!named_table'):
                new_value = self._parse_named_table(value)
                out_cmd[arg] = new_value
        return out_cmd

    def _parse_2table(self, string):
        """Parses the 2table input.

        Proper format:
        !2table:path

        Arguments:
        string: !2table command.

        Raises:
        STAPLERerror: The !2table format is not correct.

        Returns:
        String read from user defined file.
        """
        if string.count(':') != 1:
            raise STAPLERerror('Invalid !2table format:\n{0}'.format(string))
        path = string.split(':')[1]
        return utils.read_value(path, self.id)

    def _parse_named_table(self, string):
        """Parses the !named_table input.

        Proper format:
        !named_table:path:column_name_1:column_name_2

        Arguments:
        string: !named_table command.

        Raises:
        STAPLERerror: The !named_table format is not correct.

        Returns:
        String read from user defined file.
        """
        if string.count(':') != 3:
            raise STAPLERerror('Invalid !custom_table format:\n{0}'.format(string))
        path = string.split(':')[1]
        column_name_1 = string.split(':')[2]
        column_name_2 = string.split(':')[3]
        return utils.read_value_from_multi_table(path,
                                                 self.id,
                                                 column_name_1,
                                                 column_name_2)

    def _remove_user_arguments(self, out_cmd):
        """Removes the specified arguments from final command line.

        Arguments:
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
        for cmd in parsed_cmd:
            if (cmd not in self.mandatory_args and
                        cmd not in self.user_mandatory_args and
                        cmd not in self.optional_args):
                raise STAPLERerror('Unknown option:\n{0}\n'
                              'on command line:\n{1}'.format(cmd, self.in_cmd))

    def _parse_id(self, parsed_cmd):
        """Returns the bare input file name (id)"""
        input_file_name = parsed_cmd[self.mandatory_args[0]]
        input_file_name = os.path.basename(input_file_name)
        return input_file_name.split('.', 1)[0]

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
            final_cmd.append(arg + ' ' + val)
        return [' '.join(final_cmd)]
