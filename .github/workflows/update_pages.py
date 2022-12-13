#!/usr/bin/env python
# coding: utf-8
import argparse
import os
import sys
import io
import base64
from shutil import copy

import corpusstats
import pandas as pd
from ms3 import resolve_dir

INDEX_FNAME = "index.md"
GANTT_FNAME = "gantt.md"
STATS_FNAME = "stats.md"
JEKYLL_CFG_FNAME = "_config.yml"
STYLE_FNAME = "assets/css/style.scss"


def make_index_file(gantt=True, stats=True):
    file = ""
    if gantt:
        file += f"* [Modulation plans]({GANTT_FNAME})\n"
    if stats:
        file +=f"* [Corpus state]({STATS_FNAME})\n"
    return file

def generate_stats_text(pie_string, table_string):
    STATS_FILE = f"""
# Corpus Status

## Vital statistics

{table_string}

## Completion ratios

{pie_string}
"""
    return STATS_FILE


JEKYLL_CFG_FILE = "theme: jekyll-theme-tactile "

STYLE_FILE = """---
---

@import "{{ site.theme }}";

.inner {
  max-width: 95%;
  width: 1024px;
}
"""






def write_to_file(args, filename, content_str):
    path = check_dir(".") if args.out is None else args.out
    fname = os.path.join(path, filename)
    _ = check_and_create(
        os.path.dirname(fname)
    )  # in case the file name included path components
    with open(fname, "w", encoding="utf-8") as f:
        f.writelines(content_str)


def write_gantt_file(args, gantt_path=None):
    if gantt_path is None:
        gantt_path = (
            check_dir("gantt")
            if args.out is None
            else check_dir(os.path.join(args.out, "gantt"))
        )
    fnames = sorted(os.listdir(gantt_path))
    file_content = "\n".join(
        f'<iframe id="igraph" scrolling="no" style="border:none;" seamless="seamless" src="gantt/{f}" height="600" width="100%"></iframe>'
        for f in fnames)
    write_to_file(args, GANTT_FNAME, file_content)


def write_stats_file(args):
    try:
        p = corpusstats.Provider(args.github, args.token)
    except:
        print(f"corpusstats failed with the following message: {sys.exc_info()[1]}")
        return False
    pie_string = ""
    pie_array = []
    for s in p.tabular_stats:
        plot = p.pie_chart(s)
        img = io.BytesIO()
        plot.savefig(img, format="png")
        img.seek(0)
        img = base64.encodebytes(img.getvalue()).decode("utf-8")
        pie_array.append(
            f'<div class="pie_container"><img class="pie" src="data:image/png;base64, {img}"/></div>'
        )
    pie_string = "".join(pie_array)

    vital_stats = pd.DataFrame.from_dict(p.stats, orient="index")
    vital_stats = vital_stats.iloc[0:6, 0:2]
    vital_stats = vital_stats.to_markdown(index=False, headers=[])
    full_text = generate_stats_text(pie_string, vital_stats)
    write_to_file(args, STATS_FNAME, full_text)
    return True



def check_and_create(d):
    """ Turn input into an existing, absolute directory path.
    """
    if not os.path.isdir(d):
        d = resolve_dir(os.path.join(os.getcwd(), d))
        if not os.path.isdir(d):
            os.makedirs(d)
            print(f"Created directory {d}")
    return resolve_dir(d)


def check_dir(d):
    if not os.path.isdir(d):
        d = resolve_dir(os.path.join(os.getcwd(), d))
        if not os.path.isdir(d):
            print(d + " needs to be an existing directory")
            return
    return resolve_dir(d)


def copy_gantt_files(args):
    destination = check_dir(".") if args.out is None else args.out
    destination = check_and_create(os.path.join(destination, 'gantt'))
    for file in sorted(os.listdir(args.dir)):
        if file.endswith('.html'):
            source = os.path.join(args.dir, file)
            copy(source, destination)
            print(f"Copied {source} to {destination}.")
    return destination

def main(args):
    given = sum(arg is not None for arg in (args.github, args.token))
    stats, gantt = False, False
    if given == 2:
        stats = write_stats_file(args)
    elif given == 1:
        print(f"You need to specify both a repository and a token.")
    if args.dir is not None:
        destination = copy_gantt_files(args)
        write_gantt_file(args, destination)
        gantt=True
    if sum((stats, gantt)) > 0:
        index_file = make_index_file(gantt=gantt, stats=stats)
        write_to_file(args, INDEX_FNAME, index_file)
        write_to_file(args, JEKYLL_CFG_FNAME, JEKYLL_CFG_FILE)
        write_to_file(args, STYLE_FNAME, STYLE_FILE)
    else:
        print("No page was generated.")


################################################################################
#                           COMMANDLINE INTERFACE
################################################################################
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="""\
---------------------------------------------------------
| Script for updating GitHub pages for a DCML subcorpus |
---------------------------------------------------------

Description goes here

""",
    )
    parser.add_argument(
        "-g",
        "--github",
        metavar="owner/repository",
        help="If you want to generate corpusstats, you need to pass the repo in the form owner/repository_name and an access token.",
    )
    parser.add_argument(
        "-t",
        "--token",
        metavar="ACCESS_TOKEN",
        help="Token that grants access to the repository in question.",
    )
    parser.add_argument(
        "-d",
        "--dir",
        metavar="DIR",
        type=check_dir,
        help="Pass a directory to scan it for gantt charts and write the file gantt.md",
    )
    parser.add_argument(
        "-o",
        "--out",
        metavar="OUT_DIR",
        type=check_and_create,
        help="""Output directory.""",
    )
    parser.add_argument(
        "-l",
        "--level",
        default="INFO",
        help="Set logging to one of the levels {DEBUG, INFO, WARNING, ERROR, CRITICAL}.",
    )
    args = parser.parse_args()
    # logging_levels = {
    #     'DEBUG':    logging.DEBUG,
    #     'INFO':     logging.INFO,
    #     'WARNING':  logging.WARNING,
    #     'ERROR':    logging.ERROR,
    #     'CRITICAL':  logging.CRITICAL,
    #     'D':    logging.DEBUG,
    #     'I':     logging.INFO,
    #     'W':  logging.WARNING,
    #     'E':    logging.ERROR,
    #     'C':  logging.CRITICAL
    #     }
    # logging.basicConfig(level=logging_levels[args.level.upper()])
    main(args)
