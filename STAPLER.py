#!/usr/bin/env python

import datetime
import multiprocessing
import logging
import os
import sys
import shutil
import string
import subprocess
import time

from collections import namedtuple

# Catch SyntaxErrors here as this results if user is not using Python 2.7
try:
    from modules.directory import Directory
    from modules import STAPLERerror
    from modules import AvailableCommands
    from modules import utils
except SyntaxError:
    if sys.version_info[0:2] < (2,7):
        print('Error! Python version 2.7 should be used to run this program!')
        print('Current version is', '.'.join(map(str, sys.version_info[0:2])))
        sys.exit(0)
    else:
        raise



VERSION = '18.04.19'
NAME = 'STAPLER'
ART_NAME = '''
        _____________   ___  __   _______
       / __/_  __/ _ | / _ \\/ /  / __/ _ \\
      _\\ \\  / / / __ |/ ___/ /__/ _// , _/
     /___/ /_/ /_/ |_/_/  /____/___/_/|_|
Simple and swifT bioinformAtics PipeLine manageER
'''
AUTHOR = 'Jaakko Tyrmi'
START_TIME = time.strftime("%Y_%m_%d_%H_%M_%S", time.localtime())
class CurrentLogPath:
    """Class for storing current log file path"""
    path = ''
DESCRIPTION = """
This software creates command lines for bioinformatics programs. Consult
the included manual pdf, the built in help function and example data directory
for more detailed instructions.


USAGE:

The user input is a path to a staplefile plus other possible  arguments. For
more information on staplefiles, check the example staple file.

Usage example:
python STAPLER.py input/file/path.txt --SLURM

HELP USAGE:

--help
Open this helpful help screen.

--help <tool_name>
Tool specific help.

AVAILABLE MODES FOR PARALLELIZATION:

--UNIX
Parallelize workflow on any UNIX platform. The default maximum number of jobs
to create in this mode is the detected number of CPU cores. This can be
overridden by using the --MAX_JOB_COUNT parameter. Staplerfile path is required.

--LSF
Create necessary files for parallel LSF array job run. Staplerfile path is
required. NOTICE! This is an experimental feature, please report any feedback
to jaakko.tyrmi@gmail.com

--SGE
Create necessary files for parallel Sun Grid Engine (SGE) array job. The
array job can also be run on SGE relatives, such as Son of Grid Engine,
Oracle Grid Engine, Univa Grid Engine and Open Grid Scheduler. This is an
experimental feature, please report any feedback to jaakko.tyrmi@gmail.com

--SLURM
Create necessary files for parallel SLURM array job run. Staplerfile path is
required.

--TORQUE
Create necessary files for parallel TORQUE multiple job run. Staplerfile path
is required. NOTICE! This is an experimental feature, please report any
feedback to jaakko.tyrmi@gmail.com

PARALLELIZATION PARAMETERS:

--MAX_JOB_COUNT
Maximum number of jobs to create. If number of jobs exceeds this value,
two or more jobs are merged to reduce job count. By default the job count is
not limited and it equals the number of input data files. Staplerfile path is
required.

--PRIORITY
Parallelization priority. Staplerfile path is required. This parameter has no
effect on manually defined split points of staplerfile. Available values are:
continuous / c
When two or more jobs coalesce into one (i.e. single command takes several
input files, such as short read aligners and variant callers),
the coalescing jobs are combined into the same job. This increases the
run time of jobs. This is the default value.
split / s
When two or more jobs coalesce into one, the workflow is split into pre- and
after coalescence workflows. This way each job can be run in their own
separate processes. However, separate staplefiles are generated for each
workflow part, which must be manually submitted when previous workflow
finishes.

UTILITY PARAMETERS:

--VALIDATE_RUN
Checks if the the run has finished properly. Staplerfile path is required.

--FIX_RUN
Can be used if --VALIDATE_run reports the run has not finished successfully. If
In this case run can be continued with --FIX_RUN feature for only the
necessary files/steps. The original staplefile can be modified if one wants to
change resource manager parameters (run time, max RAM, etc.). Staplerfile
path is required.

--COMPRESS
Compresses finished run results (except .bam/.bai files). Staplerfile path is
required. May be used in combination with --SLURM <core_count>. NOTICE,
experimental feature.

--DECOMPRESS
Decompresses finished run results. Staplerfile path is required. May be used in
combination with --SLURM <core_count>. NOTICE, experimental feature.

--REMOVE
Removes all output directories and all of their contents of a specific workflow.
Starting point direcory or any of its contents are not removed. Staplerfile
path is required.

--VALIDATE_CONFIG
Tests the validity of config.txt file by checking each command if:
1) module(s) can be loaded (if scecified)
2) command can be found
3) modules can be unloaded (if specified)
"""

WORKFLOW_CONTROL_KEYWORDS = set(['SPLIT'])

def main(args):
    # Parse args for any help function options and exit
    args = args[1:]
    if len(args) == 0 or args[0] == '--help' or args[0] == '-h':
        parse_help_command(args)
        return 0

    # If asked, execute the config.txt validation
    if '--VALIDATE_CONFIG' in args:
        validate_config_file(args)
        return 0

    # Parse command line and input file parameters
    command_line_parameters = parse_command_line(args)
    input_file_parameters = parse_input_file(command_line_parameters)

    # Remove workflow if requested and exit
    if command_line_parameters.rm_workflow:
        dir_stack = infer_dir_stack(input_file_parameters, create_dirs=False)
        remove_workflow(input_file_parameters, dir_stack)
        return 0

    # Infer directory tree
    if command_line_parameters.compress_run is not None:
        dir_stack = infer_dir_stack(input_file_parameters, create_dirs=False)
    elif command_line_parameters.rm_workflow:
        dir_stack = infer_dir_stack(input_file_parameters, create_dirs=False)
    elif command_line_parameters.validate_run:
        dir_stack = infer_dir_stack(input_file_parameters, create_dirs=False)
    elif command_line_parameters.fix_run:
        dir_stack = infer_dir_stack(input_file_parameters, create_dirs=True)
    else:
        # Create dir stack for a new run
        try:
            dir_stack = infer_dir_stack(input_file_parameters,
                                        create_dirs=True,
                                        allow_existing_dirs=False)
        except STAPLERerror.NewDirExists:
            raise STAPLERerror.STAPLERerror('This workflow has been created '
                                            'already. Use the --REMOVE command '
                                            'to remove the\n current workflow '
                                            'if you wish to recreate it.')


    # Validate workflow success if requested and exit
    if command_line_parameters.validate_run:
        check_run_logs(input_file_parameters, dir_stack)
        validate_run_results(input_file_parameters, dir_stack)
        return 0

    # Remove workflow if requested and exit
    if command_line_parameters.rm_workflow:
        remove_workflow(input_file_parameters, dir_stack)
        return 0

    # Initialize logging
    init_logging(input_file_parameters, dir_stack)

    # Based on user input choose the appropriate function to generate command
    # line objects
    if command_line_parameters.fix_run:
        workloads, dir_stack = regenerate_command_line_objects(input_file_parameters,
                                                               dir_stack,
                                                               command_line_parameters.auto_split_workflows)
    elif command_line_parameters.compress_run is not None:
        workloads = generate_compression_command_line_objects(dir_stack, command_line_parameters)
    else:
        # Generate command lines for a new workflow
        workloads, dir_stack = generate_command_line_objects(input_file_parameters,
                                                             dir_stack,
                                                             command_line_parameters.auto_split_workflows)

    # Add dir stacks contents to log file
    log_dir_stacks_contents(dir_stack)

    # If resource manager is not defined write output to a shell script file
    if command_line_parameters.resource_manager is None:
        workload_files = write_default(workloads, input_file_parameters.output_dir)
    # If resource manager is not defined write output to a collection of output files
    else:
        # Balance workflows to an appropriate number of threads. This step is
        # not necessary if workflow is being compressed as the workloads between
        # threads have been balanced already.
        if command_line_parameters.compress_run is None:
            workloads = determine_job_workloads(workloads,
                                                command_line_parameters)
        # Write output files into an appropriate format
        if command_line_parameters.resource_manager == 'lsf':
            workload_files = write_lsf(workloads, input_file_parameters, command_line_parameters)
        elif command_line_parameters.resource_manager == 'sge':
            workload_files = write_sge(workloads, input_file_parameters, command_line_parameters)
        elif command_line_parameters.resource_manager == 'slurm':
            workload_files = write_slurm(workloads, input_file_parameters, command_line_parameters)
        elif command_line_parameters.resource_manager == 'torque':
            workload_files = write_torque(workloads, input_file_parameters, command_line_parameters)
        elif command_line_parameters.resource_manager == 'unix':
            workload_files = write_unix(workloads, input_file_parameters, command_line_parameters)
        else:
            assert False # This should not happen

        if len(workloads) == 1:
            print '\n\nCreated a single workflow, which will spawn {0} parallel jobs.'.format(len(workloads[0]))
        else:
            print '\n\nCreated {0} workflows, which will spawn the following' \
                  ' numbers of respective parallel jobs:\n{1}'.format(len(workloads),
                                                                      ', '.join(map(str, (map(len, workloads)))))

    # Print out relevant paths and instructions
    print '\nPath to your project directory, which contains all output and ' \
          'data directories:'
    print os.path.split(input_file_parameters.output_dir)[0]
    print '\nPath to your output directory, which contains all shell script ' \
          'files defining this workflow:'
    print input_file_parameters.output_dir
    print '\n'

    if command_line_parameters.resource_manager is None:
        print 'Execute the job now using the following command line:'
    elif command_line_parameters.resource_manager == 'unix':
        print 'Execute the job now using the following command line:'
    elif command_line_parameters.resource_manager == 'lsf':
        if len(workload_files) == 1:
            print 'Execute the job now by submitting the following file to ' \
                  'the resource manager using bsub command.'
        else:
            print 'Execute the job now by submitting the following files one ' \
                  'by one to the resource manager using bsub command. Wait ' \
                  'until the current job has finished until submitting the ' \
                  'next one.'
    elif command_line_parameters.resource_manager == 'sge':
        if len(workload_files) == 1:
            print 'Execute the job now by submitting the following file to ' \
                  'the resource manager using qsub command.'
        else:
            print 'Execute the job now by submitting the following files one ' \
                  'by one to the resource manager using qsub command. Wait ' \
                  'until the current job has finished until submitting the ' \
                  'next one.'
    elif command_line_parameters.resource_manager == 'slurm':
        if len(workload_files) == 1:
            print 'Execute the job now by submitting the following file to ' \
                  'SLURM using sbatch command.'
        else:
            print 'Execute the job now by submitting the following files one ' \
                  'by one to SLURM using sbatch command. Wait ' \
                  'until the current job has finished until submitting the ' \
                  'next one.'
    elif command_line_parameters.resource_manager == 'torque':
        if len(workload_files) == 1:
            print 'Execute the job now by submitting the following file to ' \
                  'the resource manager using qsub command.'
        else:
            print 'Execute the job now by submitting the following files one ' \
                  'by one to the resource manager using qsub command. Wait ' \
                  'until the current job has finished until submitting the ' \
                  'next one.'
    print '\n'.join(workload_files)
    print '\n'


