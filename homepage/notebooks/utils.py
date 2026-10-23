from __future__ import annotations

import colorsys
import os
import re
from collections import Counter, defaultdict
from fractions import Fraction
from functools import cache
from numbers import Number
from typing import (
    Dict,
    Hashable,
    Iterable,
    Iterator,
    List,
    Literal,
    Optional,
    Tuple,
    Union,
)
from urllib.error import HTTPError
from urllib.request import urlretrieve

import colorlover
import dimcat as dc
import frictionless as fl
import ms3
import numpy as np
import numpy.typing as npt

# import modin.pandas as pd
import pandas as pd
import plotly.express as px
import seaborn as sns
from dimcat import Dataset
from dimcat.base import FriendlyEnum, deserialize_json_file, get_setting
from dimcat.data import resources
from dimcat.data.resources.facets import add_chord_tone_intervals
from dimcat.data.resources.features import extend_bass_notes_feature
from dimcat.data.resources.results import TypeAlias
from dimcat.data.resources.utils import (
    join_df_on_index,
    make_adjacency_groups,
    make_group_start_mask,
    merge_columns_into_one,
    str2pd_interval,
    transpose_notes_to_c,
)
from dimcat.enums import BassNotesFormat
from dimcat.plotting import (
    make_bar_plot,
    make_scatter_3d_plot,
    make_scatter_plot,
    update_figure_layout,
)
from dimcat.steps import slicers
from dimcat.steps.analyzers import prevalence
from dimcat.utils import get_middle_composition_year, grams, make_transition_matrix
from git import Repo
from IPython.display import display
from matplotlib import gridspec
from matplotlib import pyplot as plt
from matplotlib.figure import Figure as MatplotlibFigure
from plotly import graph_objects as go
from plotly.colors import sample_colorscale
from plotly.subplots import make_subplots
from scipy.spatial import ConvexHull
from scipy.stats import entropy
from sklearn import set_config
from sklearn.decomposition import PCA
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.metrics.pairwise import cosine_distances
from sklearn.neighbors import NeighborhoodComponentsAnalysis
from sklearn.preprocessing import Normalizer, StandardScaler

from create_gantt import create_gantt, fill_yaxis_gaps

set_config(transform_output="pandas")

RANDOM_STATE = np.random.RandomState(42)

HERE = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FOLDER = os.path.abspath(os.path.join(HERE, "outputs"))
DEFAULT_OUTPUT_FORMAT = ".png"
DEFAULT_COLUMNS = ["mc", "mc_onset"]  # always added to bigram dataframes
CORPUS_COLOR_SCALE = px.colors.qualitative.D3
COLOR_SCALE_SETTINGS = dict(
    color_continuous_scale="RdBu_r", color_continuous_midpoint=2
)
TPC_DISCRETE_COLOR_MAP = dict(zip(range(-15, 20), sample_colorscale("RdBu_r", 35)))
STD_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    margin={"l": 40, "r": 0, "b": 0, "t": 80, "pad": 0},
    font={"size": 25},
    xaxis=dict(gridcolor="lightgrey"),
    yaxis=dict(gridcolor="lightgrey"),
)

CORPUS_COLOR_SCALE = px.colors.qualitative.D3

CORPUS_NAMES = {
    "ABC": "Beethoven String Quartets",
    "bach_en_fr_suites": "Bach Suites",
    "bach_solo": "Bach Solo",
    "bartok_bagatelles": "Bartok Bagatelles",
    "beethoven_piano_sonatas": "Beethoven Sonatas",
    "c_schumann_lieder": "C Schumann Lieder",
    "chopin_mazurkas": "Chopin Mazurkas",
    "corelli": "Corelli Trio Sonatas",
    "couperin_clavecin": "Couperin Clavecin",
    "couperin_concerts": "Couperin Concerts Royaux",
    "cpe_bach_keyboard": "CPE Bach Keyboard",
    "debussy_suite_bergamasque": "Debussy Suite Bergamasque",
    "dvorak_silhouettes": "Dvořák Silhouettes",
    "frescobaldi_fiori_musicali": "Frescobaldi Fiori Musicali",
    "gastoldi_baletti": "Gastoldi Baletti",
    "grieg_lyric_pieces": "Grieg Lyric Pieces",
    "handel_keyboard": "Handel Keyboard",
    "jc_bach_sonatas": "JC Bach Sonatas",
    "kleine_geistliche_konzerte": "Schütz Kleine Geistliche Konzerte",
    "kozeluh_sonatas": "Kozeluh Sonatas",
    "liszt_pelerinage": "Liszt Années",
    "mahler_kindertotenlieder": "Mahler Kindertotenlieder",
    "medtner_tales": "Medtner Tales",
    "mendelssohn_quartets": "Mendelssohn Quartets",
    "monteverdi_madrigals": "Monteverdi Madrigals",
    "mozart_piano_sonatas": "Mozart Piano Sonatas",
    "pergolesi_stabat_mater": "Pergolesi Stabat Mater",
    "peri_euridice": "Peri Euridice",
    "pleyel_quartets": "Pleyel Quartets",
    "poulenc_mouvements_perpetuels": "Poulenc Mouvements Perpetuels",
    "rachmaninoff_piano": "Rachmaninoff Piano",
    "ravel_piano": "Ravel Piano",
    "scarlatti_sonatas": "Scarlatti Sonatas",
    "schubert_dances": "Schubert Dances",
    "schubert_winterreise": "Schubert Winterreise",
    "schulhoff_suite_dansante_en_jazz": "Schulhoff Suite Dansante En Jazz",
    "schumann_kinderszenen": "R Schumann Kinderszenen",
    "schumann_liederkreis": "R Schumann Liederkreis",
    "sweelinck_keyboard": "Sweelinck Keyboard",
    "tchaikovsky_seasons": "Tchaikovsky Seasons",
    "wagner_overtures": "Wagner Overtures",
    "wf_bach_sonatas": "WF Bach Sonatas",
}

TRACES_SETTINGS = dict(marker_line_color="black")
TYPE_COLORS = dict(
    zip(
        ("Mm7", "M", "o7", "o", "mm7", "m", "%7", "MM7", "other"),
        colorlover.scales["9"]["qual"]["Paired"],
    )
)
X_AXIS = dict(gridcolor="lightgrey", zerolinecolor="grey")
Y_AXIS = dict()

COLUMN2SUNBURST_TITLE = dict(
    sd="bass degree",
    figbass="figured bass",
    interval="bass progression",
    following_figbass="subsequent figured bass",
)


class TailwindBaseColor(FriendlyEnum):
    SLATE = "SLATE"
    GRAY = "GRAY"
    ZINC = "ZINC"
    NEUTRAL = "NEUTRAL"
    STONE = "STONE"
    RED = "RED"
    ORANGE = "ORANGE"
    AMBER = "AMBER"
    YELLOW = "YELLOW"
    LIME = "LIME"
    GREEN = "GREEN"
    EMERALD = "EMERALD"
    TEAL = "TEAL"
    CYAN = "CYAN"
    SKY = "SKY"
    BLUE = "BLUE"
    INDIGO = "INDIGO"
    VIOLET = "VIOLET"
    PURPLE = "PURPLE"
    FUCHSIA = "FUCHSIA"
    PINK = "PINK"
    ROSE = "ROSE"


shade_: TypeAlias = Literal[50, 100, 200, 300, 400, 500, 600, 700, 800, 900, 950]


class TailwindColors:
    """Color palette: look for tailwindcss_v3.3.3(.png|.svg)"""

    @classmethod
    def get_color(cls, name: TailwindBaseColor | str, shade: Optional[shade_] = None):
        if shade is None:
            name_upper = name.upper()
            if hasattr(cls, name_upper):
                return getattr(cls, name_upper)
            raise ValueError(
                f"Shade has not been specified and name does not match any of the class members: {name_upper}"
            )
        tailwind_name = TailwindBaseColor(name)
        member = f"{tailwind_name.name}_{shade:03d}"
        return cls.get_color(member)

    @classmethod
    def iter_colors(
        cls,
        name: Optional[TailwindBaseColor | Iterable[TailwindBaseColor]] = None,
        shades: Optional[shade_ | Iterable[shade_]] = None,
        as_hsv: bool = False,
        names=True,
    ):
        if name is None:
            name_iterator = (name.name for name in TailwindBaseColor)
        else:
            if isinstance(name, str):
                name = [name]
            name_iterator = [TailwindBaseColor(name).name for name in name]
        if shades is None:
            shades = (50, 100, 200, 300, 400, 500, 600, 700, 800, 900, 950)
        elif isinstance(shades, int):
            shades = (shades,)
        for tailwind_name in name_iterator:
            for shade in shades:
                member = f"{tailwind_name}_{shade:03d}"
                result = cls.get_color(member)
                if as_hsv:
                    result = colorsys.rgb_to_hsv(*(round(c / 255.0, 1) for c in result))
                if names:
                    yield member, result
                else:
                    yield result


class TailwindColorsHex(TailwindColors):
    """
    Provides all colors from TailwindCSS as HTML strings.
    Copied from https://github.com/dostuffthatmatters/python-tailwind-colors/blob/
    3c1ac2359e3ae753875e06e68f5072586a0ae399/tailwind_colors/__init__.py

    Color palette: look for tailwindcss_v3.3.3(.png|.svg)

    ```python
    print(TAILWIND_COLORS.AMBER_600)
    # prints `#d97706`
    ```
    """

    @classmethod
    def get_color(
        cls, name: TailwindBaseColor | str, shade: Optional[shade_] = None
    ) -> str:
        return super().get_color(name, shade)

    @classmethod
    def iter_colors(
        cls,
        name: Optional[TailwindBaseColor | Iterable[TailwindBaseColor]] = None,
        shades: Optional[shade_ | Iterable[shade_]] = None,
        as_hsv: bool = False,
        names=True,
    ) -> Iterator[Tuple[str, str]] | Iterator[str]:
        return super().iter_colors(name, shades, as_hsv, names)

    SLATE_050: Literal["#f8fafc"] = "#f8fafc"
    SLATE_100: Literal["#f1f5f9"] = "#f1f5f9"
    SLATE_200: Literal["#e2e8f0"] = "#e2e8f0"
    SLATE_300: Literal["#cbd5e1"] = "#cbd5e1"
    SLATE_400: Literal["#94a3b8"] = "#94a3b8"
    SLATE_500: Literal["#64748b"] = "#64748b"
    SLATE_600: Literal["#475569"] = "#475569"
    SLATE_700: Literal["#334155"] = "#334155"
    SLATE_800: Literal["#1e293b"] = "#1e293b"
    SLATE_900: Literal["#0f172a"] = "#0f172a"
    SLATE_950: Literal["#020617"] = "#020617"

    GRAY_050: Literal["#f9fafb"] = "#f9fafb"
    GRAY_100: Literal["#f3f4f6"] = "#f3f4f6"
    GRAY_200: Literal["#e5e7eb"] = "#e5e7eb"
    GRAY_300: Literal["#d1d5db"] = "#d1d5db"
    GRAY_400: Literal["#9ca3af"] = "#9ca3af"
    GRAY_500: Literal["#6b7280"] = "#6b7280"
    GRAY_600: Literal["#4b5563"] = "#4b5563"
    GRAY_700: Literal["#374151"] = "#374151"
    GRAY_800: Literal["#1f2937"] = "#1f2937"
    GRAY_900: Literal["#111827"] = "#111827"
    GRAY_950: Literal["#030712"] = "#030712"

    ZINC_050: Literal["#fafafa"] = "#fafafa"
    ZINC_100: Literal["#f4f4f5"] = "#f4f4f5"
    ZINC_200: Literal["#e4e4e7"] = "#e4e4e7"
    ZINC_300: Literal["#d4d4d8"] = "#d4d4d8"
    ZINC_400: Literal["#a1a1aa"] = "#a1a1aa"
    ZINC_500: Literal["#71717a"] = "#71717a"
    ZINC_600: Literal["#52525b"] = "#52525b"
    ZINC_700: Literal["#3f3f46"] = "#3f3f46"
    ZINC_800: Literal["#27272a"] = "#27272a"
    ZINC_900: Literal["#18181b"] = "#18181b"
    ZINC_950: Literal["#09090b"] = "#09090b"

    NEUTRAL_050: Literal["#fafafa"] = "#fafafa"
    NEUTRAL_100: Literal["#f5f5f5"] = "#f5f5f5"
    NEUTRAL_200: Literal["#e5e5e5"] = "#e5e5e5"
    NEUTRAL_300: Literal["#d4d4d4"] = "#d4d4d4"
    NEUTRAL_400: Literal["#a3a3a3"] = "#a3a3a3"
    NEUTRAL_500: Literal["#737373"] = "#737373"
    NEUTRAL_600: Literal["#525252"] = "#525252"
    NEUTRAL_700: Literal["#404040"] = "#404040"
    NEUTRAL_800: Literal["#262626"] = "#262626"
    NEUTRAL_900: Literal["#171717"] = "#171717"
    NEUTRAL_950: Literal["#0a0a0a"] = "#0a0a0a"

    STONE_050: Literal["#fafaf9"] = "#fafaf9"
    STONE_100: Literal["#f5f5f4"] = "#f5f5f4"
    STONE_200: Literal["#e7e5e4"] = "#e7e5e4"
    STONE_300: Literal["#d6d3d1"] = "#d6d3d1"
    STONE_400: Literal["#a8a29e"] = "#a8a29e"
    STONE_500: Literal["#78716c"] = "#78716c"
    STONE_600: Literal["#57534e"] = "#57534e"
    STONE_700: Literal["#44403c"] = "#44403c"
    STONE_800: Literal["#292524"] = "#292524"
    STONE_900: Literal["#1c1917"] = "#1c1917"
    STONE_950: Literal["#0c0a09"] = "#0c0a09"

    RED_050: Literal["#fef2f2"] = "#fef2f2"
    RED_100: Literal["#fee2e2"] = "#fee2e2"
    RED_200: Literal["#fecaca"] = "#fecaca"
    RED_300: Literal["#fca5a5"] = "#fca5a5"
    RED_400: Literal["#f87171"] = "#f87171"
    RED_500: Literal["#ef4444"] = "#ef4444"
    RED_600: Literal["#dc2626"] = "#dc2626"
    RED_700: Literal["#b91c1c"] = "#b91c1c"
    RED_800: Literal["#991b1b"] = "#991b1b"
    RED_900: Literal["#7f1d1d"] = "#7f1d1d"
    RED_950: Literal["#450a0a"] = "#450a0a"

    ORANGE_050: Literal["#fff7ed"] = "#fff7ed"
    ORANGE_100: Literal["#ffedd5"] = "#ffedd5"
    ORANGE_200: Literal["#fed7aa"] = "#fed7aa"
    ORANGE_300: Literal["#fdba74"] = "#fdba74"
    ORANGE_400: Literal["#fb923c"] = "#fb923c"
    ORANGE_500: Literal["#f97316"] = "#f97316"
    ORANGE_600: Literal["#ea580c"] = "#ea580c"
    ORANGE_700: Literal["#c2410c"] = "#c2410c"
    ORANGE_800: Literal["#9a3412"] = "#9a3412"
    ORANGE_900: Literal["#7c2d12"] = "#7c2d12"
    ORANGE_950: Literal["#431407"] = "#431407"

    AMBER_050: Literal["#fffbeb"] = "#fffbeb"
    AMBER_100: Literal["#fef3c7"] = "#fef3c7"
    AMBER_200: Literal["#fde68a"] = "#fde68a"
    AMBER_300: Literal["#fcd34d"] = "#fcd34d"
    AMBER_400: Literal["#fbbf24"] = "#fbbf24"
    AMBER_500: Literal["#f59e0b"] = "#f59e0b"
    AMBER_600: Literal["#d97706"] = "#d97706"
    AMBER_700: Literal["#b45309"] = "#b45309"
    AMBER_800: Literal["#92400e"] = "#92400e"
    AMBER_900: Literal["#78350f"] = "#78350f"
    AMBER_950: Literal["#451a03"] = "#451a03"

    YELLOW_050: Literal["#fefce8"] = "#fefce8"
    YELLOW_100: Literal["#fef9c3"] = "#fef9c3"
    YELLOW_200: Literal["#fef08a"] = "#fef08a"
    YELLOW_300: Literal["#fde047"] = "#fde047"
    YELLOW_400: Literal["#facc15"] = "#facc15"
    YELLOW_500: Literal["#eab308"] = "#eab308"
    YELLOW_600: Literal["#ca8a04"] = "#ca8a04"
    YELLOW_700: Literal["#a16207"] = "#a16207"
    YELLOW_800: Literal["#854d0e"] = "#854d0e"
    YELLOW_900: Literal["#713f12"] = "#713f12"
    YELLOW_950: Literal["#422006"] = "#422006"

    LIME_050: Literal["#f7fee7"] = "#f7fee7"
    LIME_100: Literal["#ecfccb"] = "#ecfccb"
    LIME_200: Literal["#d9f99d"] = "#d9f99d"
    LIME_300: Literal["#bef264"] = "#bef264"
    LIME_400: Literal["#a3e635"] = "#a3e635"
    LIME_500: Literal["#84cc16"] = "#84cc16"
    LIME_600: Literal["#65a30d"] = "#65a30d"
    LIME_700: Literal["#4d7c0f"] = "#4d7c0f"
    LIME_800: Literal["#3f6212"] = "#3f6212"
    LIME_900: Literal["#365314"] = "#365314"
    LIME_950: Literal["#1a2e05"] = "#1a2e05"

    GREEN_050: Literal["#f0fdf4"] = "#f0fdf4"
    GREEN_100: Literal["#dcfce7"] = "#dcfce7"
    GREEN_200: Literal["#bbf7d0"] = "#bbf7d0"
    GREEN_300: Literal["#86efac"] = "#86efac"
    GREEN_400: Literal["#4ade80"] = "#4ade80"
    GREEN_500: Literal["#22c55e"] = "#22c55e"
    GREEN_600: Literal["#16a34a"] = "#16a34a"
    GREEN_700: Literal["#15803d"] = "#15803d"
    GREEN_800: Literal["#166534"] = "#166534"
    GREEN_900: Literal["#14532d"] = "#14532d"
    GREEN_950: Literal["#052e16"] = "#052e16"

    EMERALD_050: Literal["#ecfdf5"] = "#ecfdf5"
    EMERALD_100: Literal["#d1fae5"] = "#d1fae5"
    EMERALD_200: Literal["#a7f3d0"] = "#a7f3d0"
    EMERALD_300: Literal["#6ee7b7"] = "#6ee7b7"
    EMERALD_400: Literal["#34d399"] = "#34d399"
    EMERALD_500: Literal["#10b981"] = "#10b981"
    EMERALD_600: Literal["#059669"] = "#059669"
    EMERALD_700: Literal["#047857"] = "#047857"
    EMERALD_800: Literal["#065f46"] = "#065f46"
    EMERALD_900: Literal["#064e3b"] = "#064e3b"
    EMERALD_950: Literal["#022c22"] = "#022c22"

    TEAL_050: Literal["#f0fdfa"] = "#f0fdfa"
    TEAL_100: Literal["#ccfbf1"] = "#ccfbf1"
    TEAL_200: Literal["#99f6e4"] = "#99f6e4"
    TEAL_300: Literal["#5eead4"] = "#5eead4"
    TEAL_400: Literal["#2dd4bf"] = "#2dd4bf"
    TEAL_500: Literal["#14b8a6"] = "#14b8a6"
    TEAL_600: Literal["#0d9488"] = "#0d9488"
    TEAL_700: Literal["#0f766e"] = "#0f766e"
    TEAL_800: Literal["#115e59"] = "#115e59"
    TEAL_900: Literal["#134e4a"] = "#134e4a"
    TEAL_950: Literal["#042f2e"] = "#042f2e"

    CYAN_050: Literal["#ecfeff"] = "#ecfeff"
    CYAN_100: Literal["#cffafe"] = "#cffafe"
    CYAN_200: Literal["#a5f3fc"] = "#a5f3fc"
    CYAN_300: Literal["#67e8f9"] = "#67e8f9"
    CYAN_400: Literal["#22d3ee"] = "#22d3ee"
    CYAN_500: Literal["#06b6d4"] = "#06b6d4"
    CYAN_600: Literal["#0891b2"] = "#0891b2"
    CYAN_700: Literal["#0e7490"] = "#0e7490"
    CYAN_800: Literal["#155e75"] = "#155e75"
    CYAN_900: Literal["#164e63"] = "#164e63"
    CYAN_950: Literal["#083344"] = "#083344"

    SKY_050: Literal["#f0f9ff"] = "#f0f9ff"
    SKY_100: Literal["#e0f2fe"] = "#e0f2fe"
    SKY_200: Literal["#bae6fd"] = "#bae6fd"
    SKY_300: Literal["#7dd3fc"] = "#7dd3fc"
    SKY_400: Literal["#38bdf8"] = "#38bdf8"
    SKY_500: Literal["#0ea5e9"] = "#0ea5e9"
    SKY_600: Literal["#0284c7"] = "#0284c7"
    SKY_700: Literal["#0369a1"] = "#0369a1"
    SKY_800: Literal["#075985"] = "#075985"
    SKY_900: Literal["#0c4a6e"] = "#0c4a6e"
    SKY_950: Literal["#082f49"] = "#082f49"

    BLUE_050: Literal["#eff6ff"] = "#eff6ff"
    BLUE_100: Literal["#dbeafe"] = "#dbeafe"
    BLUE_200: Literal["#bfdbfe"] = "#bfdbfe"
    BLUE_300: Literal["#93c5fd"] = "#93c5fd"
    BLUE_400: Literal["#60a5fa"] = "#60a5fa"
    BLUE_500: Literal["#3b82f6"] = "#3b82f6"
    BLUE_600: Literal["#2563eb"] = "#2563eb"
    BLUE_700: Literal["#1d4ed8"] = "#1d4ed8"
    BLUE_800: Literal["#1e40af"] = "#1e40af"
    BLUE_900: Literal["#1e3a8a"] = "#1e3a8a"
    BLUE_950: Literal["#172554"] = "#172554"

    INDIGO_050: Literal["#eef2ff"] = "#eef2ff"
    INDIGO_100: Literal["#e0e7ff"] = "#e0e7ff"
    INDIGO_200: Literal["#c7d2fe"] = "#c7d2fe"
    INDIGO_300: Literal["#a5b4fc"] = "#a5b4fc"
    INDIGO_400: Literal["#818cf8"] = "#818cf8"
    INDIGO_500: Literal["#6366f1"] = "#6366f1"
    INDIGO_600: Literal["#4f46e5"] = "#4f46e5"
    INDIGO_700: Literal["#4338ca"] = "#4338ca"
    INDIGO_800: Literal["#3730a3"] = "#3730a3"
    INDIGO_900: Literal["#312e81"] = "#312e81"
    INDIGO_950: Literal["#1e1b4b"] = "#1e1b4b"

    VIOLET_050: Literal["#f5f3ff"] = "#f5f3ff"
    VIOLET_100: Literal["#ede9fe"] = "#ede9fe"
    VIOLET_200: Literal["#ddd6fe"] = "#ddd6fe"
    VIOLET_300: Literal["#c4b5fd"] = "#c4b5fd"
    VIOLET_400: Literal["#a78bfa"] = "#a78bfa"
    VIOLET_500: Literal["#8b5cf6"] = "#8b5cf6"
    VIOLET_600: Literal["#7c3aed"] = "#7c3aed"
    VIOLET_700: Literal["#6d28d9"] = "#6d28d9"
    VIOLET_800: Literal["#5b21b6"] = "#5b21b6"
    VIOLET_900: Literal["#4c1d95"] = "#4c1d95"
    VIOLET_950: Literal["#2e1065"] = "#2e1065"

    PURPLE_050: Literal["#faf5ff"] = "#faf5ff"
    PURPLE_100: Literal["#f3e8ff"] = "#f3e8ff"
    PURPLE_200: Literal["#e9d5ff"] = "#e9d5ff"
    PURPLE_300: Literal["#d8b4fe"] = "#d8b4fe"
    PURPLE_400: Literal["#c084fc"] = "#c084fc"
    PURPLE_500: Literal["#a855f7"] = "#a855f7"
    PURPLE_600: Literal["#9333ea"] = "#9333ea"
    PURPLE_700: Literal["#7e22ce"] = "#7e22ce"
    PURPLE_800: Literal["#6b21a8"] = "#6b21a8"
    PURPLE_900: Literal["#581c87"] = "#581c87"
    PURPLE_950: Literal["#3b0764"] = "#3b0764"

    FUCHSIA_050: Literal["#fdf4ff"] = "#fdf4ff"
    FUCHSIA_100: Literal["#fae8ff"] = "#fae8ff"
    FUCHSIA_200: Literal["#f5d0fe"] = "#f5d0fe"
    FUCHSIA_300: Literal["#f0abfc"] = "#f0abfc"
    FUCHSIA_400: Literal["#e879f9"] = "#e879f9"
    FUCHSIA_500: Literal["#d946ef"] = "#d946ef"
    FUCHSIA_600: Literal["#c026d3"] = "#c026d3"
    FUCHSIA_700: Literal["#a21caf"] = "#a21caf"
    FUCHSIA_800: Literal["#86198f"] = "#86198f"
    FUCHSIA_900: Literal["#701a75"] = "#701a75"
    FUCHSIA_950: Literal["#4a044e"] = "#4a044e"

    PINK_050: Literal["#fdf2f8"] = "#fdf2f8"
    PINK_100: Literal["#fce7f3"] = "#fce7f3"
    PINK_200: Literal["#fbcfe8"] = "#fbcfe8"
    PINK_300: Literal["#f9a8d4"] = "#f9a8d4"
    PINK_400: Literal["#f472b6"] = "#f472b6"
    PINK_500: Literal["#ec4899"] = "#ec4899"
    PINK_600: Literal["#db2777"] = "#db2777"
    PINK_700: Literal["#be185d"] = "#be185d"
    PINK_800: Literal["#9d174d"] = "#9d174d"
    PINK_900: Literal["#831843"] = "#831843"
    PINK_950: Literal["#500724"] = "#500724"

    ROSE_050: Literal["#fff1f2"] = "#fff1f2"
    ROSE_100: Literal["#ffe4e6"] = "#ffe4e6"
    ROSE_200: Literal["#fecdd3"] = "#fecdd3"
    ROSE_300: Literal["#fda4af"] = "#fda4af"
    ROSE_400: Literal["#fb7185"] = "#fb7185"
    ROSE_500: Literal["#f43f5e"] = "#f43f5e"
    ROSE_600: Literal["#e11d48"] = "#e11d48"
    ROSE_700: Literal["#be123c"] = "#be123c"
    ROSE_800: Literal["#9f1239"] = "#9f1239"
    ROSE_900: Literal["#881337"] = "#881337"
    ROSE_950: Literal["#4c0519"] = "#4c0519"


