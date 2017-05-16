#!/usr/bin/env python

import copy
import datetime
import logging
import os
import sys
import time

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

VERSION = '17.05.16'
NAME = 'STAPLER'
AUTHOR = 'Jaakko Tyrmi'
START_TIME = time.strftime("%Y_%m_%d_%H_%M_%S", time.localtime())
class Current_log_path:
    """Class for storing current log file path"""
    path = ''
DESCRIPTION = """
This script creates command lines for some bioinformatics programs. Consult
manual and use the built in help function for detailed instructions.


Usage:
The user input is a path to a staplefile plus other possible  arguments. For
more information on staple files, check the example staple file.

Usage example:
python STAPLER.py input/file/path.txt --SLURM

Additional arguments:

--help
Open this helpful help screen.

--help <tool_name>
Tool specific help.

--SLURM
Create necessary files for SLURM array job.

--SLURM <maximum_job_count>
Create necessary files for SLURM array job but limit the maximum number of
jobs. If there are more jobs than maximum_job_count multiple jobs are run
within a single job. Remember to adjust the #SBATCH --time parameter
accordingly in the staplefile.

--CHECK
Checks if the SLURM batch job based on given staple file has been successful.

--COMPRESS
Compresses finished run results (except .bam/.bai files). May be used in
combination with --SLURM <core_count>. NOTICE, experimental feature.

--DECOMPRESS
Decompresses finished run results. May be used in combination with --SLURM
<core_count>. NOTICE, experimental feature.
""".format(NAME)


def main(args):
    args = args[1:]
    mode = 'default'
    SLURM_max_jobs = None
    if len(args) == 0 or args[0] == '--help' or args[0] == '-h':
        if len(args) < 2:
            print_generic_help()
        elif len(args) == 2:
            print_specific_help(args[1])
        else:
            print 'Error! Found too many arguments for --help! Use --help with ' \
                  '0 arguments to print generic help or type --help <tool_name> ' \
                  'to get tool specific help!'
        return 0
    if '--COMPRESS' in args or '--DECOMPRESS' in args:
        workflow_compression(args)
        return 0
    if '--SLURM' in args:
        mode = 'slurm'
        # Parse if user has defined a value for SLURM_max_jobs (--SLURM 66)
        try:
            SLURM_max_jobs = int(args[args.index('--SLURM')+1])
            del args[args.index('--SLURM') + 1]
        except (IndexError, ValueError):
            pass
        args.remove('--SLURM')
    if '--CHECK' in args:
        mode = 'check'
        args.remove('--CHECK')

    if not os.path.isfile(args[0]):
        print '\nInput file not found:\n{0}\n'.format(args[0])
        print 'Use --help to print the help screen!\n'
        sys.exit(1)

    infile = args[0]

    if mode == 'check':
        check_SLURM_output(infile)
        return 0

    job_name, user_cmds, dir_stack, output_dir, slurm_config, project_ids, staplefile = \
        parse_input_file(infile)

    init_logging(job_name, staplefile, output_dir, dir_stack)
    output_cmds, dir_stack = generate_cmds(job_name,
                                            user_cmds,
                                            dir_stack)
    if project_ids is not None:
        check_project_id_validity(project_ids, output_cmds)

    log_dir_stacks_contents(dir_stack)
    write_output(output_cmds,
                 output_dir,
                 mode,
                 slurm_config,
                 project_ids,
                 job_name,
                 SLURM_max_jobs)
    print '\n\n'
    print 'Path to your project directory:'
    print os.path.split(output_dir)[0]
    print '\nPath to your output directory:'
    print output_dir

def check_project_id_validity(project_ids, user_cmds):
    """Checks that there are no conflicts in the user defined project file

    Args:
    project_ids: The user defined ids
    user_cmds: List of command instances

    Raises:
    STAPLERerror if any conflicts are found
    """
    all_project_ids = set([])
    for ids in project_ids:
        all_project_ids = all_project_ids.union(ids)

    for cmd in user_cmds:
        if cmd.id not in all_project_ids:
            raise STAPLERerror.STAPLERerror('File id {0} is not part of user '
                                            'defined project file: {1}'
                                            .format(cmd.id, all_project_ids))

    all_user_cmd_ids = set([])
    for cmd in user_cmds:
        all_user_cmd_ids.add(cmd.id)

    for project_id in list(all_project_ids):
        if project_id not in all_user_cmd_ids:
            logging.warning('There is no sample id that matches the project '
                            'file id {0}'.format(project_id))