def parse_help_command(args):
    """Parses help function related command line arguments

    Parameters:
    args: Arguments of user command line
    """
    if len(args) < 2:
        print_generic_help()
    elif len(args) == 2:
        print_specific_help(args[1])
    else:
        print 'Error! Found too many arguments for --help! Use --help with ' \
              '0 arguments to print generic help or type --help <tool_name> ' \
              'to get tool specific help!'


def print_generic_help():
    """Prints basic info and help.
    """
    print ART_NAME
    print 'Version {1}\nby {2}'.format(NAME, VERSION, AUTHOR)
    print DESCRIPTION
    tools = sorted(AvailableCommands.commands.keys(), key=lambda v: v.upper())
    print '\n\nSupported tools are:\n{0}'.format('\n'.join(tools))
    print '\nHint: Check tool specific help with --help <tool_name>\n'


def print_specific_help(tool_name):
    """Prints help for a specified tool.

    Parameters:
    args: String containing -help <tool_name>
    """
    if tool_name not in AvailableCommands.commands:
        print 'Command is not supported: {0}'.format(tool_name)
        return
    cmd = AvailableCommands.commands[tool_name]

    print 'Usage of {0}:'.format(cmd.name)
    print '\nAccepted input types:\n{0}'.format(str(list(cmd.input_types)))
    print '\nOutput types:\n{0}'.format(str(cmd.output_types))
    print '\nMandatory arguments:\n{0}'.format(str(cmd.user_mandatory_args))
    print '\nOptional arguments:\n{0}'.format(str(cmd.user_optional_args))
    print '\nParallelizable:\n{0}'.format(str(cmd.parallelizable))
    print '\nAdditional description:\n{0}'.format(str(cmd.help_description))
    print ''


def validate_config_file(args):
    """Reads through the config.txt file and reports any issues

    Parameters:
    args: Arguments of user command line
    """
    # Validate arguments
    if len(args) > 2:
        print 'Error! --VALIDATE_CONFIG does not take any arguments.'
        return

    # Check if the config.txt exists
    if not os.path.exists(utils.CONFIG_FILE_PATH):
        print 'Config file does not seem to exist. Do you wish STAPLER to ' \
              'create it now?'
        if raw_input('(y/n): ') == 'y':
            update_config_file(AvailableCommands.commands.keys(), [])
        else:
            'Create the config file manually or get it from ' \
            'https://github.com/tyrmi/STAPLER\n'
            return 0

    # Check if config.txt contains proper rows
    config_file = utils.get_config_file()
    i = 0
    config_file_defined_commands = []
    commands_to_remove = []
    for line in config_file.split('\n'):
        i += 1
        line = line.strip()
        if not line: continue
        line = line.split('\t')

        # Check the number of columns
        if len(line) != 4:
            print 'config.txt file should have 4 tab delimited columns on ' \
                  'each row. Found {0} columns on line number {1}:'.format(len(line), i)
            print ' '.join(line)
            return

        # Skip first (header) line
        if i == 1: continue

        # Skip comment lines
        if line[0].startswith('#'): continue

        # Check for duplicate rows
        if line[0] in config_file_defined_commands:
            print 'config.txt row number {0} contains configuration for ' \
                  'command {1}, which has been defined earlier in the ' \
                  'config.txt. Please remove the duplicate rows.'.format(i,
                                                                         line[0])
            return 0

        # Check if the defined command is supported by STAPLER
        if line[0] not in AvailableCommands.commands:
            commands_to_remove.append(line[0])
        else:
            # Add the current command to list
            config_file_defined_commands.append(line[0])

    # Report the commands that are found in config.txt but are not supported
    if commands_to_remove:
        print 'config.txt contains configuration for the following commands, ' \
              'that are not supported by STAPLER:'
        print '\n'.join(commands_to_remove)
        print '\n'

    # Check and report if some commands are missing from the config.txt
    commands_to_add = set(AvailableCommands.commands.keys()) - \
                      utils.CONFIG_FILE_OMITTED_COMMANDS - \
                      set(config_file_defined_commands)
    if commands_to_add:
        print 'config.txt is missing configuration for the following ' \
              'commands, that are supported by STAPLER:'
        print '\n'.join(list(commands_to_add))
        print '\n'

    # Prompt user if the issues should be automatically fixed
    if commands_to_remove or commands_to_add:
        print 'Do you wish STAPLER to automatically update config.txt by ' \
              'adding missing commands and removing unsupported commands?'
        if raw_input('(y/n): ') == 'y':
            update_config_file(commands_to_add, commands_to_remove)
            config_file_defined_commands += commands_to_add
            print 'Done. Continuing validation...\n'
        else:
            print 'OK. Continuing validation of supported commands...\n'

    # Check if modules are available on current platform
    try:
        subprocess.check_call('module')
        modules_available = True
    except subprocess.CalledProcessError:
        modules_available = False

    # Test each command on each row of config.txt
    print 'Testing the config.txt commands...'
    devnull = open(os.devnull, 'wb')
    max_width = max(map(len, config_file_defined_commands))
    i = 0
    results = []
    for cmd in config_file_defined_commands:
        i += 1
        if cmd in ('CUSTOM'): continue
        check_result = AvailableCommands.commands[cmd].validate_tool_config()
        check_result = [string.ljust(cmd, max_width)] + check_result
        results.append('\t'.join(check_result))
        #print int(float(i)/len(config_file_defined_commands)*100)
        sys.stdout.write(('\rChecking commands %s%%' % (int(float(i)/len(
            config_file_defined_commands)*100))))
        sys.stdout.flush()


    # Print results
    print '\n\nTest results:'
    print '\n'.join(results)
    print '\nNONE: The execute field is "none" in the config.txt'
    print 'OK:   Command has run perfectly.'
    print 'FAIL: Running the command has failed.'
    print '- :   Unable to test command due to failure in load_module\n'
    if modules_available:
        print 'Notice! As your platform seems to support modules, ' \
              'it is strongly advisable to run "module reset" before using ' \
              'the --VALIDATE_CONFIG feature to generate reliable results.\n'

def update_config_file(commands_to_add, commands_to_remove):
    """Creates an updated version of current config.txt file

    If config.txt does not exist, it is created.

    Arguments:
    commands_to_add: A list of commands that need to be supported
    commands_to_remove: A list of commands that are not supported (any more)
    and can be removed

    Side-effects:
    Edits an existing config.txt file or creates a new one
    """

    # Parse the config.txt file contents
    config_file_contents = {}
    if os.path.exists(utils.CONFIG_FILE_PATH):
        config_file_string = utils.get_config_file()
        first_line = True
        for line in config_file_string.split('\n'):
            if first_line:
                first_line = False
                continue
            if not line.strip(): continue
            if not line.startswith('#'):
                line = line.split('\t')
                config_file_contents[line[0]] = line

    # Remove the specified contents
    for cmd in commands_to_remove:
        config_file_contents.pop(cmd, None)

    # Add the specified contents
    for cmd in commands_to_add:
        config_file_contents[cmd] = [cmd] + ['none']*3

    # Archive old config.txt
    if os.path.exists(utils.CONFIG_FILE_PATH):
        current_time = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
        obs_ending = '-obsolete-{0}.txt'.format(current_time)
        obs_path = obs_ending.join(utils.CONFIG_FILE_PATH.rsplit('.txt',1))
        os.rename(utils.CONFIG_FILE_PATH, obs_path)

    # Print new sorted config.txt
    out_handle = open(utils.CONFIG_FILE_PATH, 'w')
    out_handle.write('cmd_name\texecute\tload_module\tunload_module')
    out_handle.write('\n')
    for cmd, line in sorted(config_file_contents.iteritems()):
        out_handle.write('\t'.join(line))
        out_handle.write('\n')
    out_handle.close()


