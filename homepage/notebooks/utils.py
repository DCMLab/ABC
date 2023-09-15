import os
from typing import List
from functools import lru_cache
import numpy as np
import colorlover
from git import Repo
import plotly.express as px
import pandas as pd

STD_LAYOUT = {
 'paper_bgcolor': '#FFFFFF',
 'plot_bgcolor': '#FFFFFF',
 'margin': {'l': 40, 'r': 0, 'b': 0, 't': 40, 'pad': 0},
 'font': {'size': 15}
}

CADENCE_COLORS = dict(zip(('HC', 'PAC', 'PC', 'IAC', 'DC', 'EC'), colorlover.scales['6']['qual']['Set1']))
CORPUS_COLOR_SCALE = px.colors.qualitative.D3
TYPE_COLORS = dict(zip(('Mm7', 'M', 'o7', 'o', 'mm7', 'm', '%7', 'MM7', 'other'), colorlover.scales['9']['qual']['Paired']))

CORPUS_NAMES = dict(
    gastoldi_baletti = 'Gastoldi Baletti',
    peri_euridice = 'Peri Euridice',
    monteverdi_madrigals = 'Monteverdi Madrigals',
    sweelinck_keyboard = 'Sweelinck Keyboard',
    frescobaldi_fiori_musicali = 'Frescobaldi Fiori Musicali',
    kleine_geistliche_konzerte = 'Schütz Kleine Geistliche Konzerte',
    corelli = 'Corelli Trio Sonatas',
    couperin_clavecin = 'Couperin Clavecin',
    handel_keyboard = 'Handel Keyboard',
    bach_en_fr_suites = 'Bach Suites',
    bach_solo = 'Bach Solo',
    couperin_concerts = 'Couperin Concerts Royaux',
    pergolesi_stabat_mater = 'Pergolesi Stabat Mater',
    scarlatti_sonatas = 'Scarlatti Sonatas',
    wf_bach_sonatas = 'WF Bach Sonatas',
    jc_bach_sonatas = 'JC Bach Sonatas',
    mozart_piano_sonatas = 'Mozart Piano Sonatas',
    pleyel_quartets = 'Pleyel Quartets',
    beethoven_piano_sonatas = 'Beethoven Sonatas',
    kozeluh_sonatas = 'Kozeluh Sonatas',
    ABC = 'Beethoven String Quartets',
    schubert_dances = 'Schubert Dances',
    schubert_winterreise = 'Schubert Winterreise',
    mendelssohn_quartets = 'Mendelssohn Quartets',
    chopin_mazurkas = 'Chopin Mazurkas',
    schumann_kinderszenen = 'R Schumann Kinderszenen',
    schumann_liederkreis = 'R Schumann Liederkreis',
    c_schumann_lieder = 'C Schumann Lieder',
    liszt_pelerinage = 'Liszt Années',
    wagner_overtures = 'Wagner Overtures',
    tchaikovsky_seasons = 'Tchaikovsky Seasons',
    dvorak_silhouettes = 'Dvořák Silhouettes',
    grieg_lyric_pieces = 'Grieg Lyric Pieces',
    mahler_kindertotenlieder = 'Mahler Kindertotenlieder',
    ravel_piano = 'Ravel Piano',
    debussy_suite_bergamasque = 'Debussy Suite Bergamasque',
    bartok_bagatelles = 'Bartok Bagatelles',
    medtner_tales = 'Medtner Tales',
    poulenc_mouvements_perpetuels = 'Poulenc Mouvements Perpetuels',
    rachmaninoff_piano = 'Rachmaninoff Piano',
    schulhoff_suite_dansante_en_jazz = 'Schulhoff Suite Dansante En Jazz',
)

def color_background(x, color="#ffffb3"):
    """Format DataFrame cells with given background color."""
    return np.where(x.notna().to_numpy(), f"background-color: {color};", None)

def corpus_mean_composition_years(df: pd.DataFrame, 
                                  year_column: str = 'composed_end') -> pd.Series:
    """Expects a dataframe containing ``year_column`` and computes its means by grouping on the first index level ('corpus' by default).
    Returns the result as a series where the index contains corpus names and the values are mean composition years.
    """
    return df.groupby(level=0)[year_column].mean().sort_values()
    
def chronological_corpus_order(df: pd.DataFrame, 
                               year_column: str = 'composed_end') -> List[str]:
    """Expects a dataframe containing ``year_column`` and corpus names in the first index level.
    Returns the corpus names in chronological order
    """
    mean_composition_years = corpus_mean_composition_years(df=df, year_column=year_column)
    return mean_composition_years.index.to_list()


@lru_cache()
def get_corpus_display_name(repo_name: str) -> str:
    """Looks up a repository name in the CORPUS_NAMES constant. If not present,
    the repo name is returned as title case.
    """
    name = CORPUS_NAMES.get(repo_name, "")
    if name == "":
        name = ' '.join(s.title() for s in repo_name.split('_'))
    return name
    

def get_repo_name(repo: Repo) -> str:
    """Gets the repo name from the origin's URL, or from the local path if there is None."""
    if isinstance(repo, str):
        repo = Repo(repo)
    if len(repo.remotes) == 0:
        return repo.git.rev_parse("--show-toplevel")
    remote = repo.remotes[0]
    return remote.url.split('.git')[0].split('/')[-1]

def print_heading(heading: str, underline: chr = '-') -> None:
    """Underlines the given heading and prints it."""
    print(f"{heading}\n{underline * len(heading)}\n")

def resolve_dir(directory: str):
    return os.path.realpath(os.path.expanduser(directory))


def value_count_df(S, thing=None, counts='counts'):
    """Value counts as DataFrame where the index has the name of the given Series or ``thing`` and where the counts
    are given in the column ``counts``.
    """
    thing = S.name if thing is None else thing
    vc = S.value_counts().rename(counts)
    normalized = vc / vc.sum()
    df = pd.concat([vc.to_frame(), normalized.rename('%')], axis=1)
    df.index.rename(thing, inplace=True)
    return df