def print_generic_help():
    """Prints basic info and help.
    """
    print '\n{0}\nVersion {1}\nby {2}'.format(NAME, VERSION, AUTHOR)
    print DESCRIPTION
    tools = sorted(AvailableCommands.commands.keys(), key=lambda v: v.upper())
    print '\n\nSupported tools are:\n{0}'.format('\n'.join(tools))
    print '\nHint: Check tool specific help with --help <tool_name>\n'


def print_specific_help(tool_name):
    """Prints help for specified tool.

    Arguments:
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
    print '\nOptional arguments:\n{0}'.format(str(cmd.optional_args))
    print '\nParallelizable:\n{0}'.format(str(cmd.parallelizable))
    print '\nAdditional description:\n{0}'.format(str(cmd.help_description))
    print ''


def parse_input_file(infile):
    """Reads the user provided input-file.

    Args:
    infile: Input path as a string.
    skip_errors: If True, errors are not raised if file format is not
    correct (Useful when user wants to check the output of run with --CHECK
    parameter mode='check').

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
        handle = open(infile)
    except IOError:
        raise STAPLERerror.STAPLERerror(
            'Unable to open input file: {0}'.format(infile))

    i = 0
    staplefile = []
    slurm_config = []
    commands = []
    dir_stack = {}
    job_name = None
    starting_point = None
    output_dir = None
    project_ids = None
    now_reading = None
    for ln in handle:
        i += 1
        ln = ln.strip()
        staplefile.append(ln)
        if i == 1:
            if ln != 'STAPLER':
                raise STAPLERerror.STAPLERerror(
                    'Input file does not start with "STAPLER"-row')
            else:
                continue
        if ln == '':
            continue

        #Read slurm config
        if ln == 'SLURM:':
            now_reading = 'slurm'
            continue
        if ln == 'SLURM END:':
            now_reading = None
            continue
        if now_reading == 'slurm':
            slurm_config.append(ln)
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

        #Read directory and file paths
        if ln.startswith('JOB_NAME:'):
            job_name = ln.replace('JOB_NAME:', '')
            job_name = job_name.strip()
            continue
        if ln.startswith('STARTING_POINT:'):
            starting_point = ln.replace('STARTING_POINT:', '')
            starting_point = starting_point.strip()
            starting_point = starting_point.rstrip('/')
            if not os.path.isdir(starting_point):
                raise STAPLERerror.STAPLERerror('The starting point directory does not exist:\n{0}'.format(starting_point))
            if not os.listdir(starting_point):
                raise STAPLERerror.STAPLERerror('The starting point directory is empty:\n{0}'.format(starting_point))
            dir_stack = [Directory(starting_point)]
            output_dir_name = '{0}_{1}_BATCH_SCRIPTS'.format(NAME, job_name)
            output_dir = os.path.join(os.path.split(starting_point)[0],
                                      output_dir_name)
            if os.path.exists(output_dir):
                raise STAPLERerror.STAPLERerror('A job with a job name:\n{0}\nhas '
                                      'already been been created in this '
                                      'directory. Use a different name, '
                                      'or remove existing job if you want to '
                                      'redo it.'.format(job_name))
            os.mkdir(output_dir)
            continue
        if ln.startswith('PROJECT_FILE:'):
            project_file_path = ln.replace('PROJECT_FILE:', '')
            project_file_path = project_file_path.strip()
            if not os.path.isfile(project_file_path):
                raise STAPLERerror.STAPLERerror('PROJECT_FILE does not exist!:\n{0}'
                                      .format(project_file_path))
            project_ids = read_project_file(project_file_path)

    if not job_name:
        raise STAPLERerror.STAPLERerror('JOB_NAME: -argument must be defined in the '
                              'staplefile!')
    if not starting_point:
        raise STAPLERerror.STAPLERerror('STARTING_POINT: -argument must be defined in the '
                              'staplefile!')
    if not output_dir:
        raise STAPLERerror.STAPLERerror('OUTPUT_DIR: -path was not found')
    handle.close()

    if not commands:
        raise STAPLERerror.STAPLERerror('No commands found from '
                              'input file: {0}'.format(infile))
    if '#SBATCH --job-name=' in '\n'.join(slurm_config):
        raise STAPLERerror.STAPLERerror('SLURM config section of the staplefile should '
                              'not contain the "#SBATCH --job-name=" line, '
                              'as this parameter is auto-generated based on '
                              'the JOB_NAME parameter!')
    if '#SBATCH --output=' in '\n'.join(slurm_config):
        raise STAPLERerror.STAPLERerror('SLURM config section of the staplefile should '
                              'not contain the "#SBATCH --output=" line, '
                              'as this parameter is auto-generated based on '
                              'the JOB_NAME parameter!')
    if '#SBATCH --error=' in '\n'.join(slurm_config):
        raise STAPLERerror.STAPLERerror('SLURM config section of the staplefile should '
                              'not contain the "#SBATCH --error=" line, '
                              'as this parameter is auto-generated based on '
                              'the JOB_NAME parameter!')

    return job_name, commands, dir_stack, output_dir, slurm_config, \
           project_ids, '\n'.join(staplefile)