def parse_command_line(args):
    """Parses and validates command line arguments into a named tuple

    Parameters:
    args: command line arguments

    Returns:
    Named tuple containing parameters defined by user's command line

    Raises:
    STAPLERerror: User has entered an unknown/invalid run parameter
        """


    # Initial validity check of input command: each argument may be
    # defined only once
    for a in args:
        if a.startswith('--'):
            if args.count(a) > 1:
                raise STAPLERerror.STAPLERerror('Each command line parameter can be '
                                                'defined only once! The following '
                                                'parameter was defined multiple times:\n '
                                                '{0}'.format(a))

    # Initialize a named tuple to store all available command line arguments
    Command_line_parameters = namedtuple('Input_file_parameters',
                                         ['all_parameters',
                                          'staplerfile_path',
                                          'resource_manager',
                                          'max_job_count',
                                          'auto_split_workflows',
                                          'compress_run',
                                          'validate_run',
                                          'fix_run',
                                          'rm_workflow'])

    # Parse user command line and check sanity of values

    # Parse the resource manager to use
    all_parameters = ' '.join(args)
    resource_manager = None
    if '--LSF' in args:
        resource_manager = 'lsf'
        args.remove('--LSF')
    if '--SGE' in args:
        if resource_manager is not None:
            raise STAPLERerror.STAPLERerror('Multiple resource managers are listed in the '
                                            'command line. Please, choose only one.')
        resource_manager = 'sge'
        args.remove('--SGE')
    if '--SLURM' in args:
        if resource_manager is not None:
            raise STAPLERerror.STAPLERerror('Multiple resource managers are listed in the '
                                            'command line. Please, choose only one.')
        resource_manager = 'slurm'
        args.remove('--SLURM')
    if '--TORQUE' in args:
        if resource_manager is not None:
            raise STAPLERerror.STAPLERerror('Multiple resource managers are listed in the '
                                            'command line. Please, choose only one.')
        resource_manager = 'torque'
        args.remove('--TORQUE')
    if '--UNIX' in args:
        if resource_manager is not None:
            raise STAPLERerror.STAPLERerror('Multiple resource managers are listed in the '
                                            'command line. Please, choose only one.')
        resource_manager = 'unix'
        args.remove('--UNIX')

    # Parse the limit for maximum number of jobs to spawn
    if '--MAX_JOB_COUNT' in args:
        if resource_manager is None:
            raise STAPLERerror.STAPLERerror('--MAX_JOB_COUNT parameter can only be defined '
                                            'if a resource manager is also defined '
                                            '(e.g. --SLURM)!')
        try:
            max_job_count = int(args[args.index('--MAX_JOB_COUNT')+1])
        except (TypeError, IndexError):
            raise STAPLERerror.STAPLERerror('--MAX_JOB_COUNT requires a positive integer '
                                            'value, e.g. --MAX_JOB_COUNT 16')
        if max_job_count < 1:
            raise STAPLERerror.STAPLERerror('--MAX_JOB_COUNT requires a positive integer '
                                            'value, e.g. --MAX_JOB_COUNT 16')
        args.pop(args.index('--MAX_JOB_COUNT')+1)
        args.remove('--MAX_JOB_COUNT')
    else:
        if resource_manager == 'unix':
            max_job_count = multiprocessing.cpu_count()
        else:
            max_job_count = None

    # Parse workflow control parameters
    if '--PRIORITY' in args:
        if resource_manager is None:
            raise STAPLERerror.STAPLERerror('--PRIORITY parameter can be used only if a '
                                            'resource manager (e.g. SLURM) is specified!')
        if resource_manager == 'unix':
            raise STAPLERerror.STAPLERerror('--PRIORITY parameter cannot be '
                                            'used in combination with --UNIX '
                                            'parameter!')
        try:
            if (args[args.index('--PRIORITY')+1]).lower() in ('continuous', 'c'):
                auto_split_workflows = False
            elif (args[args.index('--PRIORITY')+1]).lower() in ('split', 's'):
                auto_split_workflows = True
            else:
                raise STAPLERerror.STAPLERerror('Allowed values for --PRIORITY parameter are '
                                                '"continuous", "c", "split" and "s"!')
        except (TypeError, IndexError):
            raise STAPLERerror('--PRIORITY parameter requires a value! Allowed values are '
                               '"continuous", "c", "split" and "s" ')
        args.pop(args.index('--PRIORITY')+1)
        args.remove('--PRIORITY')
    else:
        if resource_manager == 'unix':
            auto_split_workflows = True
        else:
            auto_split_workflows = False
    compress_run = None

    # Parse workflow compression/decompression parameters
    if '--COMPRESS' in args:
        compress_run = 'compress'
        args.remove('--COMPRESS')
    if '--DECOMPRESS' in args:
        if '--COMPRESS' in args:
            raise STAPLERerror.STAPLERerror('--COMPRESS and --DECOMPRESS parameters can '
                                            'not be used simultaneously!')
        compress_run = 'decompress'
        args.remove('--DECOMPRESS')

    # Parse workflow validation/fixing/removing parameters
    if '--VALIDATE_RUN' in args:
        validate_run = True
        args.remove('--VALIDATE_RUN')
    else:
        validate_run = False
    if '--FIX_RUN' in args:
        fix_run = True
        args.remove('--FIX_RUN')
    else:
        fix_run = False
    if '--REMOVE' in args:
        rm_workflow = True
        args.remove('--REMOVE')
    else:
        rm_workflow = False

    # Parse path to staplefile. All other valid parameters are now read & removed
    # from args.
    if len(args) == 1:
        if os.path.isfile(args[0]):
            staplerfile_path = args[0]
        else:
            raise STAPLERerror.STAPLERerror('Command line contains an odd value:\n{0}\n '
                                            'This is not an existing path to a staplerfile '
                                            'or any other recognized parameter!'.format(
                args[0]))
    elif len(args) == 0:
        raise STAPLERerror.STAPLERerror('Command line is missing path to staplerfile!')
    elif len(args) > 1:
        for a in args:
            if os.path.isfile(a):
                odd_values = args
                args.remove(a)
                raise STAPLERerror.STAPLERerror('Command line contains some odd '
                                                'parameters! The string "{0}" is '
                                                'probably the path to stapler file, '
                                                'but the following parameters are '
                                                'unknown:\n{1}\nFor more info, '
                                                'type\npython STAPLER.py -h'.format(a,
                                                                                    '\n'.join(odd_values)))
        raise STAPLERerror.STAPLERerror('Command line is missing path to staplerfile! '
                                        'Instead, some odd parameters are present:\n{0}'.format('\n'.join(args)))

    # Do further validity checks for different parameter combinations
    if validate_run and fix_run:
        raise STAPLERerror.STAPLERerror('--VALIDATE_RUN and --FIX_RUN cannot be used '
                                        'in the same command!')
    if validate_run and rm_workflow:
        raise STAPLERerror.STAPLERerror('--REMOVE_WORKFLOW and --VALIDATE_RUN cannot be '
                                        'used in the same command!')
    if fix_run and rm_workflow:
        raise STAPLERerror.STAPLERerror('--FIX_RUN and REMOVE_WORKFLOW cannot be used in '
                                        'the same command!')
    if compress_run is not None:
        if validate_run or rm_workflow or fix_run:
            raise STAPLERerror.STAPLERerror('--VALIDATE_RUN, --REMOVE_WORKFLOW or --FIX_RUN '
                                            'parameters cannot be used in the same command '
                                            'with --COMRESS_RUN!')
    if validate_run or rm_workflow:
        if resource_manager is not None:
            raise STAPLERerror.STAPLERerror('Resource managers cannot be used when '
                                            'removing workflows!')

    command_line_parameters = Command_line_parameters(
        all_parameters=all_parameters,
        staplerfile_path=staplerfile_path,
        resource_manager=resource_manager,
        max_job_count=max_job_count,
        auto_split_workflows=auto_split_workflows,
        compress_run=compress_run,
        validate_run=validate_run,
        fix_run=fix_run,
        rm_workflow=rm_workflow)

    return command_line_parameters


def parse_input_file(command_line_parameters):
    """Reads the user provided input-file.

    Args:
    Named tuple containing parameters defined by user's command line

    Raises:
    STAPLERerror: Input file format is incorrect.

    Returns:
    job_name: Job name defined by the user.
    commands: List of commands.
    dir_stack: List of input directories for each command.
    output_dir: Path to an output dir.
    staplefile: staplefile contents for logging.
    """
    try:
        handle = open(command_line_parameters.staplerfile_path)
    except IOError:
        raise STAPLERerror.STAPLERerror(
            'Unable to open input file: {0}'.format(command_line_parameters.staplerfile_path))

    i = 0
    staplefile = []
    resource_manager_params = []
    commands = []
    job_name = None
    starting_point = None
    project_dir = None
    now_reading = None
    for ln in handle:
        i += 1
        ln = ln.strip()
        staplefile.append(ln)
        if i == 1:
            if ln != 'STAPLEFILE':
                raise STAPLERerror.STAPLERerror(
                    'Input file does not start with "STAPLEFILE"-row')
            else:
                continue
        if not ln:
            continue

        #Read resource manager configuration information
        if ln == 'RESOURCE MANAGER:':
            now_reading = 'resource manager'
            continue
        if ln == 'RESOURCE MANAGER END:':
            now_reading = None
            continue
        if now_reading == 'resource manager':
            resource_manager_params.append(ln)
            continue

        #Allow comments in parts other than SLURM config
        if ln.startswith('#'):
            continue

        #Read commands
        if ln == 'COMMANDS:':
            now_reading = 'commands'
            continue
        if ln == 'COMMANDS END:':
            now_reading = None
            continue
        if now_reading == 'commands':
            try:
                commands.append(ln)
            except KeyError:
                commands = [ln]
            continue

        #Read directory and file paths
        if ln.startswith('JOB NAME:'):
            job_name = ln.replace('JOB NAME:', '')
            job_name = job_name.strip()
            continue

        if ln.startswith('STARTING POINT DIR:'):
            starting_point = ln.replace('STARTING POINT DIR:', '')
            starting_point = starting_point.strip()
            starting_point = starting_point.rstrip('/')
            if not os.path.isdir(starting_point):
                raise STAPLERerror.STAPLERerror('The starting point directory does not exist:\n{0}'.format(starting_point))
            if not os.listdir(starting_point):
                raise STAPLERerror.STAPLERerror('The starting point directory is empty:\n{0}'.format(starting_point))
            continue

        if ln.startswith('PROJECT DIR:'):
            project_dir = ln.replace('PROJECT DIR:', '')
            project_dir = project_dir.strip()
            project_dir = project_dir.rstrip()
            if not os.path.exists(project_dir):
                raise STAPLERerror.STAPLERerror('The defined project '
                                                'directory does not exist:\n{0}'.format(project_dir))
            continue

        # All lines that can be parsed have been read and loop continued.
        raise STAPLERerror.STAPLERerror('Odd line found in '
                                        'staplerfile:\n{0}\nComment lines may '
                                        'be added by using # character. Allowed '
                                        'keywords are STAPLER, JOB NAME: and '
                                        'STARTING POINT:. Possible resource manager '
                                        'parameters must be encompassed '
                                        'within RESOURCE MANAGER: and '
                                        'RESOURCE MANAGER END: lines. '
                                        'Commands to execute must be '
                                        'encompassed within COMMANDS: and '
                                        'COMMANDS END: lines. The above line '
                                        'was not a keyword line nor a within '
                                        'resource manager or command line '
                                        'fields.'.format(ln))

    if not job_name:
        raise STAPLERerror.STAPLERerror('JOB NAME: -argument must be defined '
                                        'in the staplefile!')
    if not starting_point:
        raise STAPLERerror.STAPLERerror('STARTING POINT DIR: -argument must be '
                                        'defined in the staplefile!')
    if not project_dir:
        raise STAPLERerror.STAPLERerror('PROJECT DIR: -argument must be '
                                        'defined in the staplefile!')
    handle.close()

    if not commands:
        raise STAPLERerror.STAPLERerror('No commands found from '
                              'input file: {0}'.format(command_line_parameters.staplerfile_path))

    # Define workflow script directory path
    output_dir_name = '{0}_{1}_BATCH_SCRIPTS'.format(NAME, job_name)
    output_dir = os.path.join(project_dir, output_dir_name)
    if not os.path.exists(output_dir) and not command_line_parameters.rm_workflow:
        os.mkdir(output_dir)

    # Define namedtuple to store input file parameters
    Input_file_parameters = namedtuple('Input_file_parameters', ['job_name',
                                                                 'commands',
                                                                 'starting_point_directory',
                                                                 'project_dir',
                                                                 'output_dir',
                                                                 'resource_manager_params',
                                                                 'staplefile'])
    input_file_parameters = Input_file_parameters(job_name=job_name,
                                                  commands=commands,
                                                  starting_point_directory=starting_point,
                                                  project_dir=project_dir,
                                                  output_dir=output_dir,
                                                  resource_manager_params=resource_manager_params,
                                                  staplefile=staplefile)
    return input_file_parameters


def remove_workflow(input_file_parameters, dir_stack):
    """Deletes the directory tree (except input dir) and all contents.

    Parameters:
    input_file_parameters: Parameters defined in the staplefile.
    dir_stack: Directory tree asscociated with current staplefile.
    """
    dirs_to_del = []
    files_to_del = 0
    for d in dir_stack[1:]:
        if not os.path.exists(d.path): continue
        dirs_to_del.append(d.path)
        files_to_del += len(os.listdir(d.path))
    if os.path.exists(input_file_parameters.output_dir):
        dirs_to_del.append(input_file_parameters.output_dir)
        files_to_del += len(os.listdir(input_file_parameters.output_dir))

    if not dirs_to_del:
        print 'Nothing to remove. This workflow has not been created yet.'
        return
    else:
        print 'Removing {0} directories containing {1} files.'.format(
            len(dirs_to_del), files_to_del)
        if raw_input('Continue?\n(y/n): ') == 'y':
            print 'Removing...'
            try:
                for d in dirs_to_del:
                    shutil.rmtree(d)
            except OSError as err:
                raise STAPLERerror('Unable to remove workflow. Reason:\n'
                                   '{0}'.format(str(err)))
            print 'Done.'
        else:
            print 'Canceled.'

