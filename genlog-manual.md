# GenLog - v1.0 #

## Introduction ##

GenLog, or Generic Logger is a program for creating log *templates* that are 
used by the Generic Logger to collect information given by humans and store it 
in a table of data as an *entry*.

## Tables ##

GenLog data is handled in *tables*, which is a structure you have almost 
certainly seen before. In *tabular* data, things are stored in terms of columns
and rows. For example:

Column 1 | Column 2 | Column 3
------------------------------
       0   	  1   	     5
       8	  6	     4
       8	  3	     2

In the above table, '0, 1, 5' would be the data in the first *row*. '1, 6, 3'
would be the data in the second *column*. In GenLog, when entries are discussed
an entry is ultimately a row in the table corresponding to the log. *Fields*,
which are discussed in detail later, correspond to a column in the table That is
every field that is filled out by a user maps onto a column of the table.

## Fields and Field Types ##

Fields are the widgets that take information from the user and insert it into the
log table. Fields have a *type* that defines certain information about the field
such as its behavior and what strings of input are acceptable. Field types can
inherit the properties of other field types by saying that the field is 'typed'
as another field.

SCRIPTS DO NOT INHERIT.

How inheritance works:

First the _<name> directory of the local logger confdir is searched for the name 
of the type or script.

If it's not found there then it's searched for in the global _<name> file in the 
.loggers directory.

Once found, for types:

Each type itself has a type value, which may mean it's the child of another type.
The base case is that a field type is typed as itself, which will here be referred
to as 'genesis'.

Algorithm for finding ancestry:

Given inital field.

If inital field has a type that is genesis, return False.

If inital field has a type that is not genesis, find the ancestor
named as that type: 

- Search local _ftypes directory for name of type.

- If local found halt and return local.

- Search global _ftypes directory for name of type.

- If global found halt and return global.

- If neither yielded result raise error. 

Return ancestor and if ancestor has a type that is genesis halt.
Otherwise repeat procedure with ancestor.

Test cases:

A is genesis.

A is ancestor of B.

Algorithm given A:

Initial field has type genesis and returns False.

Algorithm given B:

Initial field has ancestor and ancestor is found.

Ancestor is A.

A is returned.

Ancestor has a type that is genesis so procedure halts.

Final result is ancestor A of B, which is correct.


## Writing a field for GenLog ##

GenLog handles its logging through execution hooks, or portions of the program 
where it is expected that external programs will be brought in to perform tasks.

When a field is defined, script names are given to handle events that occur 
during the logging process. GenLog fields are meant to be generic, and this 
includes interface. So each field supports multiple interfaces, but is ultimately
specific to these interfaces. This is an unavoidable consequence of wanting to be
able to create arbitrary user interface elements because otherwise you would need
a language for describing them or a universal standard across interfaces for what
elements mean what such as HTML, but this would no longer satisfy the stated 
requirements.

So the main act of writing a field for GenLog is to write scripts to handle these
events, but before that a field dictionary must be created as JSON in either the
_ftypes directory in the configuration directory. (.loggers/_ftypes) or in the log
directory (.loggers/logname/_ftypes).


## Search Trees: ##

Trees are the abstract search path used to determine which script named to handle
an event or which field type should be considered the ancestor of a field or 
other field type.

Right now trees work by the following:

An individual 'tree' is defined as the combination of a logname, a directory name, 
and the predefined 'path' that is followed to search directories with that name 
for a given search. Right now there are two 'trees': _scripts and _ftypes. The 
path that both follow is to start by searching the directory in the local 
logger configuration directory and then the 'global' directory in the .loggers 
directory.

As an example, lets say that a field says that it handles on_input with a 
script called "date_time". How the script would be searched for is it would
start by looking for a file named "date_time" in the _scripts directory of
the <logname>. Then if it didn't find it there it would search in the _scripts
directory of the .loggers directory which is the 'global' script repository.
If it wasn't found in either an error would be raised to this effect.

## Directory structure for generic logger: ##
- home/origin directory
 - .loggers
 - settings.conf
 - _scripts
   - Individual python scripts 
 - _ftypes
   - Individual json files representing field templates
 - **logger directories
  - settings.conf
  - logname-log.json
  - _scripts
    - Individual python scripts
  - _ftypes
    - Individual json files representing field templates

## Data Model: ##

The generic logger data model:

The logger stores *tabular* data, that is data which can be described in terms of
columns and rows in a table. Each column has a *type* that is inherited from its
field in the form that inserts into it.

How it's stored in the logname-log.json file:

- List
  - Dictionary per column
    - fname (string): The field name associated with the column.
    - olabel (string): The output label for this column.
    - type (string): The type of field for this column.
    - data (list): The actual stored data for the column.
      - individual values for each row this column is a part of 

Restrictions should eventually be stored in a tree structure along with _scripts and _ftypes 


## Exportation: ##

Three kinds of exports:

1. Exporting every log and the settings and all ftypes etc: A full backup.

2. Exporting a single log and the settings/etc: A targeted backup.

3. Exporting a number of log *entries*: A very targeted backup/export.
