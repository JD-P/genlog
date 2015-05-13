#!/usr/bin/python3

# We start by importing time and datetime. The former lets us get and write the current time and date to a file. The latter lets us get the distance between t# wo times

import time,datetime

# We import json so that we can put both the machine readable version and the version formatted for human consumption in seperate files.

import json

# We import os so that we can make the config file if it doesn't already exist, and check for its existence.

import os

# We import string for input validation

import string

# We import argparse to handle command line arguments.

import argparse

import cmd

import re

import importlib

import zipfile

class Logger():
    """Implements the core logging facilities."""
    def __init__(self, interface):
        self.interface = interface

    def import_from_path(self, modpath, path):
        """Import the module modname from path without side effects at end of
        execution. (But has side effects during.) modpath *must* be a fully 
        qualified """
        oldcache = sys.modules.copy()
        sys.path.append(path)
        pathsplit = modpath.rsplit(".", 1)
        if len(pathsplit) == 1:
            script = importlib.import_module(pathsplit[0])
        else:
            _from = pathsplit[0]
            _import = pathsplit[1]
            script = importlib.import_module(_import, _from)
        sys.path.pop() 
        sys.modules = oldcache
        return script
        

    def main(self):
        """Handle command line arguments, determine which interface to use and cede control to it."""
        paths = self.genpaths("placeholder")
        confdir = paths["confdir"]
        sys.path.append(confdir)
        parser = argparse.ArgumentParser()
        parser.add_argument("-p","--print",default=False,help='Print the text log to standard output.')
        parser.add_argument("-i","--interface",default='cli',help='Specify which interface to use. Valid options: cli')
        args = parser.parse_args()
        if args.print:
            self.tlogprint(args.print)
            return 0
        elif args.interface == 'cli':
            global log
            log = Logger(CliInterface())
            CliInterface.cli_main()
        elif args.interface == 'gui':
            print("No GUI interface available at this time.")
        else:
            raise ValueError("Interface somehow not present.")

    def getfields(self, settings, logname):
        """Extract the fields from a logger settings.conf file and convert them
        into field objects using cascading types.

        The following are information about variables in this function:

        fields: A key in the settings.conf that holds the list of field 
        descriptions.

        fdict: A dictionary that describes a field.

        fobject: A Field object constructed from the fdict. 

        fname: The name of the field. Used as default in place of flabel and
        olabel if they're not set. Also used to generate do_ methods for Cli
        interface.

        flabel: The 'description' of the field that is used by the interface
        to give a textual description to the user of what sort of input is
        expected in the field.

        olabel: The label that is used above the column when it's printed as
        text.

        ftype: The field type of the field and of the column. The type is a sort
        of template for fields that lets you style a new field after an old one.

        restrictions: The regex that determines what inputs are valid.

        onmatch: Says whether strings evaluated by the regex should or should not
        be matched by it.

        oformat: The name of the script in either this logs _scripts or the
        global _scripts namespace that determines how the column should be 
        printed for text output.

        search: The name of the script in either this logs _scripts or the
        global _scripts namespace that determines how the column should be
        searched through when given a search string.

        flist: The list of field objects returned by getfields."""
        flist = []
        fields = settings["fields"]
        for field in fields:
            fdict = {}
            cascade = self.get_ancestors(Logger, field, logname)
            cascade.reverse()
            cascade.append(field)
            for field in cascade:
                for key in field:
                    try:
                        fdict[key]
                    except KeyError:
                        fdict[key] = None
                    fdict[key] = field[key] if field[key] else fdict[key]
            fobject = Field.from_fdict(Field, fdict)
            fobject.unpack_scripts(logname=logname)
            flist.append(fobject)
        return flist

    def readconf(self, logger):
        """Read the configuration file at ~/.loggers/<LOGGER>/settings.conf and return the settings."""
        paths = self.genpaths(logger)
        # If config file already exists, read from it. If not, create it.
        # If directory for loggers doesn't exist, create it.
        try:
            config = open(paths["confpath"], 'r')
        except IOError:
            if os.path.isdir(paths["logdir"]):

                settings = {"jsonpath":paths["jsonpath"], "txtpath":paths["txtpath"]}
                json.dump(settings, config)
                config.close()
                return settings
            else:
                os.makedirs(paths["logdir"])
                self.readconf()
        # Verify the config file is valid JSON
        try:
            settings = json.load(config)
        except ValueError:
            raise ValueError("The configuration file is corrupted or not valid JSON.")
        return settings

    def load_log(self, logname):
        """Return the json of the log for logname."""
        paths = self.genpaths(logname)
        jsonpath = paths["jsonpath"]
        logfile = open(jsonpath, 'r')
        log = json.load(logfile)
        return log

    def load_log_entries(self, logname, entries, fields):
        """Load the log entries from logname given by the list of ranges
        in <entries>."""
        log = self.load_log(logname)
        for findex in range(0, len(fields)):
            field = fields[findex]
            column = log[findex]
            if field["fname"] != column["fname"]:
                raise ValueError("Order of columns has become corrupted/assumptions"
                                 " about data have been violated.")
        log_entries = set()
        for _range in entries:
            start = _range[0]
            end = (_range[-1] + 2)
            inclusive_range = range(start, end)
            for entry in inclusive_range:
                edict = {}
                for column in log:
                    fname = column["fname"]
                    edict[fname] = column["data"][entry]
                log_entries.add((entry, edict))
        return log_entries
        
    def add_entry(self, entry, logname):
        """Take an entry dictionary and write out to a JSON log based on it."""
        paths = self.genpaths(logname)
        logpath = paths["jsonpath"]
        try:
            jlog = open(logpath, 'r')
            logdata = json.load(jlog)
        except IOError:
            self.loginit(log)
        except EOFError:
            self.loginit(log)
        except ValueError:
            print("JSON log file exists, but is empty. Initalizing log file.")
            self.loginit(log)
        jlog.close()
        # FINISH WHEN YOU KNOW WHAT SORT OF DATA SINGLE LOG SESSION RETURNS
        jlog = open(log,'w')
        json.dump(jlist,jlog)
        jlog.close()
        return 0

    def genpaths(self, logger):
        """Build the paths, confdir is used to check for errors."""
        paths = {}
        paths["homedir"] = os.path.expanduser("~")
        paths["confdir"] = os.path.join(paths["homedir"], ".loggers/")
        paths["logdir"] = os.path.join(paths["confdir"], logger)
        paths["confpath"] = os.path.join(paths["logdir"], "settings.conf")
        paths["jsonpath"] = os.path.join(paths["logdir"], (logger + "-log.json"))
        paths["txtpath"] = os.path.join(paths["homedir"], "Documents/", (logger + "-log.txt"))
        return paths

    def loginit(self, jsonpath):
        """Initalize the log file if it has no prior entries."""
        logfilename = os.path.split(jsonpath)[1]
        logger = logfilename.split("-")[0]
        jlog = open(jsonpath,'a')
        settings = self.readconf(logger)
        flist = self.getfields(settings)
        edict = log(flist)
        jlist = [edict]
        json.dump(jlist,jlog)
        quit()

    def available_fields(self, logger):
        """Return the available field types."""
        # In what namespace? O_o
        pass

    def search_tree(self, tree, search_name, logname):
        """Search a given tree for a given name. Trees are the abstract search
        path used in cascading namespace searching where the local directory is
        searched for first and then the global directory searched second. See 
        the manual for more information. Returns the path that contains the 
        item being searched for.

        tree: The name of the directory that should be searched on the abstract
        path.

        search_name: The name of the script/field/etc that's being searched for
        in the 'tree' directory.

        logname: The name of the local logger.
        """
        def search_node(tree, search_name, nodepath):
            """Search an individual node in the tree."""
            treedir = os.path.join(nodepath, tree)
            try:
                files = os.listdir(treedir)
            except OSError:
                raise ValueError("Was passed an improper tree name.")
            for _file in files:
                if _file.split(".")[0] == search_name:
                    return treedir
                else:
                    return False
        
        paths = self.genpaths(logname)
        logdir = paths["logdir"]
        confdir = paths["confdir"]
        localnode = search_node(tree, search_name, logdir)
        if localnode:
            return localnode
        globalnode = search_node(tree, search_name, confdir)
        if globalnode:
            return globalnode
        else:
            return False
            

    def get_ancestors(self, field, logname):
        """Get the ancestors of a given field."""
        def get_ancestor(self, field, logname):
            name = field["name"]
            ftype = field["type"]
            if name == ftype:
                return False
            else:
                contain_dir = self.search_tree('_ftypes', ftype, logname)
                if not contain_dir:
                    raise ValueError("No field of this type in local or global"
                                     " namespace.")
                fullpath = os.path.join(contain_dir, (ftype + ".json"))
                grave = open(fullpath, 'r')
                ancestor = json.load(grave)
                grave.close()
                return ancestor
        ancestors = []
        ancestor = get_ancestor(self, field, logname)
        while ancestor:
            ancestors.append(ancestor)
            if ancestor["name"] == ancestor["type"]:
                return ancestors
            else:
                ancestor = get_ancestor(self, field, logname)

    def get_script(self, script, logname):
        """Return a script from the scripts name given as a string and the
        logname of the local logger."""
        contain_dir = self.search_tree('_scripts', script, logname)
        if not contain_dir:
            raise ValueError(("No script by name " + script + "in local or global")
                             " namespace.")
        imported_script = self.import_from_path(script, contain_dir)
        return imported_script

    def verify_logname(self, logname):
    """Verify that the user typed in a valid logname."""
    paths = Logger.genpaths(logname)
    confdir = paths["confdir"]
    # Check to make sure that user implemented a real directory name
    if os.path.isdir(confdir + logname):
        return True
    else:
        return False

    def mklogtemplate(self, logname, settings):
        """Make a new log template in the .loggers directory."""
        paths = Logger.genpaths(logname)
        os.mkdir(paths["logdir"])
        log.confinit(logname, settings)
        return True

    def confinit(self, logger, settings):
        paths = self.genpaths(logger)
        confpath = paths["confpath"]
        config = open(confpath, 'w')
        json.dump(settings, config)
        config.close()

    def verify_file_before_write(self, filepath):
        """Verify that a file does not already exist and is not a directory
        and that the path to new file is writable."""
        pathsplit = os.path.split(filepath)
        if pathsplit[1] == '':
            return 'filepath_was_directory'
        elif not os.path.isdir(pathsplit[0]):
            return 'invalid_filepath'
        elif os.path.isfile(filepath):
            yes = input(filepath + "already exists, overwrite? Y/N:")
            if yes == 'yes' or yes == 'y':
                pass
            else:
                return 'existed_no_overwrite'
        else:
            return True

    def descend_directory(self, directory, export_archive):
        """Descend a directory recursively, adding items to zip archive."""
        if os.path.isdir(directory):
            files2backup = os.listdir(directory)
            for _file in files2backup:
                file2backup = os.path.join(directory, _file)
                if os.path.isdir(file2backup):
                    self.descend_directory(file2backup)
                else:
                    export_archive.write(file2backup, _file)
        else:
            raise ValueError("Function descend_directory in export recieved"
                                 " a file as argument.")
        return export_archive

    def export(self, logname, filepath):
        """Export a log as a zipfile to filepath."""
        pathcheck = self.verify_file_before_write(filepath)
        if pathcheck is not True:
            return pathcheck
        else:
            paths = Logger.genpaths(Logger, logname)
            logdir = paths["logdir"]
            export = zipfile.ZipFile(filepath, "w")
            if os.path.isdir(logdir):
                export_archive = self.descend_directory(logdir, export)
                export_archive.close()
                return True
            else:
                return "log_does_not_exist"

    def export_all(self, filepath):
        """Export every log and all settings and directories to filepath."""
        pathcheck = self.verify_file_before_write(filepath)
        if pathcheck is not True:
            return pathcheck
        else:
            paths = Logger.genpaths(Logger, "placeholder")
            confdir = paths["confdir"]
            export = zipfile.ZipFile(filepath)
            export_archive = self.descend_directory(confdir, export)
            export_archive.close()
            return True

    def export_entries(self, logname, entries, fields, filepath):
        """Export the entries of logname given by the list of ranges <entries>
        to filepath."""
        pathcheck = self.verify_file_before_write(filepath)
        if pathcheck is not True:
            return pathcheck
        else:
            log_entries = self.load_log_entries(logname, entries, fields)
            return log_entries
        

