import os
import subprocess

from GenericBase import GenericBase
from STAPLERerror import VirtualIOError
from STAPLERerror import NotConfiguredError
import utils


class PGU(GenericBase):
    """Superclass for PGU scripts."""

    @classmethod
    def validate_tool_config(cls):
        """Checks if the current tool can be run as defined in config.txt

        """

        # Command is not defined
        try:
            cls.run_command_config()
        except NotConfiguredError:
            return ['NONE', 'NONE', 'NONE']

        devnull = open(os.devnull, 'wb')
        module_unloading_test = '-   '
        command_run_test = '-   '

        # Test if loading modules works
        if cls.load_module_config():
            try:
                subprocess.check_call(' && '.join(cls.load_module_config()),
                                      shell=True,
                                      stdout=devnull,
                                      stderr=devnull)
                module_loading_test = 'OK  '
            except subprocess.CalledProcessError:
                module_loading_test = 'FAIL'
                return [command_run_test, module_loading_test, module_unloading_test]
        else:
            module_loading_test = 'OK  '

        # Test if loading modules and then unloading them works
        if cls.unload_module_config():
            try:
                subprocess.check_call(' && '.join(cls.load_module_config() + cls.unload_module_config()),
                                      shell=True,
                                      stdout=devnull,
                                      stderr=devnull)
                module_unloading_test = 'OK  '
            except subprocess.CalledProcessError:
                module_unloading_test = 'FAIL'
        else:
            module_unloading_test = 'OK  '

        # Test if loading modules, and then running the command fails
        run_command_with_command_v = '{0} -h'.format(cls.run_command_config())
        try:
            if cls.load_module_config():
                subprocess.check_call(' && '.join(cls.load_module_config() + [run_command_with_command_v]),
                                      shell=True,
                                      stdout=devnull,
                                      stderr=devnull)
            else:
                subprocess.check_call(run_command_with_command_v,
                                      shell=True,
                                      stdout=devnull,
                                      stderr=devnull)
            command_run_test = 'OK  '
        except subprocess.CalledProcessError:
            command_run_test = 'FAIL'

        return [command_run_test, module_loading_test, module_unloading_test]



class PGU_vcf_allele_count_filter(PGU):
    """Class for generic command lines for vcf_allele_count_filter.py.

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

    name = 'stapler_PGU_vcf_allele_count_filter'
    input_types = set(['.vcf'])
    output_types = ['.vcf']
    hidden_mandatory_args = ['-i', '-o']
    user_mandatory_args = []
    remove_user_args = user_mandatory_args
    user_optional_args = ['-m', '-x', '-v']
    parallelizable = True
    help_description = '''
Tested with vcf_allele_count_filter v.16.03.11.

vcf_allele_count_filter is available from https://github.com/tyrmi/PGU
    '''


class PGU_MAD_MAX(PGU):
    """Class for generic command lines for MAD_MAX.py.

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

    name = 'stapler_PGU_MAD_MAX'
    input_types = set(['.coverageBed_out'])
    output_types = ['.bed']
    hidden_mandatory_args = ['-i', '-o']
    user_mandatory_args = []
    remove_user_args = user_mandatory_args
    user_optional_args = ['-b', '-m', '-z']
    parallelizable = True
    help_description = '''
Tested with MAD_MAX v.16.03.11.

MAD_MAX is available from https://github.com/tyrmi/PGU
    '''


class PGU_ParalogAreaBEDmatic(PGU):
    name = 'stapler_PGU_ParalogAreaBEDmatic'
    #Accept all defined types:
    input_types = set(['.vcf'])
    output_types = ['.bed']
    hidden_mandatory_args = ['-i', '-o']
    user_mandatory_args = ['-r', '-g']
    remove_user_args = []
    user_optional_args = []
    parallelizable = True
    help_description = '''
Tested with ParalogAreaBEDmatic v. 15.12.16.

ParalogAreaBEDmatic is available from https://github.com/tyrmi/PGU
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
                    IO_files['-i'] = os.path.join(in_dir.path, fl.name)
                    command_ids = [utils.infer_path_id(IO_files['-i'])]
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


class PGU_vcf2fastq(PGU):
    """Class for vcf2fastq tool.

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

    name = 'stapler_PGU_vcf2fastq'
    input_types = set(['.vcf'])
    output_types = ['.fq']
    hidden_mandatory_args = ['-i', '-o']
    user_mandatory_args = []
    remove_user_args = user_mandatory_args
    user_optional_args = []
    parallelizable = True
    help_description = '''
Tested with vcf2fastq v. 17.04.24.

vcf2fastq is available from https://github.com/tyrmi/PGU
'''


class PGU_variant_density_filter(PGU):
    """Class for parallelization of variant_density_filter.py.

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

    name = 'stapler_PGU_variant_density_filter'
    #Accept all defined types:
    input_types = {'.vcf'}
    output_types = ['.vcf']
    hidden_mandatory_args = ['-i', '-o', '-s', '-m']
    user_mandatory_args = ['-s', '-m']
    remove_user_args = []
    user_optional_args = ['-r']
    parallelizable = True
    help_description = '''
Tested with variant_density_filter v. 15.08.21.

variant_density_filter is available from https://github.com/tyrmi/PGU
    '''