class TailwindColorsRgb(TailwindColors):
    """
    Provides all colors from TailwindCSS as RGB tuples.
    Copied from https://github.com/dostuffthatmatters/python-tailwind-colors/blob/
    3c1ac2359e3ae753875e06e68f5072586a0ae399/tailwind_colors/__init__.py

    Color palette: look for tailwindcss_v3.3.3(.png|.svg)

    ```python
    print(TAILWIND_COLORS_RGB.AMBER_600)
    # prints (217, 119, 6)
    ```
    """

    @classmethod
    def get_color(
        cls, name: TailwindBaseColor | str, shade: Optional[shade_] = None
    ) -> Tuple[int, int, int]:
        return super().get_color(name, shade)

    @classmethod
    def iter_colors(
        cls,
        name: Optional[TailwindBaseColor | Iterable[TailwindBaseColor]] = None,
        shades: Optional[shade_ | Iterable[shade_]] = None,
        as_hsv: bool = False,
        names=True,
    ) -> Iterator[Tuple[str, Tuple[int, int, int]]] | Iterator[Tuple[int, int, int]]:
        return super().iter_colors(name, shades, as_hsv, names)

    SLATE_050: tuple[Literal[248], Literal[250], Literal[252]] = (248, 250, 252)
    SLATE_100: tuple[Literal[241], Literal[245], Literal[249]] = (241, 245, 249)
    SLATE_200: tuple[Literal[226], Literal[232], Literal[240]] = (226, 232, 240)
    SLATE_300: tuple[Literal[203], Literal[213], Literal[225]] = (203, 213, 225)
    SLATE_400: tuple[Literal[148], Literal[163], Literal[184]] = (148, 163, 184)
    SLATE_500: tuple[Literal[100], Literal[116], Literal[139]] = (100, 116, 139)
    SLATE_600: tuple[Literal[71], Literal[85], Literal[105]] = (71, 85, 105)
    SLATE_700: tuple[Literal[51], Literal[65], Literal[85]] = (51, 65, 85)
    SLATE_800: tuple[Literal[30], Literal[41], Literal[59]] = (30, 41, 59)
    SLATE_900: tuple[Literal[15], Literal[23], Literal[42]] = (15, 23, 42)
    SLATE_950: tuple[Literal[2], Literal[6], Literal[23]] = (2, 6, 23)

    GRAY_050: tuple[Literal[249], Literal[250], Literal[251]] = (249, 250, 251)
    GRAY_100: tuple[Literal[243], Literal[244], Literal[246]] = (243, 244, 246)
    GRAY_200: tuple[Literal[229], Literal[231], Literal[235]] = (229, 231, 235)
    GRAY_300: tuple[Literal[209], Literal[213], Literal[219]] = (209, 213, 219)
    GRAY_400: tuple[Literal[156], Literal[163], Literal[175]] = (156, 163, 175)
    GRAY_500: tuple[Literal[107], Literal[114], Literal[128]] = (107, 114, 128)
    GRAY_600: tuple[Literal[75], Literal[85], Literal[99]] = (75, 85, 99)
    GRAY_700: tuple[Literal[55], Literal[65], Literal[81]] = (55, 65, 81)
    GRAY_800: tuple[Literal[31], Literal[41], Literal[55]] = (31, 41, 55)
    GRAY_900: tuple[Literal[17], Literal[24], Literal[39]] = (17, 24, 39)
    GRAY_950: tuple[Literal[3], Literal[7], Literal[18]] = (3, 7, 18)

    ZINC_050: tuple[Literal[250], Literal[250], Literal[250]] = (250, 250, 250)
    ZINC_100: tuple[Literal[244], Literal[244], Literal[245]] = (244, 244, 245)
    ZINC_200: tuple[Literal[228], Literal[228], Literal[231]] = (228, 228, 231)
    ZINC_300: tuple[Literal[212], Literal[212], Literal[216]] = (212, 212, 216)
    ZINC_400: tuple[Literal[161], Literal[161], Literal[170]] = (161, 161, 170)
    ZINC_500: tuple[Literal[113], Literal[113], Literal[122]] = (113, 113, 122)
    ZINC_600: tuple[Literal[82], Literal[82], Literal[91]] = (82, 82, 91)
    ZINC_700: tuple[Literal[63], Literal[63], Literal[70]] = (63, 63, 70)
    ZINC_800: tuple[Literal[39], Literal[39], Literal[42]] = (39, 39, 42)
    ZINC_900: tuple[Literal[24], Literal[24], Literal[27]] = (24, 24, 27)
    ZINC_950: tuple[Literal[9], Literal[9], Literal[11]] = (9, 9, 11)

    NEUTRAL_050: tuple[Literal[250], Literal[250], Literal[250]] = (250, 250, 250)
    NEUTRAL_100: tuple[Literal[245], Literal[245], Literal[245]] = (245, 245, 245)
    NEUTRAL_200: tuple[Literal[229], Literal[229], Literal[229]] = (229, 229, 229)
    NEUTRAL_300: tuple[Literal[212], Literal[212], Literal[212]] = (212, 212, 212)
    NEUTRAL_400: tuple[Literal[163], Literal[163], Literal[163]] = (163, 163, 163)
    NEUTRAL_500: tuple[Literal[115], Literal[115], Literal[115]] = (115, 115, 115)
    NEUTRAL_600: tuple[Literal[82], Literal[82], Literal[82]] = (82, 82, 82)
    NEUTRAL_700: tuple[Literal[64], Literal[64], Literal[64]] = (64, 64, 64)
    NEUTRAL_800: tuple[Literal[38], Literal[38], Literal[38]] = (38, 38, 38)
    NEUTRAL_900: tuple[Literal[23], Literal[23], Literal[23]] = (23, 23, 23)
    NEUTRAL_950: tuple[Literal[10], Literal[10], Literal[10]] = (10, 10, 10)

    STONE_050: tuple[Literal[250], Literal[250], Literal[249]] = (250, 250, 249)
    STONE_100: tuple[Literal[245], Literal[245], Literal[244]] = (245, 245, 244)
    STONE_200: tuple[Literal[231], Literal[229], Literal[228]] = (231, 229, 228)
    STONE_300: tuple[Literal[214], Literal[211], Literal[209]] = (214, 211, 209)
    STONE_400: tuple[Literal[168], Literal[162], Literal[158]] = (168, 162, 158)
    STONE_500: tuple[Literal[120], Literal[113], Literal[108]] = (120, 113, 108)
    STONE_600: tuple[Literal[87], Literal[83], Literal[78]] = (87, 83, 78)
    STONE_700: tuple[Literal[68], Literal[64], Literal[60]] = (68, 64, 60)
    STONE_800: tuple[Literal[41], Literal[37], Literal[36]] = (41, 37, 36)
    STONE_900: tuple[Literal[28], Literal[25], Literal[23]] = (28, 25, 23)
    STONE_950: tuple[Literal[12], Literal[10], Literal[9]] = (12, 10, 9)

    RED_050: tuple[Literal[254], Literal[242], Literal[242]] = (254, 242, 242)
    RED_100: tuple[Literal[254], Literal[226], Literal[226]] = (254, 226, 226)
    RED_200: tuple[Literal[254], Literal[202], Literal[202]] = (254, 202, 202)
    RED_300: tuple[Literal[252], Literal[165], Literal[165]] = (252, 165, 165)
    RED_400: tuple[Literal[248], Literal[113], Literal[113]] = (248, 113, 113)
    RED_500: tuple[Literal[239], Literal[68], Literal[68]] = (239, 68, 68)
    RED_600: tuple[Literal[220], Literal[38], Literal[38]] = (220, 38, 38)
    RED_700: tuple[Literal[185], Literal[28], Literal[28]] = (185, 28, 28)
    RED_800: tuple[Literal[153], Literal[27], Literal[27]] = (153, 27, 27)
    RED_900: tuple[Literal[127], Literal[29], Literal[29]] = (127, 29, 29)
    RED_950: tuple[Literal[69], Literal[10], Literal[10]] = (69, 10, 10)

    ORANGE_050: tuple[Literal[255], Literal[247], Literal[237]] = (255, 247, 237)
    ORANGE_100: tuple[Literal[255], Literal[237], Literal[213]] = (255, 237, 213)
    ORANGE_200: tuple[Literal[254], Literal[215], Literal[170]] = (254, 215, 170)
    ORANGE_300: tuple[Literal[253], Literal[186], Literal[116]] = (253, 186, 116)
    ORANGE_400: tuple[Literal[251], Literal[146], Literal[60]] = (251, 146, 60)
    ORANGE_500: tuple[Literal[249], Literal[115], Literal[22]] = (249, 115, 22)
    ORANGE_600: tuple[Literal[234], Literal[88], Literal[12]] = (234, 88, 12)
    ORANGE_700: tuple[Literal[194], Literal[65], Literal[12]] = (194, 65, 12)
    ORANGE_800: tuple[Literal[154], Literal[52], Literal[18]] = (154, 52, 18)
    ORANGE_900: tuple[Literal[124], Literal[45], Literal[18]] = (124, 45, 18)
    ORANGE_950: tuple[Literal[67], Literal[20], Literal[7]] = (67, 20, 7)

    AMBER_050: tuple[Literal[255], Literal[251], Literal[235]] = (255, 251, 235)
    AMBER_100: tuple[Literal[254], Literal[243], Literal[199]] = (254, 243, 199)
    AMBER_200: tuple[Literal[253], Literal[230], Literal[138]] = (253, 230, 138)
    AMBER_300: tuple[Literal[252], Literal[211], Literal[77]] = (252, 211, 77)
    AMBER_400: tuple[Literal[251], Literal[191], Literal[36]] = (251, 191, 36)
    AMBER_500: tuple[Literal[245], Literal[158], Literal[11]] = (245, 158, 11)
    AMBER_600: tuple[Literal[217], Literal[119], Literal[6]] = (217, 119, 6)
    AMBER_700: tuple[Literal[180], Literal[83], Literal[9]] = (180, 83, 9)
    AMBER_800: tuple[Literal[146], Literal[64], Literal[14]] = (146, 64, 14)
    AMBER_900: tuple[Literal[120], Literal[53], Literal[15]] = (120, 53, 15)
    AMBER_950: tuple[Literal[69], Literal[26], Literal[3]] = (69, 26, 3)

    YELLOW_050: tuple[Literal[254], Literal[252], Literal[232]] = (254, 252, 232)
    YELLOW_100: tuple[Literal[254], Literal[249], Literal[195]] = (254, 249, 195)
    YELLOW_200: tuple[Literal[254], Literal[240], Literal[138]] = (254, 240, 138)
    YELLOW_300: tuple[Literal[253], Literal[224], Literal[71]] = (253, 224, 71)
    YELLOW_400: tuple[Literal[250], Literal[204], Literal[21]] = (250, 204, 21)
    YELLOW_500: tuple[Literal[234], Literal[179], Literal[8]] = (234, 179, 8)
    YELLOW_600: tuple[Literal[202], Literal[138], Literal[4]] = (202, 138, 4)
    YELLOW_700: tuple[Literal[161], Literal[98], Literal[7]] = (161, 98, 7)
    YELLOW_800: tuple[Literal[133], Literal[77], Literal[14]] = (133, 77, 14)
    YELLOW_900: tuple[Literal[113], Literal[63], Literal[18]] = (113, 63, 18)
    YELLOW_950: tuple[Literal[66], Literal[32], Literal[6]] = (66, 32, 6)

    LIME_050: tuple[Literal[247], Literal[254], Literal[231]] = (247, 254, 231)
    LIME_100: tuple[Literal[236], Literal[252], Literal[203]] = (236, 252, 203)
    LIME_200: tuple[Literal[217], Literal[249], Literal[157]] = (217, 249, 157)
    LIME_300: tuple[Literal[190], Literal[242], Literal[100]] = (190, 242, 100)
    LIME_400: tuple[Literal[163], Literal[230], Literal[53]] = (163, 230, 53)
    LIME_500: tuple[Literal[132], Literal[204], Literal[22]] = (132, 204, 22)
    LIME_600: tuple[Literal[101], Literal[163], Literal[13]] = (101, 163, 13)
    LIME_700: tuple[Literal[77], Literal[124], Literal[15]] = (77, 124, 15)
    LIME_800: tuple[Literal[63], Literal[98], Literal[18]] = (63, 98, 18)
    LIME_900: tuple[Literal[54], Literal[83], Literal[20]] = (54, 83, 20)
    LIME_950: tuple[Literal[26], Literal[46], Literal[5]] = (26, 46, 5)

    GREEN_050: tuple[Literal[240], Literal[253], Literal[244]] = (240, 253, 244)
    GREEN_100: tuple[Literal[220], Literal[252], Literal[231]] = (220, 252, 231)
    GREEN_200: tuple[Literal[187], Literal[247], Literal[208]] = (187, 247, 208)
    GREEN_300: tuple[Literal[134], Literal[239], Literal[172]] = (134, 239, 172)
    GREEN_400: tuple[Literal[74], Literal[222], Literal[128]] = (74, 222, 128)
    GREEN_500: tuple[Literal[34], Literal[197], Literal[94]] = (34, 197, 94)
    GREEN_600: tuple[Literal[22], Literal[163], Literal[74]] = (22, 163, 74)
    GREEN_700: tuple[Literal[21], Literal[128], Literal[61]] = (21, 128, 61)
    GREEN_800: tuple[Literal[22], Literal[101], Literal[52]] = (22, 101, 52)
    GREEN_900: tuple[Literal[20], Literal[83], Literal[45]] = (20, 83, 45)
    GREEN_950: tuple[Literal[5], Literal[46], Literal[22]] = (5, 46, 22)

    EMERALD_050: tuple[Literal[236], Literal[253], Literal[245]] = (236, 253, 245)
    EMERALD_100: tuple[Literal[209], Literal[250], Literal[229]] = (209, 250, 229)
    EMERALD_200: tuple[Literal[167], Literal[243], Literal[208]] = (167, 243, 208)
    EMERALD_300: tuple[Literal[110], Literal[231], Literal[183]] = (110, 231, 183)
    EMERALD_400: tuple[Literal[52], Literal[211], Literal[153]] = (52, 211, 153)
    EMERALD_500: tuple[Literal[16], Literal[185], Literal[129]] = (16, 185, 129)
    EMERALD_600: tuple[Literal[5], Literal[150], Literal[105]] = (5, 150, 105)
    EMERALD_700: tuple[Literal[4], Literal[120], Literal[87]] = (4, 120, 87)
    EMERALD_800: tuple[Literal[6], Literal[95], Literal[70]] = (6, 95, 70)
    EMERALD_900: tuple[Literal[6], Literal[78], Literal[59]] = (6, 78, 59)
    EMERALD_950: tuple[Literal[2], Literal[44], Literal[34]] = (2, 44, 34)

    TEAL_050: tuple[Literal[240], Literal[253], Literal[250]] = (240, 253, 250)
    TEAL_100: tuple[Literal[204], Literal[251], Literal[241]] = (204, 251, 241)
    TEAL_200: tuple[Literal[153], Literal[246], Literal[228]] = (153, 246, 228)
    TEAL_300: tuple[Literal[94], Literal[234], Literal[212]] = (94, 234, 212)
    TEAL_400: tuple[Literal[45], Literal[212], Literal[191]] = (45, 212, 191)
    TEAL_500: tuple[Literal[20], Literal[184], Literal[166]] = (20, 184, 166)
    TEAL_600: tuple[Literal[13], Literal[148], Literal[136]] = (13, 148, 136)
    TEAL_700: tuple[Literal[15], Literal[118], Literal[110]] = (15, 118, 110)
    TEAL_800: tuple[Literal[17], Literal[94], Literal[89]] = (17, 94, 89)
    TEAL_900: tuple[Literal[19], Literal[78], Literal[74]] = (19, 78, 74)
    TEAL_950: tuple[Literal[4], Literal[47], Literal[46]] = (4, 47, 46)

    CYAN_050: tuple[Literal[236], Literal[254], Literal[255]] = (236, 254, 255)
    CYAN_100: tuple[Literal[207], Literal[250], Literal[254]] = (207, 250, 254)
    CYAN_200: tuple[Literal[165], Literal[243], Literal[252]] = (165, 243, 252)
    CYAN_300: tuple[Literal[103], Literal[232], Literal[249]] = (103, 232, 249)
    CYAN_400: tuple[Literal[34], Literal[211], Literal[238]] = (34, 211, 238)
    CYAN_500: tuple[Literal[6], Literal[182], Literal[212]] = (6, 182, 212)
    CYAN_600: tuple[Literal[8], Literal[145], Literal[178]] = (8, 145, 178)
    CYAN_700: tuple[Literal[14], Literal[116], Literal[144]] = (14, 116, 144)
    CYAN_800: tuple[Literal[21], Literal[94], Literal[117]] = (21, 94, 117)
    CYAN_900: tuple[Literal[22], Literal[78], Literal[99]] = (22, 78, 99)
    CYAN_950: tuple[Literal[8], Literal[51], Literal[68]] = (8, 51, 68)

    SKY_050: tuple[Literal[240], Literal[249], Literal[255]] = (240, 249, 255)
    SKY_100: tuple[Literal[224], Literal[242], Literal[254]] = (224, 242, 254)
    SKY_200: tuple[Literal[186], Literal[230], Literal[253]] = (186, 230, 253)
    SKY_300: tuple[Literal[125], Literal[211], Literal[252]] = (125, 211, 252)
    SKY_400: tuple[Literal[56], Literal[189], Literal[248]] = (56, 189, 248)
    SKY_500: tuple[Literal[14], Literal[165], Literal[233]] = (14, 165, 233)
    SKY_600: tuple[Literal[2], Literal[132], Literal[199]] = (2, 132, 199)
    SKY_700: tuple[Literal[3], Literal[105], Literal[161]] = (3, 105, 161)
    SKY_800: tuple[Literal[7], Literal[89], Literal[133]] = (7, 89, 133)
    SKY_900: tuple[Literal[12], Literal[74], Literal[110]] = (12, 74, 110)
    SKY_950: tuple[Literal[8], Literal[47], Literal[73]] = (8, 47, 73)

    BLUE_050: tuple[Literal[239], Literal[246], Literal[255]] = (239, 246, 255)
    BLUE_100: tuple[Literal[219], Literal[234], Literal[254]] = (219, 234, 254)
    BLUE_200: tuple[Literal[191], Literal[219], Literal[254]] = (191, 219, 254)
    BLUE_300: tuple[Literal[147], Literal[197], Literal[253]] = (147, 197, 253)
    BLUE_400: tuple[Literal[96], Literal[165], Literal[250]] = (96, 165, 250)
    BLUE_500: tuple[Literal[59], Literal[130], Literal[246]] = (59, 130, 246)
    BLUE_600: tuple[Literal[37], Literal[99], Literal[235]] = (37, 99, 235)
    BLUE_700: tuple[Literal[29], Literal[78], Literal[216]] = (29, 78, 216)
    BLUE_800: tuple[Literal[30], Literal[64], Literal[175]] = (30, 64, 175)
    BLUE_900: tuple[Literal[30], Literal[58], Literal[138]] = (30, 58, 138)
    BLUE_950: tuple[Literal[23], Literal[37], Literal[84]] = (23, 37, 84)

    INDIGO_050: tuple[Literal[238], Literal[242], Literal[255]] = (238, 242, 255)
    INDIGO_100: tuple[Literal[224], Literal[231], Literal[255]] = (224, 231, 255)
    INDIGO_200: tuple[Literal[199], Literal[210], Literal[254]] = (199, 210, 254)
    INDIGO_300: tuple[Literal[165], Literal[180], Literal[252]] = (165, 180, 252)
    INDIGO_400: tuple[Literal[129], Literal[140], Literal[248]] = (129, 140, 248)
    INDIGO_500: tuple[Literal[99], Literal[102], Literal[241]] = (99, 102, 241)
    INDIGO_600: tuple[Literal[79], Literal[70], Literal[229]] = (79, 70, 229)
    INDIGO_700: tuple[Literal[67], Literal[56], Literal[202]] = (67, 56, 202)
    INDIGO_800: tuple[Literal[55], Literal[48], Literal[163]] = (55, 48, 163)
    INDIGO_900: tuple[Literal[49], Literal[46], Literal[129]] = (49, 46, 129)
    INDIGO_950: tuple[Literal[30], Literal[27], Literal[75]] = (30, 27, 75)

    VIOLET_050: tuple[Literal[245], Literal[243], Literal[255]] = (245, 243, 255)
    VIOLET_100: tuple[Literal[237], Literal[233], Literal[254]] = (237, 233, 254)
    VIOLET_200: tuple[Literal[221], Literal[214], Literal[254]] = (221, 214, 254)
    VIOLET_300: tuple[Literal[196], Literal[181], Literal[253]] = (196, 181, 253)
    VIOLET_400: tuple[Literal[167], Literal[139], Literal[250]] = (167, 139, 250)
    VIOLET_500: tuple[Literal[139], Literal[92], Literal[246]] = (139, 92, 246)
    VIOLET_600: tuple[Literal[124], Literal[58], Literal[237]] = (124, 58, 237)
    VIOLET_700: tuple[Literal[109], Literal[40], Literal[217]] = (109, 40, 217)
    VIOLET_800: tuple[Literal[91], Literal[33], Literal[182]] = (91, 33, 182)
    VIOLET_900: tuple[Literal[76], Literal[29], Literal[149]] = (76, 29, 149)
    VIOLET_950: tuple[Literal[46], Literal[16], Literal[101]] = (46, 16, 101)

    PURPLE_050: tuple[Literal[250], Literal[245], Literal[255]] = (250, 245, 255)
    PURPLE_100: tuple[Literal[243], Literal[232], Literal[255]] = (243, 232, 255)
    PURPLE_200: tuple[Literal[233], Literal[213], Literal[255]] = (233, 213, 255)
    PURPLE_300: tuple[Literal[216], Literal[180], Literal[254]] = (216, 180, 254)
    PURPLE_400: tuple[Literal[192], Literal[132], Literal[252]] = (192, 132, 252)
    PURPLE_500: tuple[Literal[168], Literal[85], Literal[247]] = (168, 85, 247)
    PURPLE_600: tuple[Literal[147], Literal[51], Literal[234]] = (147, 51, 234)
    PURPLE_700: tuple[Literal[126], Literal[34], Literal[206]] = (126, 34, 206)
    PURPLE_800: tuple[Literal[107], Literal[33], Literal[168]] = (107, 33, 168)
    PURPLE_900: tuple[Literal[88], Literal[28], Literal[135]] = (88, 28, 135)
    PURPLE_950: tuple[Literal[59], Literal[7], Literal[100]] = (59, 7, 100)

    FUCHSIA_050: tuple[Literal[253], Literal[244], Literal[255]] = (253, 244, 255)
    FUCHSIA_100: tuple[Literal[250], Literal[232], Literal[255]] = (250, 232, 255)
    FUCHSIA_200: tuple[Literal[245], Literal[208], Literal[254]] = (245, 208, 254)
    FUCHSIA_300: tuple[Literal[240], Literal[171], Literal[252]] = (240, 171, 252)
    FUCHSIA_400: tuple[Literal[232], Literal[121], Literal[249]] = (232, 121, 249)
    FUCHSIA_500: tuple[Literal[217], Literal[70], Literal[239]] = (217, 70, 239)
    FUCHSIA_600: tuple[Literal[192], Literal[38], Literal[211]] = (192, 38, 211)
    FUCHSIA_700: tuple[Literal[162], Literal[28], Literal[175]] = (162, 28, 175)
    FUCHSIA_800: tuple[Literal[134], Literal[25], Literal[143]] = (134, 25, 143)
    FUCHSIA_900: tuple[Literal[112], Literal[26], Literal[117]] = (112, 26, 117)
    FUCHSIA_950: tuple[Literal[74], Literal[4], Literal[78]] = (74, 4, 78)

    PINK_050: tuple[Literal[253], Literal[242], Literal[248]] = (253, 242, 248)
    PINK_100: tuple[Literal[252], Literal[231], Literal[243]] = (252, 231, 243)
    PINK_200: tuple[Literal[251], Literal[207], Literal[232]] = (251, 207, 232)
    PINK_300: tuple[Literal[249], Literal[168], Literal[212]] = (249, 168, 212)
    PINK_400: tuple[Literal[244], Literal[114], Literal[182]] = (244, 114, 182)
    PINK_500: tuple[Literal[236], Literal[72], Literal[153]] = (236, 72, 153)
    PINK_600: tuple[Literal[219], Literal[39], Literal[119]] = (219, 39, 119)
    PINK_700: tuple[Literal[190], Literal[24], Literal[93]] = (190, 24, 93)
    PINK_800: tuple[Literal[157], Literal[23], Literal[77]] = (157, 23, 77)
    PINK_900: tuple[Literal[131], Literal[24], Literal[67]] = (131, 24, 67)
    PINK_950: tuple[Literal[80], Literal[7], Literal[36]] = (80, 7, 36)

    ROSE_050: tuple[Literal[255], Literal[241], Literal[242]] = (255, 241, 242)
    ROSE_100: tuple[Literal[255], Literal[228], Literal[230]] = (255, 228, 230)
    ROSE_200: tuple[Literal[254], Literal[205], Literal[211]] = (254, 205, 211)
    ROSE_300: tuple[Literal[253], Literal[164], Literal[175]] = (253, 164, 175)
    ROSE_400: tuple[Literal[251], Literal[113], Literal[133]] = (251, 113, 133)
    ROSE_500: tuple[Literal[244], Literal[63], Literal[94]] = (244, 63, 94)
    ROSE_600: tuple[Literal[225], Literal[29], Literal[72]] = (225, 29, 72)
    ROSE_700: tuple[Literal[190], Literal[18], Literal[60]] = (190, 18, 60)
    ROSE_800: tuple[Literal[159], Literal[18], Literal[57]] = (159, 18, 57)
    ROSE_900: tuple[Literal[136], Literal[19], Literal[55]] = (136, 19, 55)
    ROSE_950: tuple[Literal[76], Literal[5], Literal[25]] = (76, 5, 25)


