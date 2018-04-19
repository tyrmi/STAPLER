import os

from GenericBase import GenericBase
from STAPLERerror import VirtualIOError
from STAPLERerror import STAPLERerror
import utils


class bcftools_call(GenericBase):
    """Class for creating command lines for BCFtools call.

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

    name = 'bcftools_call'
    #Accept all defined types:
    input_types = {'.vcf', '.vcf.gz', '.bcf', '.bcf.gz'}
    output_types = ['.vcf', '.bcf']
    require_output_dir = True
    hidden_mandatory_args = ['--!i', '--!o']
    user_mandatory_args = []
    remove_user_args = []
    user_optional_args = ['--chromosome-X', '--chromosome-Y',
                          '--consensus-caller', '--constrain', '--format-fields',
                          '--gvcf', '--insert-missed', '--keep-alts',
                          '--keep-masked-ref', '--multiallelic-caller',
                          '--no-version', '--novel-rate', '--ploidy',
                          '--ploidy-file', '--prior',
                          '--prior-freqs', '--pval-threshold', '--regions',
                          '--regions-file', '--samples', '--samples-file',
                          '--skip-variants', '--targets', '--targets',
                          '--targets-file', '--threads', '--variants-only', '-A',
                          '-c', '-C', '-f', '-F', '-g', '-i', '-M', '-m', '-n',
                          '-p', '-P', '-r', '-R', '-s', '-S', '-t', '-T', '-t',
                          '-V', '-v', '-X', '-Y', '-Ob', '-Ou', '-Oz', '-Ov']
    parallelizable = True
    help_description = '''
Tested with samtools 1.7.

The output file type needs to be defined by including -Ob, -Ou, -Oz or -Ov
parameters.
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
            if self.name in fl.users:
                continue
            if utils.splitext(fl.name)[-1] in self.input_types:
                IO_files['--!i'] = os.path.join(in_dir.path, fl.name)
                in_dir.use_file(fl.name, self.name)
                break

        if '--!i' not in IO_files:
            raise VirtualIOError('No more unused input files')

        # Infer output path
        output_name = os.path.split(IO_files['--!i'])[1]
        output_name = utils.splitext(output_name)[0]
        if '-Oz' in out_cmd or '-Ov' in out_cmd:
            output_name += '.vcf'
        elif '-Ob' in out_cmd or '-Ou' in out_cmd:
            output_name += '.bcf'
        else:
            raise STAPLERerror('{0} command output type needs to be defined '
                               'by including one of the following parameters: '
                               '-Ob, -Ou, -Oz or -Ov'.format(self.name))
        output_path = os.path.join(out_dir.path, output_name)
        IO_files['--!o'] = output_path
        file_names.add(output_name)
        out_dir.add_file(output_name)
        out_cmd.update(IO_files)
        command_ids = [utils.infer_path_id(IO_files['--!i'])]
        return out_cmd, command_ids


    def get_cmd(self):
        """Returns the final command line.

        Returns:
        final_cmd: List of command line produced by the object (line breaks not allowed within command lines!).
        """
        run_command = utils.parse_config(self.name, 'cmd_name', 'execute')
        final_cmd = [run_command]
        for arg, val in self.out_cmd.iteritems():
            if arg == '--!o': continue
            if arg == '--!i': continue
            final_cmd.append(arg + ' ' + val)

        final_cmd.append(self.out_cmd['--!i'])
        final_cmd.append('> ' + self.out_cmd['--!o'])
        return [' '.join(final_cmd)]


class bcftools_mpileup(GenericBase):
    """Class for creating command lines for BCFtools mpileup.

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

    name = 'bcftools_mpileup'
    #Accept all defined types:
    input_types = {'.bam'}
    output_types = ['.vcf', '.bcf']
    require_output_dir = True
    hidden_mandatory_args = ['--!i', '--!o']
    user_mandatory_args = ['-f', '--!input_files_per_command']
    remove_user_args = ['--!input_files_per_command']
    user_optional_args = ['--adjust-MQ', '--annotate', '--bam-list',
                          '--count-orphans', '--excl-flags', '--ext-prob',
                          '--fasta-ref', '--ff', '--gap-frac', '--gvcf',
                          '--ignore-overlaps', '--ignore-RG', '--illumina1.3+',
                          '--incl-flags', '--max-depth', '--max-idepth',
                          '--min-BQ', '--min-ireads', '--no-BAQ',
                          '--no-reference', '--no-version', '--open-prob',
                          '--output', '--per-sample-mF', '--platforms',
                          '--read-groups', '--redo-BAQ', '--regions', '--regions',
                          '--regions-file', '--rf', '--samples', '--samples-file',
                          '--skip-indels', '--tandem-qual', '--targets',
                          '--targets-file', '--threads', '-6', '-A', '-a', '-b',
                          '-B', '-C', '-d', '-E', '-e', '-f', '-F', '-G', '-g',
                          '-I', '-L', '-m', '--min-MQ', '-p', '-P',
                          '-q', '-Q', '-r', '-R', '-s', '-S', '-t', '-T', '-x',
                          '-Ob', '-Ou', '-Oz', '-Ov']
    parallelizable = True
    help_description = '''
Tested with samtools 1.7.

Determine the output file format by using -Ob, -Ou, -Oz or -Ov parameter.
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
        IO_files['--!i'] = []
        for fl in in_dir.files:
            if self.name in fl.users:
                continue
            if utils.splitext(fl.name)[-1] in self.input_types:
                IO_files['--!i'].append(os.path.join(in_dir.path, fl.name))
                in_dir.use_file(fl.name, self.name)
                if self.parsed_in_cmd['--!input_files_per_command'] == \
                        'single':
                    break
                elif not self.parsed_in_cmd['--!input_files_per_command'] \
                        == 'all':
                    raise STAPLERerror('The --!input_files_per_command '
                                       'should have a value "all" or '
                                       '"single"! The current value was: '
                                       '{0}'.format(self.parsed_in_cmd['--!input_files_per_command']))

        if not IO_files['--!i']:
            raise VirtualIOError('No more unused input files')

        # Make sure that input files are sorted so that first input file is the same on successive runs
        if out_cmd['--!input_files_per_command'] == 'all':
            output_name = os.path.split(sorted(IO_files['--!i'])[0])[1]
        else:
            output_name = os.path.split(IO_files['--!i'][0])[1]

        # Infer output path
        output_name = utils.splitext(output_name)[0]
        if '-Oz' in out_cmd or '-Ov' in out_cmd:
            output_name += '.vcf'
        elif '-Ob' in out_cmd or '-Ou' in out_cmd:
            output_name += '.bcf'
        else:
            raise STAPLERerror('{0} command output type needs to be defined '
                               'by including one of the following parameters: '
                               '-Ob, -Ou, -Oz or -Ov'.format(self.name))

        output_path = os.path.join(out_dir.path, output_name)
        IO_files['--!o'] = output_path
        file_names.add(output_name)
        out_dir.add_file(output_name)
        out_cmd.update(IO_files)
        command_ids = map(utils.infer_path_id, IO_files['--!i'])
        return out_cmd, command_ids


    def get_cmd(self):
        """Returns the final command line.

        Returns:
        final_cmd: List of command line produced by the object (line breaks not allowed within command lines!).
        """
        run_command = utils.parse_config(self.name, 'cmd_name', 'execute')
        final_cmd = [run_command]
        for arg, val in self.out_cmd.iteritems():
            if arg == '--!o': continue
            if arg == '--!i': continue
            final_cmd.append(arg + ' ' + val)

        for bam_path in self.out_cmd['--!i']:
            final_cmd.append(bam_path)
        final_cmd.append('> ' + self.out_cmd['--!o'])
        return [' '.join(final_cmd)]