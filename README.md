# WeedcUp
a wee little backup utility

## install

in order to use this you first need python, that you probably already have or know how to get,
then it's reccomended to create a virtual environment for the necessary libraries and enter the environment
'''
$ python -m venv .venv
$ source .venv/bin/activate
'''
python libraries are listed in requirements.txt, so they can be easily installed with
'''
$ pip install -r requirements.txt
'''
qrencode is also needed to use this program, install it in whatever way you prefer

## usage

this program can do essentially two things, rendering data to a postscript file that can be printed and rebuilding the original file from scanned qr codes

to render:
'''
$ python ./render.py input-file > output.ps
'''

the postscript file is written on the standard output, here it's being redirected to a file with shell redirection, but i don't know how to do it on windows.  


to rebuild:
'''
$ python ./rebuild.py < codes.b64 > reconstructed-file 
'''

here the `codes.b64` file contains the scanned content of the printed qr codes, one per line, and can be obtained like this:
'''
$ zbarimg --raw -q scan.png > codes.b64
'''
zbar is not a requirement, any program that outputs the content in the same way would work, you could also scan the codes one by one with a phone and paste the strings to a text file in a pinch, the rows don't need to be in any particular order

## notes
in the rendered output, besides the qr codes, there's some data written in hexadecimal, it could be used in place of the qr code in case the code was damaged or when noone has a scanner, camera or phone on hand, though i didn't get to writing the code to use them yet
