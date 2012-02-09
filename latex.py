#!/usr/bin/env python
# Tim Henderson
# tim.tadh@gmail.com

import os, sys, subprocess
from getopt import getopt, GetoptError
import tempfile

usage_message = \
'''usage: latex.py file.md'''

extended_message = \
'''Options
    -h, help                      print this message
    -s, stdin                     read from stdin instead of file
'''

error_codes = {
    'usage':1,
    'file_not_found':2,
    'option':3,
    'args':4,
}

def log(s):
    sys.stderr.write(str(s))
    sys.stderr.write('\n')
    sys.stderr.flush()

def output(s):
    sys.stdout.write(str(s))
    sys.stdout.write('\n')
    sys.stdout.flush()

## A utility function stolen from:
# http://stackoverflow.com/questions/1158076/implement-touch-using-python/1160227#1160227
def touch(fname, times = None):
    fhandle = file(fname, 'a')
    try:
        os.utime(fname, times)
    finally:
        fhandle.close()

def latex_header():
    return '''
\\documentclass[12pt]{article}
\\usepackage[margin=0.8in]{geometry}
\\usepackage{enumerate}


\\begin{document}
'''

def latex_footer():
    return '''
\\end{document}
'''

def latex(text):
    pandoc = subprocess.Popen(['pandoc', '-f', 'markdown', '-t', 'latex'], 
                              stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE)
    out, err = pandoc.communicate(text)
    if pandoc.returncode != 0:
        raise RuntimeError, err
    return out

def pdflatex(path):
    pdflatex = subprocess.Popen(['pdflatex', path],
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = pdflatex.communicate()
    log(out)
    log(err)
    if pdflatex.returncode != 0:
        raise RuntimeError, (out, err)

def main(args):
    try:
        opts, args = getopt(args,
            'hs',
            ['help', 'stdin']
        )
    except GetoptError, err:
        log(err)
        usage(error_codes['option'])

    stdin = False
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            usage()
        elif opt in ('-s', '--stdin'):
            stdin = True

    if len(args) != 1 and not stdin:
        log('One an only one file is allowed to be built at a time, you gave:')
        log(str(args))
        usage(error_codes['args'])
    elif len(args) == 0 and not stdin:
        log('One an only one file is allowed to be built at a time, you gave:')
        log(str(args))
        usage(error_codes['args'])

    if stdin:
        text = sys.stdin.read()
    else:
        file_path = args[0]
        if not os.path.exists(file_path):
            log('File "%s" does not exist' % file_path)
            usage(error_codes['file_not_found'])
        with open(file_path, 'r') as f:
            text = f.read().strip()
    
    text = text.decode('utf8').encode('utf8')
    latex_text = latex_header() + latex(text) + latex_footer()
    #output(latex_text)
    #sys.exit(0)
   
    tmpdir = '/tmp/testing' #tempfile.mkdtemp()
    os.chdir(tmpdir)
    texfile = os.path.join(tmpdir, 'page.tex')
    pdffile = os.path.join(tmpdir, 'page.pdf')
    auxfile = os.path.join(tmpdir, 'page.aux')
    logfile = os.path.join(tmpdir, 'page.log')
    
    try:
        with open(texfile, 'w') as f:
            f.write(latex_text)
        pdflatex(texfile)
    
        with open(pdffile, 'r') as f:
            output(f.read())
    finally:
        #os.unlink(pdffile)
        #os.unlink(texfile)
        #os.unlink(auxfile)
        #os.unlink(logfile)
        os.rmdir(tmpdir)

if __name__ == '__main__':
    main(sys.argv[1:])