def generate_compression_command_line_objects(dir_stack, command_line_parameters):
    """Generates command line objects to compress/decompress a workflow.

    Parameters:
    dir_stack: A list containing the directories related to current workflow
    command_line_parameters: Named tuple containing parameters defined by
    user's command line

    Returns:
    workflows: A list of command instances to execute current workflow.
    """

    # Generate command lines
    threads = []
    thread_sizes = []
    first_d = True
    for d in dir_stack:
        if first_d:
            first_d = False
            continue
        if not os.path.isdir(d.path): continue
        # Iterate over files in current directory and and generate (de)compression
        # command line for files that are in suitable format
        while True:
            try:
                # The command instance is generated without exceptions if the
                #  command execution has failed (i.e. expected output
                # file does not exist). Otherwise NewFileError is raised.
                if command_line_parameters.compress_run == 'compress':
                    command_line = AvailableCommands.commands['gzip']('', d, d)
                elif command_line_parameters.compress_run == 'decompress':
                    command_line = AvailableCommands.commands['gzip']('-d', d, d)
            except STAPLERerror.NewFileExists:
                pass
            except STAPLERerror.VirtualIOError:
                break

            abs_file_path = os.path.join(d.path, command_line.out_cmd['-!i'])

            # Create new thread for current command if new threads can be created
            if len(threads) < command_line_parameters.max_job_count or command_line_parameters.max_job_count is None:
                threads.append([command_line])
                thread_sizes.append(os.stat(abs_file_path).st_size)
            # If max number of threads have been created, add command to the thread
            # with the least amount of data to handle
            else:
                threads[thread_sizes.index(min(
                    thread_sizes))].append(command_line)
                thread_sizes[thread_sizes.index(min(thread_sizes))] += \
                    os.stat(abs_file_path).st_size

    # Report if no proper input files have been found
    if not threads and command_line_parameters.compress_run == 'compress':
        raise STAPLERerror('Workflow does not contain any files that can be compressed.')
    if not threads and command_line_parameters.compress_run == 'decompress':
        raise STAPLERerror('Workflow does not contain any files that can be decompressed.')

    # Calculate & report estimated run time for the current job
    if command_line_parameters.compress_run == 'compress':
        # Assume that gzip compression speed is 20Mb per second (should
        # give plenty of time for modern processors)
        est_run_time = 'Estimated recommended run time for this job is (hh:mm:ss):\n' \
                       '{0}'.format(datetime.timedelta(seconds=(max(thread_sizes) / 20000000) + 60))
    else:
        # Assume that gzip decompression speed is 60Mb per second (should
        # give plenty of time for modern processors)
        est_run_time = 'Estimated recommended run time for this job is (hh:mm:ss):\n' \
                       '{0}'.format(datetime.timedelta(seconds=(max(thread_sizes) / 60000000) + 60))
    print est_run_time
    logging.info(est_run_time)

    workloads = [threads]
    return workloads


def init_logging(input_file_parameters, dir_stacks):
    """Initiates the logging.

    NOTICE! This function has the side effect of changing the value of the
    class variable  Current_log_path.path!

    Parameters:
    job_name: Name of the job specified by the user.
    outdir: Destination of the log file.
    dir_stack: Available directories for job.
    """
    fl_name = '{0}_log_{1}_{2}.txt'.format(NAME,
                                           START_TIME,
                                           input_file_parameters.job_name)
    #NOTICE! Current_log_path.path is changed here!
    CurrentLogPath.path = os.path.join(input_file_parameters.output_dir,
                                       fl_name)
    logging.basicConfig(filename=CurrentLogPath.path, filemode='w',
                        format='%(asctime)s %(levelname)s:%(message)s',
                        level=logging.INFO)
    logging.info('{0} v. {1} started'.format(NAME, VERSION))
    logging.info('Job name: {0}'.format(input_file_parameters.job_name))
    logging.info('Starting point directory:\n{0}'.format(dir_stacks[0]
                                                         .path))
    logging.info('Output directory:\n{0}'.format(input_file_parameters.output_dir))
    logging.info('-'*80)
    logging.info('staplefile contents:\n{0}'.format('\n'.join(input_file_parameters.staplefile)))
    logging.info('-'*80)
    logging.info('config.txt contents:\n{0}'
                 .format(utils.get_config_file()))
    logging.info('-'*80)


def infer_dir_stack(input_file_parameters, create_dirs, allow_existing_dirs = True):
    """Infers the directory tree structure required for current workflows.

Parameters:
input_file_parameters: Parameters user has defined in the input file.
create_dirs: Bool indicating if the predicted output directies should be
created if they do not exist.

Returns:
dir_stack: List of input/output directories for the run.

Raises:
NewDirExists: If an output directory exists already and allow_existing_dirs is False
"""
    dir_stack = [Directory(input_file_parameters.starting_point_directory,
                           create_dir=create_dirs)]
    directory_name_index = 1
    for i in xrange(len(input_file_parameters.commands)):
        if input_file_parameters.commands[i] in WORKFLOW_CONTROL_KEYWORDS: continue
        command_type, command_parameters = utils.parse_staplefile_command_line(input_file_parameters.commands[i])
        if command_type.require_output_dir:
            out_dir_name = ('{0}_{1}_{2}_{3}'.format(NAME,
                                                     input_file_parameters.job_name,
                                                     directory_name_index,
                                                     command_type.name))
            out_dir_path = os.path.join(input_file_parameters.project_dir, out_dir_name)
            if os.path.exists(out_dir_path) and not allow_existing_dirs:
                raise STAPLERerror.NewDirExists()
            out_dir_path = Directory(out_dir_path, create_dir=create_dirs)
            dir_stack.append(out_dir_path)
            directory_name_index += 1
    return dir_stack


def generate_command_line_objects(input_file_parameters, dir_stack, auto_split_workflows):
    """Generates commands to execute workflow for each input file.

Parameters:
job_name: Job name defined by the user.
input_cmds: Commands the user wishes to execute for each file in starting point
dir.
dir_stacks: List containing only the starting point directory

Raises:
STAPLERerror: Command type is not supported.
"""
    workflows = []
    prev_number_of_ids_per_command = None
    prev_command_had_output_dir = True
    first_command = True
    # Bools for splitting workflow. Separate values for automatically splitting workflow and
    # user defined splits, as user defined splits are applied in 'default' execute_mode, and
    # autosplits only when workflow is parallelized
    splitting_workflow_automatically = False
    user_splitting_workflow = False
    no_command_has_required_output_dir = True
    j = 0
    dir_stack_index = -1
    for current_command_type in input_file_parameters.commands:
        # Infer split points of workflow
        # Split workflow if user has inserted the SPLIT keyword in the STAPLEfile
        if current_command_type == 'SPLIT':
            user_splitting_workflow = True
            continue

        # If previous command had no output directory (i.e. output is created
        # to input directory), there is no need to increment the dir_stack index
        if prev_command_had_output_dir:
            dir_stack_index += 1

        # Reset id number tracking if workflow is split
        if splitting_workflow_automatically or user_splitting_workflow:
            first_command = True
            prev_number_of_ids_per_command = None

        current_step_commands = []
        command_type, command_parameters = \
            utils.parse_staplefile_command_line(current_command_type)
        in_dir = dir_stack[dir_stack_index]
        if command_type.require_output_dir:
            out_dir = dir_stack[dir_stack_index+1]
            prev_command_had_output_dir = True
            no_command_has_required_output_dir = False
        else:
            out_dir = in_dir
            prev_command_had_output_dir = False
        #Read files until command class finds no more valid input files
        while True:
            try:
                current_command = command_type(command_parameters, in_dir, out_dir)
                # Check if workflow should be split (if user has defined automatic splitting)
                if not first_command and auto_split_workflows:
                    if len(current_command.command_ids) > prev_number_of_ids_per_command:
                        splitting_workflow_automatically = True

                current_step_commands.append(current_command)
                logging.info('-'*80)
                logging.info('User command line:\n{0}'.format(input_file_parameters.commands[dir_stack_index]))
                logging.info('Final command line(s):\n{0}'.format(
                    '\n'.join(current_command.command_lines)))
                logging.info('Input directory is:\n{0}'.format(in_dir.path))
                logging.info('Output directory is:\n{0}'.format(out_dir
                                                                .path))
                j += 1
                print 'Created command line number {0} for {1}...'\
                    .format(j, command_type.name)
            except STAPLERerror.NewFileExists as existing_file_name:
                if no_command_has_required_output_dir:
                    raise STAPLERerror.STAPLERerror('Starting point directory '
                                                    'already contains file '
                                                    'name {0}, which {1} '
                                                    'command would overwrite. '
                                                    'Either remove {1} from '
                                                    'this workflow or remove '
                                                    '{0} and similar files '
                                                    'from the starting point '
                                                    'directory. Notice that '
                                                    '--REMOVE command will '
                                                    'not delete any files '
                                                    'from the starting point '
                                                    'directory.'
                                                    .format(existing_file_name,
                                                            command_type.name))
                raise STAPLERerror.STAPLERerror('File with name {0} already '
                                                'exists in the output '
                                                'directory {1}. Remove the '
                                                'existing workflow or use the '
                                                '--FIX_RUN feature to create '
                                                'a fixed run.'.format(existing_file_name, out_dir.path))
            except STAPLERerror.VirtualIOError:
                break
            except STAPLERerror.NotConfiguredError:
                raise STAPLERerror.STAPLERerror('Trying to create command '
                                                'lines for {0}, '
                                                'but config.txt is missing '
                                                'configuration for this '
                                                'command. Edit config.txt '
                                                'appropriately or refer to '
                                                'manual to see how '
                                                'to do this.'.format(command_type.name))
        if not current_step_commands:
            raise STAPLERerror.STAPLERerror('No proper existing or predicted '
                                            'input files were found for '
                                            'command {0} in the input '
                                            'directory:\n{1}\nThis command '
                                            'takes input files only in the '
                                            'following formats:\n{2}\nInput '
                                            'directory is predicted to '
                                            'contain the following files:\n{'
                                            '3}'.format(command_type.name,
                                                        in_dir.path,
                                                        '\n'.join(command_type.input_types),
                                                        ', '.join(in_dir.file_names.keys())))
        if first_command:
            workflows.append([current_step_commands])
            first_command = False
        else:
            if not splitting_workflow_automatically and not user_splitting_workflow:
                workflows[-1] += [current_step_commands]
            else:
                workflows.append([current_step_commands])
        prev_number_of_ids_per_command = len(current_command.command_ids)
        splitting_workflow_automatically = False
        user_splitting_workflow = False

    return workflows, dir_stack


