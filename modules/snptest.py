import os

from GenericBase import GenericBase
from STAPLERerror import STAPLERerror
from STAPLERerror import VirtualIOError
import utils

class snptest(GenericBase):
    """Class for using SNPTEST.

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

    name = 'stapler_snptest'
    input_types = {'.gen', '.gen.gz', '.sample', '.sample.gz'}
    output_types = ['.sam']
    hidden_mandatory_args = ['-a', '-o']
    hidden_optional_args = ['-2', '-b']
    user_mandatory_args = ['-D']
    remove_user_args = []
    user_optional_args = ['--!read_format', '-l', '-m', '-M', '-n', '-p', '-r',
                          '-R', '-t', '-v', '-x']
    parallelizable = True
    help_description = '''
Tested with SNPTEST version 2.5.1.

Required input for SNPTEST is a .gen file containing genotype data and .sample 
file containing phenotype information. When used with STAPLER, the -data argument 
is mandatory, but only the path to .sample file should be defined.
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

