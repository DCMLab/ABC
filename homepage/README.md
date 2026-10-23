# corpus_docs
Sphinx project template to create a corpus documentation homepage including rendered Jupytext notebooks

## Usage


1. `git clone --recurse-submodules git@github.com:DCMLab/corpus_docs.git` will include https://github.com/DCMLab/data_reports 
   as the submodule `notebooks` 
1. `pip install -r requirements.txt` will install the requirements for both the Sphinx project and the notebooks.
1. [set the environment variable] `CORPUS_PATH` to the path where the corpus repo or metarepo is located
1. [set the environment variable] `ANNOTATED_ONLY` to one of `false|f|0` if non-annotated files are to be included
1. `make html` builds the homepage which you can view at `_build/html/index.html`.

## Next steps

This sphinx project includes  that need to be completed using the Jinja templating library: https://realpython.com/primer-on-jinja-templating/
Currently these placeholders include:
* `repo_name`: repository name as in the URLs, e.g. `beethoven_piano_sonatas`
* `pretty_repo_name`: title, e.g. `Ludwig van Beethoven - The piano sonatas`
* `zenodo_badge_id`: ID assigned by Zenodo to ensure that the badge always shows the DOI of the latest version.
* `example_fname`: one of the pieces' file names (without extension) to be used in the docs (e.g. for file paths)
* `example_full_title`: full title of the example, to be included in the text, e.g. `the first movement of the first sonata Op. 2 no. 1`
* `example_subcorpus`: (only for meta-corpora) name of the submodule to which the example belongs

The `index.rst` includes the file `repo_readme.md` which is a dummy file. During the actual building it should be 
replaced by the actual README of the repo. Nevertheless, the dummy could be used to create this README from the 
placeholder variables.

`introduction.rst` requires that for metarepos (which include submodules), the `git clone` command be extended with `--recurse-submodules -j8`

`analyses.rst` needs to be adapted such that non-annotated repos (setting yet to be introduced), the `annotations` and `cadences` notebooks are not included.
Could also be done with two different .rst files for each of the cases.