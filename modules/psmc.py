import os

from GenericBase import GenericBase
from STAPLERerror import VirtualIOError
from STAPLERerror import STAPLERerror
import utils

class psmc_fq2psmcfa(GenericBase):
    """Class for using fq2psmcfa.

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

    name = 'psmc_fq2psmcfa'
    input_types = set(['.fq', '.fq.gz'])
    output_types = ['.psmcfa']
    hidden_mandatory_args = ['-!i', '->']
    user_mandatory_args = []
    remove_user_args = user_mandatory_args
    user_optional_args = ['-c', '-n', '-v', '-x', '-q', '-g', '-s']
    parallelizable = True
    help_description = '''
This utility script is part of psmc software (.../psmc/utils/fq2psmcfa).
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
                    IO_files['-!i'] = os.path.join(in_dir.path, fl.name)
                    command_ids = [utils.infer_path_id(IO_files['-!i'])]
                    in_dir.use_file(fl.name, self.name)
                    assert len(self.output_types) == 1, 'Several output ' \
                                                        'types, override ' \
                                                        'this method!'

                    output_name = utils.splitext(fl.name)[0] + \
                                  self.output_types[0]
                    output_path = os.path.join(out_dir.path, output_name)
                    IO_files['->'] = output_path
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
        for arg, val in self.out_cmd.iteritems():
            if arg in ('-!i', '->'): continue
            final_cmd.append(arg + ' ' + val)
        final_cmd.append(self.out_cmd['-!i'])
        final_cmd.append('>' + ' ' + self.out_cmd['->'])
        return [' '.join(final_cmd)]


class psmc(GenericBase):
    """Class for using psmc.

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

    name = 'psmc'
    input_types = set(['.psmcfa'])
    output_types = ['.psmc']
    hidden_mandatory_args = ['-!i', '-o']
    user_mandatory_args = []
    remove_user_args = user_mandatory_args
    user_optional_args = ['-p', '-t', '-N', '-r', '-c', '-i', '-T', '-b', '-S',
                          '-d', '-D']
    parallelizable = True
    help_description = '''
The main psmc software. Tested with psmc version 0.6.5-r67.

One workflow possibility by using tools with STAPLER supported tools is to
chain commands vcf2fastq, fq2psmcfa and psmc. psmc_plot, psmc2history and
history2ms tools can then be used to further work with the outputs.
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
                    IO_files['-!i'] = os.path.join(in_dir.path, fl.name)
                    command_ids = [utils.infer_path_id(IO_files['-!i'])]
                    in_dir.use_file(fl.name, self.name)
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

    def get_cmd(self):
        """Returns the final command line.

        Returns:
        final_cmd: List of command line produced by the object (line breaks not allowed within command lines!).
        """
        run_command = utils.parse_config(self.name, 'cmd_name', 'execute')
        final_cmd = [run_command]
        for arg, val in self.out_cmd.iteritems():
            if arg in ('-!i', '-o'): continue
            final_cmd.append(arg + ' ' + val)
        final_cmd.append('-o' + ' ' + self.out_cmd['-o'])
        final_cmd.append(self.out_cmd['-!i'])
        return [' '.join(final_cmd)]


class psmc_plot(GenericBase):
    """Class for using psmc_plot.

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

    name = 'psmc_plot'
    input_types = set(['.psmc'])
    output_types = ['.psmc_plot']
    hidden_mandatory_args = ['-!i', '-!o']
    user_mandatory_args = []
    remove_user_args = user_mandatory_args
    user_optional_args = ['-u', '-s', '-X', '-x', '-Y', '-m', '-n', '-M', '-f',
                          '-g', '-w', '-P', '-T', '-N', '-S', '-L', '-p', '-R',
                          '-G']
    parallelizable = True
    help_description = '''
This utility script is part of psmc software (.../psmc/utils/psmc_plot.pl).
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
                    IO_files['-!i'] = os.path.join(in_dir.path, fl.name)
                    command_ids = [utils.infer_path_id(IO_files['-!i'])]
                    in_dir.use_file(fl.name, self.name)
                    assert len(self.output_types) == 1, 'Several output ' \
                                                        'types, override ' \
                                                        'this method!'

                    output_name = utils.splitext(fl.name)[0] + \
                                  self.output_types[0]
                    output_path = os.path.join(out_dir.path, output_name)
                    IO_files['-!o'] = output_path
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
        for arg, val in self.out_cmd.iteritems():
            if arg in ('-!i', '-!o'): continue
            final_cmd.append(arg + ' ' + val)
        final_cmd.append(self.out_cmd['-!o'])
        final_cmd.append(self.out_cmd['-!i'])
        return [' '.join(final_cmd)]


class psmc2history(GenericBase):
    """Class for using psmc2history.

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

    name = 'psmc2history'
    input_types = set(['.psmc'])
    output_types = ['.psmchistory']
    hidden_mandatory_args = ['-!i', '->']
    user_mandatory_args = []
    remove_user_args = user_mandatory_args
    user_optional_args = ['-n']
    parallelizable = True
    help_description = '''
This utility script is part of psmc software (.../psmc/utils/psmc2history.pl).
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
                    IO_files['-!i'] = os.path.join(in_dir.path, fl.name)
                    command_ids = [utils.infer_path_id(IO_files['-!i'])]
                    in_dir.use_file(fl.name, self.name)
                    assert len(self.output_types) == 1, 'Several output ' \
                                                        'types, override ' \
                                                        'this method!'

                    output_name = utils.splitext(fl.name)[0] + \
                                  self.output_types[0]
                    output_path = os.path.join(out_dir.path, output_name)
                    IO_files['->'] = output_path
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
        for arg, val in self.out_cmd.iteritems():
            if arg in ('-!i', '->'): continue
            final_cmd.append(arg + ' ' + val)
        final_cmd.append(self.out_cmd['-!i'])
        final_cmd.append('>' + ' ' + self.out_cmd['->'])
        return [' '.join(final_cmd)]


class psmc_history2ms(GenericBase):
    """Class for using history2ms.

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

    name = 'psmc_history2ms'
    input_types = set(['.psmchistory'])
    output_types = ['.ms_cmd']
    hidden_mandatory_args = ['-!i', '->']
    user_mandatory_args = []
    remove_user_args = user_mandatory_args
    user_optional_args = ['-n', '-L', '-s', '-u', '-R', '-g', '-d', '-r', '-M']
    parallelizable = True
    help_description = '''
This utility script is part of psmc software (.../psmc/utils/history2ms.pl).
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
                    IO_files['-!i'] = os.path.join(in_dir.path, fl.name)
                    command_ids = [utils.infer_path_id(IO_files['-!i'])]
                    in_dir.use_file(fl.name, self.name)
                    assert len(self.output_types) == 1, 'Several output ' \
                                                        'types, override ' \
                                                        'this method!'

                    output_name = utils.splitext(fl.name)[0] + \
                                  self.output_types[0]
                    output_path = os.path.join(out_dir.path, output_name)
                    IO_files['->'] = output_path
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
        for arg, val in self.out_cmd.iteritems():
            if arg in ('-!i', '->'): continue
            final_cmd.append(arg + ' ' + val)
        final_cmd.append(self.out_cmd['-!i'])
        final_cmd.append('>' + ' ' + self.out_cmd['->'])
        return [' '.join(final_cmd)]