class LogPrinter():
    """Print the log in text format(s)."""
    def tlogwrt(self, entry,log):
        """Take an entry dictionary and write out to the human readable log based on it."""
        # Check if textlog file exists, if not write instead of append
        tlog = open(log,'a')
        tlog.write("----\n")
        for lvalue in entry:
            olabel = str(entry.get(lvalue)[1])
            value = str(entry.get(lvalue)[0])
            tlog.write(olabel + " " + value + "\n\n")
        tlog.write("----\n\n")

    def tlogprint(self, entry, log):
        """Take the JSON log and print a formatted version to standard output."""
        jlog = open(log, 'r')

    def printentry(self, entry, formatting):
        """Take a given entry and return a formatted version."""
        for field in entry:
            olabel = formatting.get("olabel")
            ftag = formatting.get("oformat")
            print()

class CliInterface():
    """The command line interactive interface."""
    def main():
        """Control the interface and operate the logger."""
        logger = log.interface.uselogger()
        settings = log.readconf(logger) # Retrieve the configuration from settings.conf
        flist = log.getfields(settings) # Create a fieldlist from the fields given in settings.conf
        entry = log.interface.log(flist) # Create an entry from the fields given in fieldlist
        log.jlogwrt(entry,settings.get("jsonpath")) # Write out the new entry to the log file
        log.tlogwrt(entry,settings.get("txtpath")) # Write out the new entry to a human readable text file
        return 0

    def log(self, flist, logname):
        """Create an entry dictionary (edict) from the given fields and return it."""
        edict = {}
        for fobject in flist:
            if fobject.flabel:
                prompt = fobject.flabel
            else:
                prompt = fobject.name
            if "on_display" in fobject.handlers.keys():
                fobject.on_display_main.main(locals())
            if fobject.prompt:
                entry = False
                while not entry:
                    inbuffer = fobject.prompt(prompt)
                    entry = fobject.validate(inbuffer)
            if "on_input" in fobject.scripts.keys():
                fobject.on_input_main.main(locals())
            edict[fobject.name] = inbuffer
        return edict

    def option(self,options):
        """Take a dictionary of options and present these as choices to the user, return the selected options value."""
        index = 0
        for option in options:
            if (index % 4) == 0 and index > 0:
                print(option)
            else:
                print(option, end='')
        while 1:
            option = input()
            rvalue = options.get(option)
            if rvalue:
                return rvalue
            else:
                print("Not a valid option. Please choose one from the list.")
                continue