def regenerate_command_line_objects(input_file_parameters, dir_stack,
                                   auto_split_workflows):
    """Generates command lines that have not been successfully executed.

Parameters:
job_name: Job name defined by the user.
input_cmds: Commands the user wishes to execute for each file in starting point
dir.
dir_stacks: List containing only the starting point directory

Raises:
STAPLERerror: Command type is not supported.
"""
    workflows = []
    prev_number_of_ids_per_command = None
    prev_command_had_output_dir = True
    first_command = True
    # Bools for splitting workflow. Separate values for automatically splitting workflow and
    # user defined splits, as user defined splits are applied in 'default' execute_mode, and
    # autosplits only when workflow is parallelized
    splitting_workflow_automatically = False
    user_splitting_workflow = False
    j = 0
    dir_stack_index = -1
    for current_command_type in input_file_parameters.commands:
        # Infer split points of workflow
        # Split workflow if user has inserted the SPLIT keyword in the STAPLEfile
        if current_command_type == 'SPLIT':
            user_splitting_workflow = True
            continue

        # If previous command had no output directory (i.e. output is created
        # to input directory), there is no need to increment the dir_stack index
        if prev_command_had_output_dir:
            dir_stack_index += 1

        # Reset id number tracking if workflow is split
        if splitting_workflow_automatically or user_splitting_workflow:
            first_command = True
            prev_number_of_ids_per_command = None

        current_step_commands = []
        command_type, command_parameters = \
            utils.parse_staplefile_command_line(current_command_type)
        in_dir = dir_stack[dir_stack_index]
        if command_type.require_output_dir:
            out_dir = dir_stack[dir_stack_index+1]
            prev_command_had_output_dir = True
        else:
            out_dir = in_dir
            prev_command_had_output_dir = False

        # Read files until command class finds no more valid input files
        successfull_commands = 0
        current_command = None
        while True:
            try:
                # The command instance is generated without exceptions if the
                #  command execution has failed (i.e. expected output
                # file does not exist). Otherwise NewFileError is raised.
                current_command = command_type(command_parameters, in_dir, out_dir)
            except STAPLERerror.NewFileExists:
                successfull_commands += 1
                continue
            except STAPLERerror.VirtualIOError:
                break
            except STAPLERerror.NotConfiguredError:
                raise STAPLERerror.STAPLERerror('Trying to create command '
                                                'lines for {0}, '
                                                'but config.txt is missing '
                                                'configuration for this '
                                                'command. Edit config.txt '
                                                'appropriately or refer to '
                                                'manual to see how '
                                                'to do this.'.format(command_type.name))

            # If command can be created, check if the workflow should be split
            # automatically (when user has defined automatic splitting)
            if not first_command and auto_split_workflows:
                if len(current_command.command_ids) > prev_number_of_ids_per_command:
                    splitting_workflow_automatically = True
            current_step_commands.append(current_command)
            logging.info('-'*80)
            logging.info('User command line:\n{0}'.format(input_file_parameters.commands[dir_stack_index]))
            logging.info('Final command line(s):\n{0}'.format(
                '\n'.join(current_command.command_lines)))
            logging.info('Input directory is:\n{0}'.format(in_dir.path))
            logging.info('Output directory is:\n{0}'.format(out_dir
                                                            .path))
            j += 1
        if not current_step_commands and not successfull_commands:
            raise STAPLERerror.STAPLERerror('No proper existing or predicted '
                                            'input files were found for '
                                            'command {0} in the input '
                                            'directory:\n{1}\nThis command '
                                            'takes input files only in the '
                                            'following formats:\n{2}\nInput '
                                            'directory is predicted to '
                                            'contain the following files:\n{'
                                            '3}'.format(command_type.name,
                                                        in_dir.path,
                                                        '\n'.join(command_type.input_types),
                                                        ', '.join(in_dir.file_names.keys())))
        print '{0} command (step number {1}) was regenerated {2} ' \
              'times'.format(command_type.name, dir_stack_index+1, len(current_step_commands))
        if current_step_commands:
            if first_command:
                workflows.append([current_step_commands])
                first_command = False
            elif current_command is not None:
                if not splitting_workflow_automatically and not user_splitting_workflow:
                    workflows[-1] += [current_step_commands]
                else:
                    workflows.append([current_step_commands])

        if current_command is None:
            prev_number_of_ids_per_command = -1
        else:
            prev_number_of_ids_per_command = len(current_command.command_ids)
        splitting_workflow_automatically = False
        user_splitting_workflow = False

    return workflows, dir_stack


def check_run_logs(input_file_parameters, dir_stack):
    """Analyzes output out and error files and reports putative errors.

Parameters:
input_file_parameters: Run parameters defined in the staplefile.
dir_stacks: List containing only the starting point directory

Raises:
STAPLERerror: Command type is not supported.

Side-effects:
prints: Error messages encountered within .out and .err files produced by
resource managers.
"""
    # Check resource manager produced .out and .err files for assumed error
    # messages.
    print 'Checking runtime log files for error messages...'
    file_names = os.listdir(input_file_parameters.output_dir)

    newest_fix_index = 0
    files_to_check = []
    for file_name in sorted(file_names):
        if file_name.endswith('.out') or file_name.endswith('.err'):
            if file_name.startswith('FIX_'):
                current_fix_index = file_name.split('_')[1]
                if int(current_fix_index) > newest_fix_index:
                    newest_fix_index = current_fix_index
                    files_to_check = [file_name]
                else:
                    files_to_check.append(file_name)
            if newest_fix_index == 0:
                files_to_check.append(file_name)

    if newest_fix_index > 0:
        print 'Workflow has been fixed {0} times. Checking only the {1} .out ' \
              'and .err files of the newest run.'.format(newest_fix_index,
                                                         len(files_to_check))

    i = 0
    number_of_warnings = 0
    number_of_canceled_threads = 0
    warning_strings = ['invalid', 'exception', 'warning']
    error_strings = ['error', 'segmentation fault', 'canceled', '(err):']
    skip_strings = ['adapters with at most',
                    'no. of allowed errors',
                    'error counts']
    for file_name in files_to_check:
        handle = open(os.path.join(input_file_parameters.output_dir,
                                      file_name))

        i += 1
        finish_string_exists = False
        warning_messages = []
        error_messages = []
        j = 0
        for line in handle:
            j += 1
            line = line.lower()
            if any(s in line for s in skip_strings):
                continue
            if any(w in line for w in warning_strings):
                warning_messages.append(j)
                number_of_warnings += 1
            if any(e in line for e in error_strings):
                error_messages.append(j)
                number_of_warnings += 1
            if 'finished at:' in line:
                finish_string_exists = True
        if os.path.splitext(file_name)[1]  == '.out':
            if not finish_string_exists:
                error_messages.append('This thread has not been finished:\n{0}'
                                      .format(os.path.join(input_file_parameters.output_dir,
                                                           file_name)))

        if warning_messages or error_messages:
            print '\n\nThe following file contains possible warning/error messages:'
            print os.path.join(input_file_parameters.output_dir, file_name)
        if len(warning_messages) != 0:
            print '\nWarning messages on lines:'
            print ', '.join(map(str, warning_messages))
        if len(error_messages) != 0:
            print '\nError messages on lines:'
            print ', '.join(map(str, error_messages))

    print '\n\n{0} .out and .err files checked ({1} processes)'.format(i, i/2)
    print 'Potential problems detected: {0}'.format(number_of_warnings)


def validate_run_results(input_file_parameters, dir_stack):
    """Reports which commands have not been successfully run.

Commands found in staplefile are compared with files found in directory stack
to identify which commands have failed.

Parameters:
input_file_parameters: Run parameters defined in the staplefile.
dir_stacks: List containing only the starting point directory

Raises:
STAPLERerror: Command type is not supported.

Side-effects:
prints: Numbers of commands that have failed during runtime.
"""
    dir_stack_index = 0
    command_index = 0
    for current_command in input_file_parameters.commands:
        # Skip over SPLIT commands
        if current_command == 'SPLIT':
            continue

        command_index += 1

        # Keep track of number of commands created in the current workflow step
        number_of_successful_commands = 0

        # Infer command type, parameters, input and output directories
        command_type, command_parameters = \
            utils.parse_staplefile_command_line(current_command)
        in_dir = dir_stack[dir_stack_index]
        if command_type.require_output_dir:
            out_dir = dir_stack[dir_stack_index+1]
        else:
            out_dir = in_dir

        # Read files until command class finds no more valid input files
        number_of_potential_commands = 0
        while True:
            try:
                # The command instance is generated without exceptions if the
                #  command execution has failed (i.e. expected output
                # file does not exist). Otherwise NewFileError is raised.
                current_command = command_type(command_parameters, in_dir, out_dir)
            except STAPLERerror.NewFileExists:
                number_of_successful_commands += 1
                number_of_potential_commands += 1
                continue
            except STAPLERerror.VirtualIOError:
                break
            number_of_potential_commands += 1

        # Print validation results
        if not number_of_successful_commands:
            print '{0} command (step number {1}) has not been run.' \
                .format(command_type.name, command_index)
            continue
        if number_of_successful_commands == number_of_potential_commands:
            print '{0} command (step number {1}) has been run succesfully.' \
                .format(command_type.name, command_index)
        else:
            print '{0} command (step number {1}) workflows have failed {2}/{3} times' \
                .format(command_type.name, command_index,
                        number_of_potential_commands - number_of_successful_commands,
                        number_of_potential_commands)

        # Increment index if command requires output directory
        if command_type.require_output_dir:
            dir_stack_index += 1


def log_dir_stacks_contents(dir_stacks):
    """Write data to log file on predicted directory contents.

    Parameters:
    dir_stacks: List of predicted directories (Directory-objects).
    """
    for directory in dir_stacks:
        logging.info('-'*80)
        logging.info('Predicted directory contents of:\n{0}'
                     .format(directory.path))
        files = directory.file_names
        files = sorted(files)
        logging.info('Number of files: {0}'.format(len(files)))
        logging.info('Files:')
        logging.info('\t'.join(files))


def write_default(workflows, output_dir):
    """Writes the output in simple shell script format.

    The default format is a shell script file containing the command lines.

    Parameters:
    workflows: List of command objects.
    output_dir: Directory to write the output to.

    Raises:
    STAPLERerror: Unable to open output file.
    """

    # Calculate the total number of commands
    number_of_commands = 0
    for workflow in workflows:
        number_of_commands += sum(map(len, workflow))

    # Create command line strings
    i = 0
    out_lines = ['echo Started executing shell script at:', 'date']
    for workflow in workflows:
        for workflow_step in workflow:
            for cmd in workflow_step:
                i += 1
                cmd_list = cmd.command_lines
                cmd_list = map(clean_command_lines, cmd_list)
                out_lines.append('echo Executing command {0}/{1}:'
                                 .format(i, number_of_commands))
                for c in cmd_list:
                    c = c.replace('>', '\\>')
                    c = c.replace('|', '\\|')
                    out_lines.append('echo ' + c)
                out_lines.append('date')

                #Load modules
                if cmd.load_module:
                    for module in cmd.load_module:
                        out_lines.append(module)

                #The command
                out_lines += cmd_list

                #Unload modules
                if cmd.unload_module:
                    for module in cmd.unload_module:
                        out_lines.append(module)
    out_lines.append('echo Finished at:')
    out_lines.append('date')

    #Open and write command lines
    fl_name = '{0}_output_{1}.sh'.format(NAME, START_TIME)
    output_file_path = os.path.join(output_dir, fl_name)
    try:
        out_fl = open(output_file_path, 'w')
    except:
        raise STAPLERerror.STAPLERerror('Unable to create output file:'
                                    '\n{0}'.format(os.path.join(output_dir,
                                                                fl_name)))
    out_fl.write('#!/usr/bin/env bash\n')
    out_fl.write('\n'.join(out_lines))
    out_fl.close()
    return [output_file_path]


