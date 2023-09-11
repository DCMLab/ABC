# Data reports: Code for generating figures and tables

This repo contains five Jupyter notebooks in [{MySt}NB](https://myst-nb.readthedocs.io/en/latest/)
Markdown format. They can be opend in Jupyter Notebook or Lab using the 
[Jupytext](https://jupytext.readthedocs.io/) extension. We use this format because 

* Jupytext notebooks are great for version control
* MyST-flavoured can be integrated in a [Sphinx](https://www.sphinx-doc.org/) homepage and treated
  like any other document

## Running the notebooks

* clone the corpus: `git clone --recurse-submodules -j8 git@github.com:DCMLab/dcml_corpora.git`
* create new environment, make it visible to your Jupyter
  * for conda do `conda create --name {name} python=3.10`
  * activate it and install `pip install ipykernel`
  * `ipython kernel install --user --name={name}`
* within the new environment, install requirements, e.g. `pip install -r requirements.txt`
* open up jupyter notebook or jupyter lab and open the `.md` 
  ([documentation](https://jupytext.readthedocs.io/en/latest/paired-notebooks.html#how-to-open-scripts-with-either-the-text-or-notebook-view-in-jupyter))
* change the value `~/dcml_corpora` in the second cell to your local clone.

If the plots are not displayed and you are in JupyterLab, use [this guide](https://plotly.com/python/getting-started/#jupyterlab-support).