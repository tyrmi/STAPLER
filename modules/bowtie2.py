import os

from GenericBase import GenericBase
from STAPLERerror import STAPLERerror
from STAPLERerror import VirtualIOError
import utils

class bowtie2(GenericBase):
    """Class for using bowtie2 algorithm.

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

    name = 'bowtie2'
    input_types = {'.fastq', '.fastq.gz', '.fastq.bz2', '.fq', '.fq.gz', '.fq.bz2'}
    output_types = ['.sam']
    mandatory_args = ['-S']
    user_mandatory_args = ['-x']
    remove_user_args = ['--!read_format']
    optional_args = ['-1', '-2', '-q', '-s', '-u', '-5',
                     '-3', '--phred33', '--phred64', '--solexa-quals',
                     '--int-quals', '--end-to-end', '--very-fast', '--fast',
                     '--sensitive', '--very-sensitive', '--very-fast-local',
                     '--fast-local', '--sensitive-local',
                     '--very-sensitive-local', '-N', '-L', '-i', '--n-ceil',
                     '--dpad', '--gbar', '--ignore-quals', '--nofw', '--norc',
                     '--no-1mm-upfront', '--end-to-end', '--local', '--ma',
                     '--mp', '--np', '--rdg', '--rfg', '--score-min', '-k',
                     '-a', '-D', '-R', '-I', '--minins', '-X', '--maxins',
                     '--fr', '--rf', '--ff', '--no-mixed', '--no-discordant',
                     '--dovetail', '--no-contain', '--no-overlap', '-t',
                     '--time', '--un', '--un-gz', '--un-bz2', '--un-lz4',
                     '--al', '--al-gz', '--al-bz2', '--al-lz4', '--un-conc',
                     '--un-conc-gz', '--un-conc-bz2', '--un-conc-lz4',
                     '--al-conc', '--al-conc-gz', '--al-conc-bz2',
                     '--al-conc-lz4', '--quiet', '--met-file', '--met-stderr',
                     '--met', '--no-unal', '--no-hd', '--no-sq', '--rg-id',
                     '--rg', '--omit-sec-seq', '-o', '--offrate', '-p',
                     '--threads', '--reorder', '--mm', '--qc-filter',
                     '--seed', '--non-deterministic', '--!read_format']
    parallelizable = True
    help_description = '''
Both paired-end and single-end data can be used as input but not at the same
time. Paired-end mode is used when --!read_format argument is present in the
command line, otherwise single-end data is assumed.

--!read_format indicates the format in which read number is shown in
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
            paired_files = utils.find_pairs(in_dir,
                                            pattern=self.parsed_in_cmd[
                                                '--!read_format'],
                                            user=self.name,
                                            file_format=list(self.input_types)[0],
                                            exclusion_iterable=['pairless',
                                                                'unmatched'])
            file_names = set()
            for pair in paired_files:
                pair1, pair2 = pair

                #Infer inputs
                IO_files['-1'] = os.path.join(in_dir.path, pair1)
                in_dir.use_file(pair1, self.name)
                IO_files['-2'] = os.path.join(in_dir.path, pair2)
                in_dir.use_file(pair2, self.name)

                #Infer output
                output_name = utils.splitext(pair1)[0]
                output_name = output_name.replace(self.parsed_in_cmd[
                                                  '--!read_format'],
                                                  '')
                output_name += self.output_types[0]
                output_path = os.path.join(out_dir.path, output_name)
                IO_files['-S'] = output_path
                file_names.add(output_name)
                out_dir.add_file(output_name)
                break
        else: #Handle single end files
            file_names = set()
            for fl_name, users in in_dir.files.iteritems():
                if self.name not in users:
                    if utils.splitext(fl_name)[-1] in self.input_types:
                        IO_files['-q'] = os.path.join(in_dir.path, fl_name)
                        in_dir.use_file(fl_name, self.name)
                        assert len(self.output_types) == 1, 'Several output ' \
                                                            'types, override ' \
                                                            'this method!'

                        output_name = utils.splitext(fl_name)[0] + \
                                      self.output_types[0]
                        output_path = os.path.join(out_dir.path, output_name)
                        IO_files['-S'] = output_path
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
            final_cmd.append(arg + ' ' + val)
        return [' '.join(final_cmd)]
		