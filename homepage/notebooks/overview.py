# ---
# jupyter:
#   jupytext:
#     formats: ipynb,md:myst,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.17.0
#   kernelspec:
#     display_name: corpus_docs
#     language: python
#     name: corpus_docs
# ---

# %% [markdown]
# # Overview
#
# This notebook gives a general overview of the features included in the dataset.

# %% mystnb={"code_prompt_hide": "Hide imports", "code_prompt_show": "Show imports"} tags=["hide-cell"]
# %load_ext autoreload
# %autoreload 2
import os

import dimcat as dc
import pandas as pd
import plotly.express as px
from dimcat import filters, plotting
from IPython.display import display

import utils

# %%
RESULTS_PATH = os.path.abspath(os.path.join(utils.OUTPUT_FOLDER, "overview"))
os.makedirs(RESULTS_PATH, exist_ok=True)


def make_output_path(
    filename: str,
    extension=None,
    path=RESULTS_PATH,
) -> str:
    return utils.make_output_path(filename=filename, extension=extension, path=path)


def save_figure_as(
    fig, filename, formats=("png", "pdf"), directory=RESULTS_PATH, **kwargs
):
    if formats is not None:
        for fmt in formats:
            plotting.write_image(fig, filename, directory, format=fmt, **kwargs)
    else:
        plotting.write_image(fig, filename, directory, **kwargs)


# %% [markdown]
# **Loading data**

# %%
D = utils.get_dataset("ABC", corpus_release="v2.6")
package = D.inputs.get_package()
package_info = package._package.custom
git_tag = package_info.get("git_tag")
utils.print_heading("Data and software versions")
print("The Annotated Beethoven Corpus (ABC) version v2.6")
print(f"Datapackage '{package.package_name}' @ {git_tag}")
print(f"dimcat version {dc.__version__}\n")
D

# %%
filtered_D = filters.HasHarmonyLabelsFilter(keep_values=[True]).process(D)
all_metadata = filtered_D.get_metadata()
assert len(all_metadata) > 0, "No pieces selected for analysis."
all_metadata

# %%
mean_composition_years = utils.corpus_mean_composition_years(all_metadata)
chronological_order = mean_composition_years.index.to_list()
corpus_colors = dict(zip(chronological_order, utils.CORPUS_COLOR_SCALE))
corpus_names = {
    corp: utils.get_corpus_display_name(corp) for corp in chronological_order
}
chronological_corpus_names = list(corpus_names.values())
corpus_name_colors = {
    corpus_names[corp]: color for corp, color in corpus_colors.items()
}

# %%
mean_composition_years

# %% [markdown]
# ## Composition dates
#
# This section relies on the dataset's metadata.

# %%
valid_composed_start = pd.to_numeric(all_metadata.composed_start, errors="coerce")
valid_composed_end = pd.to_numeric(all_metadata.composed_end, errors="coerce")
print(
    f"Composition dates range from {int(valid_composed_start.min())} {valid_composed_start.idxmin()} "
    f"to {int(valid_composed_end.max())} {valid_composed_end.idxmax()}."
)


# %% [markdown]
# ### Mean composition years per corpus


# %%
def make_summary(metadata_df):
    piece_is_annotated = metadata_df.label_count > 0
    return metadata_df[piece_is_annotated].copy()


# %% tags=["hide-input"]
summary = make_summary(all_metadata)
bar_data = pd.concat(
    [
        mean_composition_years.rename("year"),
        summary.groupby(level="corpus").size().rename("pieces"),
    ],
    axis=1,
).reset_index()

N = len(summary)
fig = px.bar(
    bar_data,
    x="year",
    y="pieces",
    color="corpus",
    color_discrete_map=corpus_colors,
    title=f"Temporal coverage of the {N} annotated pieces in the Distant Listening Corpus",
)
fig.update_traces(width=5)
fig.update_layout(**utils.STD_LAYOUT)
fig.update_traces(width=5)
save_figure_as(fig, "pieces_timeline_bars")
fig.show()

# %%
summary

# %% [markdown]
# ### Composition years histogram

# %% tags=["hide-input"]
hist_data = summary.reset_index()
hist_data.corpus = hist_data.corpus.map(corpus_names)
fig = px.histogram(
    hist_data,
    x="composed_end",
    color="corpus",
    labels=dict(
        composed_end="decade",
        count="pieces",
    ),
    color_discrete_map=corpus_name_colors,
    title=f"Temporal coverage of the {N} annotated pieces in the Distant Listening Corpus",
)
fig.update_traces(xbins=dict(size=10))
fig.update_layout(**utils.STD_LAYOUT)
fig.update_legends(font=dict(size=16))
save_figure_as(fig, "pieces_timeline_histogram", height=1250)
fig.show()


# %% [markdown]
# ## Dimensions
#
# ### Overview


# %%
def make_overview_table(groupby, group_name="pieces"):
    n_groups = groupby.size().rename(group_name)
    absolute_numbers = dict(
        measures=groupby.last_mn.sum(),
        length=groupby.length_qb.sum(),
        notes=groupby.n_onsets.sum(),
        labels=groupby.label_count.sum(),
    )
    absolute = pd.DataFrame.from_dict(absolute_numbers)
    absolute = pd.concat([n_groups, absolute], axis=1)
    sum_row = pd.DataFrame(absolute.sum(), columns=["sum"]).T
    absolute = pd.concat([absolute, sum_row])
    return absolute


absolute = make_overview_table(summary.groupby("workTitle"))
# print(absolute.astype(int).to_markdown())
absolute.astype(int)


# %%
def summarize_dataset(D):
    all_metadata = D.get_metadata()
    summary = make_summary(all_metadata)
    return make_overview_table(summary.groupby(level=0))


corpus_summary = summarize_dataset(D)
print(corpus_summary.astype(int).to_markdown())

# %% [markdown]
# ### Measures

# %%
all_measures = D.get_feature("measures")
print(
    f"{len(all_measures.index)} measures over {len(all_measures.groupby(level=[0,1]))} files."
)
all_measures.head()

# %%
all_measures.get_default_analysis().plot_grouped()

# %% [markdown]
# ### Harmony labels
#
# All symbols, independent of the local key (the mode of which changes their semantics).

# %%
try:
    all_annotations = D.get_feature("harmonylabels").df
except Exception:
    all_annotations = pd.DataFrame()
n_annotations = len(all_annotations.index)
includes_annotations = n_annotations > 0
if includes_annotations:
    display(all_annotations.head())
    print(f"Concatenated annotation tables contains {all_annotations.shape[0]} rows.")
    no_chord = all_annotations.root.isna()
    if no_chord.sum() > 0:
        print(
            f"{no_chord.sum()} of them are not chords. Their values are:"
            f" {all_annotations.label[no_chord].value_counts(dropna=False).to_dict()}"
        )
    all_chords = all_annotations[~no_chord].copy()
    print(
        f"Dataset contains {all_chords.shape[0]} tokens and {len(all_chords.chord.unique())} types over "
        f"{len(all_chords.groupby(level=[0,1]))} documents."
    )
    all_annotations["corpus_name"] = all_annotations.index.get_level_values(0).map(
        utils.get_corpus_display_name
    )
    all_chords["corpus_name"] = all_chords.index.get_level_values(0).map(
        utils.get_corpus_display_name
    )
else:
    print("Dataset contains no annotations.")