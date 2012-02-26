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
    'file_not_found':5,
    'bad_file_read':6,
}

def log(s):
    sys.stderr.write(str(s))
    sys.stderr.write('\n')
    sys.stderr.flush()

def output(s):
    sys.stdout.write(str(s))
    sys.stdout.write('\n')
    sys.stdout.flush()

def assert_file_exists(path):
    '''checks if the file exists. If it doesn't causes the program to exit.
    @param path : path to file
    @returns : the path to the file (an echo) [only on success]
    '''
    path = os.path.abspath(path)
    if not os.path.exists(path):
        log('No file found. "%(path)s"' % locals())
        usage(error_codes['file_not_found'])
    return path

def read_file_or_die(path):
    '''Reads the file, if there is an error it kills the program.
    @param path : the path to the file
    @returns string : the contents of the file
    '''
    try:
        f = open(path, 'r')
        s = f.read()
        f.close()
    except Exception:
        log('Error reading file at "%s".' % path)
        usage(error_codes['bad_file_read'])
    return s

def latex_header():
    return '''
\\documentclass[12pt]{article}
\\usepackage[margin=0.8in]{geometry}
\\usepackage{enumerate}
\\usepackage{amssymb}
\\usepackage{amsmath}
\\makeatletter
\\def\\imod#1{\\allowbreak\\mkern10mu({\\operator@font mod}\\,\\,#1)}
\\makeatother


\\begin{document}
'''

def bib_include():
    return '''
\\nocite{*}
\\bibliographystyle{amsalpha}
\\bibliography{bibliography}
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
    if pdflatex.returncode != 0 or "? No pages of output." in out:
        raise RuntimeError, (out, err)

def bibtex(path):
    bibtex = subprocess.Popen(['bibtex', path],
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = bibtex.communicate()
    log(out)
    log(err)
    if bibtex.returncode != 0:
        raise RuntimeError, (out, err)


def main(args):
    try:
        opts, args = getopt(args,
            'hsb:',
            ['help', 'stdin', 'bib=']
        )
    except GetoptError, err:
        log(err)
        usage(error_codes['option'])

    stdin = False
    bib = None
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            usage()
        elif opt in ('-s', '--stdin'):
            stdin = True
        elif opt in ('-b', '--bib'):
            bib = read_file_or_die(assert_file_exists(arg))

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
    if bib is None:
        latex_text = latex_header() + latex(text) + latex_footer()
    else:
        latex_text = latex_header() + latex(text) + bib_include() + latex_footer()
    #output(latex_text)
    #sys.exit(0)
   
    tmpdir = tempfile.mkdtemp()
    mydir = os.getcwd()
    os.chdir(tmpdir)
    texfile = os.path.join(tmpdir, 'page.tex')
    pdffile = os.path.join(tmpdir, 'page.pdf')
    auxfile = os.path.join(tmpdir, 'page.aux')
    logfile = os.path.join(tmpdir, 'page.log')
    bblfile = os.path.join(tmpdir, 'page.bbl')
    blgfile = os.path.join(tmpdir, 'page.blg')
    bibfile = os.path.join(tmpdir, 'bibliography.bib')
    
    try:
        with open(texfile, 'w') as f:
            f.write(latex_text)
        if bib is not None:
            with open(bibfile,'w') as f:
                f.write(bib)        
        pdflatex(texfile)
        if bib is not None:
            bibtex('page')
            pdflatex(texfile)
            pdflatex(texfile)
    
        with open(pdffile, 'r') as f:
            output(f.read())
    except:
        os.chdir(mydir)
        with open("page.tex", 'w') as f:
            f.write(latex_text)
        os.chdir(tmpdir)
    finally:
        try: os.unlink(pdffile)
        except: pass
        os.unlink(texfile)
        os.unlink(auxfile)
        os.unlink(logfile)
        os.unlink(bibfile)
        try: os.unlink(bblfile)
        except: pass
        try: os.unlink(blgfile)
        except: pass
        os.rmdir(tmpdir)

if __name__ == '__main__':
    main(sys.argv[1:])

