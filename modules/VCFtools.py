import os

from GenericBase import GenericBase
from STAPLERerror import STAPLERerror
from STAPLERerror import VirtualIOError
import utils

class VCFtools(GenericBase):
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
    #Here the input command dictionary contains list as a value!

    name = 'vcftools'
    #Accept all defined types:
    input_types = {'.vcf', '.bcf', '.vcf.gz'}
    output_types = ['.vcf', '.bcf', '.vcf.gz']
    mandatory_args = ['--!xcf', '--!out']
    user_mandatory_args = []
    remove_user_args = ['--!compressed_output']
    optional_args = ['--temp', '--chr', '--not-chr', '--from-bp', '--to-bp',
                     '--positions', '--exclude-positions',
                     '--positions-overlap', '--exclude-position-overlap',
                     '--bed', '--exclude-bed', '--thin', '--mask',
                     '--invert-mask', '--mask-min', '--snp', '--snps',
                     '--exclude', '--keep-only-indels', '--remove-indels',
                     '--remove-filtered', '--keep-INFO', '--remove-INFO',
                     '--maf', '--max-maf', '--non-ref-af',
                     '--max-non-ref-af', '--mac', '--max-mac',
                     '--non-ref-ac', '--max-non-ref-ac', '--min-alleles',
                     '--max-alleles', '--min-meanDP', '--max-meanDP',
                     '--hwe', '--max-missing', '--max-missing-count',
                     '--phased', '--minQ', '--indv', '--remove-indv',
                     '--keep', '--remove', '--max-indv',
                     '--remove-filtered-geno-all', '--remove-filtered-geno',
                     '--minGQ', '--minDP', '--maxDP', '--freq', '--freq2',
                     '--derived', '--depth', '--site-depth',
                     '--site-mean-depth', '--geno-depth', '--hep-r2',
                     '--geno-r2', '--geno-chisq', '--id-window',
                     '--id-window-min', '--id-window-bp-min', '--min-r2',
                     '--interchrom-hap-r2', '--interchrom-geno-r2',
                     '--hap-r2-positions', '--geno-r2-positions', '--TsTv',
                     '--TsTv-summary', '--TsTv-by-count', '--TsTv-by-qual',
                     '--FILTER-summary', '--site-pi', '--window-pi',
                     '--window-pi-step', '--weir-fst-pop',
                     '--fst-window-size', '--fst-window-step', '--het',
                     '--012', '--BEAGLE-GL', '--BEAGLE-PL', '--contigs',
                     '--diff', '--diff-bcf', '--diff-discordance-matrix',
                     '--diff-indv-discordance', '--diff-indv-map ',
                     '--diff-site-discordance', '--diff-switch-error',
                     '--extract-FORMAT-info', '--get-INFO', '--gzdiff',
                     '--hardy', '--hist-indel-len', '--IMPUTE',
                     '--indv-freq-burden', '--kept-sites', '--ldhat',
                     '--ldhat-geno', '--LROH', '--missing-indv',
                     '--missing-site', '--plink', '--plink-tped', '--recode',
                     '--recode-bcf', '--recode-INFO', '--recode-INFO-all',
                     '--relatedness', '--relatedness2', '--removed-sites',
                     '--singletons', '--site-quality', '--SNPdensity',
                     '--TajimaD', '--!compressed_output']
    parallelizable = True
    help_description = '''
Tested with VCFtools v0.1.10.

Remember to include the --recode argument when necessary (which is
pretty often...)! Notice that by default the output file will be an
uncompressed vcf file whether or not the input file has been compressed.
Include the --!compress_output parameter to the command line to create
compressed output.

Known quirks and issues:
1. The format converting tools do not work yet as intended. The
output files types other than .vcf and .gz.vcf are created properly but
these files can not be used as input for other STAPLER tools.

2. The STAPLER allows all the parameters (with the exception
of --vcf, --bcf and --out) to be defined several times even though only some
parameters of VCFtools can be defined multiple times, so pay attention to the
original manual!
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
                    IO_files['--!xcf'] = os.path.join(in_dir.path, fl_name)
                    in_dir.use_file(fl_name, self.name)
                    if fl_name.endswith('.vcf.gz'):
                        fl_name = fl_name[:-7]
                    else:
                        fl_name = utils.splitext(fl_name)[0]
                    if '--recode' in out_cmd:
                        output_name = fl_name + '.vcf'
                    elif '--recode-bcf' in out_cmd:
                        output_name = fl_name + '.bcf'
                    else:
                        output_name = fl_name + '.out'
                    if '--!compressed_output' in out_cmd:
                        output_name += '.gz'
                    output_path = os.path.join(out_dir.path, output_name)
                    IO_files['--!out'] = output_path
                    file_names.add(output_name)
                    out_dir.add_file(output_name)
                    break
        if not IO_files:
            raise VirtualIOError('No more unused input files')
        out_cmd.update(IO_files)
        return out_cmd, file_names

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
            #Value is a list here:
            try:
                parsed_cmd[argument].append(value)
            except KeyError:
                parsed_cmd[argument] = [value]
            i += 1
        return parsed_cmd

    def _user_override(self, parsed_in_cmd, out_cmd):
        """Overrides auto-inferred values with possible user inputs.

        Arguments:
        parsed_in_cmd: Parsed unmodified dict of user input.
        out_cmd: Dict of auto-inferred output commands.

        Returns:
        Output commands overridden with user inputs.
        """

        for arg, value in parsed_in_cmd.iteritems():
            #User can not override mandatory arguments since these are not lists
            #Fix this if too much time...
            if arg not in self.mandatory_args:
                #Values are lists in this case
                for v in value:
                    if v.startswith('!2table'):
                        new_value = self._parse_2table(v)
                        out_cmd[arg] = new_value
                    elif v.startswith('!named_table'):
                        new_value = self._parse_named_table(v)
                        out_cmd[arg] = new_value
        return out_cmd

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
            #Value is a list here:
            if arg == '--!out':
                pass
            elif arg == '--!xcf':
                if val.endswith('.vcf'):
                    final_cmd.append('--vcf ' + val)
                if val.endswith('.bcf'):
                    final_cmd.append('--bcf ' + val)
                if val.endswith('.vcf.gz'):
                    final_cmd.append('--gzvcf ' + val)
            else:
                for v in val:
                    final_cmd.append(arg + ' ' + v)

        if self.out_cmd['--!out'].endswith('.gz'):
            final_cmd.append('--stdout | gzip > {0}'.format(self.out_cmd['--!out']))
        else:
            final_cmd.append('--stdout > {0}'.format(self.out_cmd['--!out']))
        output = ' '.join(final_cmd)
        return [output]
		