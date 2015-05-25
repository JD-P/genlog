"""
Copyright (C) 2015 John David Pressman

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.
This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.
You should have received a copy of the GNU General Public License along
with this program; if not, write to the Free Software Foundation, Inc.,
51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
"""

from logger import Logger, LogPrinter, Field, Restriction

import cmd

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
    def log(cls, flist, logname):
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

    def argparse(self, obj, argument, *input_restrictions):
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
            if self.validation(self, obj, arg, regex, orientation, errormsg):
                evaluation_results.append(arg)
                if (argindex + 1) < len(input_restrictions):
                    argindex += 1
            else:
                return False
        return evaluation_results

    def validation(self, obj, input_line, regex, orientation, errormsg):
        """Validate a line of input given a regex and orientation for a 
        Restriction and an error message to print on failure."""
        criteria = Restriction(regex, orientation)
        if criteria.validate(input_line):
            return True
        else:
            self.input_error(self, obj, errormsg)
            return False

    def pyfile_validate(self, obj, script):
        """Specifically perform validation for the name of a python file."""
        if self.validation(self, 
                          obj, 
                          script,
                          "[^A-Za-z0-9._-]",
                          "discard",
                          "Argument given was not a portable filename. Good style"
                          " says that filenames should only include characters in"
                          " the regex: [A-Za-z0-9._-]"):
            if script[-3:] == ".py":
                self.input_error("Importing scripts will strip the .py from their"
                                 " name, you should write the script name so that"
                                 " it doesn't have its .py extension.")
                return False
            else:
                return True
        else:
            return False

    def try_catch(self, obj, attribute, severity, prompt=">"):
        """Implement a try catch routine to test for presence of attribute.
        Returns true if program execution should continue."""
        try:
            getattr(obj, attribute)
        except AttributeError:
            self.input_error("Attribute " + attribute + " was not filled out.")
            yes = input("Would you like to fill it in now?")
            if yes == 'y' or yes == 'yes':
                setattr(obj, attribute, False)
                while not getattr(obj, attribute):
                    fill = input(prompt)
                    func = getattr(obj, "do_" + attribute)
                    func(fill)
                return True
            else:
                setattr(obj, attribute, None)

            if severity == 0:   
                yes = input("Discard changes and exit? y/n:")
                if yes == 'y' or yes == 'yes':
                    return 'discard_exit'
                else:
                    return 'main_exit'
            else:
                return True
        return True

    def input_error(self, obj, message):
        """Prints an error message when input validation returns False."""
        obj.stdout.write("*** Input Error: %s\n"%message)

    def export_error_handler(self, obj, filepath, export_result):
        if export_result is True:
            print("All logs exported to:" + filepath)
            return True
        elif export_result == "filepath_was_directory":
            CliUtils.input_error(self, obj, "Filepath given was directory.")
            return False
        elif export_result == "invalid_filepath":
            CliUtils.input_error(self, obj, "Filepath is invalid.")
            return False
        elif export_result == "existed_no_overwrite":
            return False
        else:
            CliUtils.input_error(self, obj, export_result)
            return False

    def print_iterable(self, iterable, indent):
        """Pretty print items in iterable with given starting indent."""
        def is_iter(obj):
            """Determine if given object is an iterable."""
            try:
                getattr(obj, "__iter__")
            except AttributeError:
                return False
            return True

        def iter_print(self, start, end, indent, iterable, print_callback):
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
            # Prevent an iterable that yields itself from eating the stack.
            if len(iterable) is 1 and iterable[0] == iterable:
                print_callback(printer_indent, iterable, item)
                return True
            for item in iterable:
                if is_iter(item):
                    self.print_iterable(self, item, (indent + 2))
                else:
                    print_callback(printer_indent, iterable, item) 
            print(printer_indent, end)

        if not is_iter(iterable):
            print(iterable)
            return False
        elif isinstance(iterable, str):
            print(iterable)
            return True
        elif not isinstance(indent, int):
            raise ValueError("Indent given was not an integer. Only whole number"
                             "s can be used as indents.")

        printer = (lambda indent, iterable, item: print(indent, item))
        printer_indent = (' ' * (indent - 1))
        if isinstance(iterable, list):
            iter_print(self, "[", "]", indent, iterable, printer)
        elif isinstance(iterable, tuple):
            iter_print(self, "(", ")", indent, iterable, printer)
        elif isinstance(iterable, range):
            print(printer_indent, iterable)
        elif isinstance(iterable, set):
            iter_print(self, "{", "}", indent, iterable, printer)
        elif isinstance(iterable, dict):
            printer = (lambda indent, iterable, 
                       item: print(indent, str(item) + ":" + str(iterable[item])))
            iter_print(self, "{", "}", indent, iterable, printer)
        else:
            iter_print(self, "?", "?", indent, iterable, printer)
        return True


