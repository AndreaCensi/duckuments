import pickle
import sys
from collections import OrderedDict

import yaml
from bs4 import Tag
from mcdp_docs import logger
from mcdp_docs.embed_css import embed_css_files
from mcdp_docs.mcdp_render_manual import get_extra_content, CROSSREF_CSS, CROSSREF_SCRIPT
from mcdp_docs.sync_from_circle import get_artefacts, get_links2
from mcdp_report.html import get_css_filename
from mcdp_utils_misc import write_data_to_file, AugmentedResult
from mcdp_utils_xml import bs, gettext

BOOKS = """
!!omap
- base:
    title: Information about the project
    
    abstract: |
        This is general information about the project
        and how to contribute to it.
    
    books: !!omap
    
        - the_duckietown_project:
            title: The Duckietown Project
            abstract: |
                Learn about the history and current status.
                    
        - guide_for_instructors:
            title: Guide for instructors

        - duckumentation: 
            title: Contributing to the documentation
             
     
- tech:
    title: Operation manuals
    
    abstract: |
    
        These are the operation manuals.
    
    books: !!omap
            
        - opmanual_duckiebot:
            title: Duckiebot manual
        
        - opmanual_duckietown:
            title: Duckietown manual
             
        - software_carpentry:
            title: Reference for useful commands
             
- SW:
    title: Software development
    
    books: !!omap
        - software_architecture:
            title: Duckietown software architecture

        - software_devel:
            title: Software development in Duckietown
             
        - code_docs:
            title: Packages documentation
             
     
- theory:
    title: Class materials
     
    books: !!omap
            
        - learning_materials:
            title: Learning materials
             
        - exercises:
            title: Exercises     
        
        - preliminaries:
            title: Preliminaries


- fall2017:
    title: Past editions
    books: !!omap
            
        - class_fall2017:
            title: Fall 2017
             
        - class_fall2017_projects:
            title: Fall 2017 projects
            
- misc:
    title: Miscellanea
    
    abstract: |
        Other content
    
    books: !!omap
        - drafts:
            title: Drafts
            
        - deprecated:
            title: Deprecated
    
"""

