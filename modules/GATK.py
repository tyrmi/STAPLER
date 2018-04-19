import os

from GenericBase import GenericBase
from STAPLERerror import STAPLERerror
from STAPLERerror import VirtualIOError
import utils

class GATK_superclass(GenericBase):
    """A superclass for GATK tools.

    The _cmd_parse function is overridden with a one that defines the input
    values as a dictionary of argument_name : list_of_values instead of
    argument_name : value
    """

    def _cmd_parse(self, cmd):
        """Turns a command line into argument-value pairs.

        The function expects that all arguments start with '-'! It is OK for
        an argument not to have a value.

        Args:
        cmd: A string containing the command line.

        Returns:
        parsed_cmd: A dict of argument-value pairs.

        Raises:
        STAPLERerror: The command line does not start with '-'
        """

        cmd = cmd.strip()

        if len(cmd) == 0:
            return {}

        if not cmd.startswith('-'):
            raise STAPLERerror("An argument does not start with '-':\n{0}".format(
                cmd))

        cmd = cmd.split(' -')
        parsed_cmd = {}
        i = 0
        for c in cmd:
            if not c:
                continue
            try:
                argument, value = c.split(' ', 1)
            except ValueError:
                argument = c.split(' ', 1)[0]
                value = ''
            if i > 0:
                argument = '-' + argument

            if argument in parsed_cmd:
                parsed_cmd[argument].append(value.strip())
            else:
                parsed_cmd[argument] = [value.strip()]
            i += 1
        return parsed_cmd


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
                    IO_files['-I'] = [os.path.join(in_dir.path, fl.name)]
                    command_ids = [utils.infer_path_id(IO_files['-I'][0])]
                    in_dir.use_file(fl.name, self.name)

                    # Infer output file
                    output_name = utils.splitext(fl.name)[0] + \
                                  self.output_types[0]
                    output_path = os.path.join(out_dir.path, output_name)
                    IO_files['-O'] = [output_path]
                    file_names.add(output_name)
                    out_dir.add_file(output_name)
                    break
        if not IO_files:
            raise VirtualIOError('No more unused input files')
        out_cmd.update(IO_files)
        return out_cmd, command_ids


    def _user_override(self, parsed_in_cmd, out_cmd):
        """Overrides auto-inferred values with possible user inputs.

        Parameters:
        parsed_in_cmd: Parsed unmodified dict of user input.
        out_cmd: Dict of auto-inferred output commands.

        Returns:
        Output commands overridden with user inputs.
        """

        for arg, values in parsed_in_cmd.iteritems():
            for v in values:
                if v.startswith('!value_table'):
                    new_value = self._parse_value_table(v)
                    out_cmd[arg] = [new_value]
        return out_cmd


    def get_cmd(self):
        """Returns the final command line.

        Returns:
        final_cmd: List of command line produced by the object (line breaks not allowed within command lines!).
        """
        run_command = utils.parse_config(self.name, 'cmd_name', 'execute')
        final_cmd = [run_command]
        for arg, val in self.out_cmd.iteritems():
            for v in val:
                final_cmd.append(arg + ' ' + v)
        return [' '.join(final_cmd)]


