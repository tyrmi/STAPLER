import os

from GenericBase import GenericBase
from STAPLERerror import VirtualIOError
from STAPLERerror import STAPLERerror
import utils

class freebayes(GenericBase):
    """Class for using freebayes.

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

    name = 'freebayes'
    #Accept all defined types:
    input_types = {'.bam'}
    output_types = ['.vcf', '.vcf.gz']
    mandatory_args = ['-b', '-v']
    user_mandatory_args = ['-f', '--!input_files_per_command']
    remove_user_args = ['--!input_files_per_command']
    optional_args = ['-r', '-s', '--populations', '-A', '-L',
                     '--failed-alleles', '--variant-input', '-l',
                     '-haplotype-basis-alleles',
                     '--report-all-haplotype-alleles', '-P', '-_', '-T', '-p',
                     '-J', '-K', '-Z', '--reference-quality', '-4', '-3',
                     '--min-coverage', '-=', '-$', '-a', '-B', '-C', '-D', '-E',
                     '-e', '-F', '-G', '-H', '-I', '-i', '-j', '-k',
                     '-m', '-M', '-n', '-N', '-O', '-q', '-Q', '-R',
                     '-S', '-u', '-U', '-u' '-V', '-w', '-W', '-X',
                     '-x', '-Y', '-z', '--observation-bias',
                     '--report-genotype-likelihood-max',
                     '--genotyping-max-banddepth', '--report-monomorphic',
                     '-t', '--!compress_output']
    parallelizable = True
    help_description = '''
Usage examples of freebayes manual suggest using unix output redirection (>) to
create output files but this implementation uses the parameter -v for
defining the output file.

The --!input_files_per_command should have a value 'all' or 'single'. In the
case of 'all' all bam files in the input directory are included into single
command line. In the case of 'single' each bam file will be processed
separately. Use of 'single' leads to the same result as the default
behaviour in version 15.01.15 and older.

To create compressed output files the --!compress_output parameter can be
included into the command line. The output will be piped to gzip and the output
files will have the .gz filename extension.
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
        IO_files['-b'] = []
        for fl_name, users in in_dir.files.iteritems():
            if self.name in users:
                continue
            if utils.splitext(fl_name)[-1] in self.input_types:
                IO_files['-b'].append(os.path.join(in_dir.path, fl_name))
                in_dir.use_file(fl_name, self.name)
                if self.parsed_in_cmd['--!input_files_per_command'] == \
                        'single':
                    break
                elif not self.parsed_in_cmd['--!input_files_per_command'] \
                        == 'all':
                    raise STAPLERerror('The --!input_files_per_command '
                                      'should have a value "all" or '
                                      '"single"! The current value was: '
                                      '{0}'.format(self.parsed_in_cmd['--!input_files_per_command']))

        if not IO_files['-b']:
            raise VirtualIOError('No more unused input files')

        if '--!compress_output' in out_cmd:
            output_name = utils.splitext(fl_name)[0] + self.output_types[1]
        else:
            output_name = utils.splitext(fl_name)[0] + self.output_types[0]
        output_path = os.path.join(out_dir.path, output_name)
        IO_files['-v'] = output_path
        file_names.add(output_name)
        out_dir.add_file(output_name)
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
            if arg == '--!compress_output': continue
            if arg == '-v': continue
            if arg == '-b':
                for v in val:
                    final_cmd.append(arg + ' ' + v)
            else:
                final_cmd.append(arg + ' ' + val)

        #Include compressed/uncompressed output
        if '--!compress_output' in self.out_cmd:
            final_cmd.append('| gzip > ' + self.out_cmd['-v'])
        else:
            final_cmd.append('> ' + self.out_cmd['-v'])
        return [' '.join(final_cmd)]

		
    def _parse_id(self, parsed_cmd):
        """Returns the bare input file name (id)"""
        cmd = parsed_cmd[self.mandatory_args[0]][0]
        cmd = os.path.basename(cmd)
        return cmd.split('.', 1)[0]


class freebayes_parallel(freebayes):
    """Class for using freebayes_parallel.

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

    name = 'freebayes-parallel'
    #Accept all defined types:
    input_types = {'.bam'}
    output_types = ['.vcf', '.vcf.gz']
    mandatory_args = ['-b', '-v']
    user_mandatory_args = ['-f', '--!input_files_per_command', '--!regions',
                           '--!threads']
    remove_user_args = ['--!input_files_per_command', '--!regions',
                        '--!threads']
    help_description = '''
This tool creates command lines for the freebayes-parallel script included in
freebayes/scripts/freebayes-parallel.

Notice the different mandatory arguments compared to regular freebayes!
The available optional arguments are the same as in regular freebayes,
but some of these may cause issues when parallelized (see
freebayes-parallel manual), so use with caution.

Define path to the region file with --!regions argument.

Define number of threads with --!threads argument.

Usage examples of freebayes manual suggest using unix output redirection (>) to
create output files but this implementation uses the parameter -v for
defining the output file.

The --!input_files_per_command should have a value 'all' or 'single'. In the
case of 'all' all bam files in the input directory are included into single
command line. In the case of 'single' each bam file will be processed
separately. Use of 'single' leads to the same result as the default
behaviour in STAPLER version 15.01.15 and older.
    '''

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
        final_cmd.append(self.parsed_in_cmd['--!regions'])
        final_cmd.append(self.parsed_in_cmd['--!threads'])
        for arg, val in self.out_cmd.iteritems():
            if arg == '-v': continue
            if arg == '-b':
                for v in val:
                    final_cmd.append(arg + ' ' + v)
            else:
                final_cmd.append(arg + ' ' + val)
        final_cmd.append('> ' + self.out_cmd['-v'])
        return [' '.join(final_cmd)]