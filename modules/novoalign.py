import os

from GenericBase import GenericBase
from STAPLERerror import STAPLERerror
from STAPLERerror import VirtualIOError
import utils

class novoalign(GenericBase):
    """Class for using BWA MEM algorithm.

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

    name = 'novoalign'
    input_types = {'.fastq'}
    output_types = ['.sam']
    mandatory_args = ['-f', '-d', '--!out']
    user_mandatory_args = ['-d', '--!read_format']
    remove_user_args = ['--!read_format']
    optional_args = ['--mmapoff', '--lockidx', '--hdrhd', '-F',
                     '-#', '-t', '-g', '-x', '-l', '-h', '-H', '--Q2Off',
                     '-a', '-n', '-s', '-5', '-s', '-o', '--softclip',
                     '--3Prime', '-R', '-r', '-e', '-q', '-rNMOri', '-nonC',
                     '--amplicons', '-i', '-v', '-m', '-k', '-K', '--rOQ',
                     '-rNMOri', '-hpstats']
    parallelizable = True
    help_description = '''
This tool allows only paired end reads to be aligned.

--!d argument is the path to index database file created by using
'novoindex' to your reference fasta file. You must do this manually.

--!read_format argument indicates the format in which read number is shown in
file names. For instance if you have paired end files samplename_R1 and
samplename_R2, the --!read_format argument should look like this:
--!read_format _R?
    '''


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

        read_format = ''
        for arg, value in out_cmd.iteritems():
            if arg == '--!read_format':
                read_format = value
                break

        if not read_format:
            raise STAPLERerror('{0} command needs a "--!read_format" argument!'
                               .format(self.name))
        if read_format.count('?') != 1:
            raise STAPLERerror('{0} needs a one "?" in --!read_format argument!'
                               .format(self.name))
        if len(read_format) < 2:
            raise STAPLERerror('{0} argument --!read_format value should have '
                          'length of at least 2!'
                               .format(self.name))
        del out_cmd[arg]

        paired_files = utils.find_pairs(in_dir,
                                        pattern=self.parsed_in_cmd[
                                            '--!read_format'],
                                        user=self.name,
                                        file_format=list(self.input_types)[0],
                                        exclusion_iterable=['pairless',
                                                            'unmatched'])
        if not paired_files:
            raise VirtualIOError('{0} argument did not find any pairs from'
                                 'folder {1}'.format(self.name, in_dir.path))

        IO_files = {}
        file_names = set()
        for pair in paired_files:
            pair1, pair2 = pair

            #Infer inputs
            IO_files['-f'] = os.path.join(in_dir.path, pair1) + ' ' + \
                             os.path.join(in_dir.path, pair2)
            in_dir.use_file(pair1, self.name)
            in_dir.use_file(pair2, self.name)

            #Infer output
            output_name = utils.splitext(pair1)[0]
            output_name = output_name.replace(self.parsed_in_cmd['--!read_format'],
                                              '')
            output_name += self.output_types[0]
            output_path = os.path.join(out_dir.path, output_name)
            IO_files['--!out'] = output_path
            file_names.add(output_name)
            out_dir.add_file(output_name)
            break
        if not IO_files:
            raise VirtualIOError('No more unused input files')
        out_cmd.update(IO_files)
        return out_cmd, file_names

    def _parse_id(self, parsed_cmd):
        """Returns the bare input file name (id)"""
        cmd = self.out_cmd['-f']
        cmd = cmd.split(' ')[0]
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
            if arg == '--!out': continue
            final_cmd.append(arg + ' ' + val)
        final_cmd.append('> ' + self.out_cmd['--!out'])
        return [' '.join(final_cmd)]
		