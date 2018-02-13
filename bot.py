#!/usr/bin/env python3

import os, sys
import mwclient
import argparse
import mwparserfromhell
import subprocess


def link_is_pdf(tag):
    return tag.text is not None and 'pdf' in tag.text


class Edition:
    def __init__(self):
        self.score_info = None
        self.pdfs = []

    def add_pdf(self, pdf_link):
        self.pdfs.append(pdf_link.title)

    def info(self):
        if self.score_info:
            return '{}, {} pages, {} kB'.format(*self.score_info)
        return ''

    def __repr__(self):
        return 'Edition({}, {})'.format(self.info(), self.pdfs)


def process_text(text):
    parsed = mwparserfromhell.parse(text)
    titles = {}
    editions = []

    for tag in parsed.filter():
        if isinstance(tag, mwparserfromhell.nodes.heading.Heading):
            titles[tag.level] = tag.title
        elif isinstance(tag, mwparserfromhell.nodes.wikilink.Wikilink):
            if link_is_pdf(tag) and titles.get(2) == 'Music files':
                editions[-1].add_pdf(tag)
        elif isinstance(tag, mwparserfromhell.nodes.template.Template):
            if tag.name == 'CPDLno':
                editions.append(Edition())
            elif tag.name == 'ScoreInfo':
                editions[-1].score_info = tag.params

    return editions


def fetch_pdf(cpdl, link, workdir):
    if link.startswith('Media:'):
        filename = link.partition(':')[2]
        pdf = cpdl.images[filename]
        imageinfo = pdf.imageinfo
        sha1 = imageinfo['sha1']
        localname = workdir + '/' + sha1
        if not os.path.exists(localname):
            with open(localname + '.pdf', 'wb') as localfile:
                pdf.download(localfile)
        return sha1, imageinfo
    else:
        raise 1


def convert(workdir, filehash):
    def fn(extn):
        return workdir + '/' + filehash + '.' + extn

    subprocess.check_call(
            'pdftoppm -singlefile -scale-to-x 1000 -scale-to-y -1 -png'.split() +
            [fn('pdf'), fn('uncut')])
    subprocess.check_call(
            ['convert', fn('uncut.png'), '-crop', '1000x500+0+0', '+repage', fn('png')])


def upload(cpdl, wd, filehash, orig):
    print('Uploading', filehash, 'for source PDF', orig)
    with open(wd + '/' + filehash + '.png', 'rb') as src:
        cpdl.upload(
                file=src, filename='Preview' + filehash + '.png',
                description='Automatic preview of {}, generated by PreviewBot.'.format(orig))


def inject_gallery(text, gallery_entries):
    lines = text.split('\n')
    for i, line in enumerate(lines):
        if line.strip() == '==General Information==':
            break
    lines[i:i] = ['==Score previews==', '<gallery widths=500 heights=250>'] + gallery_entries + ['</gallery>']
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--saved-page')
    parser.add_argument('--page')
    args = parser.parse_args()

    username, pwd = open(os.path.expanduser('~/.config/cpdl')).read().split()

    cpdl = mwclient.Site(('http', 'cpdl.org'), path='/wiki/')
    cpdl.login(username, pwd)

    page = cpdl.pages[args.page]
    if args.saved_page:
        with open(args.saved_page) as sp:
            text = sp.read()
    else:
        text = page.text()

    editions = process_text(text)

    gallery_entries = []
    for e in editions:
        for p in e.pdfs:
            filehash, imageinfo = fetch_pdf(cpdl, p, 'wd')
            convert('wd', filehash)
            upload(cpdl, 'wd', filehash, p)
            gallery_entries.append('File:{preview}|{info}|link={url}'.format(
                preview='Preview' + filehash + '.png', info=e.info(), url=imageinfo['url']))

    text = inject_gallery(text, gallery_entries)
    page.save(text, 'Generate PDF previews.')


if __name__ == '__main__':
    main()