class ApplyBQSR(GATK_superclass):
    """Class for using GATK ApplyBQSR tool.

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

    name = 'gatk_ApplyBQSR'
    input_types = set(['.bam', '.sam', '.cram'])
    output_types = ['.bam', '.sam', '.cram']
    require_output_dir = True
    hidden_mandatory_args = ['-I', '-O', '--bqsr-recal-file']
    user_mandatory_args = ['-R']
    remove_user_args = []
    user_optional_args = ['--add-output-sam-program-record',
                          '--add-output-vcf-command-line', '--arguments_file',
                          '--cloud-index-prefetch-buffer',
                          '--cloud-prefetch-buffer', '--create-output-bam-index',
                          '--create-output-bam-md5',
                          '--create-output-variant-index',
                          '--create-output-variant-md5',
                          '--disable-bam-index-caching', '--disable-read-filter',
                          '--disable-sequence-dictionary-validation',
                          '--disable-tool-default-read-filters',
                          '--emit-original-quals', '--exclude-intervals',
                          '--gatk-config-file', '--gcs-max-retries',
                          '--global-qscore-prior',
                          '--interval-exclusion-padding',
                          '--interval-merging-rule', '--interval-padding',
                          '--interval-set-rule', '--intervals', '--lenient',
                          '--preserve-qscores-less-than', '--quantize-quals',
                          '--QUIET', '--read-filter', '--read-index',
                          '--read-validation-stringency', '--reference',
                          '--round-down-quantized',
                          '--seconds-between-progress-updates',
                          '--sequence-dictionary', '--showHidden',
                          '--static-quantized-quals', '--TMP_DIR',
                          '--use-jdk-deflater', '--use-jdk-inflater',
                          '--use-original-qualities', '--verbosity', '--version',
                          '-1.0', '-CIPB', '-CPB', '-DBIC', '-DF', '-gcs-retries',
                          '-imr', '-ip', '-isr', '-ixp', '-jdk-deflater',
                          '-jdk-inflater', '-L', '-LE', '-OBI', '-OBM', '-OQ',
                          '-OVI', '-OVM', '-R', '-RF', '-VS', '-XL']
    parallelizable = True
    help_description = '''
Tested with GATK 4.0.

Notice, that --bqsr-recal-file parameter is automatically inferred, and should
not be included in the command line. The value for this parameter is a .table
file, which is expected to be found in the input directory. This can be
done by using the GATK BaseRecalibrator command.
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
                    # Infer input path
                    IO_files['-I'] = [os.path.join(in_dir.path, fl.name)]
                    command_ids = [utils.infer_path_id(IO_files['-I'][0])]
                    in_dir.use_file(fl.name, self.name)

                    # Infer --bqsr-recal-file path
                    bqsr_file_name = utils.splitext(fl.name)[0] + '.table'
                    if bqsr_file_name not in in_dir.file_names:
                        raise STAPLERerror('{0} requires two input files: a '
                                           'bam file (or equivalent) and a '
                                           'corresponding recalibration file '
                                           'with .table file extension, '
                                           'which is expected to be found in '
                                           'the input directory. Input '
                                           'directory does not contain .table '
                                           'file for input file {1}. Expected '
                                           'a .table file with name {2}. '
                                           'Predicted input directory '
                                           'contents:\n{3}'.format(self.name,
                                                                   fl.name,
                                                                   bqsr_file_name,
                                                                   in_dir.file_names.keys()))
                    IO_files['--bqsr-recal-file'] = [os.path.join(in_dir.path,
                                                                  bqsr_file_name)]

                    # Infer output path
                    output_name = fl.name
                    output_path = os.path.join(out_dir.path, output_name)
                    IO_files['-O'] = [output_path]
                    file_names.add(output_name)
                    out_dir.add_file(output_name)
                    break
        if not IO_files:
            raise VirtualIOError('No more unused input files')
        out_cmd.update(IO_files)
        return out_cmd, command_ids


class BaseRecalibrator(GATK_superclass):
    """Class for using GATK BaseRecalibrator tool.

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

    name = 'gatk_BaseRecalibrator'
    input_types = set(['.bam', '.sam', '.cram'])
    output_types = ['.table']
    require_output_dir = False
    hidden_mandatory_args = ['-I', '-O']
    user_mandatory_args = ['-R', '--!known-sites']
    remove_user_args = ['--!known-sites']
    user_optional_args = ['--add-output-sam-program-record',
                          '--add-output-vcf-command-line', '--arguments_file',
                          '--binary-tag-name', '--bqsr-baq-gap-open-penalty',
                          '--cloud-index-prefetch-buffer',
                          '--cloud-prefetch-buffer', '--create-output-bam-index',
                          '--create-output-bam-md5',
                          '--create-output-variant-index',
                          '--create-output-variant-md5',
                          '--default-base-qualities',
                          '--deletions-default-quality',
                          '--disable-bam-index-caching', '--disable-read-filter',
                          '--disable-sequence-dictionary-validation',
                          '--disable-tool-default-read-filters',
                          '--exclude-intervals', '--gatk-config-file',
                          '--gcs-max-retries', '--help', '--indels-context-size',
                          '--insertions-default-quality',
                          '--interval-exclusion-padding',
                          '--interval-merging-rule', '--interval-padding',
                          '--interval-set-rule', '--intervals', '--known-sites',
                          '--lenient',
                          '--low-quality-tail', '--maximum-cycle-value',
                          '--mismatches-context-size',
                          '--mismatches-default-quality',
                          '--preserve-qscores-less-than', '--quantizing-levels',
                          '--QUIET', '--read-filter', '--read-index',
                          '--read-validation-stringency',
                          '--seconds-between-progress-updates',
                          '--sequence-dictionary', '--TMP_DIR',
                          '--use-jdk-deflater', '--use-jdk-inflater',
                          '--use-original-qualities', '--verbosity', '--version',
                          '-1', '-1', '-CIPB', '-CPB', '-DBIC', '-DF',
                          '-gcs-retries', '-h', '-ics', '-imr', '-ip', '-isr',
                          '-ixp', '-jdk-deflater', '-jdk-inflater', '-L', '-LE',
                          '-max-cycle', '-mcs', '-OBI', '-OBM', '-OQ', '-OVI',
                          '-OVM', '-RF', '-VS', '-XL']
    parallelizable = True
    help_description = '''
Tested with GATK 4.0.

Notice that output .table files are written to the input directory.
Notice, that you may define the --!known_sites parameter multiple times.

The mandatory GATK Baserecalibrator parameter --known-sites parameter is
inferred based on the value you set for the STAPLER-specific --!known-sites
parameter the following way:
1) If --!known-sites value is a path to a specific file, the same file path is
used for all input .bam/.sam/.cram files. E.g. path/to/my_database_file.bed
2) If --!known-sites value is a path to a directory, STAPLER tries to search
for a file that has a basename corresponding to the input .bam file
basename. E.g. for input file sample_1_R1.bam the directory is expected to
contain a file with basename sample_1_R1 (such as sample_1_R1.vcf,
sample_1_R1.bcf, sample_1_R1.bed etc.).
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
                    # Parse the input file name
                    IO_files['-I'] = [os.path.join(in_dir.path, fl.name)]
                    command_ids = [utils.infer_path_id(IO_files['-I'][0])]
                    in_dir.use_file(fl.name, self.name)

                    # Parse the --!known_sites parameter
                    for p in out_cmd['--!known-sites']:
                        if os.path.isfile(p):
                            try:
                                IO_files['--known-sites'].append(p)
                            except KeyError:
                                IO_files['--known-sites'] = [p]
                        elif os.path.isdir(p):
                            input_base_name = utils.splitext(fl.name)[0]
                            ks_file_found = False
                            for ks_file in os.listdir(p):
                                ks_file_basename = utils.splitext(ks_file)[0]
                                absolute_ks_file_name = os.path.join(p, ks_file)
                                if input_base_name == ks_file_basename:
                                    try:
                                        IO_files['--known-sites'].append(absolute_ks_file_name)
                                    except KeyError:
                                        IO_files['--known-sites'] = [absolute_ks_file_name]
                                    ks_file_found = True
                                    break
                            if not ks_file_found:
                                basenames = [os.path.splitext(fn)[0] for fn in os.listdir(p)]
                                raise STAPLERerror('{0} parameter '
                                                   '--!known-sites specified '
                                                   'a path to directory, '
                                                   'but no files with '
                                                   'matching basename to '
                                                   'input file {1} were found. '
                                                   'Basename of this file is '
                                                   '{2}. The directory '
                                                   'contained files with the '
                                                   'following basenames:\n{'
                                                   '3}'.format(self.name,
                                                               fl.name,
                                                               input_base_name,
                                                               basenames))
                        else:
                            raise STAPLERerror('{0} parameter --!known-sites '
                                               'value should be a path to an '
                                               'existing file or '
                                               'directory!'.format(self.name))

                    # Parse the output file name
                    output_name = utils.splitext(fl.name)[0] + \
                                  self.output_types[0]
                    output_path = os.path.join(out_dir.path, output_name)
                    IO_files['-O'] = [output_path]
                    file_names.add(output_name)
                    out_dir.add_file(output_name)
                    break
        if not IO_files:
            raise VirtualIOError('No more unused input files')
        out_cmd.update(IO_files)
        return out_cmd, command_ids


class GenotypeGVCFs(GATK_superclass):
    """Class for using GATK GenotypeGVCFs tool.

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

    name = 'gatk_GenotypeGVCFs'
    input_types = set(['.gvcf'])
    output_types = ['.vcf']
    require_output_dir = True
    hidden_mandatory_args = ['-V', '-O']
    user_mandatory_args = ['-R']
    remove_user_args = []
    user_optional_args = ['--add-output-sam-program-record',
                          '--add-output-vcf-command-line',
                          '--annotate-with-num-discovered-alleles',
                          '--annotation', '--annotation-group',
                          '--annotations-to-exclude', '--arguments_file',
                          '--cloud-index-prefetch-buffer',
                          '--cloud-prefetch-buffer', '--create-output-bam-index',
                          '--create-output-bam-md5',
                          '--create-output-variant-index',
                          '--create-output-variant-md5', '--dbsnp',
                          '--disable-bam-index-caching', '--disable-read-filter',
                          '--disable-sequence-dictionary-validation',
                          '--disable-tool-default-annotations',
                          '--disable-tool-default-read-filters',
                          '--exclude-intervals', '--gatk-config-file',
                          '--gcs-max-retries', '--heterozygosity',
                          '--heterozygosity-stdev', '--indel-heterozygosity',
                          '--input', '--input-prior',
                          '--interval-exclusion-padding',
                          '--interval-merging-rule', '--interval-padding',
                          '--interval-set-rule', '--intervals', '--lenient',
                          '--max-alternate-alleles', '--max-genotype-count',
                          '--only-output-calls-starting-in-intervals', '--QUIET',
                          '--read-filter', '--read-index',
                          '--read-validation-stringency', '--sample-ploidy',
                          '--seconds-between-progress-updates',
                          '--sequence-dictionary', '--showHidden',
                          '--standard-min-confidence-threshold-for-calling',
                          '--TMP_DIR', '--use-jdk-deflater', '--use-jdk-inflater',
                          '--use-new-qual-calculator', '--verbosity', '--version',
                          '-A', '-AX', '-CIPB', '-CPB', '-D', '-DBIC', '-DF',
                          '-G', '-gcs-retries', '-I', '-imr', '-ip', '-isr',
                          '-ixp', '-jdk-deflater', '-jdk-inflater', '-L', '-LE',
                          '-new-qual', '-OBI', '-OBM', '-OVI', '-OVM', '-ploidy',
                          '-RF', '-stand-call-conf', '-VS', '-XL']
    parallelizable = True
    help_description = '''