SHARPWISE_COLORS = [
    "RED",  # localkey + 1 fifths
    "ROSE",  # + 2
    "ORANGE",  # + 3 etc.
    "PINK",
    "AMBER",
    "FUCHSIA",
    "YELLOW",
    "SLATE",
    "STONE",
    "NEUTRAL",
    "ZINC",
    "GRAY",
]
FLATWISE_COLORS = [
    "LIME",  # localkey - 1 fifths
    "GREEN",  # - 2
    "BLUE",  # - 3 etc.
    "CYAN",
    "EMERALD",
    "INDIGO",
    "TEAL",
    "VIOLET",
    "SLATE",
    "STONE",
    "NEUTRAL",
    "ZINC",
    "GRAY",
]

MAJOR_MINOR_COLORS = dict(
    major="#1d4ed8",  # BLUE_700
    minor="#b91c1c",  # RED_700
)


def get_fifths_color(
    fifths: int,
    minor: bool = False,
    error_color=("ZINC", 950),
):
    if pd.isnull(fifths):
        primary_color = error_color
    elif fifths == 0:
        if minor:
            primary_color = ("PURPLE", 700)
        else:
            primary_color = ("SKY", 500)
    else:
        try:
            color_index = abs(fifths) - 1
            if fifths > 0:
                color = SHARPWISE_COLORS[color_index]
            else:
                color = FLATWISE_COLORS[color_index]
            primary_color = (color, 600)
        except TypeError:
            primary_color = error_color
    color_code = TailwindColorsHex.get_color(*primary_color)
    return color_code, primary_color


