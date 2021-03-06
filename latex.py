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
    -b, bib <file>                bibliography file
    --no-bib-include              don't auto include the bib, (simply make it
                                  available)
    -m, margin <size>             set the page margin
    --multicols                   use 2 cols
    --append <string>             append the string to the end of the doc after
                                  the references
    --includedir <dir>            include this as a subdir
    --beamer                      make it a beamer
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

def usage(code=None):
    '''Prints the usage and exits with an error code specified by code. If code
    is not given it exits with error_codes['usage']'''
    log(usage_message)
    if code is None:
        log(extended_message)
        code = error_codes['usage']
    sys.exit(code)

def assert_dir_exists(path):
    '''checks if a directory exists. if not it creates it. if something exists
    and it is not a directory it exits with an error.
    '''
    path = os.path.abspath(path)
    if not os.path.exists(path):
        os.mkdir(path)
    elif not os.path.isdir(path):
        log('Expected a directory found a file. "%(path)s"' % locals())
        usage(error_codes['file_instead_of_dir'])
    return path

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

def latex_header(doc_class, margin, multicols,beamer=False):
    if not beamer:
        dc = '\\' + doc_class
        dc += '\n\\usepackage[margin=%s]{geometry}\n'
    else:
        dc = '''\\documentclass{beamer} %% %s
\\usefonttheme{serif}
\\setbeamertemplate{navigation symbols}{}
\setbeamertemplate{bibliography item}[text]
\\usecolortheme[RGB={0,0,0}]{structure}
\\usepackage{ragged2e}
\\justifying''' + ''
#'''
#\\usepackage{pgfpages}
#\\pgfpagesuselayout{2 on 1}[letterpaper,border shrink=5mm]
#'''

    header = dc + '''
\\usepackage{enumerate}
\\usepackage{amssymb}
\\usepackage{amsmath}
\\usepackage{amsthm}
\\usepackage{cancel}
\\usepackage{tabularx}
\\usepackage{url}
\\usepackage{multicol}
\\usepackage{graphicx}
\\usepackage{subfigure}
\\usepackage[multiple]{footmisc}
\\usepackage{esint}
\\usepackage{flushend}
\\makeatletter
\\def\\imod#1{\\allowbreak\\mkern10mu({\\operator@font mod}\\,\\,#1)}
\\makeatother

\\begin{document}
%s
'''
    return header % (margin, '\\begin{multicols}{2}' if multicols else '')

def bib_include():
    return '''
\\bibliographystyle{acm}
\\bibliography{bibliography}
'''

def latex_footer(multicols, append):
    return '''
%s
%s
\\end{document}
''' % ('\\end{multicols}' if multicols else '', append)

def latex(text):
    def process(line):
        sline = line.strip()
        if sline.startswith('\\input{') and sline.endswith('}'):
            fname = sline.replace('\\input{', '').replace('}', '') + '.tex'
            with open(fname, 'r') as f:
                text = f.read()
            return '\n' + '\n'.join(process(line) for line in text.split('\n')) + '\n'
        if sline.startswith('--|'):
            rest = sline.replace('--|', '')
            ret = '\n.decodeme.' + rest.encode('hex') +'\n'
            log(ret)
            return ret
        return line.replace('``', '"').replace("''", '"')
    def out_process(line):
        sline = line.strip()
        if sline.startswith('.decodeme.'):
            try:
                rest = sline.replace('.decodeme.', '')
                return rest.decode('hex')
            except:
                log(sline)
                raise
        elif sline.startswith('\\begin{enumerate}'):
            lines = list()
            lines.append(line)
            lines.append("\\setlength{\\parskip}{0pt}")
            lines.append("\\setlength{\\topsep}{0pt}")
            lines.append("\\setlength{\\partopsep}{-5pt}")
            lines.append("\\setlength{\\itemsep}{0pt}")
            lines.append("\\setlength{\\parsep}{0pt}")
            return "\n".join(lines) + '\n'
        return line
    lines = text.split('\n')
    text = '\n'.join(process(line) for line in lines if not line.startswith('-#-'))
    pandoc = subprocess.Popen(['pandoc', '-f', 'markdown', '-t', 'latex'],
                              stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE)
    out, err = pandoc.communicate(text)
    if pandoc.returncode != 0:
        raise RuntimeError, err

    return '\n'.join(out_process(line) for line in out.split('\n'))

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
            'hsb:m:d:',
            ['help', 'stdin', 'bib=', 'no-bib-include', 'margin=',
              'multicols', 'append=', 'includedir=', 'beamer',
              'doc-class=', 'includefile=',
            ]
        )
    except GetoptError, err:
        log(err)
        usage(error_codes['option'])

    stdin = False
    bib = None
    no_bib_include = False
    margin = '1.0in'
    multicols = False
    append = ''
    includedirs = list()
    includefiles = list()
    beamer = False
    doc_class = 'documentclass[12pt]{article}'
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            usage()
        elif opt in ('-s', '--stdin'):
            stdin = True
        elif opt in ('-b', '--bib'):
            bib = read_file_or_die(assert_file_exists(arg))
        elif opt in ('--no-bib-include',):
            no_bib_include = True
        elif opt in ('-m', '--margin'):
            margin = arg
        elif opt in ('--multicols',):
            multicols = True
        elif opt in ('--append',):
            append = arg
        elif opt in ('--includedir',):
            includedirs.append(assert_dir_exists(arg))
        elif opt in ('--includefile',):
            includefiles.append(assert_file_exists(arg))
        elif opt in ('--beamer',):
            beamer = True
        elif opt in ('-d', '--doc-class'):
            doc_class = arg

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
    if bib is None or no_bib_include:
        latex_text = latex_header(doc_class, margin, multicols, beamer) + latex(text) \
                     + latex_footer(multicols, append)
    else:
        latex_text = latex_header(doc_class, margin, multicols, beamer) + latex(text) \
                     + bib_include() + latex_footer(multicols, append)
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
    navfile = os.path.join(tmpdir, 'page.nav')
    snmfile = os.path.join(tmpdir, 'page.snm')
    tocfile = os.path.join(tmpdir, 'page.toc')
    bibfile = os.path.join(tmpdir, 'bibliography.bib')
    outfile = os.path.join(tmpdir, 'page.out')

    for path in includedirs:
        subprocess.check_call(['cp', '-r', path, tmpdir])
    for path in includefiles:
        subprocess.check_call(['cp', path, tmpdir])

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
            pdflatex(texfile)

        with open(pdffile, 'r') as f:
            output(f.read())
    except:
        os.chdir(mydir)
        with open("page.tex", 'w') as f:
            f.write(latex_text)
        os.chdir(tmpdir)
    finally:
        for path in includedirs:
            subprocess.check_call(['rm', '-rf', os.path.join(tmpdir,
              os.path.basename(path))])
        for path in includefiles:
            subprocess.check_call(['rm', '-rf', os.path.join(tmpdir,
              os.path.basename(path))])
        try: os.unlink(pdffile)
        except: pass
        try:os.unlink(texfile)
        except: pass
        try:os.unlink(auxfile)
        except: pass
        try: os.unlink(logfile)
        except: pass
        try: os.unlink(outfile)
        except: pass
        try:
            os.unlink(navfile)
            os.unlink(snmfile)
            os.unlink(tocfile)
        except: pass
        if bib:
            os.unlink(bibfile)
            try: os.unlink(bblfile)
            except: pass
            try: os.unlink(blgfile)
            except: pass
        os.rmdir(tmpdir)

if __name__ == '__main__':
    main(sys.argv[1:])