def read_project_file(path):
    """Reads the PROJECT file contents into a list.

    Arguments:
    path: Path to a PROJECT file.

    Raises:
    STAPLERerror: If a substring is listed more than once in the input file or no
    substrings are found.

    Returns:
    List of substrings.
    """

    project_file_handle = open(path)
    project_id_sets = []
    all_project_ids = set([])
    for line in project_file_handle:
        line = line.strip()
        if not line: continue
        ids = line.split('\t')
        for project_id in ids:
            if project_id in all_project_ids:
                raise STAPLERerror.STAPLERerror('Project id {0} is listed twice in the project file!'
                                                .format(project_id))
            all_project_ids.add(project_id)
        project_id_sets.append(set(ids))
    if not project_id_sets:
        raise STAPLERerror.STAPLERerror('No ids found from project file:\n{0}'
                              .format(path))
    project_file_handle.close()
    return project_id_sets


def check_SLURM_output(infile):
    """Checks if SLURM run has been successful.

    Failed run is recognized from a line containing the word 'CANCELED' and
    an .out file not containing 'Finished at:' substring.

    Files that contain lines with 'warning' or 'error' substrings are also
    reported.

    Arguments:
    output_dir: Directory to which SLURM outputs the .out and .err files.
    This is defined by the user in the staplefile.
    """

    #Find the output directory from the staplefile
    try:
        handle = open(infile)
    except IOError:
        raise STAPLERerror.STAPLERerror(
            'Unable to open input file: {0}'.format(infile))

    i = 0
    job_name = None
    output_dir = None
    for ln in handle:
        i += 1
        ln = ln.strip()
        if i == 1:
            if ln != 'STAPLER' and ln != 'PIPELINEMASTER1000':
                raise STAPLERerror.STAPLERerror(
                    'Input file does not start with "STAPLER"-row')
            else:
                continue

        #Read directory and file paths
        if ln.startswith('JOB_NAME:'):
            job_name = ln.replace('JOB_NAME:', '')
            job_name = job_name.strip()
            continue
        if ln.startswith('STARTING_POINT:'):
            starting_point = ln.replace('STARTING_POINT:', '')
            starting_point = starting_point.strip()
            starting_point = starting_point.rstrip('/')
            continue

    output_dir_name = '{0}_{1}_BATCH_SCRIPTS'.format(NAME, job_name)
    output_dir = os.path.join(os.path.split(starting_point)[0],
                              output_dir_name)

    handle.close()
    if not output_dir:
        raise STAPLERerror.STAPLERerror('OUTPUT_DIR: -path was not found')


    #Look for errors in output files
    i = 0
    number_of_warnings = 0
    number_of_canceled_threads = 0
    for fl in os.listdir(output_dir):
        if os.path.splitext(fl)[1] not in ('.err', '.out'):
            continue
        i += 1
        fl_path = os.path.join(output_dir, fl)
        handle = open(fl_path)
        finished_at_line = False
        warning_messages = []
        error_messages = []
        for line in handle:
            if 'warning' in line.lower():
                warning_messages.append('This file contains a potential '
                                        'warning message:\n{0}'
                                        .format(fl_path))
                number_of_warnings += 1
            if 'error' in line.lower():
                warning_messages.append('This file contains a potential error '
                                        'message:\n{0}'.format(fl_path))
                number_of_warnings += 1
            if 'CANCELED' in line:
                error_messages.append('This thread was canceled by SLURM:\n{0}'
                                      .format(fl_path))
                number_of_canceled_threads += 1
            if 'Finished at:' in line:
                finished_at_line = True
        if os.path.splitext(fl)[1]  == '.out':
            if not finished_at_line:
                error_messages.append('This thread has not been finished:\n{0}'
                                      .format(fl_path))

        if len(warning_messages) != 0:
            print '\n\nThe following warning messages were found:'
            print '\n'.join(warning_messages)
        if len(error_messages) != 0:
            print '\n\nThe following error messages were found:'
            print '\n'.join(error_messages)

    print '\n\n{0} .out and .err files checked ({1} processes)'\
        .format(i, i/2)
    print 'Potential problems detected: {0}'\
        .format(number_of_warnings)
    print 'Severe problems detected: {0}'.format(number_of_canceled_threads)


