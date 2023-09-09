---
jupytext:
  formats: ipynb,md:myst
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.15.0
kernelspec:
  display_name: corpus_docs
  language: python
  name: corpus_docs
---

# Overview

This notebook gives a general overview of the features included in the dataset.

```{code-cell} ipython3
---
mystnb:
  code_prompt_hide: Hide imports
  code_prompt_show: Show imports
tags: [hide-cell]
---
import os
from collections import defaultdict, Counter
from fractions import Fraction

from git import Repo
import dimcat as dc
import ms3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from utils import CADENCE_COLORS, CORPUS_COLOR_SCALE, STD_LAYOUT, TYPE_COLORS, color_background, corpus_mean_composition_years, value_count_df, get_corpus_display_name, get_repo_name, print_heading, resolve_dir
```

```{code-cell} ipython3
:tags: [hide-input]

CORPUS_PATH = os.path.abspath(os.path.join('..', '..'))
ANNOTATED_ONLY = os.getenv("ANNOTATED_ONLY", "True").lower() in ('true', '1', 't')
print_heading("Notebook settings")
print(f"CORPUS_PATH: {CORPUS_PATH!r}")
print(f"ANNOTATED_ONLY: {ANNOTATED_ONLY}")
CORPUS_PATH = resolve_dir(CORPUS_PATH)
```

```{code-cell} ipython3
:tags: [hide-input]

repo = Repo(CORPUS_PATH)
print_heading("Data and software versions")
print(f"Data repo '{get_repo_name(repo)}' @ {repo.commit().hexsha[:7]}")
print(f"dimcat version {dc.__version__}")
print(f"ms3 version {ms3.__version__}")
```

```{code-cell} ipython3
:tags: [remove-output]

dataset = dc.Dataset()
dataset.load(directory=CORPUS_PATH, parse_tsv=False)
```

```{code-cell} ipython3
:tags: [remove-input]

if ANNOTATED_ONLY:
    annotated_view = dataset.data.get_view('annotated')
    annotated_view.include('facets', 'measures', 'notes$', 'expanded')
    annotated_view.fnames_with_incomplete_facets = False
    dataset.data.set_view(annotated_view)
dataset.data.parse_tsv(choose='auto')
dataset.get_indices()
dataset.data
```

```{code-cell} ipython3
:tags: [remove-input]

print(f"N = {dataset.data.count_pieces()} annotated pieces, {dataset.data.count_parsed_tsvs()} parsed dataframes.")
```

```{code-cell} ipython3
---
mystnb:
  code_prompt_hide: Hide data loading
  code_prompt_show: Show data loading
tags: [hide-cell]
---
all_metadata = dataset.data.metadata()
assert len(all_metadata) > 0, "No pieces selected for analysis."
print(f"Metadata covers {len(all_metadata)} of the {dataset.data.count_pieces()} scores.")
all_notes = dataset.get_facet('notes')
all_measures = dataset.get_facet('measures')
mean_composition_years = corpus_mean_composition_years(all_metadata)
chronological_order = mean_composition_years.index.to_list()
corpus_colors = dict(zip(chronological_order, CORPUS_COLOR_SCALE))
corpus_names = {corp: get_corpus_display_name(corp) for corp in chronological_order}
chronological_corpus_names = list(corpus_names.values())
corpus_name_colors = {corpus_names[corp]: color for corp, color in corpus_colors.items()}
```

## Composition dates

This section relies on the dataset's metadata.

```{code-cell} ipython3
valid_composed_start = pd.to_numeric(all_metadata.composed_start, errors='coerce')
valid_composed_end = pd.to_numeric(all_metadata.composed_end, errors='coerce')
print(f"Composition dates range from {int(valid_composed_start.min())} {valid_composed_start.idxmin()} "
      f"to {int(valid_composed_end.max())} {valid_composed_end.idxmax()}.")
```

### Mean composition years per corpus