def determine_job_workloads(workloads, command_line_parameters):
    """Infer the number of threads to create and allocate commands to each.

    Parameters:
    workloads: Output commands grouped by the workflow step (i.e. command type)
    max_job_count: Maximum number of separate jobs to spawn
    Returns:
    parallelized_workloads: Output commands grouped by execution threads.
    """
    # Group commands by id
    parallelized_workloads = []
    i = 0
    for workflow in workloads:
        i += 1
        # Workflow is split by user with SPLIT command or automatically split
        #  at brach/join events
        thread_allocation_indexes = infer_id_groups(workflow,
                                                    command_line_parameters)
        current_workflow_threads = [[] for i in range(max(thread_allocation_indexes.values())+1)]
        for workflow_step in workflow:
            k = 0
            for output_cmd in workflow_step:
                k += 1
                # Check that each command is allocated to a single thread only
                assert len(set([thread_allocation_indexes[d] for d in output_cmd.command_ids])) == 1
                # Safe to use only the first id of each command as all point to same thread index
                current_workflow_threads[thread_allocation_indexes[output_cmd.command_ids[0]]].append(output_cmd)
        parallelized_workloads.append(current_workflow_threads)
    return parallelized_workloads


def infer_id_groups(workflow, command_line_parameters):
    """Infer which ids should be run in the same thread.

    Parameters
    workflow: List of command objects
    max_job_count: maximum number of jobs to create
    Returns:
    id_set_indexes: A dictionary of command id : index of allocated thread (allows for quick allocation of ids)
    """
    # Find the step in the current workflow with the highest number of ids
    # per command and group ids based on that (as a starting point).
    workflow_step_index_with_max_ids_per_cmd = 0
    max_ids = 0
    for workflow_step_index in xrange(len(workflow)):
        # Only check the number of command_ids on the first command of a given step
        # for performance reasons
        n_ids_of_first_cmd_of_step = len(workflow[workflow_step_index][0].command_ids)
        if n_ids_of_first_cmd_of_step > max_ids:
            max_ids = n_ids_of_first_cmd_of_step
            workflow_step_index_with_max_ids_per_cmd = workflow_step_index
    id_sets = []
    all_assigned_ids = {}
    for command in workflow[workflow_step_index_with_max_ids_per_cmd]:
        # Assert that each id is used only once
        for current_id in command.command_ids:
            if current_id in all_assigned_ids:
                raise STAPLERerror('STAPLER generates a unique ID for each '
                                   'file by removing all file extensions. '
                                   'Therefore same basename cannot exist in '
                                   'the input directory with different file '
                                   'extensions. This seems to be the for '
                                   'ID "{0}". Remove or '
                                   'rename one of the input files with '
                                   'this basename (or if using a CUSTOM '
                                   'command, define the input file type '
                                   'in the command), and then rerun '
                                   'STAPLER.'.format(current_id))
            all_assigned_ids[current_id] = command.command_lines
        id_sets.append(set(command.command_ids))

    all_assigned_ids = set(all_assigned_ids.keys())

    # In the above code some ids may remain unassigned in a workflow containing
    # multiple steps where multiple input files are combined into a single
    # one. Here any unassigned ids are added to an appropriate id_set.
    if len(workflow) > 1:
        for workflow_step in workflow:
            for cmd in workflow_step:
                current_command_id_set = set(cmd.command_ids)
                if not current_command_id_set.issubset(all_assigned_ids):
                    # i.e. at least one id of this command has not been assigned yet
                    # --> Find if the command has another id, which has been
                    # assigned to an id_set. Add the other id to the same set too.
                    assigned_id = current_command_id_set.intersection(all_assigned_ids)

                    # When fixing an existing run, it may not be possible to
                    # combine id with other id this way. In those cases create
                    # own id set for these commands.
                    if not assigned_id:
                        id_sets.append(current_command_id_set)
                        for current_id in current_command_id_set:
                            all_assigned_ids.add(current_id)
                        continue

                    assigned_id = list(assigned_id)[0]
                    for id_set in id_sets:
                        if assigned_id in id_set:
                            for unassigned_id in current_command_id_set.difference(all_assigned_ids):
                                id_set.add(unassigned_id)
                                all_assigned_ids.add(unassigned_id)
                            break

    # Check if some index sets should be combined. This may be necessary if
    # different commands take multiple input files in different parts of the
    # workflow but the input file sets are not the same for different
    # commands. This is mainly a theoretical concern and pretty much only
    # possible when using the Custom command type.
    if len(workflow) > 1:
        for command_step in workflow:
            for command in command_step:
                ids = command.command_ids
                indexes_to_combine = []
                i = 0
                for id_set in id_sets:
                    if set(ids) & id_set:
                        indexes_to_combine.append(i)
                    i += 1
                # If command_ids of any command overlap with more than one
                # id_set, the id_sets are combined.
                while len(indexes_to_combine) > 1:
                    id_sets[min(indexes_to_combine)] = \
                        id_sets[min(indexes_to_combine)].union(id_sets[max(indexes_to_combine)])
                    del id_sets[max(indexes_to_combine)]
                    indexes_to_combine.remove(max(indexes_to_combine))


    # Infer if some ids disappear along the workflow
    if len(workflow) > 1:
        omitted_ids = set([])
        for workflow_step in workflow:
            for cmd in workflow_step:
                for cmd_id in cmd.command_ids:
                    if cmd_id not in all_assigned_ids:
                        omitted_ids.add(cmd_id)

        if omitted_ids:
            raise STAPLERerror.STAPLERerror('Encountered at least one filename id, '
                                            'that disappears during workflow. This may happen '
                                            'if you have several file types in the input '
                                            'directory. Try using an explicit filename '
                                            'extension with Custom-type commands or remove '
                                            'files not intended for workflow input from your '
                                            'input directory. The file names of the odd IDs '
                                            'are: {0}'.format(' '.join(list(omitted_ids))))

    # Create a dictionary with id : thread_index for fast allocation of
    # commands to threads
    id_set_indexes = {}
    i = 0
    for current_id_set in id_sets:
        for current_id in current_id_set:
            id_set_indexes[current_id] = i
        i += 1
        # If i exceeds max_job_count, add command to an existing thread
        if command_line_parameters.max_job_count is not None:
            while i > command_line_parameters.max_job_count-1:
                i = i-command_line_parameters.max_job_count
    return id_set_indexes


def write_lsf(workloads, input_file_parameters, command_line_parameters):
    """Writes the output in LSF job array format.

    Creates sub shell scripts that contain the workflow for each input
    file separately. After this main shell script containing TORQUE
    configuration is created. This script is responsible for starting
    the sub shells as separate processes.

    Parameters:
    workloads: Output commands grouped by execution threads
    input_file_parameters: Run parameters defined in the staplefile.
    command_line_parameters: Named tuple containing parameters defined by
    user's command line

    Raises:
    STAPLERerror: Unable to open output file.
    """
    workload_index = 0
    workload_zfill_amount = len(str(len(workloads)))
    workload_file_paths = []
    for workload in workloads:
        # Each workflow part will have separate file to submit to TORQUE with
        # sbatch command. Each file has one or more associated subshell files
        # containing contents for each thread.

        # Generate strings describing current workload and thread indexes for
        # output file names
        workload_index += 1
        workload_index_string = str(workload_index).zfill(workload_zfill_amount)
        file_main_name = '{0}_LSF_WORKLOAD_{1}'.format(NAME,
                                                          workload_index_string)

        # When --FIX_RUN mode is used the output and log files files already
        # exist. To prevent overwriting these files with new ones specific
        # prefix or appendix strings are added to the new output file names.
        appendix = '.sh'
        i = 0
        if command_line_parameters.fix_run:
            mode = 'FIX'
        elif command_line_parameters.compress_run == 'compress':
            mode = 'COMPRESS'
        elif command_line_parameters.compress_run == 'decompress':
            mode = 'DECOMPRESS'
        else:
            mode = None
        while mode is not None and os.path.exists(os.path.join(input_file_parameters.output_dir,
                                                               file_main_name + appendix)):
            i += 1
            appendix = '_{0}_{1}.sh'.format(mode, i)

        # Generate subshell files
        thread_index = 0
        for thread_contents in workload:
            # Iterate over output commands of each thread and write necessary
            # subshell files for each
            out_lines = []
            for cmd in thread_contents:
                out_lines += generate_subshell_file_contents(cmd)

            # Write subshell file
            thread_index_string = str(thread_index)
            fl_name = '{0}_WORKLOAD_{1}_subshell_{2}{3}'.format(NAME,
                                                                workload_index_string,
                                                                thread_index_string,
                                                                appendix)
            try:
                out_fl = open(os.path.join(input_file_parameters.output_dir,
                                           fl_name), 'w')
            except:
                raise STAPLERerror.STAPLERerror('Unable to create output file:'
                                                '\n{0}'.format(os.path.join(
                    input_file_parameters.output_dir,
                    fl_name)))
            out_fl.write('\n'.join(out_lines))
            out_fl.write('\n')
            out_fl.close()
            thread_index += 1

        # Generate parameter file for the bsub run
        resmng_config = []
        resmng_config.append('#BSUB-J "{0}[1-{1}]"'.format(
            input_file_parameters.job_name,
            len(workload)))
        resmng_config.append('#BSUB-i {0}_WORKLOAD_{1}_subshell_{2}{3}'.format(
            NAME,
            workload_index_string,
            '%I',
            appendix))
        resmng_config.append('#BSUB-o {0}_WORKLOAD_{1}_subshell_{2}{3}.out'.format(
            NAME,
            workload_index_string,
            '%I',
            appendix))
        resmng_config += input_file_parameters.resource_manager_params

        out_fl_path = os.path.join(input_file_parameters.output_dir, file_main_name + appendix)
        workload_file_paths.append(out_fl_path)
        try:
            out_fl = open(out_fl_path, 'w')

        except IOError as emsg:
            raise STAPLERerror.STAPLERerror('Unable to create output file:'
                                            '\n{0}\n with error message:\n{1}'
                                            .format(os.path.join(input_file_parameters.output_dir,
                                                                 file_main_name + appendix),
                                                    str(emsg)))
        out_fl.write('\n'.join(resmng_config))
        out_fl.write('\n')
        out_fl.close()
    return workload_file_paths


