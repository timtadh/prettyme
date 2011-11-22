PrettyMe : Make me a pretty web page.
=====================================

I use this script to generate small one off web pages or sites. Mostly for
documentation for students in the classes I TA for. I write the documentation
in markdown and then run it through this tool to generate a webpage. 

Usage
-----

    usage: html.py --css=style.css file.md
    Options
        -h, help                      print this message
        -t, title=[title]             give the html page a title
        -c, css=[file]                give the location of the CSS to include
        -s, stdin                     read from stdin instead of file
        -H, html                      treat the file as html instead of markdown
                                        (assume it is a partial file with no body
                                        tag).

Quick Example
-------------

    ./html.py --css=default.css --title="PrettyMe README" README.md > README.html

