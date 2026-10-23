---
jupytext:
  formats: ipynb,md:myst,py:percent
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.17.0
kernelspec:
  display_name: corpus_docs
  language: python
  name: corpus_docs
---

# Annotations

```{code-cell} ipython3
---
mystnb:
  code_prompt_hide: Hide imports
  code_prompt_show: Show imports
tags: [hide-input]
---
%load_ext autoreload
%autoreload 2

import os

import dimcat as dc
import ms3
import plotly.express as px
from dimcat import groupers, plotting

import utils
```

```{code-cell} ipython3
---
editable: true
slideshow:
  slide_type: ''
tags: [hide-input]
---
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
```

**Loading data**

```{code-cell} ipython3
---
editable: true
slideshow:
  slide_type: ''
tags: [hide-input]
---
D = utils.get_dataset("ABC", corpus_release="v2.6")
package = D.inputs.get_package()
package_info = package._package.custom
git_tag = package_info.get("git_tag")
utils.print_heading("Data and software versions")
print("The Annotated Beethoven Corpus (ABC) version v2.6")
print(f"Datapackage '{package.package_name}' @ {git_tag}")
print(f"dimcat version {dc.__version__}\n")
D
```

```{code-cell} ipython3
---
editable: true
slideshow:
  slide_type: ''
tags: [hide-input]
---

```

```{code-cell} ipython3
---
editable: true
slideshow:
  slide_type: ''
---
filtered_D = D.apply_step("HasHarmonyLabelsFilter")
all_metadata = filtered_D.get_metadata()
```

```{code-cell} ipython3
assert len(all_metadata) > 0, "No pieces selected for analysis."
chronological_corpus_names = all_metadata.get_corpus_names()
```

## DCML harmony labels

```{code-cell} ipython3
:tags: [hide-input]

all_annotations = filtered_D.get_feature("DcmlAnnotations")
is_annotated_mask = all_metadata.label_count > 0
is_annotated_index = all_metadata.index[is_annotated_mask]
annotated_notes = filtered_D.get_feature("notes").subselect(is_annotated_index)
print(f"The annotated pieces have {len(annotated_notes)} notes.")
```

```{code-cell} ipython3
all_chords = filtered_D.get_feature("harmonylabels")
print(
    f"{len(all_annotations)} annotations, of which {len(all_chords)} are harmony labels."
)
```

## Harmony labels
### Unigrams
For computing unigram statistics, the tokens need to be grouped by their occurrence within a major or a minor key
because this changes their meaning. To that aim, the annotated corpus needs to be sliced into contiguous localkey
segments which are then grouped into a major (`is_minor=False`) and a minor group.

```{code-cell} ipython3
root_durations = (
    all_chords[all_chords.root.between(-5, 6)]
    .groupby(["root", "chord_type"])
    .duration_qb.sum()
)
# sort by stacked bar length:
# root_durations = root_durations.sort_values(key=lambda S: S.index.get_level_values(0).map(S.groupby(level=0).sum()),
# ascending=False)
bar_data = root_durations.reset_index()
bar_data.root = bar_data.root.map(ms3.fifths2iv)
fig = px.bar(
    bar_data,
    x="root",
    y="duration_qb",
    color="chord_type",
    title="Distribution of chord types over chord roots",
    labels=dict(
        root="Chord root expressed as interval above the local (or secondary) tonic",
        duration_qb="duration in quarter notes",
        chord_type="chord type",
    ),
)
fig.update_layout(**utils.STD_LAYOUT)
save_figure_as(fig, "chord_type_distribution_over_scale_degrees_absolute_stacked_bars")
fig.show()
```

```{code-cell} ipython3
relative_roots = all_chords[
    ["numeral", "duration_qb", "relativeroot", "localkey_is_minor", "chord_type"]
].copy()
relative_roots["relativeroot_resolved"] = ms3.transform(
    relative_roots, ms3.resolve_relative_keys, ["relativeroot", "localkey_is_minor"]
)
has_rel = relative_roots.relativeroot_resolved.notna()
relative_roots.loc[has_rel, "localkey_is_minor"] = relative_roots.loc[
    has_rel, "relativeroot_resolved"
].str.islower()
relative_roots["root"] = ms3.transform(
    relative_roots, ms3.roman_numeral2fifths, ["numeral", "localkey_is_minor"]
)
chord_type_frequency = all_chords.chord_type.value_counts()
replace_rare = ms3.map_dict(
    {t: "other" for t in chord_type_frequency[chord_type_frequency < 500].index}
)
relative_roots["type_reduced"] = relative_roots.chord_type.map(replace_rare)
# is_special = relative_roots.chord_type.isin(('It', 'Ger', 'Fr'))
# relative_roots.loc[is_special, 'root'] = -4
```

```{code-cell} ipython3
root_durations = (
    relative_roots.groupby(["root", "type_reduced"])
    .duration_qb.sum()
    .sort_values(ascending=False)
)
bar_data = root_durations.reset_index()
bar_data.root = bar_data.root.map(ms3.fifths2iv)
root_order = (
    bar_data.groupby("root")
    .duration_qb.sum()
    .sort_values(ascending=False)
    .index.to_list()
)
fig = px.bar(
    bar_data,
    x="root",
    y="duration_qb",
    color="type_reduced",
    barmode="group",
    log_y=True,
    color_discrete_map=utils.TYPE_COLORS,
    category_orders=dict(
        root=root_order,
        type_reduced=relative_roots.type_reduced.value_counts().index.to_list(),
    ),
    labels=dict(
        root="intervallic difference between chord root to the local or secondary tonic",
        duration_qb="duration in quarter notes",
        type_reduced="chord type",
    ),
    width=1000,
    height=400,
)
fig.update_layout(
    **utils.STD_LAYOUT,
    legend=dict(
        orientation="h",
        xanchor="right",
        x=1,
        y=1,
    ),
)
save_figure_as(fig, "chord_type_distribution_over_scale_degrees_absolute_grouped_bars")
fig.show()
```

```{code-cell} ipython3
print(
    f"Reduced to {len(set(bar_data.iloc[:,:2].itertuples(index=False, name=None)))} types. "
    f"Paper cites the sum of types in major and types in minor (see below), treating them as distinct."
)
```

```{code-cell} ipython3
dim_or_aug = bar_data[
    bar_data.root.str.startswith("a") | bar_data.root.str.startswith("d")
].duration_qb.sum()
complete = bar_data.duration_qb.sum()
print(
    f"On diminished or augmented scale degrees: {dim_or_aug} / {complete} = {dim_or_aug / complete}"
)
```

```{code-cell} ipython3
chords_by_mode = groupers.ModeGrouper().process(all_chords)
chords_by_mode.format = "scale_degree"
```

+++ {"jp-MarkdownHeadingCollapsed": true}

#### Whole dataset

```{code-cell} ipython3
unigram_proportions = chords_by_mode.get_default_analysis()
unigram_proportions.make_ranking_table()
```

```{code-cell} ipython3
chords_by_mode.apply_step("Counter")
```

```{code-cell} ipython3
chords_by_mode.format = "scale_degree"
chords_by_mode.get_default_analysis().make_ranking_table()
```

```{code-cell} ipython3
unigram_proportions.plot_grouped()
```