def workflow_compression(args):
    """Compress/decompress a workflow.

    Arguments:
    args: User input line (excluding possible --SLURM argument)
    mode: Run mode (default, slurm)"""
    if '--COMPRESS' in args:
        compression_string = 'COMPRESS'
    elif '--DECOMPRESS' in args:
        compression_string = 'DECOMPRESS'

    #Number of threads to create
    if len(args) == 2:
        #No --SLURM argument
        thread_number = 1
        infile = copy.deepcopy(args)
        infile.remove('--{0}'.format(compression_string))
        infile = infile[0]
    elif '--SLURM' in args and len(args) == 3:
        #SLURM parameter without thread number int
        thread_number = 1
        infile = copy.deepcopy(args)
        infile.remove('--{0}'.format(compression_string))
        infile.remove('--SLURM')
        infile = infile[0]
    elif '--SLURM' in args and len(args) == 4:
        #SLURM parameter with thread number int
        try:
            thread_number = int(args[args.index('--SLURM')+1])
        except:
            print 'No integer found after --SLURM parameter!'
            sys.exit(1)
        infile = copy.deepcopy(args)
        infile.pop(args.index('--SLURM'))
        infile.pop(args.index('--SLURM'))
        infile.remove('--{0}'.format(compression_string))
        infile = infile[0]
    else:
        print 'Odd number of arguments on command line!'
        print 'Expected arguments are --COMPRESS/--DECOMPRESS, ' \
              '<staplefile_path>, (--SLURM, <int>)'
        sys.exit(1)

    #Read the staplefile and deduce the output directory path and job name
    try:
        handle = open(infile)
    except IOError:
        print 'Unable to open input file: {0}'.format(infile)
        sys.exit(1)
    is_staplefile = False
    job_name = None
    for line in handle:
        line = line.strip()
        if line == 'STAPLER':
            is_staplefile = True
            continue
        if not is_staplefile:
            print 'Input file is not a staplefile!'
            sys.exit(1)
        #Read output directory path
        if line.startswith('JOB_NAME:'):
            job_name = line.replace('JOB_NAME:', '')
            job_name = job_name.strip()
            continue
        if line.startswith('STARTING_POINT:'):
            starting_point = line.replace('STARTING_POINT:', '')
            starting_point = starting_point.strip()
            starting_point = starting_point.rstrip('/')
            continue
    output_dir_name = '{0}_{1}_BATCH_SCRIPTS'.format(NAME, job_name)
    output_dir = os.path.join(os.path.split(starting_point)[0],
                              output_dir_name)
    handle.close()

    #Find the log file from output directory
    log_file_path = None
    for fl in os.listdir(output_dir):
        basename = os.path.splitext(fl)[0]
        if basename.startswith('STAPLER_log_') and basename.endswith(job_name):
            log_file_path = os.path.join(output_dir, fl)
    if log_file_path is None:
        print 'There seems to be no log file for this staplefile. Has this ' \
              'job been run?'
        sys.exit(1)

    #Find the files involved in the run
    thread_contents = []
    thread_sizes = []
    handle = open(log_file_path)
    read_this_line = False
    read_directories = set()
    for line in handle:
        line = line.strip()
        if line.endswith('INFO:Output directory is:'):
            read_this_line = True
            continue
        if read_this_line:
            read_this_line = False
            #Output directory may be mentioned several times in log file
            if line in read_directories:
                continue
            else:
                read_directories.add(line)
            for f in os.listdir(line):
                #BAM/BAI files are not compressed
                if f.endswith('.bam') or f.endswith('.bai'): continue
                #Include only uncompressed files for compression and vice versa
                if '--COMPRESS' in args and f.endswith('.gz'):
                    continue
                if '--DECOMPRESS' in args and not f.endswith('.gz'):
                    continue
                f = os.path.join(line, f)
                if len(thread_contents) < thread_number:
                    #Create a new thread
                    thread_contents.append([f])
                    thread_sizes.append(os.stat(f).st_size)
                else:
                    #Add the file to the thread with least data to handle
                    thread_contents[thread_sizes.index(min(
                        thread_sizes))].append(f)
                    thread_sizes[thread_sizes.index(min(thread_sizes))] += \
                        os.stat(f).st_size

    #Check that there are some files to actually (de/)compress
    if not thread_contents:
        if '--COMPRESS' in args:
            print 'No files to compress! Is this workflow compressed already?'
        if '--DECOMPRESS' in args:
            print 'No files to decompress! Is this workflow decompressed ' \
                  'already?'
        sys.exit(1)

    if '--SLURM' not in args:
        if '--COMPRESS' in args:
            out_handle = open(os.path.join(output_dir, 'COMPRESS.sh'), 'w')
            out_handle.write('#!/usr/bin/env bash\n')
            i = 0
            for line in thread_contents[0]:
                i += 1
                out_handle.write('echo Executing command {0}/{1}'.format(i,
                                                                         len(thread_contents)))
                out_handle.write('gzip --fast {0}\n'.format(line))
        elif '--DECOMPRESS' in args:
            out_handle = open(os.path.join(output_dir, 'DECOMPRESS.sh'), 'w')
            out_handle.write('#!/usr/bin/env bash\n')
            i = 0
            for line in thread_contents[0]:
                i += 1
                out_handle.write('echo Executing command {0}/{1}'.format(i,
                                                                         len(thread_contents)))
                out_handle.write('gzip -d {0}\n'.format(line))
        out_handle.close()
        print 'Estimated runtime is roughly:\n{0}'.format(datetime.timedelta(
            seconds=max(thread_sizes)/40000000))

    if '--SLURM' in args:
        i = 0
        for thread in thread_contents:
            i += 1
            fl_name = '{0}_{1}_subshell.sh'.format(compression_string, i)
            try:
                out_handle = open(os.path.join(output_dir, fl_name), 'w')
            except:
                print 'Unable to create output file:\n{0}'.format(os.path.join(output_dir, fl_name))
                sys.exit(1)
            for line in thread:
                if '--COMPRESS' in args:
                    out_handle.write('gzip --fast {0}\n'.format(line))
                elif '--DECOMPRESS' in args:
                    out_handle.write('gzip -d {0}\n'.format(line,
                                                            os.path.splitext(line)[0]))
            out_handle.close()



        try:
            out_handle = open(os.path.join(output_dir, '{0}_SBATCHABLE.sh'.format(compression_string)), 'w')
        except IOError as emsg:
            print 'Unable to create output file:\n{0}\n with error message:\n{1}'.format(os.path.join(output_dir, '{0}_SBATCHABLE.sh'.format(compression_string)), str(emsg))
            sys.exit(1)
        #Autodefine some parameters for the SLURM config
        out_handle.write('#!/bin/bash -l\n')
        out_handle.write('#SBATCH --partition=parallel\n')
        out_handle.write('#SBATCH --job-name={0}_{1}\n'.format(compression_string, job_name))
        out_handle.write('#SBATCH --output={0}_{1}_%A_%a.out\n'.format(compression_string, job_name))
        out_handle.write('#SBATCH --error={0}_{1}_%A_%a.err\n'.format(compression_string, job_name))
        out_handle.write('#SBATCH --ntasks=1\n')
        out_handle.write('#SBATCH --mem-per-cpu=500\n')
        #Assume that gzip compression speed is 20Mb per second (should give plenty of time for new processors)
        if '--COMPRESS' in args:
            #Assume that gzip compression speed is 20Mb per second (should
            # give plenty of time for modern processors)
            out_handle.write('#SBATCH --time={0}\n'.format(datetime.timedelta(seconds=(max(thread_sizes)/20000000)+60)))
        else:
            #Assume that gzip decompression speed is 60Mb per second (should
            # give plenty of time for modern processors)
            out_handle.write('#SBATCH --time={0}\n'.format(datetime.timedelta(seconds=(max(thread_sizes)/60000000)+60)))
        #Include the parameters the user has defined
        out_handle.write('#SBATCH --array={0}-{1}\n'.format(1, len(thread_contents)))
        out_handle.write('\n\n')
        out_handle.write('source {0}_{1}_subshell.sh\n'.format(compression_string,
                                                                   '"$SLURM_ARRAY_TASK_ID"'))
        out_handle.close()
    print '\nOutput file created to directory:\n{0}\n'.format(output_dir)


