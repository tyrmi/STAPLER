import os

from GenericBase import GenericBase
from STAPLERerror import STAPLERerror
from STAPLERerror import VirtualIOError
import utils


class bgzip(GenericBase):
    """Class for indexing .vcf files with bgzip & tabix.

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

    name = 'bgzip'
    input_types = set(['.vcf', '.gff', '.bed', '.sam', '.vcf.gz'])
    output_types = ['.vcf', '.gff', '.bed', '.sam', '.vcf.gz']
    mandatory_args = ['-!i', '-!o', '-!d']
    user_mandatory_args = []
    remove_user_args = user_mandatory_args
    optional_args = ['-b', '-d', '-i', '-s']
    parallelizable = True
    help_description = '''
Tested with bgzip version 1.2.1.

When the input file has a .gz file extension (and -d parameter is not
included) the input file is expected to be compressed with gzip. In this case
thw file will first be decompressed with zcat and then compressed with bgzip.
This decompression creates a temporary intermediate file into the output
directory (with a .tmp file extension). The .tmp files will be removed after
bgzip compression. In this case the output of this command includes three
lines: decompression with zcat, compression with bgzip and removal of the
decompressed file. Notice that if the run is aborted before finishing, the tmp
files will remain the output directory.

Notice! The parameter -f is always included in the output so that shell script
can be rerun without interactive session (eg. sbatched to SLURM).
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
                    IO_files['-!i'] = os.path.join(in_dir.path, fl_name)
                    in_dir.use_file(fl_name, self.name)
                    IO_files['-!d'] = None

                    if '-d' in self.out_cmd: # decompress the input file
                        if os.path.splitext(fl_name)[1] != '.gz':
                            raise STAPLERerror('When decompressing files, input '
                                          'files should have .gz file '
                                          'extension. Current file: {0}'.format(os.path.join(in_dir.path,
                                                                                             fl_name)))
                        output_name = os.path.splitext(fl_name)[0]
                        output_path = os.path.join(out_dir.path, output_name)
                        IO_files['-!o'] = output_path
                    else: # compress the input file
                        if os.path.splitext(fl_name)[1] == '.gz':
                            # file is assumed to be compressed with regular gzip,
                            # so it must be decompressed and then compressed again with bgzip
                            IO_files['-!d'] = os.path.join(out_dir.path,
                                                           os.path.splitext(fl_name)[0] + '.tmp')
                            output_name = fl_name
                        else:
                            output_name = fl_name + '.gz'
                        output_path = os.path.join(out_dir.path, output_name)
                        IO_files['-!o'] = output_path
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
            run_command = self.name

        #Include the user arguments specified by the user
        user_parameters = []
        for arg, val in self.out_cmd.iteritems():
            if arg not in self.mandatory_args:
                user_parameters.append(arg + ' ' + val)

        if self.out_cmd['-!d'] is None: # i.e. input file is not compressed
            final_cmd = ('{0} -c {1} {2} > {3}'.format(run_command,
                                                       ' '.join(user_parameters),
                                                       self.out_cmd['-!i'],
                                                       self.out_cmd['-!o']))
            final_cmd = [final_cmd]
        else: # i.e. input file is compressed
            final_cmd = ['zcat {0} > {1}'.format(self.out_cmd['-!i'],
                                                    self.out_cmd['-!d'])]
            final_cmd.append(('{0} -f -c {1} {2} > {3}'.format(run_command,
                                                               ' '.join(user_parameters),
                                                               self.out_cmd['-!d'],
                                                               self.out_cmd['-!o'])))
            final_cmd.append('rm -f {0}'.format(self.out_cmd['-!d']))
        return final_cmd


class tabix(GenericBase):
    """Class for indexing .vcf files with bgzip & tabix.

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

    name = 'tabix'
    input_types = set(['.vcf.gz'])
    output_types = []
    mandatory_args = ['-!i']
    user_mandatory_args = []
    remove_user_args = user_mandatory_args
    optional_args = ['-0', '-b', '-c', '-C', '-e', '-m', '-p', '-s', '-S',
                     '-h', '-H', '-l', '-r', '-R', '-T']
    parallelizable = True
    help_description = '''
Tested with tabix version 1.2.1.

This tool expects the input files (gff, bed, sam, vcf) to be compressed and
indexed with bgzip. The REGION syntax of tabix is not supported, a target file
can be used instead (by using the -T parameter).

Notice! The parameter -f is always included in the output so that shell script
can be rerun without interactive session (eg. sbatched to SLURM).
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
                    IO_files['-!i'] = os.path.join(in_dir.path, fl_name)
                    in_dir.use_file(fl_name, self.name)
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
            if arg != '-!i':
                final_cmd.append(arg + ' ' + val)
        final_cmd.append(self.out_cmd['-!i'])
        return [' '.join(final_cmd)]
