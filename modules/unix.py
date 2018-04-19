import copy
import itertools
import logging
import os

from GenericBase import GenericBase
from STAPLERerror import STAPLERerror
from STAPLERerror import VirtualIOError
import directory
import utils


class gzip(GenericBase):
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

    name = 'gzip'
    input_types = set([])
    output_types = []
    require_output_dir = False
    hidden_mandatory_args = ['-!i']
    user_mandatory_args = []
    remove_user_args = user_mandatory_args
    user_optional_args = ['-1', '-2', '-3', '-4', '-5', '-6', '-7', '-8', '-9',
                          '-d', '-f', '-k', '-N', '-n', '-q', '-r', '-v', '--fast',
                          '--best', '--stdout', '--decompress', '--uncompress',
                          '--force', '--keep', '--name', '--no-name', '--quiet',
                          '--recursive', '--verbose']
    parallelizable = True
    help_description = '''
This implementation of gzip compresses or decompresses the contents of input 
directory. (De)Compressed files replace the input files in the input directory,
therefore output directory is not created.

When compressing files any file type is a valid input. When decompressing
(i.e. when -d, --uncompress or --decompress parameters are present) only files
with .gz file extension are used as an input.
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
                if '-d' in out_cmd or '--decompress' in out_cmd or '--uncompress' in out_cmd: # Decompress input file, is .gz ending
                    if os.path.splitext(fl.name)[1] != '.gz': continue
                    output_name = os.path.splitext(fl.name)[0]
                else: # Compress input file, must not have .gz ending
                    output_name = fl.name + '.gz'
                    if os.path.splitext(fl.name)[1] == '.gz': continue

                IO_files['-!i'] = os.path.join(in_dir.path, fl.name)
                command_ids = [utils.infer_path_id(IO_files['-!i'])]
                in_dir.use_file(fl.name, self.name)
                assert len(self.output_types) < 2, 'Several output ' \
                                                   'types, override ' \
                                                   'this method!'
                file_names.add(output_name)
                in_dir.rm_file(fl.name)
                in_dir.add_file(output_name)
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
        final_cmd.append(self.out_cmd['-!i'])
        for arg, val in self.out_cmd.iteritems():
            if arg == '-!i': continue
            print arg, val
            final_cmd.append(arg + ' ' + val)
        return [' '.join(final_cmd)]