def write_sge(workloads, input_file_parameters, command_line_parameters):
    """Writes the output in Sun Grid Engine job array submission format.

    Creates sub shell scripts that contain the workflow for each input
    file separately. After this main shell script containing SGE
    configuration is created. This script is responsible for starting
    the sub shells as separate processes.

    Parameters:
    workloads: Output commands grouped by execution threads
    input_file_parameters: Run parameters defined in the staplefile.
    command_line_parameters: Named tuple containing parameters defined by
    user's command line

    Raises:
    STAPLERerror: Unable to open output file.
    """
    validate_resource_manager_parameters(
        input_file_parameters.resource_manager_params,
        ['# -o', '# -e', '# -t'])

    workload_index = 0
    workload_zfill_amount = len(str(len(workloads)))
    workload_file_paths = []
    for workload in workloads:
        # Each workflow part will have separate file to submit to TORQUE with
        # sbatch command. Each file has one or more associated subshell files
        # containing contents for each thread.

        # Generate strings describing current workload and thread indexes for
        # output file names
        workload_index += 1
        workload_index_string = str(workload_index).zfill(workload_zfill_amount)
        file_main_name = '{0}_SGE_WORKLOAD_{1}'.format(NAME,
                                                       workload_index_string)

        # When --FIX_RUN mode is used the output and log files files already
        # exist. To prevent overwriting these files with new ones specific
        # prefix or appendix strings are added to the new output file names.
        prefix = ''
        appendix = '.sh'
        i = 0
        if command_line_parameters.fix_run:
            mode = 'FIX'
        elif command_line_parameters.compress_run == 'compress':
            mode = 'COMPRESS'
        elif command_line_parameters.compress_run == 'decompress':
            mode = 'DECOMPRESS'
        else:
            mode = None
        while mode is not None and os.path.exists(os.path.join(input_file_parameters.output_dir,
                                                               file_main_name + appendix)):
            i += 1
            prefix = '{0}_{1}_'.format(mode, i)
            appendix = '_{0}_{1}.sh'.format(mode, i)

        # Generate subshell files
        thread_index = 1
        for thread_contents in workload:
            # Iterate over output commands of each thread and write necessary
            # subshell files for each
            out_lines = []
            for cmd in thread_contents:
                out_lines += generate_subshell_file_contents(cmd)

            # Write subshell file
            thread_index_string = str(thread_index)
            fl_name = '{0}_WORKLOAD_{1}_subshell_{2}{3}'.format(NAME,
                                                                workload_index_string,
                                                                thread_index_string,
                                                                appendix)
            try:
                out_fl = open(os.path.join(input_file_parameters.output_dir,
                                           fl_name), 'w')
            except:
                raise STAPLERerror.STAPLERerror('Unable to create output file:'
                                                '\n{0}'.format(os.path.join(
                    input_file_parameters.output_dir,
                    fl_name)))
            out_fl.write('\n'.join(out_lines))
            out_fl.write('\n')
            out_fl.close()
            thread_index += 1

        # Create lines for SGE input file by generating job-name, output,
        # error and array parameters based on user input

        status_file_basename = os.path.join(input_file_parameters.output_dir,
                                            prefix +
                                            input_file_parameters.job_name + '_$TASK_ID')

        # IF YOU ADD NEW AUTOMATICALLY INFERRED PARAMETERS, REMEMBER TO VALIDATE
        # THEM AT THE BEGINNING OF THIS FUNCTION
        resmng_config = list(input_file_parameters.resource_manager_params)
        resmng_config.append('#$ -o {0}.out'.format(status_file_basename))
        resmng_config.append('#$ -e {0}.err'.format(status_file_basename))
        resmng_config.append('#$ -t {0}-{1}'.format(1, len(workload)))

        resmng_config.append('\n\n')
        subshell_file_path = '{0}_WORKLOAD_{1}_subshell_{2}{3}'.format(NAME,
                                                                       workload_index_string,
                                                                       '"$SGE_TASK_ID"',
                                                                       appendix)
        subshell_file_path = os.path.join(input_file_parameters.output_dir,
                                          subshell_file_path)
        resmng_config.append('source {0}'.format(subshell_file_path))

        out_fl_path = os.path.join(input_file_parameters.output_dir,
                                   file_main_name + appendix)
        workload_file_paths.append(out_fl_path)
        try:
            out_fl = open(out_fl_path, 'w')

        except IOError as emsg:
            raise STAPLERerror.STAPLERerror('Unable to create output file:'
                                            '\n{0}\n with error message:\n{1}'
                                            .format(os.path.join(input_file_parameters.output_dir,
                                                                 file_main_name + appendix),
                                                    str(emsg)))
        out_fl.write('\n'.join(resmng_config))
        out_fl.write('\n')
        out_fl.close()
    return workload_file_paths


def write_slurm(workloads, input_file_parameters, command_line_parameters):
    """Writes the output in SLURM array job format.

    Creates sub shell scripts that contain the workflow for each input
    file separately. After this main shell script containing SLURM
    configuration is created. This script is responsible for starting
    the sub shells as separate processes.

    Parameters:
    workloads: Output commands grouped by execution threads
    input_file_parameters: Run parameters defined in the staplefile.
    command_line_parameters: Named tuple containing parameters defined by
    user's command line

    Raises:
    STAPLERerror: Unable to open output file.
    """
    workload_index = 0
    workload_zfill_amount = len(str(len(workloads)))
    workload_file_paths = []
    for workload in workloads:
        # Each workflow part will have separate file to submit to SLURM with
        # sbatch command. Each file has one or more associated subshell files
        # containing contents for each thread.

        # Generate strings describing current workload and thread indexes for
        # output file names
        workload_index += 1
        workload_index_string = str(workload_index).zfill(workload_zfill_amount)
        file_main_name = '{0}_SBATCH_WORKLOAD_{1}'.format(NAME,
                                                              workload_index_string)

        # When --FIX_RUN mode is used the output and log files files already
        # exist. To prevent overwriting these files with new ones specific
        # prefix or appendix strings are added to the new output file names.
        appendix = '.sh'
        prefix = ''
        i = 0
        if command_line_parameters.fix_run:
            mode = 'FIX'
        elif command_line_parameters.compress_run == 'compress':
            mode = 'COMPRESS'
        elif command_line_parameters.compress_run == 'decompress':
            mode = 'DECOMPRESS'
        else:
            mode = None

        while mode is not None and os.path.exists(os.path.join(input_file_parameters.output_dir,
                                                               file_main_name + appendix)):
            i += 1
            prefix = '{0}_{1}_'.format(mode, i)
            appendix = '_{0}_{1}.sh'.format(mode, i)

        # Generate subshell files
        thread_index = 0
        for thread_contents in workload:
            # Iterate over output commands of each thread and write necessary
            # subshell files for each
            out_lines = []
            for cmd in thread_contents:
                out_lines += generate_subshell_file_contents(cmd)

            # Write subshell file
            thread_index += 1
            thread_index_string = str(thread_index)
            fl_name = '{0}_WORKLOAD_{1}_subshell_{2}{3}'.format(NAME,
                                                                workload_index_string,
                                                                thread_index_string,
                                                                appendix)
            try:
                out_fl = open(os.path.join(input_file_parameters.output_dir,
                                           fl_name), 'w')
            except:
                raise STAPLERerror.STAPLERerror('Unable to create output file:'
                                                '\n{0}'.format(os.path.join(
                    input_file_parameters.output_dir,
                    fl_name)))
            out_fl.write('\n'.join(out_lines))
            out_fl.write('\n')
            out_fl.close()

        # Create lines for SLURM input file by generating job-name, output,
        # error and array parameters based on user input
        status_file_basename = os.path.join(input_file_parameters.output_dir,
                                            prefix + input_file_parameters.job_name)
        resmng_config = list(input_file_parameters.resource_manager_params)
        resmng_config.append('#SBATCH --job-name={0}'.format(input_file_parameters.job_name))
        resmng_config.append('#SBATCH --output={0}_%A_%a.out'.format(status_file_basename))
        resmng_config.append('#SBATCH --error={0}_%A_%a.err'.format(status_file_basename))
        resmng_config.append('#SBATCH --array={0}-{1}'.format(1, len(workload)))

        resmng_config.append('\n\n')
        subshell_file_path = '{0}_WORKLOAD_{1}_subshell_{2}{3}'.format(NAME,
                                                                       workload_index_string,
                                                                       '"$SLURM_ARRAY_TASK_ID"',
                                                                       appendix)
        subshell_file_path = os.path.join(input_file_parameters.output_dir,
                                          subshell_file_path)
        resmng_config.append('source {0}'.format(subshell_file_path))

        out_fl_path = os.path.join(input_file_parameters.output_dir,file_main_name + appendix)
        workload_file_paths.append(out_fl_path)
        try:
            out_fl = open(out_fl_path, 'w')

        except IOError as emsg:
            raise STAPLERerror.STAPLERerror('Unable to create output file:'
                                            '\n{0}\n with error message:\n{1}'
                                            .format(os.path.join(input_file_parameters.output_dir,
                                                                 file_main_name + appendix),
                                                    str(emsg)))
        out_fl.write('\n'.join(resmng_config))
        out_fl.write('\n')
        out_fl.close()
    return workload_file_paths


