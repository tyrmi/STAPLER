import copy
import itertools
import logging
import os

from GenericBase import GenericBase
from STAPLERerror import STAPLERerror
from STAPLERerror import VirtualIOError
import directory
import utils


class trimmomatic(GenericBase):
    """Class for generic command lines, also superclass for STAPLER input classes.

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

    name = 'trimmomatic'
    #Accept all defined types:
    input_types = {'.fastq'}
    output_types = ['.fastq']
    hidden_mandatory_args = ['--!fastq1', '--!out_1', '-threads']
    user_mandatory_args = ['-threads']
    remove_user_args = ['--!PE', '--!SE', '--!read_format']
    user_optional_args = ['--!PE', '--!SE', '--!read_format', '--!fastq2',
                          '--!out_2', '--!out_unpaired_1', '--!out_unpaired_2',
                          '-ILLUMINACLIP', '-SLIDINGWINDOW', '-MAXINFO', '-LEADING',
                          '-TRAILING', '-CROP', '-HEADCROP', '-MINLEN', '-AVGQUAL',
                          '-TOPHRED33', '-TOPHRED64']
    parallelizable = True
    help_description = '''
Tested with Trimmomatic version 0.32.

When using Trimmomatic through STAPLER the command line syntax is
somewhat different from Trimmomatic itself:

The processing steps should be defined in staplefile following syntax:
trimmomatic -ILLUMINACLIP TruSeq-3SE:2:30:10 -LEADING 3 ...
instead of:
java -jar trimmomatic-32.jar <IOpaths> ILLUMINACLIP:TruSeq-3SE:2:30:10
LEADING:3 ...


NOTICE! Paired-end/single-end mode must be selected by using --!PE or --!SE
argument respectively. Also notice that the --!read_format argument is mandatory
in paired-end mode.

In paired end mode (--!PE) this tool expects to find two read files for each
sample. STAPLER automatically defines two fastq files for input and
four fastq files for output (see Trimmomatic manual for details). The unpaired
fastq output files are marked with '..._unpaired.out' file extensions, and they
can not be used by subsequent commands in STAPLER.

In single-end mode (--!SE) a single read file is expected for each sample.

--!read_format argument indicates the format in which read number is shown in
file names. For instance if you have paired end files samplename_R1 and
samplename_R2, the --!read_format argument should look like this:
--!read_format _R?
    '''
    def _validate_user_input(self, in_cmd):
        """Ensures the user has included all mandatory arguments.

        Parameters:
        in_cmd: String the user has input.

        Raises:
        STAPLERerror: Invalid format.
        """

        for m_cmd in self.user_mandatory_args:
            if m_cmd not in in_cmd:
                raise STAPLERerror('{0} command needs the following argument: {'
                                   '1}'.format(self.name, m_cmd))
            if not in_cmd[m_cmd]:
                raise STAPLERerror('{0} command needs the following argument to '
                                   'have a value: {'
                                   '1}'.format(self.name, m_cmd))

        if '--!PE' not in self.parsed_in_cmd and '--!SE' not in self.parsed_in_cmd:
            raise STAPLERerror('For {0} the --!PE or --!SE must be '
                               'defined! Neither argument was found from '
                               'current command line!'.format(self.name))

        if '--!PE' in self.parsed_in_cmd and '--!SE' in self.parsed_in_cmd:
            raise STAPLERerror('For {0} the --!PE or --!SE must be defined! Both '
                               'arguments were found in the current command line'
                               '!'.format(self.name))

        if '--!PE' in self.parsed_in_cmd and '--!read_format' not in self.parsed_in_cmd:
            raise STAPLERerror('--!read_format argument was not found from current '
                               'command! It is mandatory in --!PE mode!'.format(self.name))


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

        if '--!PE' in self.parsed_in_cmd:
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

            paired_files = in_dir.file_pairs(pattern=self.parsed_in_cmd[
                '--!read_format'],
                                             user=self.name,
                                             file_formats=list(self.input_types),
                                             exclusion_iterable=['pairless',
                                                                 'unmatched'])
            if not paired_files:
                raise VirtualIOError('{0} argument did not find any pairs from'
                                     'folder {1}'.format(self.name, in_dir.path))

            IO_files = {}
            file_names = set()
            for pair in paired_files:
                pair1, pair2 = pair
                if self.name not in in_dir.file_names[pair1].users and self.name not in in_dir.file_names[pair2].users:
                    #Infer inputs
                    IO_files['--!fastq1'] = os.path.join(in_dir.path, pair1)
                    command_ids = [utils.infer_path_id(IO_files['--!fastq1'])]
                    in_dir.use_file(pair1, self.name)
                    IO_files['--!fastq2'] = os.path.join(in_dir.path, pair2)
                    command_ids.append(utils.infer_path_id(IO_files['--!fastq2']))
                    in_dir.use_file(pair2, self.name)

                    #Infer output
                    IO_files['--!out_1'] = os.path.join(out_dir.path, pair1)
                    IO_files['--!out_2'] = os.path.join(out_dir.path, pair2)

                    IO_files['--!out_unpaired_1'] = os.path.join(out_dir.path,
                                                                 pair1+'.pairless_1.out')
                    IO_files['--!out_unpaired_2'] = os.path.join(out_dir.path,
                                                                 pair2+'.pairless_2.out')
                    file_names.add(pair1)
                    out_dir.add_file(pair1)
                    file_names.add(pair2)
                    out_dir.add_file(pair2)
                    break

        if '--!SE' in self.parsed_in_cmd:
            IO_files = {}
            file_names = set()
            for fl in in_dir.files:
                if self.name not in fl.users:
                    if utils.splitext(fl.name)[-1] in self.input_types:
                        IO_files['--!fastq1'] = os.path.join(in_dir.path,
                                                             fl.name)
                        command_ids = [utils.infer_path_id(IO_files['--!fastq1'])]
                        in_dir.use_file(fl.name, self.name)
                        assert len(self.output_types) == 1, 'Several output ' \
                                                            'types, override ' \
                                                            'this method!'

                        output_name = utils.splitext(fl.name)[0] + \
                                      self.output_types[0]
                        output_path = os.path.join(out_dir.path, output_name)
                        IO_files['--!out_1'] = output_path
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

        #Set the IO in proper order into the beginning of the command line
        if '--!PE' in self.parsed_in_cmd:
            final_cmd.append('PE')
            final_cmd.append('-threads' + ' ' + self.out_cmd['-threads'])
            final_cmd.append(self.out_cmd['--!fastq1'])
            final_cmd.append(self.out_cmd['--!fastq2'])
            final_cmd.append(self.out_cmd['--!out_1'])
            final_cmd.append(self.out_cmd['--!out_unpaired_1'])
            final_cmd.append(self.out_cmd['--!out_2'])
            final_cmd.append(self.out_cmd['--!out_unpaired_2'])
        if '--!SE' in self.parsed_in_cmd:
            final_cmd.append('SE')
            final_cmd.append('-threads' + ' ' + self.out_cmd['-threads'])
            final_cmd.append(self.out_cmd['--!fastq1'])
            final_cmd.append(self.out_cmd['--!out_1'])

        #Add trimming steps to the command line in the same order as in input
        #  command:
        cmd = self.in_cmd.split(' -')
        parsed_cmd = []
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
            parsed_cmd.append(argument)
            i += 1

        for c in parsed_cmd:
            if c in {'-ILLUMINACLIP', '-SLIDINGWINDOW', '-MAXINFO', '-LEADING',
                     '-TRAILING', '-CROP', '-HEADCROP', '-MINLEN', '-AVGQUAL',
                     '-TOPHRED33', '-TOPHRED64'}:
                final_cmd.append('{0}:{1}'.format(c.lstrip('-'),
                                                  self.out_cmd[c]))
        return [' '.join(final_cmd)]

