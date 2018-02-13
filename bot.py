#!/usr/bin/env python3

import os, sys
import mwclient
import argparse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('page')
    args = parser.parse_args()

    username, pwd = open(os.path.expanduser('~/.config/cpdl')).read().split()

    cpdl = mwclient.Site(('http', 'cpdl.org'), path='/wiki/')
    cpdl.login(username, pwd)

    page = cpdl.pages[args.page]
    text = page.text() + '\nEdited by PreviewBot}.'
    page.save(text, 'Test editing.')


if __name__ == '__main__':
    main()