def init_logging(job_name, staplefile, outdir, dir_stacks):
    """Initiates the logging.

    NOTICE! This function has the side effect of changing the value of the
    class variable  Current_log_path.path!

    Arguments:
    job_name: Name of the job specified by the user.
    outdir: Destination of the log file.
    dir_stack: Available directories for job.
    """
    fl_name = '{0}_log_{1}_{2}.txt'.format(NAME, START_TIME, job_name)
    #NOTICE! Current_log_path.path is changed here!
    Current_log_path.path = os.path.join(outdir, fl_name)
    logging.basicConfig(filename=Current_log_path.path, filemode='w',
                        format='%(asctime)s %(levelname)s:%(message)s',
                        level=logging.INFO)
    logging.info('{0} v. {1} started'.format(NAME, VERSION))
    logging.info('Job name: {0}'.format(job_name))
    logging.info('Starting point directory:\n{0}'.format(dir_stacks[0]
                                                         .path))
    logging.info('Output directory:\n{0}'.format(outdir))
    logging.info('-'*80)
    logging.info('staplefile contents:\n{}'.format(staplefile))
    logging.info('-'*80)
    logging.info('installation_config.txt contents:\n{0}'
                 .format(utils.get_config_file()))
    logging.info('-'*80)


def generate_cmds(job_name, input_cmds, dir_stack):
    """Generates command lines.

Arguments:
job_name: Job name defined by the user.
input_cmds: Commands the user wishes to execute for each file in starting point
dir.
dir_stacks: List containing only the starting point directory

Raises:
STAPLERerror: Command type is not supported.
"""
    out_cmd_lines = []
    cmds = input_cmds
    j = 0
    for i in range(len(cmds)):
        cmd = cmds[i].split()
        try:
            cmd_type = AvailableCommands.commands[cmd[0]]
        except KeyError:
            raise STAPLERerror.STAPLERerror(
                'The following command type is not '
                'supported: {0}'.format(cmds[i]))
        cmd = ' '.join(cmd[1:])

        dir_stack_pointer = correct_dir_pointer(cmd_type, dir_stack)
        in_dir = dir_stack[dir_stack_pointer]
        out_dir = os.path.split(in_dir.path)[0]
        out_dir_name = ('{0}_{1}_{2}_{3}'.format(NAME,
                                                 job_name,
                                                 i,
                                                 cmd_type.name))
        out_dir = os.path.join(out_dir, out_dir_name)
        out_dir = Directory(out_dir)

        #Read files until command class finds no more valid input files
        while True:
            try:
                out_cmd_lines.append(cmd_type(cmd, in_dir, out_dir))
                logging.info('-'*80)
                logging.info('User command line:\n{0}'.format(cmds[i]))
                logging.info('Final command line(s):\n{0}'.format(
                    '\n'.join(out_cmd_lines[-1].get_cmd())))
                logging.info('Input directory is:\n{0}'.format(in_dir.path))
                logging.info('Output directory is:\n{0}'.format(out_dir
                                                                .path))
                j += 1
                print 'Created command line number {0} for {1}...'\
                    .format(j, cmd_type.name)
            except STAPLERerror.VirtualIOError:
                break

        dir_stack.append(out_dir)
    return out_cmd_lines, dir_stack


