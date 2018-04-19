import os

from GenericBase import GenericBase
from STAPLERerror import VirtualIOError
from STAPLERerror import STAPLERerror
import utils


class samtools_index(GenericBase):
    """Class for creating command lines for samtools index.

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

    name = 'samtools_index'
    #Accept all defined types:
    input_types = {'.bam'}
    output_types = []
    require_output_dir = False
    hidden_mandatory_args = ['--!i']
    user_mandatory_args = []
    remove_user_args = user_mandatory_args
    user_optional_args = ['-b', '-c', '-m']
    parallelizable = True
    help_description = '''
Tested with samtools 1.2.

The index files are generated into the input directory.
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
                    # Infer input file
                    IO_files['--!i'] = os.path.join(in_dir.path, fl.name)
                    command_ids = [utils.infer_path_id(IO_files['--!i'])]
                    in_dir.use_file(fl.name, self.name)

                    # Add index file to the input directory
                    in_dir.add_file(fl.name + '.bai')
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
            if arg in {'--!i', '--!o'}: continue
            final_cmd.append(arg + ' ' + val)
        final_cmd.append(self.out_cmd['--!i'])
        return [' '.join(final_cmd)]


class samtools_rmdup(GenericBase):
    """Class for creating command lines for samtools rmdup.

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

    name = 'samtools_rmdup'
    #Accept all defined types:
    input_types = {'.bam'}
    output_types = ['.bam']
    hidden_mandatory_args = ['--!i', '--!o']
    user_mandatory_args = []
    remove_user_args = user_mandatory_args
    user_optional_args = ['-s', '-S']
    parallelizable = True
    help_description = '''
Tested with samtools 0.1.19

Notice that this function does not seem to work in the current version of
samtools (1.2), use of older version is therefore recommended. Beware module
conflicts!
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
                    IO_files['--!i'] = os.path.join(in_dir.path, fl.name)
                    command_ids = [utils.infer_path_id(IO_files['--!i'])]
                    in_dir.use_file(fl.name, self.name)
                    assert len(self.output_types) == 1, 'Several output ' \
                                                        'types, override ' \
                                                        'this method!'

                    output_name = utils.splitext(fl.name)[0] + \
                                  self.output_types[0]
                    output_path = os.path.join(out_dir.path, output_name)
                    IO_files['--!o'] = output_path
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
        final_cmd.append(self.out_cmd['--!i'])
        final_cmd.append(self.out_cmd['--!o'])
        for arg, val in self.out_cmd.iteritems():
            if arg in {'--!i', '--!o'}: continue
            final_cmd.append(arg + ' ' + val)
        return [' '.join(final_cmd)]

