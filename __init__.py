import pymol
from pymol import cmd
import tempfile
import os,math,re
import sys
import requests
from pymol.cmd import _cmd, DEFAULT_ERROR, DEFAULT_SUCCESS, _raising, is_ok, is_error, is_list, space_sc, safe_list_eval, is_string, loadable

def __init_plugin__(app=None):
    '''
    Add an entry to the PyMOL "Plugin" menu
    '''
    from pymol.plugins import addmenuitemqt
    addmenuitemqt('Import Alphafold2 model from EMBL', run_plugin_gui)


# global reference to avoid garbage collection of our dialog
dialog = None


def run_plugin_gui():
    '''
    Open our custom dialog
1991
    '''
    global dialog

    if dialog is None:
        dialog = make_dialog()

    dialog.show()


def make_dialog():
    # entry point to PyMOL's API
    from pymol import cmd

    # pymol.Qt provides the PyQt5 interface, but may support PyQt4
    # and/or PySide as well
    from pymol.Qt import QtWidgets
    from pymol.Qt.utils import loadUi
    from pymol.Qt.utils import getSaveFileNameWithExt

    # create a new Window
    dialog = QtWidgets.QDialog()

    # populate the Window from our *.ui file which was created with the Qt Designer
    uifile = os.path.join(os.path.dirname(__file__), 'Alphafold2import.ui')
    form = loadUi(uifile, dialog)

    # callback for the OK button

    def importAF():
        ## Import user input from the widget
        code = form.code.text()
        name = form.name.text()
        if form.cif.isChecked():
            type = 'cif'
        elif form.pdb.isChecked():
            type = 'pdb'
        else: 
            type = ''
        fetchAF2(code=code, name=name, type=type)

    # hook up button callbacks
    form.pushButton.clicked.connect(importAF)
    form.closeButton.clicked.connect(dialog.close)

    return dialog

def _fetchAF2(code, name, state, finish, discrete, multiplex, zoom, type, path,
        file, quiet, _self=cmd):
    '''
    code = str: single UniProt identifier
    name = str: object name
    state = int: object state
    finish =
    discrete = bool: make discrete multi-state object
    multiplex = bool: split states into objects (like split_states)
    zoom = int: zoom to new loaded object
    type = str: pdb, mmcif 
    path = str: fetch_path
    file = str or file: file name or open file handle
    '''
    r = DEFAULT_ERROR


    # file types can be: pdb, cif
    # bioType is the string representation of the type
    # nameFmt is the file name pattern after download
    bioType = type
    nameFmt = '{code}-AF-v{version}.{type}'
    if type == 'pdb':
        pass
    elif type == 'cif':
        pass
    elif re.match(r'pdb\d+$', type):
        bioType = 'bio'
    else:
        raise ValueError('type')

    url = 'https://alphafold.ebi.ac.uk/files/AF-{code}-F1-model_v{version}.{type}'
   
    versions = [9, 8, 7, 6, 5, 4, 3, 2, 1] #Dirty fix, but should hold up for the foreseeable future
    for version in versions:
        response = requests.get(url.format(code=code,version=version, type=bioType))
        if response.status_code == 200:
            latest_version = version
            break

    fobj = None
    contents = None

    if not file or file in (1, '1', 'auto'):
        file = os.path.join(path, nameFmt.format(code=code, version=latest_version, type=bioType))

    if not is_string(file):
        fobj = file
        file = None
    elif os.path.exists(file):
        # skip downloading
        url = nameFmt

    url = url.format(code=code, version=latest_version, type=bioType)

    try:
        contents = _self.file_read(url)

        # assume HTML content means error on server side without error HTTP code
        if b'<html' in contents[:500].lower():
            raise pymol.CmdException

    except pymol.CmdException:
        if not quiet:
            print(" Warning: failed to fetch from %s" % (url,))
        

    if file:
        try:
            fobj = open(file, 'wb')
        except IOError:
            print(' Warning: Cannot write to "%s"' % file)

    if fobj:
        fobj.write(contents)
        fobj.flush()
        if file:
            fobj.close()

    if not file:
        return DEFAULT_SUCCESS

    if os.path.exists(file):
        r = _self.load(file, name, state, '',
                finish, discrete, quiet, multiplex, zoom)
    elif contents and bioType in ('pdb', 'bio'):
        r = _self.read_pdbstr(contents, name, state,
                finish, discrete, quiet, zoom, multiplex)
    elif contents and bioType in ('cif', 'cc'):
        r = _self.load_raw(contents, 'cif', name, state,
                finish, discrete, quiet, multiplex, zoom)
    cmd.spectrum(expression='b', palette='red_white_blue', selection=name)
    if not _self.is_error(r):
        return name

    print(" Error-fetch: unable to load '%s'." % code)
    return DEFAULT_ERROR