class CliUtils():
    """Class object to store static methods related to the Cli interface."""
    def argparse(cls, self, argument, *input_restrictions):
        """Parse the arguments given to a cmd do_ method. input_restriction takes
        dictionaries representing arguments and their restriction parameters."""
        argsplit = argument.split()
        evaluation_results = []
        argindex = 0
        for arg in argsplit:
            restriction = input_restrictions[argindex]
            regex = restriction["regex"]
            orientation = restriction["orientation"]
            errormsg = restriction["errormsg"]
            if cls.validation(cls, self, arg, regex, orientation, errormsg):
                evaluation_results.append(arg)
                if (argindex + 1) < len(input_restrictions):
                    argindex += 1
            else:
                return False
        return evaluation_results

    def validation(cls, self, input_line, regex, orientation, errormsg):
        """Set the name of the field/column."""
        criteria = Restriction(regex, orientation)
        if criteria.validate(input_line):
            return True
        else:
            cls.input_error(cls, self, errormsg)
            return False

    def pyfile_validate(cls, self, script):
        """Specifically perform validation for the name of a python file."""
        if cls.validation(cls, 
                          self, 
                          script,
                          "[^A-Za-z0-9._-]",
                          "discard",
                          "Argument given was not a portable filename. Good style"
                          " says that filenames should only include characters in"
                          " the regex: [A-Za-z0-9._-]"):
            if script[-3:] == ".py":
                cls.input_error("Importing scripts will strip the .py from their"
                                 " name, you should write the script name so that"
                                 " it doesn't have its .py extension.")
                return False
            else:
                return True
        else:
            return False

    def try_catch(cls, self, prompt=">", attribute, severity):
        """Implement a try catch routine to test for presence of attribute.
        Returns true if program execution should continue."""
        try:
            getattr(self, attribute)
        except AttributeError:
            cls.input_error("Attribute " + attribute + " was not filled out.")
            yes = input("Would you like to fill it in now?")
            if yes == 'y' or yes == 'yes':
                setattr(self, attribute, False)
                while not getattr(self, attribute):
                    fill = input(prompt)
                    func = getattr(self, "do_" + attribute)
                    func(fill)
                return True
            else:
                setattr(self, attribute, None)

            if severity == 0:   
                yes = input("Discard changes and exit? y/n:")
                if yes == 'y' or yes == 'yes':
                    return 'discard_exit'
                else:
                    return 'main_exit'
            else:
                return True
        return True

    def input_error(cls, self, message):
        """Prints an error message when input validation returns False."""
        self.stdout.write("*** Input Error: %s\n"%message)

    def print_iterable(cls, iterable, indent):
        """Pretty print items in iterable with given starting indent."""
        def is_iter(obj):
            """Determine if given object is an iterable."""
            try:
                getattr(obj, "__iter__")
            except AttributeError:
                return False
            return True

        def iter_print(cls, start, end, indent, iterable, print_callback):
            """Print iterable objects according to a template. Start prints the
            beginning 'marker' for the object. (eg. A '[' for a list.) And end
            prints the ending 'marker'. (eg. A ']' for a list.) Indent says how
            many spaces to indent printed items. Iterable is the item to be 
            printed. print_callback is a lambda statement that prints individual
            items in the iterable as a side effect of being called. It takes the
            parameters indent and item to print.
            """
            printer_indent = (' ' * (indent - 1))
            print(printer_indent, start)
            for item in iterable:
                if is_iter(item):
                    cls.print_iterable(cls, item, (indent + 2))
                else:
                    print_callback(printer_indent, iterable, item) 
            print(printer_indent, end)

        if not is_iter(iterable):
            print(iterable)
            return False
        elif not isinstance(indent, int):
            raise ValueError("Indent given was not an integer. Only whole number"
                             "s can be used as indents.")

        printer = (lambda indent, iterable, item: print(indent, item))
        printer_indent = (' ' * (indent - 1))
        if isinstance(iterable, list):
            iter_print(cls, "[", "]", indent, iterable, printer)
        elif isinstance(iterable, tuple):
            iter_print(cls, "(", ")", indent, iterable, printer)
        elif isinstance(iterable, range):
            print(printer_indent, iterable)
        elif isinstance(iterable, set):
            iter_print(cls, "{", "}", indent, iterable, printer)
        elif isinstance(iterable, dict):
            printer = (lambda indent, iterable, 
                       item: print(indent, str(item) + ":" + str(iterable[item])))
            iter_print(cls, "{", "}", indent, iterable, printer)
        else:
            iter_print(cls, "?", "?", indent, iterable, printer)
        return True

