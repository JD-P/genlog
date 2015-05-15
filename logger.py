#!/usr/bin/python3

# We start by importing time and datetime. The former lets us get and write the current time and date to a file. The latter lets us get the distance between two times

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
        qualified pkgname."""
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

    def search_column(self, column_data, searchterm, field):
        """Search the column with the regex searchterm using the fields search 
        function or a fallback."""
        if "search" in field.scripts.keys():
            search_results = field.search(searchterm, column_data)
            return search_results
        else:
            try:
                pattern = re.compile(searchterm)
            except:
                return 'regex_compile_error'
            search_results = []
            for index in range(0, len(column_data)):
                item = column_data[index]
                if pattern.search(item):
                    search_results.append((index, item))
            return search_results

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

    def export_direct(self, data, filepath):
        """Export the objects in data to zipped json archive at filepath."""
        pathcheck = self.verify_file_before_write(filepath)
        if pathcheck is not True:
            return pathcheck
        else:
            export_archive = zipfile.ZipFile(filepath, "w")
            data_json = json.dumps(data)
            export_archive.writestr("data.json", data_json)
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
            export_archive = zipfile.ZipFile(filepath, "w")
            entries_json = json.dumps(log_entries)
            export_archive.writestr("entries.json", entries_json)
            export_archive.close()
            return True
        

class LogPrinter():
    """Genlog implements a dynamic log printing system that gives execution 
    hooks to style output and control line wrapping. Each column declares a
    minimum and maximum width, which works within the context of the log itself
    declaring a minimum and maximum width for each line of the output. 

    Each minimum and maximum is either *fixed* or *dynamic*. Dynamic columns
    can be trimmed to fit the requirements of the log output, fixed columns
    *must* be printed with their full width on each line. Fixed columns are
    dangerous because if they exceed the fixed properties of the log you get an
    error so dynamic columns are always preferred where possible. 

    With columns fixed and dynamic control what happens when line wrapping is 
    forced by the output. In logs it controls what is allowable output and how 
    much space columns have to work with.

    The exact behavior of each is as follows:

    For logs:

    Fixed Minimum:
        Each line *must* be at least as many characters as the minimum defined.

    Fixed Maximum:
        Each line *must* be no more than as many characters as the maximum 
        defined.
    
    Dynamic Minimum:
        The printer will try to optimize the widths of columns so that each line
        is at least this many characters long. But it won't gauruntee it.

    Dynamic Maximum:
        The printer will try to optimize the widths of columns so that each line
        is no more than this many characters, but it won't guauruntee it.

    For columns:

    Fixed Maximum:
        The printer *must* give the column this much space for line wrapping.

    Fixed Minimum:
        The printer *must* give the column this much space for line wrapping.
        Only taken into account when the column has a dynamic maximum.

    Dynamic Maximum:
        The printer will try to optimize the widths of columns so that
        this field will have its ideal line wrapping width. But it's not 
        guarunteed.

    Dynamic Minimum:
        The printer will try to optimize the widths of columns so that 
        this field will have at least this much line wrapping width. But it's
        not guarunteed.

    Printer objects are composed from two base objects, a Minimum and a Maximum
    which have their dynamicism as object attributes along with a width. Each 
    column has an execution hook that takes the data in the column and has full
    access to pythons programming facilities to manipulate and style the data.
    Each log has an execution hook that takes each row in the log after it's been
    styled by the execution hooks for each column and returns styling applied 
    across the entire row, with control of seperators and the header and footer
    of the log file.

    The process for determining how much space each column gets is as follows:

    Fixed width columns are allotted the necessary space from what is available.
    Since fixed maximums demand that a certain amount of space be *available*
    they are considered first and their minimums ignored. If these exceed the
    fixed parameters of the PrintLog object then an error is raised. Next the
    fixed minimums are considered for those fields which have a dynamic maximum.
    If these combined with the fixed maximums exceed the fixed parameters of the
    log an error is raised. 

    Finally dynamic column widths are considered. For dynamic columns
    the amount of space left is evaluated and if sufficient all dynamic columns
    are granted their maximum line wrapping width. Otherwise the smallest column
    width is used to determine a ratio between the columns that will be used to
    trim their lengths down from their dynamic maximums. When a column reaches
    it's minimum dynamic or otherwise then trimming other dynamic maximums down
    to their minimum will take priority over trimming past the dynamic minimum.

    Only once all other resources have been exhausted will the printer start
    trimming widths past their dynamic minimums to save space.

    Dealing with unbounded maximums:
    As fixed maximums are allowed to declare an unbounded amount of space using 
    the '*', if this is the case then all dynamic columns are reduced to their 
    minimum fixed or otherwise and more will be trimmed in the case of conflicts.

    Dynamic maximums that declare an unbounded amount of space are given as much
    space as it is possible to give within the constraint that it will not bring
    column widths down past their minimum dynamic or otherwise.

    If multiple columns declare unbounded widths then the space will be divided
    equally among them.
    """
    class AbstractWidth():
        """Base class for minimum and maximum widths for columns."""
        def __init__(self, width, width_type='dynamic'):
            if width_type not in ('dynamic', 'fixed'):
                raise ValueError("Width type" + width_type + "not a valid type.")
            elif not isinstance(width, int):
                raise ValueError("Width must be of type int, got '" + 
                                 str(type(width)) + "'.")
            elif width < 1:
                raise ValueError("Width must be at least one.")
            else:
                self.width = width
                self.width_type = width_type

    class Minimum(AbstractWidth):
        """Set the minimum width of a column in the text output.
        Valid values for width_type are 'dynamic' and 'fixed'.
        """
        pass

    class Maximum(AbstractWidth):
        """Set the maximum width of a column in the text output.
        Valid values for width_type are 'dynamic' and 'fixed'.
        """
        pass

    class AbstractPrint():
        """Base class for print objects such as logs and columns."""
        def __init__(self, minimum, maximum)::
            if minimum.width > maximum.width:
                raise ValueError("Minimum was greater than Maximum.")
            self.minimum = minimum
            self.maximum = maximum

    class PrintLog(AbstractPrint):
        'Defines the line wrapping width and dimensions of a log output medium.'
        def __init__(self, minimum, maximum):
            super()__init__(self, minimum, maximum)
            self.fixed_column_spacing = {}
            self.dynamic_column_spacing = {}

        def _print_debug(self, pcolumn_widths):
            """Print debugging info for someone to figure out what fixed columns
            caused an error."""
            erronous_pcolumns = {}
            for pcolumn in pcolumns:
                fname = pcolumn.column["fname"]
                

        def add_fixed_spacing(self, pcolumn):
            """Add and check the space declaration to the print objects internal 
            tracker."""
            if pcolumn.maxium.width_type == 'fixed':
                print_object.column_spacing[pcolumn] = pcolumn.maximum.width
                self.column_spacing[pcolumn] = pcolumn.maximum.width
            elif pcolumn.minimum.width_type == 'fixed' and pcolumn.maximum.width_type == 'dynamic':
                print_object.column_spacing[pcolumn] = pcolumn.minimum.width
                self.column_spacing[pcolumn] = pcolumn.minimum.width
            else:
                return False
            fixed_max_pcolumn_widths = {}
            fixed_min_pcolumn_widths = {}
            for space_declaration in self.fixed_column_spacing:
                fwidth = fixed_column_spacing[space_declaration]
                if space_declaration.maximum.width >= fwidth:
                    fname = space_declaration.column["fname"]
                    fixed_max_pcolumn_widths[fname] = fwidth
                else:
                    fname = space_declaration.column["fname"]
                    fixed_min_pcolumn_widths[fname] = fwidth
            if sum(fixed_max_widths) > self.maximum.width:
                print(self.fixed_column_spacing)
                raise ValueError("Length of fixed

        def add_dynamic_spacing(self, pcolumn):
            """
            
            
    class PrintColumn(AbstractPrint):
        'Defines the line wrapping width of a single column to be printed.'
        def __init__(self, minimum, maximum, column):
            super()__init__(self, minimum, maximum)
            self.column = column

    class OutputFormat():
        """Template class for an oformat module. 
        """
        def spacing(self, column, column_formats, print_object, known={}):
            """A stub to be filled in by a real function.

            Should return a PrintColumn object.
            """
            pass

        def format(self, column, width):
            """A stub to be filled in by a real function."""
            pass

    def print_to(self, log, print_object):
        """Print a log object given as JSON and return text formatted according
        to the properties of the given print object."""
        #routine to grab the oformat scripts and etc for each column

    def spacing_negotiation(self, column_formats, print_object):
        """Call the spacing declaration method of each oformat script module.
        Each call is passed the other oformat modules and the print_object to
        prepare spacing for. The first step of the log printing process is to
        figure out the space allocated to each column to print in, each call
        ultimately returns a PrintColumn object that is evaluated by the Printer
        to determine final widths for each column. 

        Since the PrintColumn returned might depend on what the other columns
        declare it is possible that a oformat spacing negotiation method might
        run the spacing negotiation methods of the other columns with the same
        information it recieved when it was called along with its desired width
        to see what that means the other columns will declare and adjust its own
        width accordingly.

        column_formats: A list of tuples where each tuple is a pair with
        a column on the left and its oformat module on the right.

        print_object: The print medium to prepare spacing for.
        """
        column_widths = []
        for method in column_formats:
            column_formats[0] = column
            column_formats[1] = oformat
            declaration = oformat.spacing(column, column_formats, print_object)
            column_widths.append(declaration)
        return column_widths

    def determine_widths(self, column_widths, print_object):
        """Given the spacing declarations of each column and the dimensions of
        the print medium, determine how much space each column will actually get 
        to print in.
        """
        for pcolumn in column_widths:
            print_object.add_spacing(pcolumn)

    
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
