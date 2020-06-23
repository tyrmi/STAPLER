import os

from GenericBase import GenericBase
from STAPLERerror import STAPLERerror
from STAPLERerror import VirtualIOError
import utils

class soap2(GenericBase):
    """Class for using soap2 algorithm.

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

    name = 'stapler_soap2'
    input_types = {'.fastq', '.fq'}
    output_types = ['.sam']
    hidden_mandatory_args = ['-a', '-o']
    hidden_optional_args = ['-2', '-b']
    user_mandatory_args = ['-D']
    remove_user_args = []
    user_optional_args = ['--!read_format', '-l', '-m', '-M', '-n', '-p', '-r',
                          '-R', '-t', '-v', '-x']
    parallelizable = True
    help_description = '''
Tested with soap2 version 2.21.

Both paired-end and single-end data can be used as input but not at the same
time. Paired-end mode is used when --!read_format argument is present in the
command line, otherwise single-end data is assumed.

--!read_format argument is mandatory if you have paired-end data.
This argument indicates the format in which read number is shown in
file names. For instance if you have paired end files samplename_R1 and
samplename_R2, the --!read_format argument should look like this:
--!read_format _R?

Notice, that STAPLER uses soap parameter -2 to create output files with
unpaired alignments. These files have file extension ".unpaired" and are
omitted from possible further steps of the workflow.
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
                    IO_files['-a'] = os.path.join(in_dir.path, pair1)
                    command_ids.append(utils.infer_path_id(IO_files['-a']))
                    in_dir.use_file(pair1, self.name)
                    IO_files['-b'] = os.path.join(in_dir.path, pair2)
                    command_ids.append(utils.infer_path_id(IO_files['-b']))
                    in_dir.use_file(pair2, self.name)

                    #Infer output
                    output_name = utils.splitext(pair1)[0]
                    output_name = output_name.replace(self.parsed_in_cmd[
                                                          '--!read_format'],
                                                      '')
                    output_name += self.output_types[0]
                    output_path = os.path.join(out_dir.path, output_name)
                    IO_files['-o'] = output_path
                    file_names.add(output_name)
                    out_dir.add_file(output_name)
                    IO_files['-2'] = output_path + '.unpaired'
                    break

        else: #Handle single end files
            file_names = set()
            for fl in in_dir.files:
                if self.name not in fl.users:
                    if utils.splitext(fl.name)[-1] in self.input_types:
                        IO_files['-a'] = os.path.join(in_dir.path, fl.name)
                        command_ids.append(utils.infer_path_id(IO_files['-a']))
                        in_dir.use_file(fl.name, self.name)
                        assert len(self.output_types) == 1, 'Several output ' \
                                                            'types, override ' \
                                                            'this method!'

                        output_name = utils.splitext(fl.name)[0] + \
                                      self.output_types[0]
                        output_path = os.path.join(out_dir.path, output_name)
                        IO_files['-o'] = output_path
                        file_names.add(output_name)
                        out_dir.add_file(output_name)
                        break

        if not IO_files:
            raise VirtualIOError('No more unused input files')
        out_cmd.update(IO_files)
        return out_cmd, command_ids