def correct_dir_pointer(cmd_type, dir_stack):
    """Find a dir from stack that contains files in correct format as input.

Arguments:
cmd_type: Type of the command to search inputs for.
dir_stack: List of predicted directories (Directory-objects).
Returns:
Index of dir_stack.
"""
    for i in range(len(dir_stack) - 1, -1, -1):
        for tp in cmd_type.input_types:
            if tp in dir_stack[i].entry_types:
                return i
    raise STAPLERerror.STAPLERerror('No proper input files found for cmd type '
                          '{0} from any previous '
                          'output folder!'.format(cmd_type))


def log_dir_stacks_contents(dir_stacks):
    """Write data to log file on predicted directory contents.

    Arguments:
    dir_stacks: List of predicted directories (Directory-objects).
    """
    for directory in dir_stacks:
        logging.info('-'*80)
        logging.info('Predicted directory contents of:\n{0}'
                     .format(directory.path))
        files = directory.files.keys()
        files = sorted(files)
        logging.info('Number of files: '.format(len(files)))
        logging.info('Files:')
        logging.info('\t'.join(files))


def write_output(output_cmds, output_dir, mode, slurm_config, project_ids,
                 job_name, SLURM_max_jobs):
    """Chooses the output function.

    Arguments:
    output_cmds: List of command objects.
    output_dir: Directory to write the output to.
    mode: Format in which to output command lines.
    slurm_config: Configuration data for SLURM output.
    """

    if mode == 'default':
        write_default(output_cmds, output_dir)
    elif mode == 'slurm':
        write_slurm(output_cmds, output_dir, slurm_config, project_ids,
                    job_name, SLURM_max_jobs)