def _multifetchAF2(code,name,state,finish,discrete,multiplex,zoom,type,path,file,quiet,_self):
    import string
    r = DEFAULT_SUCCESS
    code_list = code.split()
    name = name.strip()
    if (name!='') and (len(code_list)>1) and (discrete<0):
        discrete = 1 # by default, select discrete  when loading
        # multiple PDB entries into a single object

    all_type = type
    for obj_code in code_list:
        obj_name = name
        type = all_type

        if not type:
            if 1 < len(obj_code) < 4:
                type = 'cc'
            else:
                type = _self.get('fetch_type_default')

        if not obj_name:
            obj_name = obj_code

        obj_name = _self.get_legal_name(obj_name)

        r = _fetchAF2(obj_code, obj_name, state, finish,
                discrete, multiplex, zoom, type, path, file, quiet, _self)

    return r

@cmd.extend
def fetchAF2(code, name='', state=0, finish=1, discrete=-1,
          multiplex=-2, zoom=-1, type='', async_=0, path='',
          file=None, quiet=1, _self=cmd, **kwargs):

    '''
DESCRIPTION

"fetch" downloads a file from the internet (if possible)

USAGE

fetch code [, name [, state [, finish [, discrete [, multiplex
    [, zoom [, type [, async [, path ]]]]]]]]]

ARGUMENTS

code = a single UniProt identifier or a list of identifiers. 

name = the object name into which the file should be loaded.

state = the state number into which the file should loaded.

type = str: cif, pdb {default: cif}

async_ = 0/1: download in the background and do not block the PyMOL
command line {default: 0 -- changed in PyMOL 2.3}

PYMOL API

cmd.fetchAF2(string code, string name, int state, init finish,
          int discrete, int multiplex, int zoom, string type,
          int async, string path, string file, int quiet)
          
NOTES

When running in interactive mode, the fetch command loads
structures asyncronously by default, meaning that the next command
may get executed before the structures have been loaded.  If you
need synchronous behavior in order to insure that all structures
are loaded before the next command is executed, please provide the
optional argument "async=0".

Fetch requires a direct connection to the internet and thus may
not work behind certain types of network firewalls.

    '''
    state, finish, discrete = int(state), int(finish), int(discrete)
    multiplex, zoom = int(multiplex), int(zoom)
    async_, quiet = int(kwargs.pop('async', async_)), int(quiet)

    if kwargs:
        raise pymol.CmdException('unknown argument: ' + ', '.join(kwargs))

    r = DEFAULT_SUCCESS
    if not path:
        # blank paths need to be reset to '.'
        path = _self.get('fetch_path') or '.'
    if async_ < 0: # by default, run asynch when interactive, sync when not
        async_ = not quiet
    args = (code, name, state, finish, discrete, multiplex, zoom, type, path, file, quiet, _self)
    kwargs = { '_self' : _self }
    if async_:
        _self.async_(_multifetchAF2, *args, **kwargs)
    else:
        try:
            _self.block_flush(_self)
            r = _multifetchAF2(*args)
        finally:
            _self.unblock_flush(_self)
    return r

