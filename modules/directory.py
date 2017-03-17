import logging
import os

from STAPLERerror import STAPLERerror
import utils

class Directory():
    """Contains information of files in a directory.

    If a directory already exists, it is expected to be empty.

    Methods:
    add_file
    use_file
    get_absolute_file_path

    Attributes:
    path: The directory path.
    files: Dict where keys are files in this directory and values a list of
    objects that have already used this file as an input.
    entry_types: Set of file types found in this dir
    """

    def __init__(self, path):
        """
        Arguments:
        path: Absolute path to folder.

        Raises:
        STAPLERerror: Raised if path does not point to an empty dir.
        ValueError: Raised if file paths are absolute.
        """
        self.path = path.strip()
        self.files = {}
        self.entry_types = set()
        self.dirs = {}
        if os.path.exists(path) and not os.path.isdir(path):
            raise ValueError('An entry with name {0} exists but it is not a directory'.format(path))
        if os.path.isdir(path):
            for entry in os.listdir(path):
                if os.path.isfile(os.path.join(path, entry)):
                    self.add_file(entry)
                elif os.path.isdir(os.path.join(path, entry)):
                    self.add_dir(entry)
        else:
            try:
                os.mkdir(path)
            except OSError as e:
                raise STAPLERerror('Unable to create a new dir to location with '
                                 'error message:\n{0}'.format(str(e)))


    def add_file(self, fl_name):
        """Adds a new file to the folder.

        Arguments:
        fl_name: Name of the file.

        Raises:
        ValuerError: If a file with same name exists already, file path is
        absolute or path exists but is not a file.
        """
        if fl_name in self.files:
            print 'WARNING! File with name {0} already exists in the folder:\n{1}'\
                .format(fl_name, self.path)
            logging.warning('WARNING! File with name {0} already exists in the folder:\n{1}' \
                            .format(fl_name, self.path))
        if os.path.isabs(fl_name):
            raise ValueError('File name is absolute path:\n{0}'.format(fl_name))
        absolute_path = os.path.join(self.path, fl_name)
        if os.path.exists(absolute_path) and not os.path.isfile(absolute_path):
            raise ValueError('Path exists but is not a file!')

        self.files[fl_name] = []
        self.entry_types.add(utils.splitext(fl_name)[1])


    def add_dir(self, dir_name):
        """Adds a new directory to the folder.

        Arguments:
        fl_name: Name of the directory.

        Raises:
        ValueError: If a directory with same name exists already, directory
        path is absolute or path exists but is not directory.
        """
        if dir_name in self.dirs:
            raise ValueError('Directory with name {0} already '
                             'exists in the folder:\n{1}'.format(dir_name,
                                                                 self.path))
        if os.path.isabs(dir_name):
            raise ValueError('Directory name is absolute path:\n{0}'.format(dir_name))

        absolute_path = os.path.join(self.path, dir_name)
        if os.path.isdir(absolute_path):
            self.dirs[dir_name] = Directory(os.path.join(absolute_path))
            dir_name = dir_name.rstrip('/')
            # Intepret directory names with dot as having a file extension
            # This bahavior is because some tools take directories instead of
            # files as inputs, and the directory "type" must be identified
            if os.path.splitext(dir_name)[1]:
                self.entry_types.add(os.path.splitext(dir_name)[1])
        elif os.path.exists(absolute_path) and not os.path.isdir(absolute_path):
            raise ValueError('Path exists but is not a directory!')


    def use_file(self, fl_name, user_tool_name):
        """Adds a new user to specific file.

        Arguments:
        fl_name: Name of the file in question.
        user_tool_name: Name of the user tool.
        """
        self.files[fl_name].append(user_tool_name)


    def get_absolute_file_path(self, file_name):
        """Returns the absolute path to requested file found in this folder.

        Arguments:
        file_name: Name of the file for which abs path is requested.
        Returns:
        String containing the absolute path.
        """
        assert file_name in self.files
        return os.path.join(self.path, file_name)