class CliMainMenu(cmd.Cmd):
    """Implements a command line main menu for the generic logger."""
    def do_list(self, arg):
        """List all the log templates stored in the system. Takes no arguments."""
        paths = Logger.genpaths("placeholder")
        confdir = paths["confdir"]
        templates = os.listdir(confdir)
        for template in templates:
            print(template)

    def do_use(self, logname):
        """Use the logger given as argument: USE <LOGNAME>"""
        if CliUtils.validation(CliUtils,
                               self,
                               logname, 
                               "[^A-Za-z]", 
                               'discard', 
                               "Non-alphabet character in logname."):
            if Logger.verify_logname(Logger, logname):
                log = CliLogMenu(logname)
                log.cmdloop("Logger: Type 'new' for new entry, 'help' for more" 
                            " options.")
                return False

    def do_new(self, logname):
        """Create a new logger with the name passed after command: NEW <LOGNAME>"""
        if CliUtils.validation(CliUtils,
                               self,
                               logname, 
                               "[^A-Za-z]", 
                               'discard', 
                               "Non-alphabet character in logname."):
            new_log = CliMkLogTemplate(logname)
            new_log.cmdloop(logname.capitalize() + ":" + " Type 'add' to create"
                            " a new log entry. Type 'view' to look at an old one"
                            ". Type 'edit' to make changes to an entry that's"
                            " already been made and 'help' for more options.")
            return False

    def do_export(self, filepath):
        """Export all logs and settings as zipfile to filepath: EXPORT <FILEPATH>"""
        export_result = Logger.export_all(Logger, filepath)
        if export_result is True:
            print("All logs exported to:" + filepath)
        elif export_result == "filepath_was_directory":
            CliUtils.input_error(CliUtils, self, "Filepath given was directory.")
            return False
        elif export_result == "invalid_filepath":
            CliUtils.input_error(CliUtils, self, "Filepath is invalid.")
            return False
        elif export_result == "existed_no_overwrite":
            return False
        else:
            CliUtils.input_error(CliUtils, self, export_result)
            return False

    def do_import(self, directory):
        """Import a log from directory: IMPORT <DIRECTORY_PATH>"""
        CliUtils.input_error(CliUtils, self, "Imports are not implemented yet.")
        return False

    def do_exit(self, arg):
        """Exit the logger. Takes no arguments."""
        return True