class CliMainMenu(cmd.Cmd):
    """Implements a command line main menu for the generic logger."""
    prompt = "(GenLogMenu)> "
    def do_list(self, arg):
        """List all the log templates stored in the system. Takes no arguments."""
        templates = Logger.available_logs(Logger)
        if templates:
            for template in templates:
                print(template)
        else:
            print("No log templates installed on this system. Create one with"
                  " the 'new' command from this menu.")

    def do_use(self, logname):
        """Use the logger given as argument: USE <LOGNAME>"""
        if not CliUtils.validation(CliUtils,
                                   self,
                                   logname, 
                                   "[^A-Za-z]", 
                                   'discard', 
                                   "Non-alphabet character in logname."):
            return False
        elif logname == '':
            CliUtils.input_error(CliUtils, self, "Didn't give a logname.")
            return False
        else:
            if Logger.verify_logname(Logger, logname):
                log = CliLogMenu(logname)
                log.cmdloop("Logger: Type 'new' for new entry, 'help' for more" 
                            " options.\n\n")
                return False

    def do_new(self, logname):
        """Create a new logger with the name passed after command: NEW <LOGNAME>"""
        if CliUtils.validation(CliUtils,
                               self,
                               logname, 
                               "[^A-Za-z]", 
                               'discard', 
                               "Non-alphabet character in logname."):
            if logname == '':
                CliUtils.input_error(CliUtils, self, 
                                     "No name was given for new logger.")
                return False
            new_log = CliMkLogTemplate(logname)
            new_log.cmdloop(logname.capitalize() + ":" + " Type 'add' to create"
                            " a new log template and 'help' for more options.\n\n")
            return False

    def do_export(self, filepath):
        """Export all logs and settings as zipfile to filepath: EXPORT <FILEPATH>"""
        export_result = Logger.export_all(Logger, filepath)
        CliUtils.export_error_handler(CliUtils, self, filepath, export_result)
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
        self.prompt = ("(" + logname + ")" + "> ")
        settings = Logger.readconf(Logger, self.logger)
        self.fields = Logger.getfields(Logger, settings, self.logger)
        self.log = Logger.load_log(Logger, logger)
        self.cursor = []

    def do_status(self, arg):
        """Print the status of cursor: Takes no arguments."""
        CliUtils.print_iterable(CliUtils, self.cursor, 4)
        return False

    def do_add(self, arg):
        """Write a new entry in the log: ADD"""
        edict = CliUtils.log(CliUtils, self.fields, self.logger)
        index = (len(self.log[0]["data"]) - 1)
        self.cursor.append((index, edict))
        return False

    def do_view(self, identifier):
        """View log that's specified by identifier given as argument: VIEW 
        <IDENTIFIER>"""
        pass

    def do_search(self, column, searchterm):
        """Search the column using search term. Search terms are regexes, but some
        column types implement their own custom search functionality that may 
        extend or replace this entirely."""
        field = self.fields[column]
        column_dict = self.log[column]
        if field["fname"] != column_dict["fname"]:
            raise ValueError("Columns out of sync/data corruption. Assumption"
                             " about data has been violated.")
        else:
            data = column_dict["data"]
            search_results = Logger.search_column(Logger, data, searchterm, field)
            if search_results == 'regex_compile_error':
                CliUtils.input_error(CliUtils, self, "Search term was not a valid Regex.")
                return False
            else:
                CliUtils.print_iterable(CliUtils, self, search_results, 4)
            

    def do_edit(self, identifier):
        """Edit the entry that's specified by identifier given as argument: EDIT
        <IDENTIFIER>"""
        pass

    def do_export(self, args):
        """This command does different things depending on what it recieves as
        it's first argument. If the first argument is 'cursor' it exports the 
        contents of cursor to a second argument filepath. If the first argument
        is 'entries' then it takes a colon seperated list of ranges as a second
        argument and uses those to grab and export the logs indicated by the
        ranges to the filepath given as a third argument. If the first argument 
        is 'log' then it exports the entire log to the filepath given as a second 
        argument.

        Examples:

        export cursor <filepath> (Exports content of cursor to filepath.)

        export entries 10,15:30,35 <filepath> (Exports the set of entries between and
        including ten and fifteen, and between and including thirty and thirty 
        five to filepath.)

        export log <filepath> (Exports the entire log to filepath.)
        """
        argsplit = args.split()
        if argsplit[0] == 'cursor':
            filepath = argsplit[1]
            export_result = Logger.export_direct(Logger, self.cursor, filepath)
            CliUtils.export_error_handler(CliUtils, self, filepath, export_result)
            return False
        elif argsplit[0] == 'entries':
            if CliUtils.validation(CliUtils,
                                   self,
                                   "(?:([0-9]+),([0-9]+)(:?)?)+",
                                   "keep",
                                   "Range given was not a range: Ranges should be "
                                   "comma seperated value pairs seperated by colons"
                                   ". eg. 0,5:50,60"):
                entries = []
                ranges = argsplit[1].split(":")
                for _range in ranges:
                    pair = _range.split(",")
                    start = pair[0]
                    end = pair[1]
                    entries.append(range(start, end))
                filepath = argsplit[2]
                export_result = Logger.export_entries(Logger, 
                                                      self.logger,
                                                      entries,
                                                      self.fields,
                                                      filepath)
                CliUtils.export_error_handler(CliUtils, self, filepath, export_result)
                return False
        elif argsplit[0] == 'log':
            export_result = Logger.export(Logger, self.logger, filepath)
            CliUtils.export_error_handler(CliUtils, self, filepath, export_result)
            return False
        else:
            CliUtils.input_error(CliUtils, self, "Invalid first argument '" + 
                                 argsplit[0] + "'. See help for more details.")
            return False

    def do_finish(self, arg):
        """Write log entries and return to the main menu. Takes no arguments: FINISH"""
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
        self.prompt = "(MkTemplate)> "
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
            CliUtils.try_catch(CliUtils, self, "formatting", 1, self.prompt)
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
        self.prompt = "(MkField)> "
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
            print_status(self, printable)
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

    def do_list_ftypes(self, arg):
        """List the global ftypes on the system. Takes no arguments."""
        ftypes = Logger.available_ftypes(Logger)
        if not ftypes:
            print("No ftypes were found in the global field type directory."
                  " Something is wrong with your installation of Genlog.")
        else:
            for ftype in ftypes:
                print(ftype)
        return False

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
