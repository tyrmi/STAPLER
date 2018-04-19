import os
import subprocess

from GenericBase import GenericBase
from STAPLERerror import STAPLERerror
from STAPLERerror import VirtualIOError
import utils


class bayenv2(GenericBase):
    """Class for using bayenv2.

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

    name = 'bayenv2'
    input_types = set(['.SNPFILEDIR'])
    output_types = ['.bf']
    hidden_mandatory_args = ['-i', '-o', '-e', '-m', '--!SNPFILEDIR_path']
    user_mandatory_args = ['-k', '-p', '-n']
    remove_user_args = []
    user_optional_args = ['-c', '-f', '-r', '-s', '-t', '-x', '-X', '-z']
    parallelizable = True
    help_description = '''
Tested with bayenv2 released in Apr 22 2015.
Input directory and files created with bayenv2_SNPSFILE_breaker.py

NOTICE that it is not necessary to modify the bayenv line from the default in
the config.txt.

This tool can be used to parallelize bayenv2 environmental correlation
testing. This implementation expects the input directory to contain a
subdirectory for each SNPFILE. Each directory should also contain MATRIXFILE,
ENVIRONFILE and the bayenv executable (since bayenv requires input files to
be located in the same directory as the executable). The file names are
expected to be MATRIXFILE.txt, ENVIRONFILE.txt and bayenv2.
Such directory structure can be generated automatically from a single SNPSFILE
by using bayenv2_SNPSFILE_breakear.py (https://github.com/tyrmi/PGU). The
output files generated with -t parameter can be collected into a single
output file with resultmatic.py (https://github.com/tyrmi/PGU).
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
        for sub_dir_name, sub_dir in in_dir.dirs.iteritems():
            if self.name in sub_dir.users: continue
            sub_dir_name = sub_dir_name.rstrip('/')
            if not os.path.splitext(sub_dir_name)[1] in self.input_types: continue
            for fl in sub_dir.files:
                if utils.splitext(fl.name)[1] == '.SNPFILE':
                    if 'MATRIXFILE.txt' not in sub_dir.files:
                        raise STAPLERerror('MATRIXFILE.txt not found in directory {0}'
                                           .format(os.path.join(in_dir.path, sub_dir_name)))
                    if 'ENVIRONFILE.txt' not in sub_dir.files:
                        raise STAPLERerror('ENVIRONFILE.txt not found in directory {0}'
                                           .format(os.path.join(in_dir.path, sub_dir_name)))
                    if 'bayenv2' not in sub_dir.files:
                        raise STAPLERerror('bayenv2 executable not found in directory {0}'
                                           .format(os.path.join(in_dir.path, sub_dir_name)))
                    IO_files['--!SNPFILEDIR_path'] = os.path.join(in_dir.path,
                                                                  sub_dir_name)
                    IO_files['-i'] = fl.name
                    command_ids = utils.infer_path_id(IO_files['-i'])
                    IO_files['-m'] = 'MATRIXFILE.txt'
                    IO_files['-e'] = 'ENVIRONFILE.txt'
                    sub_dir.users.append(self.name)

                    assert len(self.output_types) == 1, 'Several output ' \
                                                        'types, override ' \
                                                        'this method!'
                    output_name = utils.splitext(fl.name)[0]
                    IO_files['-o'] = os.path.join(out_dir.path, output_name)
                    file_names.add(output_name + '.bf')
                    out_dir.add_file(output_name + '.bf', fl.identifier)
                    out_cmd.update(IO_files)
                    return out_cmd, command_ids
        raise VirtualIOError('No more unused input files')


    @classmethod
    def validate_tool_config(cls):
        """Checks if the current tool can be run as defined in config.txt

        """

        # Command is not defined
        devnull = open(os.devnull, 'wb')
        module_unloading_test = '-  '
        command_run_test = 'OK'

        # Test if loading modules works
        if cls.load_module_config():
            try:
                subprocess.check_call(' && '.join(cls.load_module_config()),
                                      shell=True,
                                      stdout=devnull,
                                      stderr=devnull)
                module_loading_test = 'OK'
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

        return [command_run_test, module_loading_test, module_unloading_test]

    def get_cmd(self):
        """Returns the final command line.

        Returns:
        final_cmd: List of command line produced by the object (line breaks not allowed within command lines!).
        """
        bayenv2_command = ['./bayenv2']
        for arg, val in self.out_cmd.iteritems():
            if arg == '--!SNPFILEDIR_path':
                continue
            bayenv2_command.append(arg + ' ' + val)
        bayenv2_command = ' '.join(bayenv2_command)
        return ['cd ' + self.out_cmd['--!SNPFILEDIR_path'],
                'chmod u=rwx bayenv2',
                bayenv2_command]