class CliLogMenu(cmd.Cmd):
    """Implements the menu for an individual logger invoked by do_use()"""
    def __init__(self, logname):
        """Store given logname and run init of parent."""
        super().__init__()
        self.logger = logname
        self.prompt = ("(" + logname + ")" + ">")
        settings = Logger.readconf(Logger, self.logger)
        self.fields = Logger.getfields(Logger, settings, self.logger)
        self.cursor = []

    def do_add(self, arg):
        """Write a new entry in the log: ADD"""
        pass

    def do_view(self, identifier):
        """View log that's specified by identifier given as argument: VIEW 
        <IDENTIFIER>"""
        pass

    def do_search(self, column, searchterm):
        """Search the column using search term. Search terms are regexes, but some
        column types implement their own custom search functionality that may 
        extend or replace this entirely."""
        pass

    def do_edit(self, identifier):
        """Edit the log that's specified by identifier given as argument: EDIT
        <IDENTIFIER>"""
        pass

    def do_export(self, arg):
        """Export log if nothing in cursor, otherwise export entries in cursor 
        to filepath, takes no arguments: EXPORT"""

    def do_finish(self, arg):
        """Write log entries and return to the main menu. Takes no arguments: FINISH"""
        return True


class Field():
    """Implements the base field object for the generic logger."""
    def __init__(self, logname=None, name=None, flabel=None, 
                 olabel=None, ftype=None, prompt=None,
                 restrictions=None, onmatch=None, handlers=None, 
                 oformat=None, search=None):
        self.logname = logname
        self.name = name
        self.flabel = flabel
        self.olabel = olabel
        self.ftype = ftype
        self.prompt = prompt
        self.restrictions = restrictions
        self.onmatch = onmatch
        self.handlers = handlers
        self.oformat = oformat
        self.search = search
    
    def validate(self, line):
        """Validate a line of input according to field restrictions."""
        criteria = Restriction(self.restrictions, self.onmatch)
        if criteria.validate(line):
            return True
        else:
            return False

    def field_dict(self, fdict_template):
        """Return a flat dictionary of the field objects attributes. Given a 
        dictionary with keys that correspond to the name of the attributes you 
        want from the field object fills in the values and returns the dictionary.
        """
        if "type" in fdict_template.keys():
            fdict_template["type"] = self.ftype
        for attribute in fdict_template:
            try:
                fdict_template[attribute] = getattr(self, attribute)
            except AttributeError:
                raise ValueError("field_dict tried to access an attribute that"
                                 " was not part of field object.")
        return fdict_template

    def from_fdict(self, fdict):
        """Return a field object from a flat field dictionary."""
        new_fobject = Field()
        for key in fdict:
            try:
                setattr(new_fobject, key, fdict[key])
            except TypeError:
                raise TypeError("from_fdict recieved dictionary with key that"
                                " was of type other than string.")
        return new_fobject
            
    def get_script(self, script, logname):
        return Logger.get_script(Logger, script, logname)
        
    def unpack_scripts(self, 
                       scripts=self.scripts,
                       logname=self.logname):
        """Unpack given scripts and assign them as methods of field object."""
        for scriptkey in scriptnames:
            scriptname = scriptnames[scriptkey]
            if scriptname:
                script = self.get_script(scriptname, logname)
            else:
                setattr(self, (scriptkey + "_main"), None)
            setattr(self, (scriptkey + "_main"), script)
        return True