def write_torque(workloads, input_file_parameters, command_line_parameters):
    """Writes the output in TORQUE multiple job submission format.

    Creates sub shell scripts that contain the workflow for each input
    file separately. After this main shell script containing TORQUE
    configuration is created. This script is responsible for starting
    the sub shells as separate processes.

    Parameters:
    workloads: Output commands grouped by execution threads
    input_file_parameters: Run parameters defined in the staplefile.
    command_line_parameters: Named tuple containing parameters defined by
    user's command line

    Raises:
    STAPLERerror: Unable to open output file.
    """
    validate_resource_manager_parameters(
        input_file_parameters.resource_manager_params,
        ['#PBS -k', '#PBS -N', '#PBS -d', '#PBS -e', '#PBS -t'])

    workload_index = 0
    workload_zfill_amount = len(str(len(workloads)))
    workload_file_paths = []
    for workload in workloads:
        # Each workflow part will have separate file to submit to TORQUE with
        # sbatch command. Each file has one or more associated subshell files
        # containing contents for each thread.

        # Generate strings describing current workload and thread indexes for
        # output file names
        workload_index += 1
        workload_index_string = str(workload_index).zfill(workload_zfill_amount)
        file_main_name = '{0}_TORQUE_WORKLOAD_{1}'.format(NAME,
                                                          workload_index_string)

        # When --FIX_RUN mode is used the output and log files files already
        # exist. To prevent overwriting these files with new ones specific
        # prefix or appendix strings are added to the new output file names.
        appendix = '.sh'
        i = 0
        if command_line_parameters.fix_run:
            mode = 'FIX'
        elif command_line_parameters.compress_run == 'compress':
            mode = 'COMPRESS'
        elif command_line_parameters.compress_run == 'decompress':
            mode = 'DECOMPRESS'
        else:
            mode = None
        while mode is not None and os.path.exists(os.path.join(input_file_parameters.output_dir,
                                                               file_main_name + appendix)):
            i += 1
            appendix = '_{0}_{1}.sh'.format(mode, i)

        # Generate subshell files
        thread_index = 0
        for thread_contents in workload:
            # Iterate over output commands of each thread and write necessary
            # subshell files for each
            out_lines = []
            for cmd in thread_contents:
                out_lines += generate_subshell_file_contents(cmd)

            # Write subshell file
            thread_index_string = str(thread_index)
            fl_name = '{0}_WORKLOAD_{1}_subshell_{2}{3}'.format(NAME,
                                                                workload_index_string,
                                                                thread_index_string,
                                                                appendix)
            try:
                out_fl = open(os.path.join(input_file_parameters.output_dir,
                                           fl_name), 'w')
            except:
                raise STAPLERerror.STAPLERerror('Unable to create output file:'
                                                '\n{0}'.format(os.path.join(
                    input_file_parameters.output_dir,
                    fl_name)))
            out_fl.write('\n'.join(out_lines))
            out_fl.write('\n')
            out_fl.close()
            thread_index += 1

        # Create lines for TORQUE input file by generating job-name, output,
        # error and array parameters based on user input

        # IF YOU ADD NEW AUTOMATICALLY INFERRED PARAMETERS, REMEMBER TO VALIDATE
        # THEM AT THE BEGINNING OF THIS FUNCTION
        resmng_config = list(input_file_parameters.resource_manager_params)
        resmng_config.append('#PBS -k eo')
        resmng_config.append('#PBS -N {0}'.format(input_file_parameters.job_name))
        resmng_config.append('#PBS -d {0}'.format(input_file_parameters.output_dir))
        resmng_config.append('#PBS -e {0}'.format(input_file_parameters.output_dir))
        resmng_config.append('#PBS -t {0}-{1}'.format(0, len(workload)-1))

        resmng_config.append('\n\n')
        subshell_file_path = '{0}_WORKLOAD_{1}_subshell_{2}{3}'.format(NAME,
                                                                       workload_index_string,
                                                                       '"${PBS_ARRAYID}"',
                                                                       appendix)
        subshell_file_path = os.path.join(input_file_parameters.output_dir,
                                          subshell_file_path)
        resmng_config.append('source {0}'.format(subshell_file_path))

        out_fl_path = os.path.join(input_file_parameters.output_dir,file_main_name + appendix)
        workload_file_paths.append(out_fl_path)
        try:
            out_fl = open(out_fl_path, 'w')
        except IOError as emsg:
            raise STAPLERerror.STAPLERerror('Unable to create output file:'
                                            '\n{0}\n with error message:\n{1}'
                                            .format(os.path.join(input_file_parameters.output_dir,
                                                                 file_main_name + appendix),
                                                    str(emsg)))
        out_fl.write('\n'.join(resmng_config))
        out_fl.write('\n')
        out_fl.close()
    return workload_file_paths


def write_unix(workloads, input_file_parameters, command_line_parameters):
    """Writes a parallelized workflow by using UNIX run background feature (&).

    Creates sub shell scripts that contain the workflow for each input
    file separately. After this main shell script is written, where each
    workflow is set to run as background process by using the shell & character.
    Workflow parts are separated by wait command to synchronize progress
    between parts.

    Parameters:
    workloads: Output commands grouped by execution threads
    input_file_parameters: Run parameters defined in the staplefile.
    command_line_parameters: Named tuple containing parameters defined by
    user's command line

    Raises:
    STAPLERerror: Unable to open output file.
    """

    workload_index = 0
    workload_zfill_amount = len(str(len(workloads)))
    background_process_list = []
    for workload in workloads:
        # Each workflow part will have separate file to submit to TORQUE with
        # sbatch command. Each file has one or more associated subshell files
        # containing contents for each thread.

        # Generate strings describing current workload and thread indexes for
        # output file names
        workload_index += 1
        workload_index_string = str(workload_index).zfill(workload_zfill_amount)
        file_main_name = '{0}_UNIX_WORKLOAD_1'.format(NAME)

        # Add information about current workflow to the main shell script
        background_process_list.append('echo "Running workload part {0}"'.format(
            workload_index))

        # When --FIX_RUN mode is used the output and log files files already
        # exist. To prevent overwriting these files with new ones specific
        # prefix or appendix strings are added to the new output file names.
        appendix = '.sh'
        i = 0
        if command_line_parameters.fix_run:
            mode = 'FIX'
        elif command_line_parameters.compress_run == 'compress':
            mode = 'COMPRESS'
        elif command_line_parameters.compress_run == 'decompress':
            mode = 'DECOMPRESS'
        else:
            mode = None
        while mode is 'FIX' and os.path.exists(os.path.join(input_file_parameters.output_dir,
                                                            file_main_name + appendix)):
            i += 1
            appendix = '_{0}_{1}.sh'.format(mode, i)

        if mode in ('COMPRESS', 'DECOMPRESS'):
            appendix = '_{0}.sh'.format(mode)
            while os.path.exists(os.path.join(input_file_parameters.output_dir,
                                              file_main_name + appendix)):
                i += 1
                appendix = '_{0}_{1}.sh'.format(mode, i)


        # Generate subshell files
        thread_index = 0
        thread_zfill_amount = len(str(len(workload)))
        for thread_contents in workload:
            # Iterate over output commands of each thread and write necessary
            # subshell files for each
            out_lines = []
            for cmd in thread_contents:
                out_lines += generate_subshell_file_contents(cmd)

            # Write subshell file
            thread_index_string = str(thread_index).zfill(thread_zfill_amount)
            fl_name = '{0}_WORKLOAD_{1}_subshell_{2}{3}'.format(NAME,
                                                                workload_index_string,
                                                                thread_index_string,
                                                                appendix)
            try:
                out_fl = open(os.path.join(input_file_parameters.output_dir,
                                           fl_name), 'w')
            except:
                raise STAPLERerror.STAPLERerror('Unable to create output file:'
                                                '\n{0}'.format(os.path.join(
                    input_file_parameters.output_dir,
                    fl_name)))
            out_fl.write('\n'.join(out_lines))
            out_fl.write('\n')
            out_fl.close()
            # i.e. use UNIX source to run input shell script, redirect stdout
            # and stderr to an .out file.
            background_process_list.append('source {0} >> {0}.out 2>&1 &'.format(
                os.path.join(input_file_parameters.output_dir,
                             fl_name)))
            thread_index += 1

        # Workflow steps are written to a single output file (instead of
        # separate files). "wait" command is inserted in between workflow parts
        # to synchronize workflows.
        background_process_list.append('wait\n\n')

    # Write the main shell script file
    resmng_config = list(input_file_parameters.resource_manager_params)
    resmng_config.append('\n\n')
    resmng_config.append('\n'.join(background_process_list))

    out_fl_path = os.path.join(input_file_parameters.output_dir, file_main_name + appendix)
    try:
        out_fl = open(out_fl_path, 'w')
    except IOError as emsg:
        raise STAPLERerror.STAPLERerror('Unable to create output file:'
                              '\n{0}\n with error message:\n{1}'
                              .format(os.path.join(input_file_parameters.output_dir,
                                                   file_main_name + appendix),
                                      str(emsg)))
    out_fl.write('\n'.join(resmng_config))
    out_fl.write('\n')
    out_fl.close()
    return [out_fl_path]


def validate_resource_manager_parameters(user_defined_parameters,
                                         auto_defined_parameters):
    """Checks that user is has not defined any parameters that are auto-created

    Parameters:
    user_defined_parameters: List of parameters defined by the user in the
    STAPLERFILE
    auto_defined_parameters: List of parameters defined automatically by
    STAPLER for the current resource manager
    Raises:
    STAPLERerror: User has defined a resource manager parameter in the
    STAPLERFILE that is automatically generated by STAPLER
    """
    for udp in user_defined_parameters:
        for adp in auto_defined_parameters:
            if udp.startswith(adp):
                raise STAPLERerror.STAPLERerror('Resource manager parameter {0} '
                                                'should not be defined in '
                                                'the staplerfile, '
                                                'as it is automatically '
                                                'inferred by {1}.'.format(adp, NAME))


def generate_subshell_file_contents(cmd):
    """Creates a list of necessary information for each output command.

    Parameters:
    cmd: Instance of GenericBase or subclass of it

    Returns:
    out_lines: List of strings to be written to a subshell file
    """


    out_lines = []

    # Invoke commands to produce their output command string(s)
    cmd_list = cmd.command_lines
    cmd_list = map(clean_command_lines, cmd_list)

    # Write current command to stdout
    out_lines.append('echo ' + '-'*80)
    out_lines.append('echo Executing the following command:')
    for c in cmd_list:
        out_lines.append('echo "' + c + '"')
    out_lines.append('date')

    # Write current command to errout
    out_lines.append('echo ' + '-'*80 + ' >&2')
    out_lines.append('echo Executing the following command: >&2')
    for c in cmd_list:
        out_lines.append('echo "' + c + '" >&2')
    out_lines.append('date >&2')

    # Write module load commands required for current command to
    # the output shell script
    if cmd.load_module:
        for module in cmd.load_module:
            out_lines.append(module)

    # Write command lines to the output shell script
    out_lines += cmd_list
    out_lines += ['#']*5

    # Write module unload commands required for current command
    # to the output shell script
    if cmd.unload_module:
        for module in cmd.unload_module:
            out_lines.append(module)

    #Write to stdout
    out_lines.append('echo Finished at:')
    out_lines.append('date')
    #Write to errout
    out_lines.append('echo Finished at: >&2')
    out_lines.append('date >&2')

    return out_lines


def clean_command_lines(cmd):
    """Ensures that arguments and values are (single) white space -separated.

    Parameters:
    cmd: command line string
    Returns:
    cmd: command line string
    """
    cmd = ' '.join(cmd.split())
    return cmd


def check_log():
    """Reads log file produced by STAPLERs current run and prints report"""
    errors = 0
    warnings = 0
    log_handle = open(CurrentLogPath.path)
    for line in log_handle:
        if 'ERROR:' in line:
            errors += 1
        elif 'WARNING' in line:
            warnings += 1
    log_handle.close()
    if errors or warnings:
        print '!'*80
        if errors:
            print '{0} errors occurred during the run! See log file for more ' \
                  'details!'.format(errors)
        if warnings:
            print '{0} warnings occurred during the run! See log file for ' \
                  'more details!'.format(warnings)
        print 'Run was completed anyway.'
        print '\n\n'


#Start
arguments = sys.argv
if '--debug' in arguments:
    print_debug = True
    arguments.remove('--debug')
else:
    print_debug = False

try:
    main(arguments)
except STAPLERerror.STAPLERerror as e:
    print '\n{0}\n\nProgram run aborted!'.format(str(e))
    logging.error(str(e))
    logging.error('Program run aborted!')
    if print_debug:
        raise
    else:
        print 'Check the log file for additional details!'
        sys.exit(1)


logging.shutdown()
#Report if errors and warnings are written in log filed
if CurrentLogPath.path:
    check_log()
elif '--CHECK' in arguments:
    pass