def add_mode_column(df: pd.DataFrame) -> pd.DataFrame:
    """Returns a copy of a DataFrame (which needs to have 'localkey_is_minor' boolean col) and adds a 'mode' column
    containing 'major' and 'minor'.
    """
    assert (
        "localkey_is_minor" in df.columns
    ), "df must have a 'localkey_is_minor' column"
    mode_col = df.localkey_is_minor.map({True: "minor", False: "major"}).rename("mode")
    return pd.concat([df, mode_col], axis=1)


def realign_subplot_axes(
    fig: go.Figure, x_axes: bool | dict = False, y_axes: bool | dict = True
) -> None:
    """For a given plotly figure, allow all x-axes (column-wise) and/or y-axes (row-wise) to have
    their own ranges. The function operates in-place, modifying the figure without returning it.
    y-axis defaults to True for backwards compatibility

    Args:
        fig: The plotly figure to be modified.
        x_axes, y_axes:
            If True, the respective axes will be realigned.
            If a dictionary, they will additionally be updated with the specified settings.

    Examples:

        realign_subplot_axes(fig, y_axes=True)
        realign_subplot_axes(fig, x_axes=dict(showticklabels=True))
    """
    if not (x_axes or y_axes):
        return
    subplot_rows = fig._grid_ref  # a list of lists, indicative of the grid dimensions
    n_cols: int = len(subplot_rows[0])  # needed in either case
    if x_axes:
        x_settings = x_axes if isinstance(x_axes, dict) else {}
        for col in range(1, n_cols + 1):
            # set the layout.xaxis.matches property of all subplots in the same column to the
            # x-axis name of the first subplot in that column. 'x1' is accepted for 'x' (the very first).
            fig.update_xaxes(x_settings, col=col, matches=f"x{col}")
    if y_axes:
        y_settings = y_axes if isinstance(y_axes, dict) else None
        n_rows = len(subplot_rows)
        for row in range(1, n_rows + 1):
            # set the layout.yaxis.matches property of all subplots in the same row to the
            # y-axis name of the first subplot in that row. Y-axis names are numbered row-wise,
            # such that the first y-axis in the second row is 'y3' (if there are 2 columns).
            first_y = (row - 1) * n_cols + 1
            fig.update_yaxes(y_settings, row=row, matches=f"y{first_y}")


def count_subsequent_occurrences(
    S: pd.Series,
    interval: int | List[int],
    k_min: int = 1,
    include_zero: bool = True,
    df: bool = True,
):
    """Count subsequent occurrences of one or several numbers in a sequence.

    Parameters
    ----------
    S : pd.Series
    interval: int or list
    k_min : int
        Minimal sequence length to take into account, defaults to 1
    include_zero : bool
        By default, zero is always accepted as part of the sequence. Zeros never increase
        sequence length.
    df : bool
        Defaults to True, so the function returns a DataFrame with index segments and sequence lengths.
        Pass False to return a list of index segments only.
    """
    try:
        interval_list = [int(interval)]
        if include_zero:
            interval_list.append(0)
    except Exception:
        interval_list = interval
        if include_zero and 0 not in interval_list:
            interval_list.append(0)

    ix_chunks = pd.DataFrame(columns=["ixs", "n"]) if df else []
    current = []
    n = 0
    for ix, value in S.items():
        if not pd.isnull(value) and value in interval_list:
            current.append(ix)
            if value != 0:
                n += 1
        else:
            if not pd.isnull(value):
                current.append(ix)
            if n >= k_min:
                if df:
                    ix_chunks.loc[len(ix_chunks)] = (current, n)
                else:
                    ix_chunks.append((current, n))
            current = []
            n = 0
    return ix_chunks


def color_background(x, color="#ffffb3"):
    """Format DataFrame cells with given background color."""
    return np.where(x.notna().to_numpy(), f"background-color: {color};", None)


def corpus_mean_composition_years(
    df: pd.DataFrame,
    composed_start_column: str = "composed_start",
    composed_end_column: str = "composed_end",
    name: str = "mean_composition_year",
) -> pd.Series:
    """Expects a dataframe containing ``year_column`` and computes its means by grouping on the first index level
    ('corpus' by default).
    Returns the result as a series where the index contains corpus names and the values are mean composition years.
    """
    years = get_middle_composition_year(df, composed_start_column, composed_end_column)
    return years.groupby(level=0).mean().sort_values().rename(name)


def chronological_corpus_order(
    df: pd.DataFrame, year_column: str = "composed_end"
) -> List[str]:
    """Expects a dataframe containing ``year_column`` and corpus names in the first index level.
    Returns the corpus names in chronological order
    """
    mean_composition_years = corpus_mean_composition_years(
        df=df, composed_end_column=year_column
    )
    return mean_composition_years.index.to_list()


def cumulative_fraction(S, start_from_zero=False):
    """Accumulate the value counts of a Series so they can be plotted."""
    values_df = S.value_counts().to_frame("x").reset_index()
    total = values_df.x.sum()
    values_df["y"] = values_df.x.cumsum() / total
    if start_from_zero:
        return pd.concat(
            [pd.DataFrame({"chord": pd.NA, "x": 0, "y": 0.0}, index=[0]), values_df],
            ignore_index=True,
        )
    return values_df


def flatten_series_name(series: pd.Series) -> pd.Series:
    if not isinstance(series.name, tuple):
        return series
    new_name = ", ".join(series.name)
    return series.rename(new_name)


def frictionless_field2modin_dtype(name, _) -> Optional[str]:
    category_fields = [  # often recurring string values
        "act_dur",
        "corpus",
        "duration",
        "gracenote",
        "mc_offset",
        "mc_onset",
        "mn_onset",
        "name",
        "nominal_duration",
        "piece",
        "scalar",
        "timesig",
        "tremolo",
    ]
    string_fields = [  # mostly distinct string values
        "next",
        "quarterbeats",  # (mostly) unique fractions
    ]
    int_fields = [  # sparse integer columns (many NA values)
        "numbering_offset",
        "tied",
        "tpc",
        "volta",
    ]
    boolean_fields = [
        "dont_count",
        "globalkey_is_minor",
        "localkey_is_minor",
    ]
    # left for inference, no NA values:
    # chord_id: int
    # duration_qb: float
    # i: int
    # keysig: int
    # mc: int
    # midi: int
    # mn: int
    # octave: int
    # staff: int
    # tpc: int
    # voice: int
    if name in category_fields:
        return "category"
    if name in string_fields:
        return "string"
    if name in int_fields:
        return "Int64"
    if name in boolean_fields:
        return "boolean"
    # print(f"{name} ({dtype}): infer")


def frictionless_types2modin_types(schema):
    return {
        name: outcome
        for name, dtype in schema.items()
        if (outcome := frictionless_field2modin_dtype(name, dtype))
    }


@cache
def get_corpus_display_name(repo_name: str) -> str:
    """Looks up a repository name in the CORPUS_NAMES constant. If not present,
    the repo name is returned as title case.
    """
    name = CORPUS_NAMES.get(repo_name, "")
    if name == "":
        name = " ".join(s.title() for s in repo_name.split("_"))
    return name


def get_hull_coordinates(
    pca_coordinates: pd.DataFrame,
    cluster_labels: pd.Series | List[int] | npt.NDArray[int],
) -> Dict[int | str, pd.DataFrame]:
    """Groups the coordinates by cluster and computes the convex hull for each. Returns a
    {cluster_id -> hull_coordinates} dictionary.
    """
    cluster_hulls = {}
    for cluster, coordinates in pca_coordinates.groupby(cluster_labels):
        if len(coordinates) < 4:
            cluster_hulls[cluster] = coordinates
            continue
        hull = ConvexHull(points=coordinates)
        cluster_hulls[cluster] = coordinates.take(hull.vertices)
    return cluster_hulls


def get_lower_triangle_values(data: Union[pd.DataFrame, np.array], offset: int = 0):
    is_dataframe = isinstance(data, pd.DataFrame)
    if is_dataframe:
        matrix = data.values
    else:
        matrix = data
    i, j = np.tril_indices_from(matrix, offset)
    values = matrix[i, j]
    if not is_dataframe:
        return values
    try:
        level_0 = merge_index_levels(data.index[i])
        level_1 = merge_index_levels(data.columns[j])
        index = pd.MultiIndex.from_arrays([level_0, level_1])
    except Exception:
        print(data.index[i], data.columns[j])
    return pd.Series(values, index=index)


def get_modin_dtypes(path):
    descriptor_path = os.path.join(path, "all_subcorpora.datapackage.json")
    fl_package = fl.Package(descriptor_path)
    facet_schemas = {}
    for fl_resource in fl_package.resources:
        _, facet_name = fl_resource.name.split(".")
        facet_schemas[facet_name] = fl_resource.schema
    facet_schema_types = {
        facet_name: {field.name: field.type for field in fl_schema.fields}
        for facet_name, fl_schema in facet_schemas.items()
    }
    modin_dtypes = {
        facet_name: frictionless_types2modin_types(fl_types)
        for facet_name, fl_types in facet_schema_types.items()
    }
    return modin_dtypes


def get_repo_name(repo: Repo) -> str:
    """Gets the repo name from the origin's URL, or from the local path if there is None."""
    if isinstance(repo, str):
        repo = Repo(repo)
    if len(repo.remotes) == 0:
        return repo.git.rev_parse("--show-toplevel")
    remote = repo.remotes[0]
    return remote.url.split(".git")[0].split("/")[-1]


def graph_data2sankey(
    stage_nodes: Dict[str, Dict[str, int]],
    edge_weights: Dict[Tuple[int, int], int],
    color_map: Optional[Dict[str, str]] = None,
    **kwargs,
):
    """Create a Sankey diagram from the nodes of every stage and the edge weights between them.
    Color map lets you define a color per label, which is then automatically assigned to all nodes accordingly.
    """
    data = pd.DataFrame(
        [(u, v, w) for (u, v), w in edge_weights.items()],
        columns=["source", "target", "value"],
    )
    node2label = {
        node: label for nodes in stage_nodes.values() for label, node in nodes.items()
    }
    labels = [node2label[i] for i in range(len(node2label))]
    if color_map:
        color = [color_map[label] for label in labels]
        kwargs["color"] = color
    return make_sankey(data, labels, **kwargs)


def load_facets(
    path,
    suffix="",
):
    modin_types = get_modin_dtypes(path)
    facets = {}
    for file in os.listdir(path):
        facet_regex = "^all_subcorpora" + suffix + r"\.(.+)\.tsv$"
        facet_match = re.match(facet_regex, file)
        if not facet_match:
            continue
        facet_name = facet_match.group(1)
        facet_path = os.path.join(path, file)
        # if facet_name == "metadata":
        #     index_col = [0, 1]
        # else:
        #     index_col = [0, 1, 2]
        dtypes = modin_types[facet_name]
        facet_df = pd.read_csv(
            facet_path,
            sep="\t",
            # index_col=index_col,
            dtype=dtypes,
        )
        facets[facet_name] = facet_df
    return facets


def make_output_path(
    filename: str,
    extension=None,
    path=None,
    use_subfolders: bool = False,
) -> str:
    if extension:
        extension = "." + extension.lstrip(".")
    else:
        extension = DEFAULT_OUTPUT_FORMAT
    file = f"{filename}{extension}"
    if path:
        if not use_subfolders:
            return resolve_dir(os.path.join(path, file))
        directory = path
    else:
        directory = os.getcwd()
    if use_subfolders:
        if extension in (".tsv", ".zip"):
            directory = os.path.join(directory, "data")
        else:
            directory = os.path.join(directory, "figs")
    return os.path.join(directory, file)


def make_evenly_distributed_color_map(labels: Iterable[str]) -> List[str]:
    """Returns a list of HSV colour strings of the same length as the input list. Identical labels
    are assigned the same color. Unique labels are distributed evenly around the HUE circle to
    generate the colors."""
    unique_labels = set(labels)
    color_step = 100 / len(unique_labels)
    unique_colors = {
        label: f"hsv({round(i * color_step)}%,100%,100%)"
        for i, label in enumerate(unique_labels)
    }
    node_color = list(map(lambda lst: unique_colors[lst], labels))
    return node_color


def make_sankey(
    data: pd.DataFrame,
    labels: List[str],
    x: Optional[List[float]] = None,
    y: Optional[List[float]] = None,
    node_pos: Optional[Dict[int, Tuple[float, float]]] = None,
    margin={"l": 10, "r": 10, "b": 10, "t": 10},
    pad=20,
    node_color="auto",
    arrangement: Literal["snap", "perpendicular", "freeform", "fixed"] = "snap",
    **kwargs,
):
    """Create a Sankey diagram with Plotly. Labels, node_pos, x, y, and color have the same length, corresponding to the
    number of nodes. Source and target are expressed as indices of these lists. Only labels is required.

    As of March 2024, Plotly ignores coordinates entirely when only one of x or y is specified. Furthermore,
    there is a bug that ignores positions where x or y equals 0.

    Args:
        data:
            Dataframe with the columns "source", "target" and "value". Optionally, a "color" column
            can be added for colouring the bands.
        labels: List of node labels.
        x, y:
            List of x and y coordinates for the nodes. Needs to be aligned with labels. If node_pos is defined in
            addition, x and y override the respective coordinates in node_pos, if specified.
        node_pos: {node_id -> (x, y)} dictionary of coordinates. If None, the nodes are placed automatically.
        margin:
        pad:
        node_color:
            A list of colors. If "auto", the colors are chosen automatically based on an equal division of the
            hue circle.
        **kwargs: Layout options.

    Returns:

    """
    if node_color == "auto":
        node_color = make_evenly_distributed_color_map(labels)
    x_pos, y_pos = [], []
    if node_pos is not None:
        for node in range(len(node_pos)):
            x_coord, y_coord = node_pos[node]
            x_pos.append(x_coord)
            y_pos.append(y_coord)
    if x is not None:
        x_pos = x
    if y is not None:
        y_pos = y

    link_dict = dict(source=data.source, target=data.target, value=data.value)
    if "color" in data.columns:
        link_dict["color"] = data.color
    fig = go.Figure(
        go.Sankey(
            arrangement=arrangement,
            node=dict(
                pad=pad,
                # thickness = 20,
                # line = dict(color = "black", width = 0.5),
                label=labels,
                x=x_pos if x_pos else None,
                y=y_pos if y_pos else None,
                color=node_color,
            ),
            link=link_dict,
        ),
    )

    fig.update_layout(margin=margin, **kwargs)
    return fig


def make_sunburst(
    chords: pd.DataFrame,
    parent: str,
    filter_accidentals: bool = False,
    terminal_symbol: str = "⋉",
    inspect=False,
):
    """

    Args:
        chords: DataFrame containing columns "sd" and "sd_progression"
        parent: Label to be displayed in the middle.
        filter_accidentals:
            If set to True, scale degrees with accidentals (precisely: with a length > 1) are replaced by white space.
        inspect: Set to True to show a data sample instead of a sunburst plot.

    Returns:

    """
    in_scale = []
    sd2prog = defaultdict(Counter)
    for sd, sd_prog in chords[["sd", "sd_progression"]].itertuples(index=False):
        if not filter_accidentals or len(sd) == 1:
            in_scale.append(sd)
            sd2prog[sd].update(
                [terminal_symbol] if pd.isnull(sd_prog) else [str(sd_prog)]
            )
    label_counts = Counter(in_scale)
    labels, values = list(label_counts.keys()), list(label_counts.values())
    # labels, values = zip(*list((sd, label_counts[sd]) for sd in sorted(label_counts)))
    parents = [parent] * len(labels)
    labels = [parent] + labels
    parents = [""] + parents
    values = [len(chords)] + values
    # print(sd2prog)
    if inspect:
        print(len(labels), len(parents), len(values))
        for scad, prog_counts in sd2prog.items():
            for prog, cnt in prog_counts.most_common():
                labels.append(prog)
                parents.append(scad)
                values.append(cnt)
                if cnt < 3000:
                    break
                print(f"added {prog}, {scad}, {cnt}")
            break

    fig = go.Figure(
        go.Sunburst(labels=labels, parents=parents, values=values, branchvalues="total")
    )
    fig.update_layout(margin=dict(t=0, l=0, r=0, b=0))
    return fig


def merge_index_levels(index, join_str=True) -> pd.Index:
    if index.nlevels == 1:
        return index
    if join_str:
        series = merge_columns_into_one(index.to_frame(index=False), join_str=join_str)
        return pd.Index(series)
    return index.to_flat_index()