def go():
    groups = OrderedDict(yaml.load(BOOKS))

    import os

    dist = 'duckuments-dist'

    html = Tag(name='html')
    head = Tag(name='head')
    meta = Tag(name='meta')
    meta.attrs['content'] = "text/html; charset=utf-8"
    meta.attrs['http-equiv'] = "Content-Type"

    stylesheet = 'v_manual_split'
    link = Tag(name='link')
    link['rel'] = 'stylesheet'
    link['type'] = 'text/css'
    link['href'] = get_css_filename('compiled/%s' % stylesheet)
    head.append(link)

    body = Tag(name='body')

    style = Tag(name='style')

    style.append(CSS)


    head.append(style)
    head.append(meta)

    html.append(head)
    html.append(body)

    divgroups = Tag(name='div')
    all_crossrefs = Tag(name='div')

    res = AugmentedResult()

    for id_group, group in groups.items():
        divgroup = Tag(name='div')
        divgroup.attrs['class'] = 'group'
        divgroup.attrs['id'] = id_group

        h0 = Tag(name='h1')
        h0.append(group['title'])

        divgroup.append(h0)

        if 'abstract' in group:
            p = Tag(name='p')
            p.append(group['abstract'])
            divgroup.append(p)

        books = group['books']
        # divbook = Tag(name='div')
        books = OrderedDict(books)
        for id_book, book in books.items():
            d = os.path.join(dist, id_book)
            d0 = dist

            errors_and_warnings = os.path.join(d, 'out', 'errors_and_warnings.pickle')
            if os.path.exists(errors_and_warnings):
                resi = pickle.loads(open(errors_and_warnings).read())
                res.merge(resi)
            else:
                msg = 'Path does not exist: %s' % errors_and_warnings
                logger.error(msg)

            artefacts = get_artefacts(d0, d)

            div = Tag(name='div')
            div.attrs['class'] = 'book-div'
            div.attrs['id'] = id_book
            div_inside = Tag(name='div')
            div_inside.attrs['class'] = 'div_inside'
            links = get_links2(artefacts)

            for a in links.select('a'):
                s = gettext(a)
                if 'error' in s or 'warning' in s or 'task' in s:
                    a['class'] = 'EWT'
            # p  = Tag(name='p')

            if False:
                h = Tag(name='h3')
                h.append(book['title'])

                # div_inside.append(h)
                if 'abstract' in book:
                    p = Tag(name='p')
                    p.append(book['abstract'])
                    div_inside.append(p)

            div_inside.append(links)
            div.append(div_inside)

            toc = os.path.join(d, 'out/toc.html')
            if os.path.exists(toc):
                data = open(toc).read()
                x = bs(data)
                for a in x.select('a[href]'):
                    href = a.attrs['href']
                    a.attrs['href'] = id_book + '/out/' + href
                div.append(x)
            crossrefs = os.path.join(d, 'crossref.html')
            if os.path.exists(crossrefs):
                x = bs(open(crossrefs).read())
                all_crossrefs.append(x.__copy__())
            else:
                logger.error('File does not exist %s' % crossrefs)

            divgroup.append(div)
        divgroups.append(divgroup)


    out_pickle = sys.argv[3]
    from mcdp_docs.manual_constants import MCDPManualConstants

    nwarnings = len(res.get_notes_by_tag(MCDPManualConstants.NOTE_TAG_WARNING))
    ntasks = len(res.get_notes_by_tag(MCDPManualConstants.NOTE_TAG_TASK))
    nerrors = len(res.get_notes_by_tag(MCDPManualConstants.NOTE_TAG_ERROR))
    logger.info('%d tasks' % ntasks)
    logger.warning('%d warnings' % nwarnings)
    logger.error('%d nerrors' % nerrors)

    from mcdp_docs.mcdp_render_manual import write_errors_and_warnings_files
    write_errors_and_warnings_files(res, os.path.dirname(out_pickle))

    # write_data_to_file(pickle.dumps(res), out_pickle, quiet=False)

    extra = get_extra_content(AugmentedResult())

    extra.attrs['id'] = 'extra'
    body.append(extra)
    body.append(divgroups)

    embed_css_files(html)

    for e in body.select('.notes-panel'):
        e.extract()
    out = sys.argv[1]
    write_data_to_file(str(html), out)

    manifest = [dict(display='summary', filename=os.path.basename(out))]
    mf = os.path.join(os.path.dirname(out), 'summary.manifest.yaml')
    write_data_to_file(yaml.dump(manifest), mf)

    out_crossrefs = sys.argv[2]

    html = Tag(name='html')
    head = Tag(name='head')
    body = Tag(name='body')
    style = Tag(name='style')
    style.append(CROSSREF_CSS)
    head.append(style)
    html.append(head)

    script = Tag(name='script')
    script.append(CROSSREF_SCRIPT)
    body.append(all_crossrefs)
    body.append(script)
    html.append(body)

    write_data_to_file(str(html), out_crossrefs)


# language=css
CSS = """
    body {
        width: 100% !important;
        margin: 1em !important;
        padding: 0 !important;

    }
    .EWT {
        display: none;
        font-weight: bold;
        font-size: smaller;
        color: darkblue;
    } 
    a.EWT {
        text-decoration: none;
        font-family: arial;
    } 
    .show_todos .EWT {
        display: inline;
    }
    .toc_what {
        display: none;
    }

    .toc_a_for_part {
        padding-top: 0;

    }

    .toc_a_for_book {
        font-size: 150%;
        font-weight: bold;
        margin-top: 0.2em;
    }
    .toc_a_for_book::after {
        font-size: 100%;
    }

    h3 {
        font-size: 150%;
        color: black;
        text-align: left;
        border-bottom: 0;
        margin-top: 0.3em;
        padding-top: 0;
    }

    div.group {
        column-count: auto;
        column-width: 22em;
        width: calc(100% - 4em);
        display: block;
        background-color: #eaeaea;
        padding: 1em;
        margin: 1em;
        min-height: 12em;
    }

    div.book-div span a:nth-child(2) {
        margin-right: 2em;
    }
    div.book-div {
        background-color: #ddd;
        margin: 1em;
        padding: 10px;
    }
    .div_inside {
        break-inside: avoid;
    }
    ul,li {
    list-style: none;
    }
    #extra .notes-panel {
    display: none; 
    }
    .toc_ul-depth-3 {
    display: none;
    }
    """

if __name__ == '__main__':
    go()
