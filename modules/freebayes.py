import os

from GenericBase import GenericBase
from STAPLERerror import VirtualIOError
from STAPLERerror import STAPLERerror
import utils

class freebayes(GenericBase):
    """Class for using freebayes.

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

    name = 'stapler_freebayes'
    #Accept all defined types:
    input_types = {'.bam'}
    output_types = ['.vcf', '.vcf.gz']
    hidden_mandatory_args = ['-b', '-v']
    user_mandatory_args = ['-f', '--!input_files_per_command']
    remove_user_args = ['--!input_files_per_command']
    user_optional_args = ['--allele-balance-priors-off',
                          '--base-quality-cap', '--binomial-obs-priors-off',
                          '--cnv-map', '--contamination-estimates', '--debug',
                          '--dont-left-align-indels',
                          '--exclude-unobserved-genotypes', '--fasta-reference',
                          '--genotype-qualities', '--genotype-variant-threshold',
                          '--genotyping-max-banddepth',
                          '--genotyping-max-iterations', '--gvcf', '--gvcf-chunk',
                          '--haplotype-basis-alleles', '--haplotype-length',
                          '--harmonic-indel-quality', '--hwe-priors-off',
                          '--legacy-gls', '--max-complex-gap', '--max-coverage',
                          '--min-alternate-count', '--min-alternate-fraction',
                          '--min-alternate-qsum', '--min-alternate-total',
                          '--min-base-quality', '--min-coverage',
                          '--min-mapping-quality', '--min-repeat-entropy',
                          '--min-repeat-size', '--min-supporting-allele-qsum',
                          '--min-supporting-mapping-qsum',
                          '--mismatch-base-quality-threshold', '--no-complex',
                          '--no-indels', '--no-mnps', '--no-partial-observations',
                          '--no-population-priors', '--no-snps',
                          '--observation-bias', '--only-use-input-alleles',
                          '--ploidy', '--pooled-continuous', '--pooled-discrete',
                          '--populations', '--posterior-integration-limits',
                          '--prob-contamination', '--pvar',
                          '--read-dependence-factor', '--read-indel-limit',
                          '--read-max-mismatch-fraction', '--read-mismatch-limit',
                          '--read-snp-limit', '--reference-quality', '--region',
                          '--report-all-haplotype-alleles',
                          '--report-genotype-likelihood-max',
                          '--report-monomorphic', '--samples',
                          '--standard-filters', '--strict-vcf',
                          '--targets', '--theta', '--use-best-n-alleles',
                          '--use-duplicate-reads', '--use-mapping-quality',
                          '--use-reference-allele', '--variant-input', '--vcf',
                          '-@', '-=', '-$', '-0', '-3', '-4', '-a', '-A',
                          '-B', '-C', '-d', '-D', '-dd', '-E', '-e',
                          '-F', '-G', '-H', '-i', '-I', '-J', '-j', '-k', '-K',
                          '-l', '-m', '-N', '-n', '-O', '-p', '-P', '-q',
                          '-Q', '-R', '-r', '-S', '-s', '-t', '-T', '-u', '-U',
                          '-V', '-w', '-W', '-X', '-Y', '-z', '-Z',
                          '--!compress_output']
    parallelizable = True
    help_description = '''
Tested with freebayes v1.1.0-54-g49413aa

The --!input_files_per_command should have a value 'all' or 'single'. In the
case of 'all' all bam files in the input directory are included into single
command line, producing a single output file. In the case of 'single' each
bam file will be processed separately, producing an output file for every
input file.

To create compressed output files the --!compress_output parameter can be
included into the command line. The output will be piped to gzip and the
output files will have the .gz filename extension.
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
        IO_files['-b'] = []
        for fl in in_dir.files:
            if self.name in fl.users:
                continue
            if utils.splitext(fl.name)[-1] in self.input_types:
                # Save the name of the first input file to be used for naming
                # the output file
                IO_files['-b'].append(os.path.join(in_dir.path, fl.name))
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

        if not IO_files['-b']:
            raise VirtualIOError('No more unused input files')

        # Make sure that input files are sorted so that first input file is the same on successive runs
        if out_cmd['--!input_files_per_command'] == 'all':
            output_name = os.path.split(sorted(IO_files['-b'])[0])[1]
        else:
            output_name = os.path.split(IO_files['-b'][0])[1]

        if '--!compress_output' in out_cmd:
            output_name = utils.splitext(output_name)[0] + self.output_types[1]
        else:
            output_name = utils.splitext(output_name)[0] + self.output_types[0]
        output_path = os.path.join(out_dir.path, output_name)
        IO_files['-v'] = output_path
        file_names.add(output_name)
        out_dir.add_file(output_name)
        out_cmd.update(IO_files)
        command_ids = map(utils.infer_path_id, IO_files['-b'])
        return out_cmd, command_ids


    def get_cmd(self):
        """Returns the final command line.

        Returns:
        final_cmd: List of command line produced by the object (line breaks not allowed within command lines!).
        """
        run_command = utils.parse_config(self.name, 'cmd_name', 'execute')
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
        cmd = self.out_cmd['-v']
        cmd = os.path.basename(cmd)
        return cmd.split('.', 1)[0]