class CliMkLogTemplate(cmd.Cmd):
    """Make a log template when 'new' is used from the main menu."""
    def __init__(self, logname):
        """Set the name of the new template. Fields are stored in a list because
        among other things dictionaries are unordered.
        """
        super().__init__()
        self.logname = logname
        self.fields = []
        self.prompt = "(MkTemplate)>"
        self.settings = {}

    def do_status(self, arg):
        """Print the currently set values for this log template."""
        print(self.logname + ":")
        findex = 0
        for field in self.fields:
            print((' '  * 3), (str(findex) + "."), field)
            findex += 1
        for setting in self.settings:
            print((' ' * 3), (setting.capitalize() + ":"), self.settings[setting])
        return False

    def do_add(self, arg):
        """Add a new field by dropping into the field editor. Takes no arguments."""
        FieldEditor = CliFieldEditor(self.logname)
        field = FieldEditor.cmdloop("Fill out the attributes for this field."
                                    " (For assistance type: help)")
        self.fields.append(field)

    def do_remove(self, fieldindex):
        """Remove a field that's been added to the template: remove <fieldindex>"""
        self.fields.pop(fieldindex)

    def do_movpos(self, args):
        """Move the position of field AT arg1 to BEFORE the field at arg2:
        move <arg1> <arg2>
        """
        positions = CliUtils.argparse(CliUtils, 
                                      self, 
                                      args,
                                      {"regex": "[^0-9]",
                                       "orientation": "discard",
                                       "errormsg": "Entered a non-numerical value"
                                       " as part of input. Input should only be"
                                       " index integers."})
        if positions:
            at = positions[0]
            before = positions[1]
            mov_field = self.fields.pop(at)
            self.fields.insert(before, mov_field)
            
    def do_formatting(self, script):
        """Set the script used to format the log for text output."""
        if CliUtils.pyfile_validate(CliUtils, self, script):
            self.settings["formatting"] = script
        
    def do_finalize(self, arg):
        """Verify that at least one field has been specified and warns on unset
        attributes. Takes no arguments."""
        if self.fields:
            CliUtils.try_catch(CliUtils, self, self.prompt, "formatting", 1)
            self.settings["fields"] = self.fields
            Logger.mklogtemplate(Logger, self.logname, self.settings)
            print("Log template written! Returning to main menu...")
            time.sleep(3)
            return True
        else:
            print("You must specify at least one field to create a log template.")
            yes = input("Discard changes and exit? y/n:")
            if yes == "yes" or yes == "y":
                return True
            else:
                return False
                