```{code-cell} ipython3
:tags: [hide-input]

summary = all_metadata.copy()
summary.length_qb = all_measures.groupby(level=[0,1]).act_dur.sum() * 4.0
summary = pd.concat([summary,
                     all_notes.groupby(level=[0,1]).size().rename('notes'),
                    ], axis=1)
bar_data = pd.concat([mean_composition_years.rename('year'), 
                      summary.groupby(level='corpus').size().rename('pieces')],
                     axis=1
                    ).reset_index()
fig = px.bar(bar_data, x='year', y='pieces', color='corpus',
             color_discrete_map=corpus_colors,
            )
fig.update_traces(width=5)
fig.update_layout(**STD_LAYOUT)
fig.update_yaxes(gridcolor='lightgrey')
fig.update_traces(width=5)
```

### Composition years histogram

```{code-cell} ipython3
:tags: [hide-input]

hist_data = summary.reset_index()
hist_data.corpus = hist_data.corpus.map(corpus_names)
fig = px.histogram(hist_data, x='composed_end', color='corpus',
                   labels=dict(composed_end='decade',
                               count='pieces',
                              ),
                   color_discrete_map=corpus_name_colors,
                  )
fig.update_traces(xbins=dict(
    size=10
))
fig.update_layout(**STD_LAYOUT)
fig.update_yaxes(gridcolor='lightgrey')
fig.show()
```

## Dimensions

### Overview

```{code-cell} ipython3
:tags: [hide-input]

corpus_metadata = summary.groupby(level=0)
n_pieces = corpus_metadata.size().rename('pieces')
absolute_numbers = dict(
    measures = corpus_metadata.last_mn.sum(),
    length = corpus_metadata.length_qb.sum(),
    notes = corpus_metadata.notes.sum(),
    labels = corpus_metadata.label_count.sum(),
)
absolute = pd.DataFrame.from_dict(absolute_numbers)
absolute = pd.concat([n_pieces, absolute], axis=1)
sum_row = pd.DataFrame(absolute.sum(), columns=['sum']).T
absolute = pd.concat([absolute, sum_row])
relative = absolute.div(n_pieces, axis=0)
complete_summary = pd.concat([absolute, relative, absolute.iloc[:1,2:].div(absolute.measures, axis=0)], axis=1, keys=['absolute', 'per piece', 'per measure'])
complete_summary = complete_summary.apply(pd.to_numeric).round(2)
complete_summary.index = complete_summary.index.map(dict(corpus_names, sum='sum'))
complete_summary
```

### Measures

```{code-cell} ipython3
print(f"{len(all_measures.index)} measures over {len(all_measures.groupby(level=[0,1]))} files.")
all_measures.head()
```

```{code-cell} ipython3
print("Distribution of time signatures per XML measure (MC):")
all_measures.timesig.value_counts(dropna=False)
```

### Harmony labels

All symbols, independent of the local key (the mode of which changes their semantics).

```{code-cell} ipython3
try:
    all_annotations = dataset.get_facet('expanded')
except Exception:
    all_annotations = pd.DataFrame()
n_annotations = len(all_annotations.index)
includes_annotations = n_annotations > 0
if includes_annotations:
    display(all_annotations.head())
    print(f"Concatenated annotation tables contains {all_annotations.shape[0]} rows.")
    no_chord = all_annotations.root.isna()
    if no_chord.sum() > 0:
        print(f"{no_chord.sum()} of them are not chords. Their values are: {all_annotations.label[no_chord].value_counts(dropna=False).to_dict()}")
    all_chords = all_annotations[~no_chord].copy()
    print(f"Dataset contains {all_chords.shape[0]} tokens and {len(all_chords.chord.unique())} types over {len(all_chords.groupby(level=[0,1]))} documents.")
    all_annotations['corpus_name'] = all_annotations.index.get_level_values(0).map(get_corpus_display_name)
    all_chords['corpus_name'] = all_chords.index.get_level_values(0).map(get_corpus_display_name)
else:
    print(f"Dataset contains no annotations.")
```