def plot_cum(
    S=None,
    cum=None,
    x_log: bool = True,
    markersize: int = 4,
    n_labels: int = 10,
    font_size: Optional[int] = None,
    left_range: Optional[Tuple[float, float]] = None,
    right_range: Optional[Tuple[float, float]] = None,
    percent=True,
    **kwargs,
):
    """Pass either a Series or cumulative_fraction(S).reset_index()"""
    if cum is None:
        cum = cumulative_fraction(S).reset_index()
        cum.index = cum.index + 1
    fig = make_subplots(
        specs=[
            [
                {
                    "secondary_y": True,
                }
            ]
        ]
    )
    ix = cum.index
    scatter_args = dict(
        x=ix,
        y=cum.x,
        name="Absolute count",
        marker=dict(size=markersize),
    )
    if n_labels > 0:
        text_labels, text_positions = [], []
        for i, chrd in enumerate(cum.chord):
            if i < n_labels:
                text_labels.append(chrd)
                if i % 2:
                    text_positions.append("top center")
                else:
                    text_positions.append("bottom center")
            else:
                text_labels.append("")
                text_positions.append("top center")
        scatter_args["text"] = text_labels
        scatter_args["textposition"] = text_positions
        scatter_args["mode"] = "markers+text"
    else:
        scatter_args["mode"] = "markers"
    fig.add_trace(
        go.Scatter(**scatter_args),
        secondary_y=False,
    )
    cum_frac = cum.y
    cum_frac_name = "Cumulative fraction"
    right_dtick = 0.1
    if percent:
        cum_frac *= 100
        cum_frac_name += " (%)"
        right_dtick *= 100
    fig.add_trace(
        go.Scatter(
            x=ix,
            y=cum_frac,
            name=cum_frac_name,
            mode="markers",
            marker=dict(size=markersize),
        ),
        secondary_y=True,
    )
    fig.update_xaxes(
        title_text="Rank of chord label", zeroline=False, gridcolor="lightgrey"
    )
    if x_log:
        ranks = np.log(len(ix)) / np.log(10)
        fig.update_xaxes(type="log", range=(-0.01 * ranks, 1.01 * ranks))
    else:
        ranks = len(ix)
        fig.update_xaxes(range=(-0.02 * ranks, 1.02 * ranks))
    left_y_axis = dict(
        title_text="Absolute label count",
        secondary_y=False,
        type="log",
        gridcolor="lightpink",
        zeroline=True,
        dtick=1,
    )
    right_y_axis = dict(
        title_text=cum_frac_name,
        secondary_y=True,
        gridcolor="lightgrey",
        zeroline=False,
        dtick=right_dtick,
    )
    if left_range is not None:
        left_y_axis["range"] = left_range
    if right_range is not None:
        right_y_axis["range"] = right_range
    layout_args = dict(
        kwargs, legend=dict(orientation="h", itemsizing="constant", x=-0.05)
    )
    if font_size is not None:
        layout_args["font"] = dict(size=font_size)
    fig.update_layout(**layout_args)
    fig.update_yaxes(**left_y_axis)
    fig.update_yaxes(**right_y_axis)
    return fig


def get_component_analysis_coordinates(
    component_analysis: (
        PCA | LinearDiscriminantAnalysis | NeighborhoodComponentsAnalysis
    ),
    data: pd.DataFrame,
    y: pd.Series = None,
    concat: bool = False,
) -> Tuple[
    pd.DataFrame, PCA | LinearDiscriminantAnalysis | NeighborhoodComponentsAnalysis
]:
    coordinates = component_analysis.fit_transform(data, y)
    # coordinates.index = data.index
    if concat:
        coordinates = pd.concat([data, coordinates], axis=1)
    return coordinates, component_analysis


def plot_component_analysis(
    coordinates,
    info="data",
    color=None,
    symbol=None,
    size=None,
    n_components: Optional[Literal[2, 3]] = None,
    height=800,
    **kwargs,
) -> Optional[go.Figure]:
    if n_components is None:
        n_components = min(3, len(coordinates.columns))
    coordinates_reset = coordinates.reset_index()
    concatenate_this = [coordinates_reset]
    # approach: assemble plotting data by appending columns with additional information ('concatenate_this')
    # all indices are reset but kept at first in case they contain additional information.
    # After concatenation, importantly, duplicate columns are removed
    hover_data = coordinates_reset.columns.to_list()
    if color is not None:
        if isinstance(color, pd.Series):
            concatenate_this.append(color.reset_index())
            color = color.name
        else:
            assert (
                color in coordinates_reset.columns
            ), f"{color!r} not a column: {coordinates_reset.columns}"
        hover_data.append(color)
    if symbol is not None:
        if isinstance(symbol, pd.Series):
            concatenate_this.append(symbol.reset_index())
            symbol = symbol.name
        else:
            assert (
                symbol in coordinates_reset.columns
            ), f"{symbol!r} not a column: {coordinates_reset.columns}"
        hover_data.append(symbol)

    if size is None:
        constant_size = 3
    elif isinstance(size, Number):
        constant_size = size
    else:
        constant_size = 0
        if isinstance(size, pd.Series):
            concatenate_this.append(size.reset_index())
            size = size.name
        else:
            assert (
                size in coordinates_reset.columns
            ), f"{size!r} not a column: {coordinates_reset.columns}"
        hover_data.append(size)
    if len(concatenate_this) > 1:
        scatter_data = pd.concat(concatenate_this, axis=1)
    else:
        scatter_data = coordinates_reset
    # remove duplicate column names
    scatter_data = scatter_data.loc[:, ~scatter_data.columns.duplicated()]
    title = kwargs.pop("title", None)
    if not title:
        title = f"{n_components} principal components of the {info}"
    plot_args = dict(
        symbol=symbol,
        hover_data=hover_data,
        title=title,
        height=height,
        group_cols=color,
        **kwargs,
    )
    columns = coordinates.columns
    for i, (arg, col) in enumerate(zip(("x_col", "y_col", "z_col"), columns)):
        if i == n_components:
            break
        plot_args[arg] = col
    if constant_size:
        plot_args["traces_settings"] = dict(marker=dict(size=constant_size))
    if n_components < 3:
        return make_scatter_plot(scatter_data, **plot_args)
    return make_scatter_3d_plot(scatter_data, **plot_args)


def plot_components(
    component_analysis: (
        PCA | LinearDiscriminantAnalysis | NeighborhoodComponentsAnalysis
    ),
    show_features=20,
):
    if hasattr(component_analysis, "components_"):
        components = component_analysis.components_
    # elif hasattr(component_analysis, "scalings_"):
    #     components = component_analysis.scalings_
    else:
        raise ValueError(
            f"{component_analysis.__class__.__name__} has no components_ attribute"
        )
    for i, component_name in enumerate(component_analysis.get_feature_names_out()):
        index = component_analysis.feature_names_in_
        component = pd.Series(
            components[i],
            index=index,
            name="coefficient",
        ).sort_values(ascending=False, key=abs)
        fig = px.bar(
            component.iloc[:show_features],
            labels=dict(index="feature", value="coefficient"),
            title=f"{show_features} most weighted features of {component_name}",
        )
        fig.show()


def plot_lda(
    data=None,
    y=None,
    shrinkage: Literal["auto"] | float = "auto",
    solver: Literal["svd", "lsqr", "eigen"] = "eigen",
    lda_coordinates=None,
    info="data",
    color=None,
    symbol=None,
    size=None,
    n_components: Literal[2, 3] = 3,
    height=800,
    **kwargs,
) -> Optional[go.Figure]:
    if data is None:
        assert lda_coordinates is not None, "Either data or coordinates must be given"
        n_coord = len(lda_coordinates.columns)
        assert (
            n_coord >= n_components
        ), f"{n_coord} coordinates insufficient for plotting {n_components} dimensions"
        if n_coord > n_components:
            lda_coordinates = lda_coordinates.iloc[:, :n_components]
    else:
        assert y is not None, "y must be given if an LDA is to be computed from data"
        lda_coordinates, lda = get_component_analysis_coordinates(
            LinearDiscriminantAnalysis(
                n_components=n_components,
                shrinkage=shrinkage,
                solver=solver,
            ),
            data,
            y=y,
        )
        print(
            f"Explained variance ratio: {lda.explained_variance_ratio_} "
            f"({lda.explained_variance_ratio_.sum():.1%})"
        )
    fig = plot_component_analysis(
        coordinates=lda_coordinates,
        info=info,
        color=color,
        symbol=symbol,
        size=size,
        n_components=n_components,
        height=height,
        **kwargs,
    )
    return fig
    # if data is None or show_features < 1:
    #     return fig
    # fig.show()
    # plot_components(lda, show_features=show_features)


def plot_nca(
    data=None,
    y=None,
    nca_coordinates=None,
    info="data",
    show_features=20,
    color=None,
    symbol=None,
    size=None,
    n_components: Literal[2, 3] = 3,
    height=800,
    **kwargs,
) -> Optional[go.Figure]:
    if data is None:
        assert nca_coordinates is not None, "Either data or coordinates must be given"
        n_coord = len(nca_coordinates.columns)
        assert (
            n_coord >= n_components
        ), f"{n_coord} coordinates insufficient for plotting {n_components} dimensions"
        if n_coord > n_components:
            nca_coordinates = nca_coordinates.iloc[:, :n_components]
    else:
        assert y is not None, "y must be given if an NCA is to be computed from data"
        nca_coordinates, nca = get_component_analysis_coordinates(
            NeighborhoodComponentsAnalysis(n_components=n_components), data, y=y
        )
    fig = plot_component_analysis(
        coordinates=nca_coordinates,
        info=info,
        color=color,
        symbol=symbol,
        size=size,
        n_components=n_components,
        height=height,
        **kwargs,
    )
    if data is None or show_features < 1:
        return fig
    fig.show()
    plot_components(nca, show_features=show_features)


def plot_pca(
    data=None,
    pca_coordinates=None,
    info="data",
    show_features=20,
    color=None,
    symbol=None,
    size=None,
    n_components: Literal[2, 3] = 3,
    height=800,
    **kwargs,
) -> Optional[go.Figure]:
    if data is None:
        assert pca_coordinates is not None, "Either data or coordinates must be given"
        n_coord = len(pca_coordinates.columns)
        assert (
            n_coord >= n_components
        ), f"{n_coord} coordinates insufficient for plotting {n_components} dimensions"
        if n_coord > n_components:
            pca_coordinates = pca_coordinates.iloc[:, :n_components]
    else:
        pca_coordinates, pca = get_component_analysis_coordinates(
            PCA(n_components), data
        )
        print(
            f"Explained variance ratio: {pca.explained_variance_ratio_} "
            f"({pca.explained_variance_ratio_.sum():.1%})"
        )
    fig = plot_component_analysis(
        coordinates=pca_coordinates,
        info=info,
        color=color,
        symbol=symbol,
        size=size,
        n_components=n_components,
        height=height,
        **kwargs,
    )
    if data is None or show_features < 1:
        return fig
    fig.show()
    plot_components(pca, show_features=show_features)


def plot_transition_heatmaps(
    full_grams_left: List[tuple],
    full_grams_right: Optional[List[tuple]] = None,
    frequencies=True,
    remove_repeated: bool = False,
    sort_scale_degrees: bool = False,
    **kwargs,
) -> MatplotlibFigure:
    left_transition_matrix = make_transition_matrix(
        full_grams_left,
        distinct_only=remove_repeated,
        normalize=frequencies,
        percent=True,
    )
    left_unigrams = pd.Series(Counter(sum(full_grams_left, [])))
    if sort_scale_degrees:
        left_unigrams = left_unigrams.sort_index(key=scale_degree_order)
    else:
        left_unigrams = left_unigrams.sort_values(ascending=False)
    if "∅" in left_unigrams.index:
        left_unigrams["∅"] = 0
    left_unigrams_norm = left_unigrams / left_unigrams.sum()
    ix_intersection = left_unigrams_norm.index.intersection(
        left_transition_matrix.index
    )
    col_intersection = left_unigrams_norm.index.intersection(
        left_transition_matrix.columns
    )
    left_transition_matrix = left_transition_matrix.loc[
        ix_intersection, col_intersection
    ]
    left_unigrams_norm = left_unigrams_norm.loc[ix_intersection]

    if full_grams_right is None:
        right_transition_matrix = None
        right_unigrams_norm = None
    else:
        right_transition_matrix = make_transition_matrix(
            full_grams_right,
            distinct_only=remove_repeated,
            normalize=frequencies,
            percent=True,
        )
        right_unigrams = pd.Series(Counter(sum(full_grams_right, [])))
        if sort_scale_degrees:
            right_unigrams = right_unigrams.sort_index(key=scale_degree_order)
        else:
            right_unigrams = right_unigrams.sort_values(ascending=False)
        if "∅" in right_unigrams.index:
            right_unigrams["∅"] = 0
        right_unigrams_norm = right_unigrams / right_unigrams.sum()
        ix_intersection = right_unigrams_norm.index.intersection(
            right_transition_matrix.index
        )
        col_intersection = right_unigrams_norm.index.intersection(
            right_transition_matrix.columns
        )
        right_transition_matrix = right_transition_matrix.loc[
            ix_intersection, col_intersection
        ]
        right_unigrams_norm = right_unigrams_norm.loc[ix_intersection]

    return make_transition_heatmap_plots(
        left_transition_matrix,
        left_unigrams_norm,
        right_transition_matrix,
        right_unigrams_norm,
        frequencies=frequencies,
        **kwargs,
    )


def prepare_sunburst_data(
    sliced_harmonies_table: pd.DataFrame,
    filter_accidentals: bool = False,
    terminal_symbol: str = "⋉",
) -> pd.DataFrame:
    """

    Args:
        sliced_harmonies_table: DataFrame containing the columns "sd", "sd_progression", "figbass",

    Returns:

    """
    if filter_accidentals:
        chord_data = sliced_harmonies_table[
            sliced_harmonies_table.sd.str.len() == 1
        ].copy()  # scale degrees without
    else:
        chord_data = sliced_harmonies_table.copy()
    # accidentals
    chord_data["interval"] = ms3.transform(
        chord_data.sd_progression, safe_interval, terminal_symbol=terminal_symbol
    ).fillna(terminal_symbol)
    chord_data.figbass.fillna("3", inplace=True)
    chord_data["following_figbass"] = (
        chord_data.groupby(
            level=[0, 1, 2],
        )
        .figbass.shift(-1)
        .fillna(terminal_symbol)
    )
    return chord_data