class CliFieldEditor(cmd.Cmd):
    """Implement the field editor used as part of creating a log template."""
    def __init__(self, logger):
        """Set the name of the logger being created.""" 
        super().__init__()
        self.logger = logger
        self.scripts = {}


    def cmdloop(self, intro=None):
        """Repeatedly issue a prompt, accept input, parse an initial prefix
        off the received input, and dispatch to action methods, passing them
        the remainder of the line as argument.

        """

        self.preloop()
        if self.use_rawinput and self.completekey:
            try:
                import readline
                self.old_completer = readline.get_completer()
                readline.set_completer(self.complete)
                readline.parse_and_bind(self.completekey+": complete")
            except ImportError:
                pass
        try:
            if intro is not None:
                self.intro = intro
            if self.intro:
                self.stdout.write(str(self.intro)+"\n")
            stop = None
            while not stop:
                if self.cmdqueue:
                    line = self.cmdqueue.pop(0)
                else:
                    if self.use_rawinput:
                        try:
                            line = input(self.prompt)
                        except EOFError:
                            line = 'EOF'
                    else:
                        self.stdout.write(self.prompt)
                        self.stdout.flush()
                        line = self.stdin.readline()
                        if not len(line):
                            line = 'EOF'
                        else:
                            line = line.rstrip('\r\n')
                line = self.precmd(line)
                stop = self.onecmd(line)
                stop = self.postcmd(stop, line)
            return self.postloop()
        finally:
            if self.use_rawinput and self.completekey:
                try:
                    import readline
                    readline.set_completer(self.old_completer)
                except ImportError:
                    pass

    def do_status(self, arg):
        """Print the status of attributes in the field, takes no arguments:
        status"""
        def print_status(self, printable):
            try:
                attribute = getattr(self, printable)
                CliUtils.print_iterable(CliUtils, printable, 4)
            except AttributeError:
                print((printable + ":"), "Not set.")

        for printable in ["name", 
                          "flabel", 
                          "olabel", 
                          "type",
                          "prompt",
                          "restrictions", 
                          "onmatch",
                          "scripts",
                          "oformat",
                          "search"]:
            print_status(printable)
        return False
            
        

    def do_name(self, name):
        """Set the name of the field/column: name <name>"""
        if self.validation(name, 
                      "[^A-Za-z]", 
                      'discard', 
                      "Non-alphabet character in fname."):
            self.name = name

    def do_flabel(self, flabel):
        """Set the field label of the field/column: flabel <flabel>"""
        # Flabel has no input restrictions.
        self.flabel = flabel

    def do_olabel(self, olabel):
        """Set the output label of the field/column: olabel <olabel>"""
        # Olabel has no input restrictions.
        self.olabel = olabel

    def do_type(self, ftype):
        """Set the field type of the field/column: type <ftype>"""
        paths = Logger.genpaths(self.logger)
        ftypepath = os.path.join(paths["logdir"], "types.json")
        ftypes = json.load(ftypepath)
        try:
            self.type = ftypes[ftype]
        except KeyError:
            self.input_error("Type given as argument was not a valid type in types.json")

    def do_prompt(self, script):
        """Set the script that displays the prompt for user input. Use no 
        arguments to set to None: prompt <script>"""
        if script == '':
            self.prompt = "no_prompt"
            return False
        else:
            if CliUtils.pyfile_validate(CliUtils, self, script):
                self.scripts["prompt"] = script
                self.prompt = True
                return False
            else:
                return False

    def do_restrictions(self, restrictions):
        """Set the regex of the field/column: restrictions <regex>"""
        # Regex has no input restrictions but is allowed to be wrong.
        self.restrictions = restrictions

    def do_onmatch(self, onmatch):
        """Set whether strings should match or not match restriction regex,
        valid values are 'keep' and 'discard': onmatch <keep|discard>"""
        if self.validation(onmatch,
                           "keep|discard",
                           "keep",
                           "Argument given was not 'keep' or 'discard'."):
            self.onmatch = onmatch

    def do_add_handler(self, args):
        """Set the script <script> that handles the event <event>: add_handler
        <event> <script>"""
        argsplit = args.split()
        event = argsplit[0]
        script = argsplit[1]
        if CliUtils.pyfile_validate(CliUtils, self, script):
            pass
        else:
            return False
        if CliUtils.validation(CliUtils, 
                               self, 
                               event, 
                               "[^A-Za-z_]", 
                               "discard", 
                               "Event names can only have alphabetic"
                               " characters and underscores."): 
            self.scripts[event] = script
            return False
        else:
            return False

    def do_rm_handler(self, event):
        """Remove the handler given by event: rm_handler <event>"""
        self.scripts.pop(event)
        return False

    def do_oformat(self, script):
        """Set the script that is used to format the field for text output: oformat <scriptname>"""
        if self.validation(script,
                           "[^A-Za-z0-9._-]",
                           "discard",
                           "Argument given was not a portable filename. Good style"
                           " says that filenames should only include characters in"
                           " the regex: [A-Za-z0-9._-]"):
            if script[-3:] == ".py":
                self.input_error("Importing scripts will strip the .py from their"
                                 " name, you should write the script name so that"
                                 " it doesn't have its .py extension.")
            else:
                self.scripts["oformat"] = script
                self.oformat = True

    def do_search(self, script):
        """Set the script that is used to search data in this column: search <scriptname>"""
        if self.validation(script,
                           "[^A-Za-z0-9._-]",
                           "discard",
                           "Argument given was not a portable filename. Good style"
                           " says that filenames should only include characters in"
                           " the regex: [A-Za-z0-9._-]"):
            if script[-3:] == ".py":
                self.input_error("Importing scripts will strip the .py from their"
                                 " name, you should write the script name so that"
                                 " it doesn't have its .py extension.")
            else:
                self.scripts["search"] = script
                self.search = True

    def do_finalize(self, arg):
        """Finish and save field. Makes sure that mandatory attributes are filled 
        out, warns on others."""
        def try_catch(attribute, severity):
            """Implement a try catch routine to test for presence of attribute.
            Returns true if program execution should continue."""
            try:
                getattr(self, attribute)
            except AttributeError:
                self.input_error("Attribute " + attribute + " was not filled out.")
                yes = input("Would you like to fill it in now?")
                if yes == 'y' or yes == 'yes':
                    setattr(self, attribute, False)
                    while not getattr(self, attribute):
                        fill = input(self.prompt)
                        func = getattr(self, "do_" + attribute)
                        func(fill)
                    return True
                else:
                    setattr(self, attribute, None)

                if severity == 0:   
                    yes = input("Discard changes and exit? y/n:")
                    if yes == 'y' or yes == 'yes':
                        return 'discard_exit'
                    else:
                        return 'main_exit'
                else:
                    return True
            return True
        
        # Mandatory attributes
        mandatory_sev = 0
        name = try_catch("name", mandatory_sev)
        if name == 'discard_exit':
            return True
        elif name == 'main_exit':
            return False
        ftype = try_catch("type", mandatory_sev)
        if ftype == 'discard_exit':
            return True
        elif ftype == 'main_exit':
            return False
        prompt = try_catch("prompt", mandatory_sev)
        if prompt == 'discard_exit':
            return True
        elif ftype == 'main_exit':
            return False
        # Warning attributes
        warn_sev = 1
        try_catch("flabel", warn_sev)
        try_catch("olabel", warn_sev)
        try_catch("restrictions", warn_sev)
        try_catch("onmatch", warn_sev)
        try_catch("oformat", warn_sev)
        try_catch("search", warn_sev)
        self._field = {"name":self.name,
                       "flabel":self.flabel,
                       "olabel":self.olabel,
                       "type":self.type,
                       "restrictions":self.restrictions,
                       "onmatch":self.onmatch,
                       "scripts":self.scripts}
        return True

    def postloop(self):
        """Return the field that is in turn returned by the main cmdloop."""
        return self._field

    def validation(self, input_line, regex, orientation, errormsg):
        """Set the name of the field/column."""
        criteria = Restriction(regex, orientation)
        if criteria.validate(input_line):
            return True
        else:
            self.input_error(errormsg)
            return False

    def input_error(self, message):
        """Prints an error message when input validation returns False."""
        self.stdout.write("*** Input Error: %s\n"%message)


class Restriction():
    """Bundle together a regex restriction, whether input should be discarded on
    match or on None."""
    def __init__(self, regex, onmatch):
        self.regex = regex
        self.onmatch = onmatch
    
    def validate(line):
        """Validate a line of input by matching it against the regex."""
        if self.regex = None:
            return True
        restrictions = re.compile(self.regex)
        match = restrictions.search(line)
        if match and self.onmatch == 'keep':
            return True
        elif not match and self.onmatch == 'discard':
            return True
        else:
            return False

Logger.main()
