import os

from GenericBase import GenericBase
from STAPLERerror import STAPLERerror
from STAPLERerror import VirtualIOError
import utils

class bwa_mem(GenericBase):
    """Class for using BWA MEM algorithm.

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

    name = 'stapler_bwa_mem'
    input_types = {'.fastq', '.fq'}
    output_types = ['.sam']
    hidden_mandatory_args = ['--!fastq1', '--!reference_path', '--!out']
    user_mandatory_args = ['--!reference_path']
    remove_user_args = ['--!read_format']
    user_optional_args = ['--!read_format', '--!fastq2', '-t', '-k', '-w', '-d',
                          '-r', '-c', '-A', '-B', '-O', '-E', '-L', '-U', '-R', '-v',
                          '-M', '-T', '-P', '-p', '-C', '-H']
    parallelizable = True
    help_description = '''
Both paired-end and single-end data can be used as input but not at the same
time. Paired-end mode is used when --!read_format argument is present in the
command line, otherwise single-end data is assumed.

--!read_format argument is mandatory if you have paired-end data.
This argument indicates the format in which read number is shown in
file names. For instance if you have paired end files samplename_R1 and
samplename_R2, the --!read_format argument should look like this:
--!read_format _R?

--!reference_path argument is the path to index database file created by
applying 'bwa index' to your reference fasta file. You must do this manually.
    '''

    def _select_IO(self, out_cmd, in_dir, out_dir):
        """Infers the input and output file paths.

        This method must keep the directory objects up to date of the file
        edits!

        Parameters:
        in_cmd: A dict containing the command line.
        in_dir: Input directory.
        out_dir: Output directory.

        Returns:
        out_cmd: Dict containing the output commands
        command_identifier: Input file name based identifier for the current command

        Raises:
        VirtualIOError: No valid input file can be found.
        """
        command_ids = []
        if '--!reference_path' not in self.parsed_in_cmd:
            raise STAPLERerror('--!reference_path argument is required for this '
                               'command!')
        if not os.path.isfile(self.parsed_in_cmd['--!reference_path']):
            raise STAPLERerror('The path to reference file does not exist:\n{0}'
                               .format(self.parsed_in_cmd['--!reference_path']))

        read_format = ''
        for arg, value in out_cmd.iteritems():
            if arg == '--!read_format':
                read_format = value
                break

        if read_format:
            if read_format.count('?') != 1:
                raise STAPLERerror('{0} needs a one "?" in --!read_format argument!'
                                   .format(self.name))
            if len(read_format) < 2:
                raise STAPLERerror('{0} argument --!read_format value should have '
                                   'length of at least 2!'
                                   .format(self.name))
            del out_cmd[arg]

        IO_files = {}
        #Handle paired end files
        if read_format:
            paired_files = in_dir.file_pairs(pattern=self.parsed_in_cmd['--!read_format'],
                                             user=self.name,
                                             file_formats=list(self.input_types),
                                             exclusion_iterable=['pairless',
                                                                 'unmatched'])
            file_names = set()
            for pair in paired_files:
                pair1, pair2 = pair
                if self.name not in in_dir.file_names[pair1].users and self.name not in in_dir.file_names[pair2].users:
                    #Infer inputs
                    IO_files['--!fastq1'] = os.path.join(in_dir.path, pair1)
                    command_ids.append(utils.infer_path_id(IO_files['--!fastq1']))
                    in_dir.use_file(pair1, self.name)
                    IO_files['--!fastq2'] = os.path.join(in_dir.path, pair2)
                    command_ids.append(utils.infer_path_id(IO_files['--!fastq2']))
                    in_dir.use_file(pair2, self.name)

                    #Infer output
                    output_name = utils.splitext(pair1)[0]
                    output_name = output_name.replace(self.parsed_in_cmd[
                                                          '--!read_format'],
                                                      '')
                    output_name += self.output_types[0]
                    output_path = os.path.join(out_dir.path, output_name)
                    IO_files['--!out'] = output_path
                    file_names.add(output_name)
                    out_dir.add_file(output_name)
                    break
        else: #Handle single end files
            file_names = set()
            for fl in in_dir.files:
                if self.name not in fl.users:
                    if utils.splitext(fl.name)[-1] in self.input_types:
                        IO_files['--!fastq1'] = os.path.join(in_dir.path, fl.name)
                        command_ids.append(utils.infer_path_id(IO_files['--!fastq1']))
                        in_dir.use_file(fl.name, self.name)
                        assert len(self.output_types) == 1, 'Several output ' \
                                                            'types, override ' \
                                                            'this method!'

                        output_name = utils.splitext(fl.name)[0] + \
                                      self.output_types[0]
                        output_path = os.path.join(out_dir.path, output_name)
                        IO_files['--!out'] = output_path
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
            if arg in ['--!reference_path',
                       '--!fastq1',
                       '--!fastq2',
                       '--!out']:
                continue
            final_cmd.append(arg + ' ' + val)
        final_cmd.append(self.out_cmd['--!reference_path'])
        final_cmd.append(self.out_cmd['--!fastq1'])
        if '--!fastq2' in self.out_cmd:
            final_cmd.append(self.out_cmd['--!fastq2'])
        final_cmd.append('> ' + self.out_cmd['--!out'])
        return [' '.join(final_cmd)]



class bwa_bwasw(GenericBase):
    """Class for using BWA MEM algorithm.

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

    name = 'stapler_bwa_bwasw'
    input_types = {'.fastq', '.fq'}
    output_types = ['.sam']
    hidden_mandatory_args = ['--!fastq1', '--!reference_path', '--!out']
    user_mandatory_args = ['--!reference_path']
    remove_user_args = []
    user_optional_args = ['--!read_format', '-a', '-b', '-q', '-r', '-w', '-m',
                          '-t', '-H', '-C', '-M', '-S', '-I', '-T', '-c', '-z',
                          '-s', '-N', '-G']
    parallelizable = True
    help_description = '''
Both paired-end and single-end data can be used as input but not at the same
time. Paired-end mode is used when --!read_format argument is present in the
command line, otherwise single-end data is assumed.

--!read_format argument is mandatory if you have paired-end data.
This argument indicates the format in which read number is shown in
file names. For instance if you have paired end files samplename_R1 and
samplename_R2, the --!read_format argument should look like this:
--!read_format _R?

--!reference_path argument is the path to index database file created by
applying 'bwa index' to your reference fasta file. You must do this manually.
    '''

    def _select_IO(self, out_cmd, in_dir, out_dir):
        """Infers the input and output file paths.

        This method must keep the directory objects up to date of the file
        edits!

        Parameters:
        in_cmd: A dict containing the command line.
        in_dir: Input directory.
        out_dir: Output directory.

        Returns:
        out_cmd: Dict containing the output commands
        command_identifier: Input file name based identifier for the current command

        Raises:
        VirtualIOError: No valid input file can be found.
        """
        command_ids = []
        if '--!reference_path' not in self.parsed_in_cmd:
            raise STAPLERerror('--!reference_path argument is required for this '
                               'command!')
        if not os.path.isfile(self.parsed_in_cmd['--!reference_path']):
            raise STAPLERerror('The path to reference file does not exist:\n{0}'
                               .format(self.parsed_in_cmd['--!reference_path']))

        read_format = ''
        for arg, value in out_cmd.iteritems():
            if arg == '--!read_format':
                read_format = value
                break

        if read_format:
            if read_format.count('?') != 1:
                raise STAPLERerror('{0} needs a one "?" in --!read_format argument!'
                                   .format(self.name))
            if len(read_format) < 2:
                raise STAPLERerror('{0} argument --!read_format value should have '
                                   'length of at least 2!'
                                   .format(self.name))
            del out_cmd[arg]

        IO_files = {}
        #Handle paired end files
        if read_format:
            paired_files = in_dir.file_pairs(pattern=self.parsed_in_cmd['--!read_format'],
                                             user=self.name,
                                             file_formats=list(self.input_types),
                                             exclusion_iterable=['pairless',
                                                                 'unmatched'])
            file_names = set()
            for pair in paired_files:
                pair1, pair2 = pair
                if self.name not in in_dir.file_names[pair1].users and self.name not in in_dir.file_names[pair2].users:
                    #Infer inputs
                    IO_files['--!fastq1'] = os.path.join(in_dir.path, pair1)
                    command_ids.append(utils.infer_path_id(IO_files['--!fastq1']))
                    in_dir.use_file(pair1, self.name)
                    IO_files['--!fastq2'] = os.path.join(in_dir.path, pair2)
                    command_ids.append(utils.infer_path_id(IO_files['--!fastq2']))
                    in_dir.use_file(pair2, self.name)

                    #Infer output
                    output_name = utils.splitext(pair1)[0]
                    output_name = output_name.replace(self.parsed_in_cmd[
                                                          '--!read_format'],
                                                      '')
                    output_name += self.output_types[0]
                    output_path = os.path.join(out_dir.path, output_name)
                    IO_files['--!out'] = output_path
                    file_names.add(output_name)
                    out_dir.add_file(output_name)
                    break
        else: #Handle single end files
            file_names = set()
            for fl in in_dir.files:
                if self.name not in fl.users:
                    if utils.splitext(fl.name)[-1] in self.input_types:
                        IO_files['--!fastq1'] = os.path.join(in_dir.path, fl.name)
                        command_ids.append(utils.infer_path_id(IO_files['--!fastq']))
                        in_dir.use_file(fl.name, self.name)
                        assert len(self.output_types) == 1, 'Several output ' \
                                                            'types, override ' \
                                                            'this method!'

                        output_name = utils.splitext(fl.name)[0] + \
                                      self.output_types[0]
                        output_path = os.path.join(out_dir.path, output_name)
                        IO_files['--!out'] = output_path
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
            if arg in ['--!reference_path',
                       '--!fastq1',
                       '--!fastq2',
                       '--!out']:
                continue
            final_cmd.append(arg + ' ' + val)
        final_cmd.append(self.out_cmd['--!reference_path'])
        final_cmd.append(self.out_cmd['--!fastq1'])
        if '--!fastq2' in self.out_cmd:
            final_cmd.append(self.out_cmd['--!fastq2'])
        final_cmd.append('> ' + self.out_cmd['--!out'])
        return [' '.join(final_cmd)]