def prepare_tf_idf_data(
    long_format_data: pd.DataFrame,
    index: str | List[str],
    columns: str | List[str],
    smooth=1e-20,
) -> Tuple[pd.Series, pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    unigram_distribution = (
        long_format_data.groupby(columns).duration_qb.sum().sort_values(ascending=False)
    )
    absolute_frequency_matrix = long_format_data.pivot_table(
        index=index,
        columns=columns,
        values="duration_qb",
        aggfunc="sum",
    )
    tf = (
        absolute_frequency_matrix.fillna(0.0)
        .add(smooth)
        .div(absolute_frequency_matrix.sum(axis=1), axis=0)
    )  # term frequency
    (
        D,
        V,
    ) = absolute_frequency_matrix.shape  # D = number of documents, V = vocabulary size
    df = (
        absolute_frequency_matrix.notna().sum().sort_values(ascending=False)
    )  # absolute document frequency
    f = absolute_frequency_matrix.fillna(0.0)
    idf = pd.Series(np.log(D / df), index=df.index)  # inverse document frequency
    return unigram_distribution, f, tf, df, idf


def prettify_counts(counter_object: Counter):
    N = counter_object.total()
    print(f"N = {N}")
    df = pd.DataFrame(
        counter_object.most_common(), columns=["progression", "count"]
    ).set_index("progression")
    df["%"] = (df["count"] * 100 / N).round(2)
    return df


def print_heading(heading: str, underline: chr = "-") -> None:
    """Underlines the given heading and prints it."""
    print(f"{heading}\n{underline * len(heading)}\n")


def remove_non_chord_labels(
    df,
    remove_erroneous_chords: bool = True,
):
    print(f"Length before: {len(df.index)}")
    non_chord = df.chord.isna()
    print(f"There are {non_chord.sum()} non-chord labels which we are going to delete:")
    display(df.loc[non_chord, "label"].value_counts())
    if remove_erroneous_chords:
        erroneous_chord = df.root.isna() & ~non_chord
        if erroneous_chord.sum() > 0:
            print(
                f"There are {erroneous_chord.sum()} labels with erroneous chord annotations which we are going to "
                f"delete:"
            )
            display(df.loc[erroneous_chord, "label"].value_counts())
            non_chord |= erroneous_chord
    result = df.drop(df.index[non_chord])
    print(f"Length after: {len(result.index)}")
    return result


def remove_none_labels(df):
    print(f"Length before: {len(df.index)}")
    is_none = (df.chord == "@none").fillna(False)
    print(f"There are {is_none.sum()} @none labels which we are going to delete.")
    result = df.drop(df.index[is_none])
    print(f"Length after: {len(result.index)}")
    return result


def resolve_dir(directory: str):
    return os.path.realpath(os.path.expanduser(directory))


def rectangular_sunburst(
    sliced_harmonies_table: pd.DataFrame,
    path,
    height=1500,
    title="Sunburst",
    terminal_symbol: str = "⋉",
) -> go.Figure:
    chord_data = prepare_sunburst_data(
        sliced_harmonies_table, terminal_symbol=terminal_symbol
    )
    title = f"{title} ({' - '.join(COLUMN2SUNBURST_TITLE[col] for col in path)})"
    fig = px.sunburst(
        chord_data,
        path=path,
        height=height,
        title=title,
    )
    return fig


def scale_degree_order(
    scale_degree: str | Iterable[str],
) -> Tuple[int, int] | List[Tuple[int, int]]:
    """Can be used as key function for sorting scale degrees."""
    if not isinstance(scale_degree, str):
        return list(map(scale_degree_order, scale_degree))
    if scale_degree == "∅":
        return (10,)
    match = re.match(r"([#b]*)([1-7])", scale_degree)
    accidental, degree = match.groups()
    return int(degree), accidental.count("#") - accidental.count("b")


def safe_interval(fifths, terminal_symbol="⋉"):
    if pd.isnull(fifths):
        return terminal_symbol
    return ms3.fifths2iv(fifths, smallest=True)


def sorted_gram_counts(lists_of_symbols, n=2, k=25):
    return prettify_counts(
        Counter(
            {
                t: count
                for t, count in sorted(
                    Counter(grams(lists_of_symbols, n=n, to_string=True)).items(),
                    key=lambda a: a[1],
                    reverse=True,
                )[:k]
            }
        )
    )


def value_count_df(
    S: pd.Series,
    name: Optional[str] = None,
    counts_column: str = "counts",
    round: Optional[int] = 2,
    rank_index: bool = False,
):
    """Value counts as DataFrame where the index has the name of the given Series or ``name`` and where the counts
    are given in the column ``counts``.
    """
    name = S.name if name is None else name
    vc = S.value_counts().rename(counts_column)
    normalized = 100 * vc / vc.sum()
    if round is not None:
        normalized = normalized.round(round)
    df = pd.concat([vc.to_frame(), normalized.rename("%")], axis=1)
    df.index.rename(name, inplace=True)
    if rank_index:
        df = df.reset_index()
        df.index += 1
        df.index.rename("rank", inplace=True)
    return df


def ix_segments2values(df, ix_segments, cols=["bass_degree", "chord"]):
    res = {col: [] for col in cols}
    for segment in ix_segments:
        col2list = get_cols(df, segment, cols)
        for col in cols:
            res[col].append(col2list[col])
    for col, list_of_lists in res.items():
        res[col] = [" ".join(val) for val in list_of_lists]
    return res


def get_cols(df, ix, cols):
    if isinstance(cols, str):
        cols = [cols]
    df = df.loc[ix]
    return {col: df[col].to_list() for col in cols}


def summarize(df):
    norepeat = (df.bass_note != df.bass_note.shift()).fillna(True)
    seconds_asc = count_subsequent_occurrences(df.bass_interval_pc, [1, 2])
    seconds_asc_vals = ix_segments2values(df, seconds_asc.ixs)
    seconds_desc = count_subsequent_occurrences(df.bass_interval_pc, [-1, -2])
    seconds_desc_vals = ix_segments2values(df, seconds_desc.ixs)
    both = count_subsequent_occurrences(df.bass_interval_pc, [1, 2, -1, -2])
    both_vals = ix_segments2values(df, both.ixs)
    n_stepwise = both.n.sum()
    length_norepeat = norepeat.sum()
    res = pd.Series(
        {
            "globalkey": df.globalkey.unique()[0],
            "localkey": df.localkey.unique()[0],
            "length": len(df),
            "length_norepeat": length_norepeat,
            "n_stepwise": n_stepwise,
            "%_stepwise": round(100 * n_stepwise / length_norepeat, 1),
            "n_ascending": seconds_asc.n.sum(),
            "n_descending": seconds_desc.n.sum(),
            "bd": " ".join(df.loc[norepeat, "bass_degree"].to_list()),
            "stepwise_bd": both_vals["bass_degree"],
            "stepwise_chords": both_vals["chord"],
            "ascending_bd": seconds_asc_vals[
                "bass_degree"
            ],  # ix_segments2list(df, seconds_asc.ixs),
            "ascending_chords": seconds_asc_vals["chord"],
            "descending_bd": seconds_desc_vals["bass_degree"],
            "descending_chords": seconds_desc_vals["chord"],
            "ixa": df.index[0],
            "ixb": df.index[-1],
        }
    )
    return res


def add_bass_degree_columns(feature_df):
    feature_df = extend_bass_notes_feature(feature_df)
    feature_df = add_chord_tone_intervals(feature_df)
    return feature_df


def make_key_region_summary_table(df, *groupby_args, **groupby_kwargs):
    """Takes an extended harmonies table that is segmented by local keys. The segments are iterated over using the
    *groupby_args and **groupby_kwargs arguments.
    """
    groupby_kwargs = dict(groupby_kwargs, group_keys=False)
    df = add_bass_degree_columns(df)
    # if "bass_interval" not in df.columns:
    #     bass_interval_column = df.groupby(
    #         *groupby_args, **groupby_kwargs
    #     ).bass_note.apply(lambda bd: bd.shift(-1) - bd)
    #     pc_interval_column = ms3.transform(bass_interval_column, ms3.fifths2pc)
    #     pc_interval_column = pc_interval_column.where(
    #         pc_interval_column <= 6, pc_interval_column % -6
    #     )
    #     if mutate_dataframe:
    #         df["bass_interval"] = bass_interval_column
    #         df["bass_interval_pc"] = pc_interval_column
    #     else:
    #         df = pd.concat(
    #             [
    #                 df,
    #                 bass_interval_column.rename("bass_interval"),
    #                 pc_interval_column.rename("bass_interval_pc"),
    #             ],
    #             axis=1,
    #         )
    return df.groupby(*groupby_args, **groupby_kwargs).apply(summarize)


def make_transition_heatmap_plots(
    left_transition_matrix: pd.DataFrame,
    left_unigrams: pd.Series,
    right_transition_matrix: Optional[pd.DataFrame] = None,
    right_unigrams: Optional[pd.Series] = None,
    top: int = 30,
    two_col_width=12,
    frequencies: bool = False,
    fontsize=8,
    labelsize=12,
    top_margin=0.99,
    bottom_margin=0.10,
    right_margin=0.005,
    left_margin=0.085,
) -> MatplotlibFigure:
    """
    Adapted from https://zenodo.org/records/2764889/files/reproduce_ABC.ipynb?download=1 which is the Jupyter notebook
    accompanying Moss FC, Neuwirth M, Harasim D, Rohrmeier M (2019) Statistical characteristics of tonal harmony: A
    corpus study of Beethoven’s string quartets. PLOS ONE 14(6): e0217242. https://doi.org/10.1371/journal.pone.0217242

    Args:
        left_unigrams:
        right_unigrams:
        left_transition_matrix:
        right_transition_matrix:
        top:
        two_col_width:
        frequencies: If set to True, the values of the unigram Series are interpreted as normalized frequencies and
            are multiplied with 100 for display on the y-axis.

    """
    # set custom context for this plot
    with plt.rc_context(
        {
            # disable spines for entropy bars
            "axes.spines.top": False,
            "axes.spines.left": False,
            "axes.spines.bottom": False,
            "axes.spines.right": False,
            "font.family": "sans-serif",
        }
    ):

        def make_gridspec(
            left,
            right,
        ):
            gridspec_ratio = [0.25, 2.0]
            hspace = None
            wspace = 0.0
            gs = gridspec.GridSpec(1, 2, width_ratios=gridspec_ratio)
            gs.update(
                left=left,
                right=right,
                wspace=wspace,
                hspace=hspace,
                bottom=bottom_margin,
                top=top_margin,
            )
            return gs

        def add_entropy_bars(
            unigrams,
            bigrams,
            axis,
        ):
            # settings for margins etc.
            barsize = [0.0, 0.7]
            s_min = pd.Series(
                (
                    bigrams.apply(lambda x: entropy(x, base=2), axis=1)
                    / np.log2(bigrams.shape[0])
                )[:top].values,
                index=[
                    i + f" ({str(round(fr * 100, 1))})" if frequencies else i
                    for i, fr in zip(bigrams.index, unigrams[:top].values)
                ],
            )
            ax = s_min.plot(kind="barh", ax=axis, color="k")

            # create a list to collect the plt.patches data
            totals_min = []

            # find the values and append to list
            for i in ax.patches:
                totals_min.append(round(i.get_width(), 2))

            for i, p in enumerate(ax.patches):
                axis.text(
                    totals_min[i] - 0.01,
                    p.get_y() + 0.3,
                    f"${totals_min[i]}$",
                    color="w",
                    fontsize=fontsize,
                    verticalalignment="center",
                    horizontalalignment="left",
                )
            axis.set_xlim(barsize)

            axis.invert_yaxis()
            axis.invert_xaxis()
            axis.set_xticklabels([])
            axis.tick_params(
                axis="both",  # changes apply to the x-axis
                which="both",  # both major and minor ticks are affected
                left=False,  # ticks along the bottom edge are off
                right=False,
                bottom=False,
                labelleft=True,
                labelsize=labelsize,
            )

        def add_heatmap(transition_value_matrix, axis, colormap):
            sns.heatmap(
                transition_value_matrix,
                annot=True,
                fmt=".1f",
                cmap=colormap,
                ax=axis,
                # vmin=vmin,
                # vmax=vmax,
                annot_kws={"fontsize": fontsize, "rotation": 60},
                cbar=False,
            )
            axis.set_yticks([])
            axis.tick_params(bottom=False)

        single_col_width = two_col_width / 2
        plot_two_sides = right_transition_matrix is not None
        if plot_two_sides:
            assert (
                right_unigrams is not None
            ), "right_unigrams must be provided if right_bigrams is provided"
            fig = plt.figure(figsize=(two_col_width, single_col_width))
            gs1 = make_gridspec(
                left=left_margin,
                right=0.5 - right_margin,
            )
        else:
            fig = plt.figure(figsize=(single_col_width, single_col_width))
            gs1 = make_gridspec(
                left=left_margin,
                right=1.0 - right_margin,
            )

        # LEFT-HAND SIDE

        ax1 = plt.subplot(gs1[0, 0])

        add_entropy_bars(
            left_unigrams,
            left_transition_matrix,
            ax1,
        )

        ax2 = plt.subplot(gs1[0, 1])

        add_heatmap(
            left_transition_matrix[left_transition_matrix > 0].iloc[
                :top, :top
            ],  # only display non-zero values
            axis=ax2,
            colormap="Blues",
        )

        # RIGHT-HAND SIDE

        plot_two_sides = right_transition_matrix is not None
        if plot_two_sides:
            assert (
                right_unigrams is not None
            ), "right_unigrams must be provided if right_bigrams is provided"

            gs2 = make_gridspec(
                left=0.5 + left_margin,
                right=1.0 - right_margin,
            )

            ax3 = plt.subplot(gs2[0, 0])
            add_entropy_bars(
                right_unigrams,
                right_transition_matrix,
                ax3,
            )

            ax4 = plt.subplot(gs2[0, 1])
            add_heatmap(
                right_transition_matrix[right_transition_matrix > 0].iloc[:top, :top],
                axis=ax4,
                colormap="Reds",
            )

        fig.align_labels()
    return fig


# region phrase stage helpers


def make_effective_numeral_criterion(phrase_annotations):
    """Currently not in use. This is a reduced version of make_effective_numeral_or_its_dominant_criterion but
    is not uses by it because it would not considerable reduce the code duplication.
    """
    numeral_type_effective_key = phrase_annotations.get_phrase_data(
        reverse=True,
        columns=[
            "numeral",
            "chord_type",
            "effective_localkey",
            "effective_localkey_is_minor",
        ],
        drop_levels="phrase_component",
    )
    return ms3.transform(
        numeral_type_effective_key,
        ms3.rel2abs_key,
        ["numeral", "effective_localkey", "effective_localkey_is_minor"],
    ).rename("effective_numeral")


def make_effective_numeral_or_its_dominant_criterion(phrase_annotations):
    numeral_type_effective_key = phrase_annotations.get_phrase_data(
        reverse=True,
        columns=[
            "numeral",
            "chord_type",
            "effective_localkey",
            "effective_localkey_is_minor",
        ],
        drop_levels="phrase_component",
    )
    dominant_selector = make_dominant_selector(numeral_type_effective_key)
    effective_numeral = ms3.transform(
        numeral_type_effective_key,
        ms3.rel2abs_key,
        ["numeral", "effective_localkey", "effective_localkey_is_minor"],
    ).rename("effective_numeral_or_its_dominant")
    return effective_numeral.where(
        ~dominant_selector,
        numeral_type_effective_key.effective_localkey,
    )


def _make_root_roman_or_its_dominants_criterion(
    phrase_data: resources.PhraseData,
    inspect_masks: bool = False,
) -> Tuple[pd.DataFrame, pd.Series, pd.Series]:
    # region prepare required chord features
    localkey_tonic_fifths = ms3.transform(
        phrase_data,
        ms3.roman_numeral2fifths,
        ["localkey_resolved", "globalkey_is_minor"],
    )
    globalkey_tpc = ms3.transform(phrase_data.globalkey, ms3.name2fifths)
    localkey_tonic_tpc = localkey_tonic_fifths.add(globalkey_tpc).rename(
        "localkey_tonic_tpc"
    )
    expected_root_tpc = (
        ms3.transform(
            phrase_data,
            ms3.roman_numeral2fifths,
            ["effective_localkey", "globalkey_is_minor"],
        )
        .add(globalkey_tpc)
        .rename("expected_root_tpc")
    )
    is_dominant = make_dominant_selector(phrase_data)
    expected_root_tpc = expected_root_tpc.where(is_dominant).astype("Int64")
    expected_numeral = phrase_data.relativeroot.fillna(
        phrase_data.effective_localkey_is_minor.map({True: "i", False: "I"})
    ).rename(
        "expected_numeral"
    )  # this is equivalent to the effective_localkey (which is relative to the global tonic),
    # but relative to the localkey
    effective_numeral = (
        ms3.transform(
            phrase_data,
            ms3.rel2abs_key,
            ["numeral", "effective_localkey_resolved", "globalkey_is_minor"],
        )
        .astype("string")
        .rename("effective_numeral")
    )
    root_tpc = (
        ms3.transform(
            pd.concat(
                [
                    effective_numeral,
                    phrase_data.globalkey_is_minor,
                ],
                axis=1,
            ),
            ms3.roman_numeral2fifths,
        )
        .add(globalkey_tpc)
        .astype("Int64")
        .rename("root_tpc")
    )
    subsequent_root_tpc = root_tpc.shift().rename("subsequent_root_tpc")
    # set ultima rows (first of phrase_id groups) to NA
    all_but_ultima_selector = ~make_group_start_mask(subsequent_root_tpc, "phrase_id")
    subsequent_root_tpc.where(all_but_ultima_selector, inplace=True)
    subsequent_root_roman = phrase_data.root_roman.shift().rename(
        "subsequent_root_roman"
    )
    subsequent_root_roman.where(all_but_ultima_selector, inplace=True)
    subsequent_numeral_is_minor = (
        effective_numeral.str.islower().shift().rename("subsequent_numeral_is_minor")
    )
    subsequent_numeral_is_minor.where(all_but_ultima_selector, inplace=True)
    # endregion prepare required chord features
    # region prepare masks
    # naming can be confusing: phrase data is expected to be reversed, i.e. the first row is a phrase's ultima chord
    # hence, when column names say "subsequent", the corresponding variable names say "previous" to avoid confusion
    # regarding the direction of the shift. In other words, .shift() yields previous values (values of preceding rows)
    # that correspond to subsequent chords
    merge_with_previous = (expected_root_tpc == subsequent_root_tpc).fillna(False)
    copy_decision_from_previous = effective_numeral.where(is_dominant)
    copy_decision_from_previous = copy_decision_from_previous.eq(
        copy_decision_from_previous.shift()
    ).fillna(False)
    copy_chain_decision_from_previous = expected_root_tpc.eq(
        expected_root_tpc.shift()
    ).fillna(
        False
    )  # has same expectation as previous dominant and will take on its value if the end of a dominant chain
    # is resolved; otherwise it keeps its own expected tonic as value
    dominant_grouper, _ = make_adjacency_groups(is_dominant, groupby="phrase_id")
    first_merge_index_in_group = {
        group: mask.values.argmax()
        for group, mask in merge_with_previous.groupby(dominant_grouper)
        if mask.any()
    }  # for each dominant group where at least one dominant resolves ('merge_with_previous' is True), the index of
    # the revelant row within the group, which serves as signal for a potential dominant chain starting with this index
    # to be fille with the expected resolution of its first member
    potential_dominant_chain_mask = (
        merge_with_previous | copy_chain_decision_from_previous
    )
    dominant_chains_groupby = potential_dominant_chain_mask.groupby(dominant_grouper)
    dominant_chain_fill_indices = []
    for (group, dominant_chain), index in zip(
        dominant_chains_groupby, dominant_chains_groupby.indices.values()
    ):
        fill_after = first_merge_index_in_group.get(group)
        if fill_after is None:
            continue
        fill_from = fill_after + 1
        for do_fill, ix in zip(dominant_chain[fill_from:], index[fill_from:]):
            # collect all indices following the first (which is already merged and will provide the root_numeral to be
            # propagated) which are either the same dominant (copy_chain_decision_from_previous) or the previous
            # dominant's dominant (merge_with_previous), but stop when the chain is broken, leaving unconnected
            # dominants alone with their own expected resolutions
            if not do_fill:
                break
            dominant_chain_fill_indices.append(ix)
    dominant_chain_fill_mask = np.zeros_like(potential_dominant_chain_mask, bool)
    dominant_chain_fill_mask[dominant_chain_fill_indices] = True
    # endregion prepare masks
    # region make criteria

    # without dominant chains
    # for this criterion, only those dominants that resolve as expected take on the value of their expected tonic, so
    # that, otherwise, they are available for merging with their own dominant
    root_dominant_criterion = expected_numeral.where(
        is_dominant & merge_with_previous, phrase_data.root_roman
    )
    root_dominant_criterion.where(
        ~merge_with_previous, subsequent_root_roman, inplace=True
    )
    root_dominant_criterion = (
        root_dominant_criterion.where(~copy_decision_from_previous)
        .ffill()
        .rename("root_roman_or_its_dominant")
    )

    # with dominant chains
    # for this criterion, all dominants
    root_dominants_criterion = expected_numeral.where(
        is_dominant & all_but_ultima_selector, phrase_data.root_roman
    )
    root_dominants_criterion.where(
        ~merge_with_previous, subsequent_root_roman, inplace=True
    )
    root_dominants_criterion = (
        root_dominants_criterion.where(~dominant_chain_fill_mask)
        .ffill()
        .rename("root_roman_or_its_dominants")
    )
    # endregion make criteria
    concatenate_this = [
        localkey_tonic_tpc,
        phrase_data,
        effective_numeral,
        expected_numeral,
        expected_root_tpc,
        root_tpc,
        subsequent_root_tpc,
        subsequent_root_roman,
        subsequent_numeral_is_minor,
    ]
    if inspect_masks:
        concatenate_this += [
            merge_with_previous.rename("merge_with_previous"),
            copy_decision_from_previous.rename("copy_decision_from_previous"),
            copy_chain_decision_from_previous.rename(
                "copy_chain_decision_from_previous"
            ),
            potential_dominant_chain_mask.rename("potential_dominant_chain_mask"),
            pd.Series(
                dominant_chain_fill_mask,
                index=phrase_data.index,
                name="dominant_chain_fill_mask",
            ),
        ]
    phrase_data_df = pd.concat(concatenate_this, axis=1)
    return phrase_data_df, root_dominant_criterion, root_dominants_criterion


def make_root_roman_or_its_dominants_criterion(
    phrase_annotations: resources.PhraseAnnotations,
    merge_dominant_chains: bool = True,
    query: Optional[str] = None,
    inspect_masks: bool = False,
):
    """For computing this criterion, dominants take on the numeral of their expected tonic chord except when they are
    part of a dominant chain that resolves as expected. In this case, the entire chain takes on the numeral of the
    last expected tonic chord. This results in all chords that are adjacent to their corresponding dominant or to a
    chain of dominants resolving into the respective chord are grouped into a stage. All other numeral groups form
    individual stages.
    """
    phrase_data = get_phrase_chord_tones(
        phrase_annotations,
        additional_columns=[
            "relativeroot",
            "localkey_resolved",
            "localkey_is_minor",
            "effective_localkey_resolved",
            "effective_localkey_is_minor",
            "timesig",
            "mn_onset",
            "numeral",
            "root_roman",
            "chord_type",
        ],
        query=query,
    )
    (
        phrase_data_df,
        root_dominant_criterion,
        root_dominants_criterion,
    ) = _make_root_roman_or_its_dominants_criterion(phrase_data, inspect_masks)
    if merge_dominant_chains:
        phrase_data_df = pd.concat([root_dominant_criterion, phrase_data_df], axis=1)
        regroup_by = root_dominants_criterion
    else:
        phrase_data_df = pd.concat([root_dominants_criterion, phrase_data_df], axis=1)
        regroup_by = root_dominant_criterion
    phrase_data = phrase_data.from_resource_and_dataframe(
        phrase_data,
        phrase_data_df,
    )
    return phrase_data.regroup_phrases(regroup_by)


def make_stage_data(
    phrase_feature,
    columns="chord",
    components="body",
    drop_levels=3,
    reverse=True,
    level_name="stage",
    wide_format=True,
    query=None,
) -> resources.PhraseData:
    """Function sets the defaults for the stage TSVs produced in the following."""
    phrase_data = phrase_feature.get_phrase_data(
        columns=columns,
        components=components,
        drop_levels=drop_levels,
        reverse=reverse,
        level_name=level_name,
        wide_format=wide_format,
        query=query,
    )
    return phrase_data


def get_max_range(widths) -> Tuple[int, int, int]:
    """Index range capturing the first until last occurrence of the maximum value."""
    maximum, first_ix, last_ix = 0, 0, 0
    for i, width in enumerate(widths):
        if width > maximum:
            maximum = width
            first_ix = i
            last_ix = i
        elif width == maximum:
            last_ix = i
    return first_ix, last_ix + 1, maximum


def merge_up_to_max_width(
    lowest_tpc: npt.NDArray, tpc_width: npt.NDArray, largest: int
) -> Tuple[npt.NDArray, npt.NDArray]:
    """Spans = lowest_tpc + tpc_width. Spans greater equal ``largest`` are left untouched. Smaller spans are merged as
    long as the merge does not result in a range larger than ``largest``.
    """
    lowest, highest = None, None
    merge_n = 0
    result_l, result_w = [], []

    def do_merge():
        """Add the readily merged section to the results, reset the counters."""
        nonlocal lowest, highest, merge_n
        if merge_n:
            result_l.extend([lowest] * merge_n)
            result_w.extend([highest - lowest] * merge_n)
            lowest, highest = None, None
            merge_n = 0

    for low, width in zip(lowest_tpc, tpc_width):
        if width > largest:
            do_merge()
            result_l.append(low)
            result_w.append(width)
            continue
        high = low + width
        if lowest is None:
            # start new merge range
            lowest = low
            highest = high
            merge_n += 1
            continue
        merge_low_point = min((low, lowest))
        merge_high_point = max((high, highest))
        merge_width = merge_high_point - merge_low_point
        if merge_width <= largest:
            # merge
            lowest = merge_low_point
            highest = merge_high_point
        else:
            do_merge()
            lowest = low
            highest = high
        merge_n += 1
    do_merge()
    return result_l, result_w


def _compute_smallest_fifth_ranges(
    lowest_tpc: npt.NDArray,
    tpc_width: npt.NDArray,
    smallest: int = 6,
    largest: int = 9,
    verbose: bool = False,
) -> Tuple[npt.NDArray, npt.NDArray]:
    """Recursively groups the given TPC "hull" into diatonic bands. Each entry of the two arrays represents a chord,
    in a way that lowest_tpc is the lowest tonal pitch class on the line of fifths, and tpc_width (by addition)
    represents the distance to the highest tonal pitch class on the line of fifths.

    Recursive mechanism:

    * Stop criterion: if ``max(tpc_width) ≤ smallest``, merge the whole hull into one band up to a
      range of ``largest``.
    * Otherwise split the hull in three parts: left, middle, right: Middle spans the left_most to the
      right-most occurrence of max(tpc_width). Process the middle part by leaving all spans ``≥ largest`` untouched
      and merging smaller spans as long as the merge does not result in a range larger than ``largest``.
    * Process left and right recursively.

    Args:
        lowest_tpc: Lowest tonal pitch class on the line of fifths for each chord in the sequence.
        tpc_width: For each chord, the span of tonal pitch classes on the line of fifths.
        smallest:
            Stop criterion: if ``max(tpc_width) <= smallest``, merge the whole hull into one band
            up to a range of ``largest``. Defaults to 6, which corresponds to 6 fifths, i.e., 7 tones of a diatonic.
        largest:
            Merge adjacent spans up to this range. Defaults to 9, which corresponds to 9 fifths, i.e.,
            10 tones of a major-minor extended diatonic.
        verbose:
            Print log messages.

    Returns:
        Hull representing merged spans of tonal pitch classes on the line of fifths.
    """
    if len(lowest_tpc) < 2:
        return lowest_tpc, tpc_width
    first_max_ix, last_max_ix, max_val = get_max_range(tpc_width)
    if verbose:
        print(f"max({tpc_width}) = {max_val}, [{first_max_ix}:{last_max_ix}]")
    if max_val <= smallest:
        if verbose:
            print(
                f"Calling merge_up_to_max_width({lowest_tpc}, {tpc_width}) because max_val {max_val} < {largest}"
            )
        return merge_up_to_max_width(lowest_tpc, tpc_width, largest=largest)
    left_l, left_w = _compute_smallest_fifth_ranges(
        lowest_tpc[:first_max_ix],
        tpc_width[:first_max_ix],
        smallest=smallest,
        largest=largest,
        verbose=verbose,
    )
    middle_l, middle_w = merge_up_to_max_width(
        lowest_tpc[first_max_ix:last_max_ix],
        tpc_width[first_max_ix:last_max_ix],
        largest=largest,
    )
    right_l, right_w = _compute_smallest_fifth_ranges(
        lowest_tpc[last_max_ix:],
        tpc_width[last_max_ix:],
        smallest=smallest,
        largest=largest,
        verbose=verbose,
    )
    result_l = np.concatenate([left_l, middle_l, right_l])
    result_w = np.concatenate([left_w, middle_w, right_w])
    return result_l, result_w


def compute_smallest_diatonics(
    phrase_data: resources.PhraseData,
    smallest: int = 6,
    largest: int = 9,
    verbose: bool = False,
) -> pd.DataFrame:
    """Recursively computes diatonic bands based on a lower and an upper bound.

    Args:
        phrase_data: PhraseData for a single phrase (requires the columns 'lowest_tpc' and 'tpc_width').
        smallest:
            Stop criterion: if ``max(tpc_width) <= smallest``, merge the whole hull into
            bands spanning ``≤ largest`` fifths. Defaults to 6, which corresponds to 6 fifths,
            i.e., 7 tones of a diatonic.
        largest:
            Merge adjacent spans up to this range. Defaults to 9, which corresponds to 9 fifths, i.e.,
            10 tones of a major-minor extended diatonic.
        verbose:
            Print log messages.

    Returns:
        A DataFrame with columns 'lowest_tpc' and 'tpc_width' representing the merged spans of tonal
        pitch classes for the given chord sequence.
    """
    lowest, widths = _compute_smallest_fifth_ranges(
        phrase_data.lowest_tpc.values,
        phrase_data.tpc_width.values,
        smallest=smallest,
        largest=largest,
        verbose=verbose,
    )
    return pd.DataFrame(
        dict(lowest_tpc=lowest, tpc_width=widths), index=phrase_data.index
    )


def make_criterion(
    phrase_feature: (
        resources.PhraseAnnotations
        | resources.PhraseComponents
        | resources.PhraseLabels
    ),
    criterion_name: Optional[str] = None,
    columns="chord",
    components="body",
    drop_levels=3,
    reverse=True,
    level_name="stage",
    query=None,
    join_str: Optional[str | bool] = None,
    fillna: Optional[Hashable] = None,
) -> pd.Series:
    """Convenience function for calling ``.get_phrase_data()`` with certain defaults and merging
    the resulting columns into one (when multiple).
    """
    phrase_data = phrase_feature.get_phrase_data(
        columns=columns,
        components=components,
        drop_levels=drop_levels,
        reverse=reverse,
        level_name=level_name,
        wide_format=False,
        query=query,
    )
    if not isinstance(columns, str) and len(columns) > 1:
        phrase_data = merge_columns_into_one(
            phrase_data, join_str=join_str, fillna=fillna
        )
        if criterion_name is None:
            criterion_name = "_and_".join(columns)
    else:
        phrase_data = phrase_data.iloc(axis=1)[0]
        if criterion_name is None:
            if isinstance(columns, str):
                criterion_name = columns
            else:
                criterion_name = columns[0]
    result = phrase_data.rename(criterion_name)
    return result


def make_criterion_stages(
    phrase_annotations: resources.PhraseAnnotations,
    criteria_dict: Dict[str, str | List[str]],
    join_str=True,
):
    """Takes a {name -> [columns]} dict."""
    uncompressed = make_stage_data(
        phrase_annotations,
        columns=["chord_and_mode", "duration_qb"],
        wide_format=False,
    )
    name2phrase_data = {"uncompressed": uncompressed}
    for name, columns in criteria_dict.items():
        criterion = make_criterion(
            phrase_annotations,
            columns=columns,
            criterion_name=name,
            join_str=join_str,
        )
        name2phrase_data[name] = uncompressed.regroup_phrases(criterion)
    return name2phrase_data


def get_stage_durations(phrase_data: resources.PhraseData):
    return phrase_data.groupby(
        ["corpus", "piece", "phrase_id", "stage"]
    ).duration_qb.sum()


def get_criterion_phrase_lengths(phrase_data: resources.PhraseData):
    """In terms of number of stages after merging."""
    stage_index = phrase_data.index.to_frame(index=False)
    phrase_id_col = stage_index.columns.get_loc("phrase_id")
    groupby = stage_index.columns.to_list()[: phrase_id_col + 1]
    stage_lengths = stage_index.groupby(groupby).stage.max() + 1
    return stage_lengths.rename("phrase_length")


def get_criterion_stage_entropies(
    phrase_data: resources.PhraseData, criterion_name: Optional[str] = None
):
    if not criterion_name:
        criterion_name = phrase_data.columns.to_list()[0]
    phrases = phrase_data[criterion_name].groupby(["phrase_id", "stage"]).first()
    return phrases.groupby("stage").apply(lambda S: entropy(S.value_counts(), base=2))


def get_metrics_means(name2phrase_data: Dict[str, resources.PhraseData]):
    criterion_metric2value = {}
    for name, stages in name2phrase_data.items():
        stage_durations = get_stage_durations(stages)
        criterion_metric2value[(name, "mean stage duration", "mean")] = (
            stage_durations.mean()
        )
        criterion_metric2value[(name, "mean stage duration", "sem")] = (
            stage_durations.sem()
        )
        phrase_lengths = get_criterion_phrase_lengths(stages)
        criterion_metric2value[(name, "mean phrase length", "mean")] = (
            phrase_lengths.mean()
        )
        criterion_metric2value[(name, "mean phrase length", "sem")] = (
            phrase_lengths.sem()
        )
        stage_entropies = get_criterion_stage_entropies(stages)
        criterion_metric2value[(name, "mean stage entropy", "mean")] = (
            stage_entropies.mean()
        )
        criterion_metric2value[(name, "mean stage entropy", "sem")] = (
            stage_entropies.sem()
        )
    metrics = pd.Series(criterion_metric2value, name="value").unstack(sort=False)
    metrics.index.names = ["criterion", "metric"]
    return metrics


def plot_corpuswise_criteria_means(
    criterion2values: Dict[str, pd.Series],
    category_title="stage_type",
    y_axis_label="mean duration of stages in ♩",
    chronological_corpus_names: Optional[List[str]] = None,
    **kwargs,
):
    """Takes a {trace_name -> values} dict where each entry will be turned into a bar plot trace for comparison."""
    aggregated = {
        name: durations.groupby("corpus").agg(["mean", "sem"])
        for name, durations in criterion2values.items()
    }
    df = pd.concat(aggregated, names=[category_title])
    corpora = df.index.get_level_values("corpus").unique()
    if chronological_corpus_names is not None:
        corpus_order = [
            corpus for corpus in chronological_corpus_names if corpus in corpora
        ]
    else:
        corpus_order = corpora
    return make_bar_plot(
        df,
        x_col="corpus",
        y_col="mean",
        error_y="sem",
        color=category_title,
        category_orders=dict(corpus=corpus_order),
        labels=dict(mean=y_axis_label, corpus=""),
        **kwargs,
    )


def plot_corpuswise_criteria(
    criterion2values,
    category_title="stage_type",
    y_axis_label="entropy of stage distributions in bits",
    chronological_corpus_names: Optional[List[str]] = None,
    **kwargs,
):
    """Takes a {trace_name -> PhraseData} dict where each entry will be turned into a bar plot trace for comparison."""
    df = pd.concat(criterion2values, names=[category_title])
    corpora = df.index.get_level_values("corpus").unique()
    if chronological_corpus_names is not None:
        corpus_order = [
            corpus for corpus in chronological_corpus_names if corpus in corpora
        ]
    else:
        corpus_order = corpora
    return make_bar_plot(
        df,
        x_col="corpus",
        y_col="entropy",
        color=category_title,
        category_orders=dict(corpus=corpus_order),
        labels=dict(entropy=y_axis_label, corpus=""),
        **kwargs,
    )


def _compare_criteria_stage_durations(
    name2phrase_data: Dict[str, resources.PhraseData],
    chronological_corpus_names: Optional[List[str]] = None,
):
    durations_dict = {
        name: get_stage_durations(stages) for name, stages in name2phrase_data.items()
    }
    return plot_corpuswise_criteria_means(
        durations_dict,
        chronological_corpus_names=chronological_corpus_names,
        height=800,
    )


def compare_criteria_stage_durations(
    phrase_annotations: resources.PhraseAnnotations,
    criteria_dict: Dict[str, str | List[str]],
    join_str=True,
    chronological_corpus_names: Optional[List[str]] = None,
):
    name2phrase_data = make_criterion_stages(
        phrase_annotations, criteria_dict, join_str=join_str
    )
    return _compare_criteria_stage_durations(
        name2phrase_data, chronological_corpus_names=chronological_corpus_names
    )


def _compare_criteria_phrase_lengths(
    name2phrase_data: Dict[str, resources.PhraseData],
    chronological_corpus_names: Optional[List[str]] = None,
):
    lengths_dict = {
        name: get_criterion_phrase_lengths(durations)
        for name, durations in name2phrase_data.items()
    }
    return plot_corpuswise_criteria_means(
        lengths_dict,
        y_axis_label="mean number of stages per phrase",
        height=800,
        chronological_corpus_names=chronological_corpus_names,
    )


def compare_criteria_phrase_lengths(
    phrase_annotations: resources.PhraseAnnotations,
    criteria_dict: Dict[str, str | List[str]],
    join_str=True,
    chronological_corpus_names: Optional[List[str]] = None,
):
    name2phrase_data = make_criterion_stages(
        phrase_annotations, criteria_dict, join_str=join_str
    )
    return _compare_criteria_phrase_lengths(
        name2phrase_data, chronological_corpus_names=chronological_corpus_names
    )


def _compare_criteria_entropies(
    name2phrase_data: Dict[str, resources.PhraseData],
    chronological_corpus_names: Optional[List[str]] = None,
):
    entropies = {
        name: get_criterion_stage_entropies(durations)
        for name, durations in name2phrase_data.items()
    }
    return plot_corpuswise_criteria(
        entropies, chronological_corpus_names=chronological_corpus_names, height=800
    )


def compare_criteria_entropies(
    phrase_annotations,
    criteria_dict,
    join_str=True,
    chronological_corpus_names: Optional[List[str]] = None,
):
    name2phrase_data = make_criterion_stages(
        phrase_annotations, criteria_dict, join_str=join_str
    )
    return _compare_criteria_entropies(
        name2phrase_data, chronological_corpus_names=chronological_corpus_names
    )


def make_dominant_selector(phrase_data):
    """Phrase data must have columns 'numeral', 'chord_type', 'effective_localkey_is_minor'"""
    is_dominant = phrase_data.numeral.eq("V") & phrase_data.chord_type.isin(
        {"Mm7", "M", "Fr"}
    )
    leading_tone_is_root = (
        phrase_data.numeral.eq("#vii") & phrase_data.effective_localkey_is_minor
    ) | (phrase_data.numeral.eq("vii") & ~phrase_data.effective_localkey_is_minor)
    is_rootless_dominant = leading_tone_is_root & phrase_data.chord_type.isin(
        {"o", "o7", "%7", "Ger", "It"}
    )
    dominant_selector = is_dominant | is_rootless_dominant
    return dominant_selector


def get_phrase_chord_tones(
    phrase_annotations: resources.PhraseAnnotations,
    additional_columns: Optional[Iterable[str]] = None,
    query: Optional[str] = None,
) -> resources.PhraseData:
    """"""
    columns = [
        "label",
        "duration_qb",
        "chord",
        "localkey",
        "effective_localkey",
        "globalkey",
        "globalkey_is_minor",
        "chord_tones",
    ]
    if additional_columns is not None:
        column_extension = [c for c in additional_columns if c not in columns]
        add_relative_chord_tones = "chord_tones" in column_extension
        columns.extend(column_extension)
    else:
        add_relative_chord_tones = False
    chord_tones = phrase_annotations.get_phrase_data(
        reverse=True, columns=columns, drop_levels="phrase_component", query=query
    )
    df = chord_tones.df
    df.chord_tones.where(df.chord_tones != (), inplace=True)
    df.chord_tones.ffill(inplace=True)
    df = ms3.transpose_chord_tones_by_localkey(df, by_global=True).rename(
        columns=dict(chord_tones="chord_tone_tpcs")
    )
    if add_relative_chord_tones:
        df = pd.concat([df, chord_tones.df.chord_tones], axis=1)
    df["lowest_tpc"] = df.chord_tone_tpcs.map(min)
    df["highest_tpc"] = df.chord_tone_tpcs.map(max)
    df["tpc_width"] = df.highest_tpc - df.lowest_tpc
    return chord_tones.from_resource_and_dataframe(chord_tones, df)


# endregion phrase stage helpers
# region phrase Gantt helpers
def make_start_finish(duration_qb: pd.Series) -> pd.DataFrame:
    """Turns a duration_qb column into a dataframe with a Start and Finish column for use in a Gantt chart.
    The timestamps are negative quarterbeats leading up to 0, which is the end of the phrase. The ultima, which has
    duration 0 because its duration is part of the codetta, is assigned a duration of 1 for plotting.
    """
    starts = (-duration_qb.cumsum()).rename("Start")  # .astype("datetime64[s]")
    ends = starts.shift().fillna(1).rename("Finish")  # .astype("datetime64[s]")
    return pd.DataFrame({"Start": starts, "Finish": ends})


def plot_phrase(
    phrase_timeline_data,
    colorscale=None,
    shapes: Optional[List[dict]] = None,
    layout: Optional[dict] = None,
    font_size: Optional[int] = None,  # for everything
    textfont_size: Optional[
        int
    ] = None,  # for traces, independently of axis labels, legends, etc.
    x_axis: Optional[dict] = None,
    y_axis: Optional[dict] = None,
    color_axis: Optional[dict] = None,
    traces_settings: Optional[dict] = None,
    title=None,
) -> go.Figure:
    """Timeline (Gantt) data for a single phrase."""
    dummy_resource_value = phrase_timeline_data.Resource.iat[0]
    phrase_timeline_data = fill_yaxis_gaps(
        phrase_timeline_data, "chord_tone_tpc", Resource=dummy_resource_value
    )
    if phrase_timeline_data.Task.isna().any():
        names = ms3.transform(phrase_timeline_data.chord_tone_tpc, ms3.fifths2name)
        phrase_timeline_data.Task.fillna(names, inplace=True)
    corpus, piece, phrase_id, *_ = phrase_timeline_data.index[0]
    globalkey = phrase_timeline_data.globalkey.iat[0]
    if title is None:
        title = f"Phrase {phrase_id} from {corpus}/{piece} ({globalkey})"
    kwargs = dict(title=title, colors=colorscale)
    if shapes:
        kwargs["shapes"] = shapes
    fig = create_gantt(
        phrase_timeline_data.sort_values("chord_tone_tpc", ascending=False), **kwargs
    )
    # fig.update_layout(hovermode="x", legend_traceorder="grouped")
    # fig.update_traces(hovertemplate="Task: %{text}<br>Start: %{x}<br>Finish: %{y}")
    if "timesig" in phrase_timeline_data.columns and "mn_onset" in phrase_timeline_data:
        timesigs = phrase_timeline_data.timesig.dropna().unique()
        if len(timesigs) == 1:
            timesig = timesigs[0]
            measure_duration = Fraction(timesig) * 4.0
            phrase_end_offset = -phrase_timeline_data.mn_onset.iat[0] * 4.0
            if x_axis is None:
                x_axis = dict(
                    dtick=measure_duration,
                    tick0=phrase_end_offset,
                )
            else:
                if "dtick" not in x_axis:
                    x_axis["dtick"] = measure_duration
                if "tick0" not in x_axis:
                    x_axis["tick0"] = phrase_end_offset
    update_figure_layout(
        fig,
        layout=layout,
        font_size=font_size,
        textfont_size=textfont_size,
        x_axis=x_axis,
        y_axis=y_axis,
        color_axis=color_axis,
        traces_settings=traces_settings,
    )
    return fig


def make_rectangle_shape(
    x0: Number,
    x1: Number,
    y0: Number,
    y1: Number,
    text: Optional[str] = None,
    textposition: str = "top left",
    layer: Literal["below", "above"] = "above",
    **kwargs,
) -> dict:
    result = dict(type="rect", x0=x0, x1=x1, y0=y0, y1=y1, layer=layer, **kwargs)
    if text:
        label = result.get("label", dict())
        if "text" not in label:
            label["text"] = text
        if "textposition" not in label:
            label["textposition"] = textposition
        result["label"] = label
    return result


# endregion phrase Gantt helpers
# region chord-tone profile helpers


def compare_corpus_frequencies(
    chord_slices: resources.DimcatResource,
    features: str | Iterable[str] | Dict[str, str | Iterable[str]],
    concatenation_axis=1,
):
    make_dict = isinstance(features, dict)
    if make_dict:
        doc_freqs = {}
    else:
        doc_freqs = []
        if isinstance(features, str):
            features = [features]
    for feature in features:
        if make_dict:
            key = feature
            feature = features[key]
        analyzer = prevalence.PrevalenceAnalyzer(index="corpus", columns=feature)
        matrix = analyzer.process(chord_slices)
        document_frequencies = (
            matrix.document_frequencies(name="corpus_frequency")
            .sort_values(ascending=False)
            .astype("Int64")
            .reset_index()
        )
        if make_dict:
            doc_freqs[key] = document_frequencies
        else:
            doc_freqs.append(document_frequencies)
    return pd.concat(doc_freqs, axis=concatenation_axis)


def make_chord_slices(
    sliced_notes: resources.Notes,
    slice_info: resources.HarmonyLabels,
):
    """Merge the harmony labels on the note events such that each note can be related to the respective label."""
    slice_info = slice_info.droplevel(-1)
    localkey_tpc = ms3.transform(
        slice_info[["localkey", "globalkey_is_minor"]], ms3.roman_numeral2fifths
    )
    concatenate_this = [
        # adds columns to harmony labels before joining on the notes
        slice_info,
        (
            ms3.transform(
                slice_info.globalkey,
                ms3.name2fifths,
            )
        ).rename("globalkey_tpc"),
        (
            relativeroot_tpc := ms3.transform(
                slice_info[["relativeroot_resolved", "localkey_is_minor"]],
                ms3.roman_numeral2fifths,
            ).fillna(0)
        ).rename("relativeroot_tpc"),
        (slice_info.root + localkey_tpc).rename("root_per_globalkey"),
        (slice_info.root - relativeroot_tpc).rename("root_per_tonicization"),
    ]
    slice_info = pd.concat(concatenate_this, axis=1)
    # do the join
    added_columns = [
        col for col in slice_info.columns if col not in sliced_notes.columns
    ]
    slice_info = join_df_on_index(
        slice_info[added_columns], sliced_notes.index, how="right"
    )
    # merge harmony labels and notes allowing for notes to be transposed to C
    chord_slices = pd.concat([sliced_notes, slice_info], axis=1)
    transposed_notes = transpose_notes_to_c(chord_slices)
    # add more columns expressing notes as varies types of fifths profiles
    concatenate_this = [
        chord_slices,
        transposed_notes,
        (chord_slices.tpc - chord_slices.globalkey_tpc).rename(
            "fifths_over_global_tonic"
        ),
        (
            transposed_notes.fifths_over_local_tonic - chord_slices.relativeroot_tpc
        ).rename("fifths_over_tonicization"),
        (transposed_notes.fifths_over_local_tonic - chord_slices.root).rename(
            "fifths_over_root"
        ),
    ]
    # return concatenate_this
    chord_slices = pd.concat(concatenate_this, axis=1)
    return chord_slices


def get_sliced_notes(
    D: Optional[Dataset] = None,
    basepath: Optional[str] = None,
    cache_name: Optional[str] = "chord_slices",
    recompute: bool = False,
):
    if D is None:
        package_path = resolve_dir(
            "~/distant_listening_corpus/distant_listening_corpus.datapackage.json"
        )
        D = Dataset.from_package(package_path)
    if basepath is None:
        basepath = resolve_dir(get_setting("default_basepath"))
    if cache_name and not recompute:
        cache_path = os.path.join(basepath, f"{cache_name}.resource.json")
        if os.path.isfile(cache_path):
            print(f"Loading {cache_path}")
            chord_slices = deserialize_json_file(cache_path)
            chord_slices.load()
            # work around for correct IntervalIndex deserialization
            converted = list(map(str2pd_interval, chord_slices.index.levels[2]))
            chord_slices._df.index = chord_slices._df.index.set_levels(
                converted, level=2
            )
            return chord_slices
    print("Computing chord slices...")
    label_slicer = slicers.HarmonyLabelSlicer()
    sliced_D = label_slicer.process(D)
    sliced_notes = sliced_D.get_feature(resources.Notes)
    chord_slices = make_chord_slices(sliced_notes, label_slicer.slice_metadata)
    chord_slices = resources.DimcatResource.from_dataframe(chord_slices, "chord_slices")
    if cache_name:
        chord_slices.store_resource(basepath=basepath, name=cache_name)
    return chord_slices


def make_chord_tone_profile(
    chord_slices: pd.DataFrame,
) -> pd.DataFrame:
    """Chord tone profiles in long format. Come with the absolute column 'duration_qb' and the
    relative column 'proportion', normalized per chord per corpus.
    """
    chord_tone_profiles = chord_slices.groupby(
        ["corpus", "chord_and_mode", "fifths_over_local_tonic"]
    ).duration_qb.sum()
    normalization = chord_tone_profiles.groupby(["corpus", "chord_and_mode"]).sum()
    chord_tone_profiles = pd.concat(
        [
            chord_tone_profiles,
            chord_tone_profiles.div(normalization).rename("proportion"),
        ],
        axis=1,
    )
    chord_tone_profiles.index = chord_tone_profiles.index.set_levels(
        chord_tone_profiles.index.levels[2].map(int), level=2
    )
    return chord_tone_profiles


def make_cosine_distances(
    tf,
    standardize=False,
    norm: Optional[Literal["l1", "l2", "max"]] = None,
    flat_index: bool = False,  # useful for plotting
):
    if standardize:
        scaler = StandardScaler()
        scaler.set_output(transform="pandas")
        tf = scaler.fit_transform(tf)
    if norm:
        scaler = Normalizer(norm=norm)
        scaler.set_output(transform="pandas")
        tf = scaler.fit_transform(tf)
    if flat_index:
        index = merge_index_levels(tf.index)
    else:
        index = tf.index
    distance_matrix = pd.DataFrame(cosine_distances(tf), index=index, columns=index)
    return distance_matrix


def sort_tpcs_by_piano_keys(
    tpcs: Iterable[int], ascending: bool = True, start: Optional[int] = None
) -> list[int]:
    """Sort tonal pitch classes by order on the piano.

    Args:
        tpcs: Tonal pitch classes to sort.
        ascending: Pass False to sort by descending order.
        start: Start on or above this TPC.
    """
    result = sorted(tpcs, key=lambda x: (ms3.fifths2pc(x), -x))
    if start is not None:
        pcs = ms3.fifths2pc(result)
        start = ms3.fifths2pc(start)
        i = 0
        while i < len(pcs) - 1 and pcs[i] < start:
            i += 1
        result = result[i:] + result[:i]
    return result if ascending else list(reversed(result))


def plot_chord_profiles(
    chord_profiles,
    chord_and_mode,
    xaxis_format: Optional[BassNotesFormat] = BassNotesFormat.SCALE_DEGREE,
    **kwargs,
):
    chord, mode = chord_and_mode.split(", ")
    minor = mode == "minor"
    chord_tones = ms3.chord2tpcs(chord, minor=minor)
    bass_note = chord_tones[0]
    profiles = chord_profiles.query(
        f"chord_and_mode == '{chord_and_mode}'"
    ).reset_index()
    tpc_order = sort_tpcs_by_piano_keys(
        profiles.fifths_over_local_tonic.unique(), start=bass_note
    )

    if xaxis_format is None or xaxis_format == BassNotesFormat.FIFTHS:
        x_col = "fifths_over_local_tonic"
        category_orders = None
    else:
        x_values = profiles.fifths_over_local_tonic
        format = BassNotesFormat(xaxis_format)
        if format == BassNotesFormat.SCALE_DEGREE:
            profiles["Scale degree"] = ms3.transform(
                x_values, ms3.fifths2sd, minor=minor
            )
            x_col = "Scale degree"
            category_orders = {"Scale degree": ms3.fifths2sd(tpc_order, minor=minor)}

    fig = make_bar_plot(
        profiles,
        x_col=x_col,
        y_col="proportion",
        color="corpus",
        title=f"Chord profiles of {chord_and_mode}",
        category_orders=category_orders,
        **kwargs,
    )
    return fig


def plot_document_frequency(
    chord_tones: resources.PrevalenceMatrix | pd.DataFrame,
    info: str = "vocabularies",
    **kwargs,
):
    if isinstance(chord_tones, pd.DataFrame):
        df = chord_tones
    else:
        df = chord_tones.document_frequencies()
    vocabulary = merge_columns_into_one(df.index.to_frame(index=False), join_str=True)
    doc_freq_data = pd.DataFrame(
        dict(
            chord_tones=vocabulary,
            document_frequency=df.values,
            rank=range(1, len(vocabulary) + 1),
        )
    )
    D, V = df.shape
    settings = dict(
        x_col="rank",
        y_col="document_frequency",
        hover_data="chord_tones",
        log_x=True,
        log_y=True,
        title=f"Document frequencies of {info} (D = {D}, V = {V})",
    )
    if kwargs:
        settings.update(kwargs)
    fig = make_scatter_plot(
        doc_freq_data,
        **settings,
    )
    return fig


def prepare_chord_tone_data(
    chord_slices: pd.DataFrame,
    groupby: str | List[str],
    chord_and_mode: Optional[str | Iterable[str]] = None,
    smooth=1e-20,
) -> Tuple[pd.Series, pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    if isinstance(groupby, str):
        groupby = [groupby]
    if chord_and_mode is None:
        return prepare_tf_idf_data(
            chord_slices,
            index=groupby,
            columns=["chord_and_mode", "fifths_over_local_tonic"],
            smooth=smooth,
        )
    if isinstance(chord_and_mode, str):
        absolute_data = chord_slices.query(f"chord_and_mode == '{chord_and_mode}'")
        return prepare_tf_idf_data(
            absolute_data,
            index=groupby,
            columns=["fifths_over_local_tonic"],
            smooth=smooth,
        )
    results = [
        prepare_chord_tone_data(
            chord_slices, groupby=groupby, chord_and_mode=cm, smooth=smooth
        )
        for cm in chord_and_mode
    ]
    concatenated_results = []
    for tup in zip(*results):
        concatenated_results.append(pd.concat(tup, axis=1, keys=chord_and_mode))
    return tuple(concatenated_results)


def prepare_numeral_chord_tone_data(
    chord_slices: pd.DataFrame,
    groupby: str | List[str],
    numeral: Optional[str | Iterable[str]] = None,
    smooth=1e-20,
) -> Tuple[pd.Series, pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    if isinstance(groupby, str):
        groupby = [groupby]
    if numeral is None:
        return prepare_tf_idf_data(
            chord_slices,
            index=groupby,
            columns=["numeral", "fifths_over_local_tonic"],
            smooth=smooth,
        )
    if isinstance(numeral, str):
        absolute_data = chord_slices.query(f"numeral == '{numeral}'")
        return prepare_tf_idf_data(
            absolute_data,
            index=groupby,
            columns=["numeral", "fifths_over_local_tonic"],
            smooth=smooth,
        )
    results = [
        prepare_numeral_chord_tone_data(
            chord_slices, groupby=groupby, numeral=cm, smooth=smooth
        )
        for cm in numeral
    ]
    concatenated_results = []
    for tup in zip(*results):
        concatenated_results.append(pd.concat(tup, axis=1, keys=numeral))
    return tuple(concatenated_results)


def replace_boolean_column_level_with_mode(
    matrix: resources.PrevalenceMatrix,
    level: int = 0,
    name: str = "mode",
):
    """Replaces True with 'minor' and False with 'major' in the given column index level and renames it.
    Function operates inplace.
    """
    old_columns = matrix._df.columns
    bool_values = old_columns.levels[level]
    mode_values = bool_values.map(
        {True: "minor", False: "major", "True": "minor", "False": "major"}
    )
    new_columns = old_columns.set_levels(mode_values, level=0)
    new_columns.set_names(name, level=level, inplace=True)
    matrix._df.columns = new_columns


def plot_cosine_distances(tf: pd.DataFrame, standardize=True):
    cos_distance_matrix = make_cosine_distances(tf, standardize=standardize)
    fig = go.Figure(
        data=go.Heatmap(
            z=cos_distance_matrix,
            x=cos_distance_matrix.columns,
            y=cos_distance_matrix.index,
            colorscale="Blues",
            colorbar=dict(title="Cosine distance"),
            zmax=1.0,
        ),
        layout=dict(
            title="Piece-wise cosine distances between chord-tone profiles",
            width=1000,
            height=1000,
        ),
    )
    return fig


# endregion chord-tone profile helpers


def get_dataset(
    corpus_name,
    target_dir=".",
    corpus_release="latest",
):
    url_release_component = (
        "releases/latest/download"
        if corpus_release == "latest"
        else f"releases/download/{corpus_release}"
    )

    def download_if_missing(filename, filepath):
        try:
            if not os.path.exists(filepath):
                url = f"https://github.com/DCMLab/{corpus_name}/{url_release_component}/{filename}"
                urlretrieve(url, filepath)
        except HTTPError as e:
            raise RuntimeError(
                f"Retrieving {corpus_name!r}@{corpus_release!r} from {url!r} failed: {e}"
            ) from e
        assert os.path.exists(
            filepath
        ), f"An error occured and {filepath} is not available."

    zip_name, json_name = f"{corpus_name}.zip", f"{corpus_name}.datapackage.json"
    zip_path, json_path = os.path.join(target_dir, zip_name), os.path.join(
        target_dir, json_name
    )
    download_if_missing(zip_name, zip_path)
    download_if_missing(json_name, json_path)
    return dc.Dataset.from_package(json_path)