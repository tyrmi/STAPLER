import os

from GenericBase import GenericBase
from STAPLERerror import VirtualIOError
import utils

class bedtools_coverageBed(GenericBase):
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

    name = 'bedtools_coverageBed'
    input_types = set(['.bam'])
    output_types = ['.coverageBed_out']
    mandatory_args = ['-abam', '--!>']
    user_mandatory_args = []
    remove_user_args = []
    optional_args = ['-d', '-hist', '-s', '-split']
    parallelizable = True
    help_description = '''
Tested with coverageBed v2.17.0
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
                    IO_files['-abam'] = os.path.join(in_dir.path, fl_name)
                    in_dir.use_file(fl_name, self.name)
                    assert len(self.output_types) == 1, 'Several output ' \
                                                        'types, override ' \
                                                        'this method!'

                    output_name = utils.splitext(fl_name)[0] + \
                                  self.output_types[0]
                    output_path = os.path.join(out_dir.path, output_name)
                    IO_files['--!>'] = output_path
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
        for arg, val in self.out_cmd.iteritems():
            if arg != '--!>': continue
            final_cmd.append(arg + ' ' + val)
        final_cmd.append('> ' + self.out_cmd['--!>'])
        return [' '.join(final_cmd)]


class bedtools_multiBamCov(GenericBase):
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

    name = 'bedtools_multiBamCov'
    input_types = set(['.bam'])
    output_types = ['.multiBamCov_out']
    mandatory_args = ['-bams', '--!>']
    user_mandatory_args = ['-bed']
    remove_user_args = ['--!input_all_bams']
    optional_args = ['--!input_all_bams', '-split', '-s', '-S', '-f', '-r',
                     '-q', '-D', '-F', '-p']
    parallelizable = True
    help_description = '''
Tested with coverageBed v2.17.0

If the --!input_all_bams parameter is included in the command, all bam files
found in the input directory are handled in single multiBamCov run. Otherwise,
there will be an output file for each input file.
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
        i = 0
        bam_list = []
        for fl_name, users in in_dir.files.iteritems():
            if self.name not in users:
                if utils.splitext(fl_name)[-1] in self.input_types:
                    i += 1
                    bam_list.append(os.path.join(in_dir.path, fl_name))
                    in_dir.use_file(fl_name, self.name)
                    assert len(self.output_types) == 1, 'Several output ' \
                                                        'types, override ' \
                                                        'this method!'
                    #Single output is created even if several output files
                    # are used
                    if i == 1:
                        output_name = utils.splitext(fl_name)[0] + \
                                      self.output_types[0]
                        output_path = os.path.join(out_dir.path, output_name)
                        IO_files['--!>'] = output_path
                        file_names.add(output_name)
                        out_dir.add_file(output_name)
                    if not '--!input_all_bams' in out_cmd:
                        break
        if not IO_files:
            raise VirtualIOError('No more unused input files')
        IO_files['-bams'] = bam_list
        out_cmd.update(IO_files)
        return out_cmd, file_names

    def _parse_id(self, parsed_cmd):
        """Returns the bare input file name (id)"""
        cmd = parsed_cmd[self.mandatory_args[0]][0]
        cmd = os.path.basename(cmd)
        return cmd.split('.', 1)[0]


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
            if arg == '--!>': continue
            if arg == '-bams':
                final_cmd.append('-bams {0}'.format(' '.join(val)))
                continue
            final_cmd.append(arg + ' ' + val)
        final_cmd.append('> ' + self.out_cmd['--!>'])
        return [' '.join(final_cmd)]
		