Tested with GATK 4.0.
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
                    IO_files['-V'] = [os.path.join(in_dir.path, fl.name)]
                    command_ids = [utils.infer_path_id(IO_files['-V'][0])]
                    in_dir.use_file(fl.name, self.name)
                    output_name = utils.splitext(fl.name)[0] + \
                                  self.output_types[0]
                    output_path = os.path.join(out_dir.path, output_name)
                    IO_files['-O'] = [output_path]
                    file_names.add(output_name)
                    out_dir.add_file(output_name)
                    break
        if not IO_files:
            raise VirtualIOError('No more unused input files')
        out_cmd.update(IO_files)
        return out_cmd, command_ids


class HaplotypeCaller(GATK_superclass):
    """Class for using GATK HaplotypeCaller tool.

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

    name = 'gatk_HaplotypeCaller'
    input_types = set(['.bam', '.sam', '.cram'])
    output_types = ['.vcf', '.gvcf']
    require_output_dir = True
    hidden_mandatory_args = ['-I', '-O']
    user_mandatory_args = ['-R', '--!input_files_per_command']
    remove_user_args = ['--!input_files_per_command']
    user_optional_args = ['--activity-profile-out', '--alleles', 'null',
                          '--annotate-with-num-discovered-alleles',
                          '--annotation', '-A', '--annotation-group', '-G',
                          '--annotations-to-exclude', '-AX', '--arguments_file',
                          '--assembly-region-out',
                          '--base-quality-score-threshold',
                          '--cloud-index-prefetch-buffer', '-CIPB',
                          '--cloud-prefetch-buffer', '-CPB',
                          '--contamination-fraction-to-filter', '-contamination',
                          '--dbsnp', '-D', '--disable-bam-index-caching', '-DBIC',
                          '--disable-tool-default-annotations',
                          '--gcs-max-retries', '-gcs-retries',
                          '--genotyping-mode', '--graph-output', '-graph',
                          '--heterozygosity', '--heterozygosity-stdev',
                          '--indel-heterozygosity', '--interval-merging-rule',
                          '-imr', '--intervals', '-L',
                          '--max-reads-per-alignment-start',
                          '--min-base-quality-score', '-mbq',
                          '--native-pair-hmm-threads',
                          '--native-pair-hmm-use-double-precision',
                          '--output-mode', '--sample-name', '-ALIAS',
                          '--sample-ploidy', '-ploidy',
                          '--standard-min-confidence-threshold-for-calling',
                          '-stand-call-conf', '--use-new-qual-calculator',
                          '-new-qual', '--version',
                          '--add-output-sam-program-record',
                          '--add-output-vcf-command-line',
                          '--create-output-bam-index', '-OBI',
                          '--create-output-bam-md5', '-OBM',
                          '--create-output-variant-index', '-OVI',
                          '--create-output-variant-md5', '-OVM',
                          '--disable-read-filter', '-DF',
                          '--disable-sequence-dictionary-validation',
                          '--disable-tool-default-read-filters',
                          '--exclude-intervals', '-XL', '--gatk-config-file',
                          '--interval-exclusion-padding', '-ixp',
                          '--interval-padding', '-ip', '--interval-set-rule',
                          '-isr', '--lenient', '-LE', '--QUIET', 'false',
                          '--read-filter', '-RF', '--read-index',
                          '--read-validation-stringency', '-VS',
                          '--seconds-between-progress-updates',
                          '--sequence-dictionary', '--TMP_DIR',
                          '--use-jdk-deflater', '-jdk-deflater',
                          '--use-jdk-inflater', '-jdk-inflater', '--verbosity',
                          '--active-probability-threshold', '--all-site-pls',
                          '--allow-non-unique-kmers-in-ref',
                          '--assembly-region-padding', '--bam-output', '-bamout',
                          '--bam-writer-type', '--comp', '--consensus',
                          '--contamination-fraction-per-sample-file',
                          '-contamination-file', '--debug',
                          '--disable-optimizations',
                          '--do-not-run-physical-phasing',
                          '--dont-increase-kmer-sizes-for-cycles',
                          '--dont-trim-active-regions',
                          '--dont-use-soft-clipped-bases',
                          '--emit-ref-confidence', '-ERC', '--gvcf-gq-bands',
                          '-GQB', '--indel-size-to-eliminate-in-ref-model',
                          '--input-prior', '--kmer-size',
                          '--max-alternate-alleles', '--max-assembly-region-size',
                          '--max-genotype-count',
                          '--max-num-haplotypes-in-population',
                          '--max-prob-propagation-distance',
                          '--min-assembly-region-size',
                          '--min-dangling-branch-length', '--min-pruning',
                          '--num-pruning-samples',
                          '--pair-hmm-gap-continuation-penalty',
                          '--pcr-indel-model',
                          '--phred-scaled-global-read-mismapping-rate',
                          '--showHidden', '--smith-waterman',
                          '--use-alleles-trigger',
                          '--use-filtered-reads-for-annotations',
                          '--recover-dangling-heads']
    parallelizable = True
    help_description = '''
Tested with GATK 4.0.

The --!input_files_per_command should have a value 'all' or 'single'. In the
case of 'all' all bam files in the input directory are included into single
command line, producing a single output file. In the case of 'single' each
bam file will be processed separately, producing an output file for every
input file
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

        if self.parsed_in_cmd['--!input_files_per_command'][0] not in ('single', 'all'):
            raise STAPLERerror('The --!input_files_per_command should '
                               'have a value "all" or "single"! The '
                               'current value was: {0}'.format(self.parsed_in_cmd['--!input_files_per_command']))
        IO_files = {'-I':[]}
        command_ids = []
        file_names = set()
        for fl in in_dir.files:
            if self.name not in fl.users:
                if utils.splitext(fl.name)[-1] in self.input_types:
                    IO_files['-I'].append(os.path.join(in_dir.path, fl.name))
                    command_ids.append(utils.infer_path_id(fl.name))
                    in_dir.use_file(fl.name, self.name)
                    if self.parsed_in_cmd['--!input_files_per_command'][0]  == 'single':
                        break
        if not IO_files['-I']:
            raise VirtualIOError('No more unused input files')

        # Make sure that input files are sorted so that first input file is the same on successive runs
        if out_cmd['--!input_files_per_command'] == 'all':
            output_name = os.path.split(sorted(IO_files['-I'])[0])[1]
        else:
            output_name = os.path.split(IO_files['-I'][0])[1]

        if '-ERC' in out_cmd or '--emit-ref-confidence' in out_cmd:
            output_name = utils.splitext(output_name)[0] + \
                          self.output_types[1]
        else:
            output_name = utils.splitext(output_name)[0] + \
                          self.output_types[0]
        output_path = os.path.join(out_dir.path, output_name)
        IO_files['-O'] = [output_path]
        file_names.add(output_name)
        out_dir.add_file(output_name)
        out_cmd.update(IO_files)
        return out_cmd, command_ids


class IndexFeatureFile(GATK_superclass):
    """Class for using GATK BaseRecalibrator tool.

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

    name = 'gatk_IndexFeatureFile'
    input_types = set(['.vcf', '.bed', '.vcf.gz', '.bed.gz'])
    output_types = []
    require_output_dir = False
    hidden_mandatory_args = ['-F']
    user_mandatory_args = []
    remove_user_args = []
    user_optional_args = ['--arguments_file', '--gatk-config-file',
                          '--gcs-max-retries', '--help', '--output', '--QUIET',
                          '--showHidden', '--TMP_DIR', '--use-jdk-deflater',
                          '--use-jdk-inflater', '--verbosity', '-gcs-retries',
                          '-jdk-deflater', '-jdk-inflater', '-verbosity']
    parallelizable = True
    help_description = '''
Tested with GATK 4.0.

Notice that index files are written to the input directory.
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
                    IO_files['-F'] = [os.path.join(in_dir.path, fl.name)]
                    command_ids = utils.infer_path_id(fl.name)
                    in_dir.use_file(fl.name, self.name)
                    assert len(self.output_types) < 2, 'Several output ' \
                                                       'types, override ' \
                                                       'this method!'
                    output_name = fl.name + '.idx'
                    file_names.add(output_name)
                    out_dir.add_file(output_name)
                    break
        if not IO_files:
            raise VirtualIOError('No more unused input files')
        out_cmd.update(IO_files)
        return out_cmd, [command_ids]
