import logging
import os

from GenericBase import GenericBase
from STAPLERerror import STAPLERerror
from STAPLERerror import VirtualIOError
import utils

class fastqc(GenericBase):
    """Class for generic command lines, also superclass for STAPLER input classes.

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

    name = 'fastqc'
    #Accept all defined types:
    input_types = {'.bam', '.fastq'}
    output_types = ['.unknown']
    mandatory_args = ['-!i', '-o']
    user_mandatory_args = []
    remove_user_args = user_mandatory_args
    optional_args = ['--casava', '--extract', '--java', '--noextract',
                     '--nogroup', '--format', '--threads', '--contaminants',
                     '--kmers', '--quiet']
    parallelizable = True
    help_description = '''
Tested with FastQC v0.10.1.

STAPLER creates a single command line for each input file instead
of defining all input files in single command. Normally this has no effect
on the end user, but allows one to use for instance !2tables as a part of
these commands.
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
                    IO_files['-!i'] = os.path.join(in_dir.path, fl_name)
                    in_dir.use_file(fl_name, self.name)
                    assert len(self.output_types) == 1, 'Several output ' \
                                                        'types, override ' \
                                                        'this method!'
                    IO_files['-o'] = out_dir.path
                    file_names.add(fl_name)
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
        final_cmd.append(self.out_cmd['-!i'])
        for arg, val in self.out_cmd.iteritems():
            if arg == '-!i': continue
            final_cmd.append(arg + ' ' + val)
        return [' '.join(final_cmd)]
		