def write_default(output_cmds, output_dir):
    """Writes the output in simple shell script format.

    The default format is a shell script file containing the command lines.

    Arguments:
    output_cmds: List of command objects.
    output_dir: Directory to write the output to.

    Raises:
    STAPLERerror: Unable to open output file.
    """

    #Create command line strings
    i = 0
    out_lines = ['echo Started executing shell script at:', 'date']
    for cmd in output_cmds:
        i += 1
        cmd_list = cmd.get_cmd()
        cmd_list = map(clean_command_lines, cmd_list)
        out_lines.append('echo Executing command {0}/{1}:'
                         .format(i, len(output_cmds)))
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
    try:
        out_fl = open(os.path.join(output_dir, fl_name), 'w')
    except:
        raise STAPLERerror.STAPLERerror('Unable to create output file:'
                                    '\n{0}'.format(os.path.join(output_dir,
                                                                fl_name)))
    out_fl.write('#!/usr/bin/env bash\n')
    out_fl.write('\n'.join(out_lines))
    out_fl.close()


def write_slurm(output_cmds, output_dir, slurm_config, project_ids, job_name, SLURM_max_jobs):
    """Writes the output in SLURM array job format.

    Creates sub shell scripts that contain the workflow for each input
    file separately. After this main shell script containing SLURM
    configuration is created. This script is also responsible for starting
    the sub shells as separate processes.

    Arguments:
    output_cmds: List of command objects.
    output_dir: Directory to write the output to.
    slurm_config: Configuration data for SLURM output.

    Raises:
    STAPLERerror: Unable to open output file.
    """

    #Define IDs, i.e. how many jobs will be created and the contents of each
    if project_ids and SLURM_max_jobs is not None:
        raise STAPLERerror.STAPLERerror('Project file can not be used when maximum job count'
                              'is defined in the STAPLER command line!')
    if project_ids:
        ids = project_ids
        logging.info('-'*80)
        logging.info('Using user defined ids:\n{0}'.format(ids))
        logging.info('-'*80)
    else:
        ids = get_ids(output_cmds)
        logging.info('-'*80)
        logging.info('Using auto-inferred ids:\n{0}'.format(ids))
        logging.info('-'*80)
    if SLURM_max_jobs is not None:
        id_groups = split_ids_to_groups(ids, SLURM_max_jobs)
    else:
        id_groups = []


    # Create command lines separately for each ID
    i = 0
    used_commands = set([])
    while True:
        # Define available IDs for the current output file
        if SLURM_max_jobs:
            try:
                current_output_ids = id_groups[i]
            except IndexError:
                break
        else:
            try:
                current_output_ids = ids[i]
            except IndexError:
                break
        out_lines = []
        for cmd in output_cmds:
            #Make sure each command is created only once
            if cmd in used_commands: continue
            if not cmd.parallelizable:
                raise STAPLERerror.STAPLERerror('{0} is not parallelizable!'
                                      .format(cmd.name))
            if (SLURM_max_jobs is None and not project_ids and current_output_ids == cmd.id) or \
                    (SLURM_max_jobs is None and project_ids and cmd.id in current_output_ids) or \
                    (SLURM_max_jobs is not None and cmd.id in current_output_ids):
                used_commands.add(cmd)
                cmd_list = cmd.get_cmd()
                cmd_list = map(clean_command_lines, cmd_list)

                #Write to stdout
                out_lines.append('echo ' + '-'*80)
                out_lines.append('echo Executing the following command:')
                for c in cmd_list:
                    c = c.replace('>', '\\>')
                    c = c.replace('|', '\\|')
                    out_lines.append('echo ' + c)
                out_lines.append('date')

                #Write to errout
                out_lines.append('echo ' + '-'*80 + ' >&2')
                out_lines.append('echo Executing the following command: >&2')
                for c in cmd_list:
                    c = c.replace('>', '\\>')
                    c = c.replace('|', '\\|')
                    out_lines.append('echo ' + c + ' >&2')
                out_lines.append('date >&2')

                #Load modules:
                if cmd.load_module:
                    for module in cmd.load_module:
                        out_lines.append(module)

                #The commands
                out_lines += cmd_list
                out_lines += ['#']*5

                #Unload modules
                if cmd.unload_module:
                    for module in cmd.unload_module:
                        out_lines.append(module)

        if not out_lines:
            logging.warning('No commands to execute for ID:\n{0}\n'
                            'Make sure you have all the necessary input files '
                            'in the input directory and file names/IDs do not '
                            'contain typos!'.format(current_output_ids))
        #Write to stdout
        out_lines.append('echo Finished at:')
        out_lines.append('date')
        #Write to errout
        out_lines.append('echo Finished at: >&2')
        out_lines.append('date >&2')
        #Open and write file
        i += 1
        fl_name = '{0}_{1}_subshell_{2}.sh'.format(NAME, i, START_TIME)
        try:
            out_fl = open(os.path.join(output_dir, fl_name), 'w')
        except:
            raise STAPLERerror.STAPLERerror('Unable to create output file:'
                                  '\n{0}'.format(os.path.join(output_dir,
                                                              fl_name)))
        out_fl.write('\n')
        out_fl.write('\n'.join(out_lines))
        out_fl.close()

    #Autodefine some parameters for the SLURM config
    slurm_config.insert(1, '#SBATCH --error={0}_%A_%a.err'.format(job_name))
    slurm_config.insert(1, '#SBATCH --output={0}_%A_%a.out'.format(job_name))
    slurm_config.insert(1, '#SBATCH --job-name={0}'.format(job_name))
    #Include the parameters the user has defined
    if SLURM_max_jobs is None:
        slurm_config.append('#SBATCH --array={0}-{1}'.format(1, len(ids)))
    else:
        slurm_config.append('#SBATCH --array={0}-{1}'.format(1, len(id_groups)))
    slurm_config.append('\n\n')
    slurm_config.append('source {0}_{1}_subshell_{2}.sh'.format(NAME,
                                                         '"$SLURM_ARRAY_TASK_ID"',
                                                         START_TIME))
    slurm_main_name = '{0}_SBATCHABLE_{1}.sh'.format(NAME, START_TIME)

    try:
        out_fl = open(os.path.join(output_dir, slurm_main_name), 'w')

    except IOError as emsg:
        raise STAPLERerror.STAPLERerror('Unable to create output file:'
                              '\n{0}\n with error message:\n{1}'
                              .format(os.path.join(output_dir,
                                                   slurm_main_name),
                                      str(emsg)))
    out_fl.write('\n'.join(slurm_config))
    out_fl.close()


def get_ids(output_cmds):
    """Get all the IDs used in the workflow.

    Arguments:
    output_cmds: Objects containing the output commands and metadata.

    Returns:
    List of different ids used.
    """

    ids = []
    ID = None
    for cmd in output_cmds:
        if cmd.id != ID:
            ID = cmd.id
            if ID not in ids:
                ids.append(ID)
    return ids


def split_ids_to_groups(ids, n):
    """Split ids into n groups.

    Arguments:
    ids: List of ids
    n: Number of ids to assign per group

    Return:
    List of id groups
    """
    return [ids[i::n] for i in xrange(n)]


def clean_command_lines(cmd):
    """Ensures that arguments and values are (single) white space -separated.

    Arguments:
    cmd: command line string
    Returns:
    cmd: command line string
    """
    cmd = ' '.join(cmd.split())
    return cmd


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
if Current_log_path.path:
    print '\nReading log file for problems...'
    errors = 0
    warnings = 0
    log_handle = open(Current_log_path.path)
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
    else:
        print 'Run successfully completed!'
elif '--CHECK' in arguments:
    pass
else:
    print 'LOG WAS NOT READ!'