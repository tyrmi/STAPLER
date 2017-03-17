import os

from STAPLERerror import STAPLERerror
from STAPLERerror import VirtualIOError
from GenericBase import GenericBase
import utils


class MosaikBuild(GenericBase):
    """Class for MosaikBuild tool of Mosaik aligner.

    Attributes:
    name: Name of the function.
    input_types: Input types accepted by this application.
    output_type: List of output types produced by the application.
    mandatory_args: Args that the final command line must have.
    user_mandatory_args: Args that the user must provide.
    remove_user_args: Args that will be removed from the final command.
    optional_args: Args that may be part of the command line.
    """

    name = 'MosaikBuild'
    input_types = {'.fastq'}
    output_types = ['.dat']
    mandatory_args = ['-q', '-q2', '-out']
    user_mandatory_args = ['--!read_format']
    optional_args = ['-assignQual', '-bd', '-cn', '-ds', '-fq', '-fq2', '-fr',
                     '-fr2', '-gd', '-id', '-il', '-il', '-ln', '-mfl', '-out',
                     '-pu', '-q', '-q2', '-quiet', '-sam', '-split', '-srf',
                     '-st', '-tp', '-ts']
    help_description = """
Tested with version 2.2.30.

Notice that this tool skips files containing the following substrings in
names:
'pairless'
'unmatched'

--!read_format argument tells the script how to read pair number from in file
names. The read number is expected to be 1 or 2. --!read_format character
contains the read number replaced with "?" and surrounding characters.

For instance if you have paired end files samplename_R1 and samplename_R2,
the --!read_format argument should look like this:
--!read_format _R?"""

    def _select_IO(self, out_cmd, in_dir, out_dir):
        """Returns a dict containing the proper IO commands.

        This method must keep the directory objects up to date of the file
        edits!

        Arguments:
        in_cmd: A string containing the command line.
        in_dir: Input directory.
        out_dir: Output directory.

        Returns:
        IO_files: Dict containing the proper IO commands.
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
                                        user=self.name,
                                        file_format= list(self.input_types)[0],
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
            IO_files['-q'] = os.path.join(in_dir.path, pair1)
            in_dir.use_file(pair1, self.name)
            IO_files['-q2'] = os.path.join(in_dir.path, pair2)
            in_dir.use_file(pair2, self.name)

            #Infer output
            output_name = utils.splitext(pair1)[0] + self.output_types[0]
            output_path = os.path.join(out_dir.path, output_name)
            IO_files['-out'] = output_path
            file_names.add(output_name)
            out_dir.add_file(output_name)
            break
        if not IO_files:
            raise VirtualIOError('No more unused input files')
        out_cmd.update(IO_files)
        return out_cmd, file_names


class MosaikAligner(GenericBase):
    """Class for using MosaikAligner of Mosaik toolkit.

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

    name = 'MosaikAligner'
    #Accept all defined types:
    input_types = {'.dat'}
    output_types = ['.dat']
    mandatory_args = ['-in', '-out', '-ia']
    user_mandatory_args = ['-ia']
    remove_user_args = []
    optional_args = ['-a', '-act', '-bw', '-gep', '-gop', '-hgop', '-hs', '-j',
                     '-kd', '-lm', '-ls', '-m', '-mhp', '-mhr', '-min',
                     '-minp', '-mm', '-mmp', '-mms', '-ms', '-ncg', '-om',
                     '-omi', '-p', '-pd', '-quiet', '-sref', '-srefn',
                     '-statmq', '-zn', '-ibs', '-annpe', '-annse']
    parallelizable = True
    help_description = '''
    Tested with version 2.2.30.

    Creation of reference sequence archive (for -ia) is not supported by this
    script. Do need to do this manually beforehand, as the existence of this
    file is checked by this script!
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

        IO_files = {}
        file_names = set()
        for fl_name, users in in_dir.files.iteritems():
            if self.name not in users:
                if utils.splitext(fl_name)[-1] in self.input_types:
                    IO_files['-in'] = os.path.join(in_dir.path, fl_name)
                    in_dir.use_file(fl_name, self.name)
                    assert len(self.output_types) == 1, 'Several output ' \
                                                        'types, override ' \
                                                        'this method!'

                    output_name = utils.splitext(fl_name)[0] + \
                                  self.output_types[0]
                    output_path = os.path.join(out_dir.path, output_name)
                    IO_files['-out'] = output_path
                    file_names.add(output_name)
                    out_dir.add_file(output_name)
                    break
        if not IO_files:
            raise VirtualIOError('No more unused input files')
        out_cmd.update(IO_files)
        return out_cmd, file_names


class MosaikText(GenericBase):
    """Class for using MosaikAligner of Mosaik toolkit.

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

    name = 'MosaikText'
    #Accept all defined types:
    input_types = {'.dat'}
    output_types = ['.sam', '.axt', '.bam', '.bed', '.eland']
    mandatory_args = ['-in']
    user_mandatory_args = []
    remove_user_args = user_mandatory_args
    optional_args = ['-sam', '-axt', '-bam', '-bed', '-eland', '-u']
    parallelizable = True
    help_description = '''
Tested with version 2.2.30.

The user must provide one of the output formats in optional arguments!
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

        IO_files = {}
        file_names = set()
        for fl_name, users in in_dir.files.iteritems():
            if self.name not in users:
                if utils.splitext(fl_name)[-1] in self.input_types:
                    IO_files['-in'] = os.path.join(in_dir.path, fl_name)
                    in_dir.use_file(fl_name, self.name)
                    out_extension = ''
                    for optional_arg in ['-sam', '-axt', '-bam', '-bed',
                                         '-eland']:
                        if optional_arg in self.parsed_in_cmd:
                            if out_extension:
                                raise STAPLERerror('{0} allows only one '
                                              'output format, '
                                              'found several:\n{1}'
                                                   .format(self.name,
                                                      self.in_cmd))
                            out_extension = optional_arg.replace('-', '.')
                    if not out_extension:
                        raise STAPLERerror('Input command should contain output '
                                      'argument:\n{0}'.format(self.in_cmd))
                    output_name = utils.splitext(fl_name)[0] + out_extension
                    output_path = os.path.join(out_dir.path, output_name)
                    IO_files['-sam'] = output_path
                    file_names.add(output_name)
                    out_dir.add_file(output_name)
                    break
        if not IO_files:
            raise VirtualIOError('No more unused input files')
        out_cmd.update(IO_files)
        return out_cmd, file_names
