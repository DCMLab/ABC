---
jupytext:
  formats: md:myst,ipynb
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

# Annotations

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
pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 100)
import plotly.express as px
import plotly.graph_objects as go

from utils import STD_LAYOUT, CADENCE_COLORS, CORPUS_COLOR_SCALE, TYPE_COLORS, chronological_corpus_order, color_background, corpus_mean_composition_years, get_corpus_display_name, get_repo_name, resolve_dir, value_count_df, get_repo_name, print_heading, resolve_dir
```

```{code-cell} ipython3
:tags: [hide-input]

CORPUS_PATH = os.getenv('CORPUS_PATH', "/home/hentsche/tmp/all_subcorpora/")
print_heading("Notebook settings")
print(f"CORPUS_PATH: {CORPUS_PATH!r}")
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

annotated_view = dataset.data.get_view('annotated')
annotated_view.include('facets', 'measures', 'expanded')
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
all_metadata = dataset.data.metadata()
assert len(all_metadata) > 0, "No pieces selected for analysis."
print(f"Metadata covers {len(all_metadata)} of the {dataset.data.count_pieces()} scores.")
mean_composition_years = corpus_mean_composition_years(all_metadata)
chronological_order = mean_composition_years.index.to_list()
corpus_colors = dict(zip(chronological_order, CORPUS_COLOR_SCALE))
corpus_names = {corp: get_corpus_display_name(corp) for corp in chronological_order}
chronological_corpus_names = list(corpus_names.values())
corpus_name_colors = {corpus_names[corp]: color for corp, color in corpus_colors.items()}
```

## DCML harmony labels

```{code-cell} ipython3
:tags: [hide-input]

try:
    all_annotations = dataset.get_facet('expanded')
except Exception:
    all_annotations = pd.DataFrame()
n_annotations = len(all_annotations.index)
includes_annotations = n_annotations > 0
if includes_annotations:
    display(all_annotations.head())
    print(f"Concatenated annotation tables contain {all_annotations.shape[0]} rows.")
    no_chord = all_annotations.root.isna()
    if no_chord.sum() > 0:
        print(f"{no_chord.sum()} of them are not chords. Their values are: {all_annotations.label[no_chord].value_counts(dropna=False).to_dict()}")
    all_chords = all_annotations[~no_chord].copy()
    print(f"Dataset contains {all_chords.shape[0]} tokens and {len(all_chords.chord.unique())} types over {len(all_chords.groupby(level=[0,1]))} documents.")
    all_annotations['corpus_name'] = all_annotations.index.get_level_values(0).map(corpus_names)
    all_chords['corpus_name'] = all_chords.index.get_level_values(0).map(corpus_names)
else:
    print(f"Dataset contains no annotations.")
```

## Key areas

```{code-cell} ipython3
from ms3 import roman_numeral2fifths, transform, resolve_all_relative_numerals, replace_boolean_mode_by_strings
keys_segmented = dc.LocalKeySlicer().process_data(dataset)
keys = keys_segmented.get_slice_info()
print(f"Overall number of key segments is {len(keys.index)}")
keys["localkey_fifths"] = transform(keys, roman_numeral2fifths, ['localkey', 'globalkey_is_minor'])
keys.head(5).style.apply(color_background, subset="localkey")
```

### Durational distribution of local keys

All durations given in quarter notes

```{code-cell} ipython3
key_durations = keys.groupby(['globalkey_is_minor', 'localkey']).duration_qb.sum().sort_values(ascending=False)
print(f"{len(key_durations)} keys overall including hierarchical such as 'III/v'.")
```

```{code-cell} ipython3
keys_resolved = resolve_all_relative_numerals(keys)
key_resolved_durations = keys_resolved.groupby(['globalkey_is_minor', 'localkey']).duration_qb.sum().sort_values(ascending=False)
print(f"{len(key_resolved_durations)} keys overall after resolving hierarchical ones.")
key_resolved_durations
```

#### Distribution of local keys for piece in major and in minor

`globalkey_mode=minor` => Piece is in Minor

```{code-cell} ipython3
pie_data = replace_boolean_mode_by_strings(key_resolved_durations.reset_index())
px.pie(pie_data, names='localkey', values='duration_qb', facet_col='globalkey_mode')
```

#### Distribution of intervals between localkey tonic and global tonic

```{code-cell} ipython3
localkey_fifths_durations = keys.groupby(['localkey_fifths', 'localkey_is_minor']).duration_qb.sum()
bar_data = replace_boolean_mode_by_strings(localkey_fifths_durations.reset_index())
bar_data.localkey_fifths = bar_data.localkey_fifths.map(ms3.fifths2iv)
fig = px.bar(bar_data, x='localkey_fifths', y='duration_qb', color='localkey_mode', log_y=True, barmode='group',
             labels=dict(localkey_fifths='Roots of local keys as intervallic distance from the global tonic', 
                   duration_qb='total duration in quarter notes',
                   localkey_mode='mode'
                  ),
             color_discrete_sequence=CORPUS_COLOR_SCALE,
             )
fig.update_layout(**STD_LAYOUT)
fig.update_yaxes(gridcolor='lightgrey')
fig.show()
```

### Ratio between major and minor key segments by aggregated durations
#### Overall

```{code-cell} ipython3
keys.duration_qb = pd.to_numeric(keys.duration_qb)
maj_min_ratio = keys.groupby("localkey_is_minor").duration_qb.sum().to_frame()
maj_min_ratio['fraction'] = (100.0 * maj_min_ratio.duration_qb / maj_min_ratio.duration_qb.sum()).round(1)
maj_min_ratio
```

#### By dataset

```{code-cell} ipython3
segment_duration_per_dataset = keys.groupby(["corpus", "localkey_is_minor"]).duration_qb.sum().round(2)
norm_segment_duration_per_dataset = 100 * segment_duration_per_dataset / segment_duration_per_dataset.groupby(level="corpus").sum()
maj_min_ratio_per_dataset = pd.concat([segment_duration_per_dataset, 
                                      norm_segment_duration_per_dataset.rename('fraction').round(1).astype(str)+" %"], 
                                     axis=1)
maj_min_ratio_per_dataset['corpus_name'] = maj_min_ratio_per_dataset.index.get_level_values('corpus').map(corpus_names)
maj_min_ratio_per_dataset['mode'] = maj_min_ratio_per_dataset.index.get_level_values('localkey_is_minor').map({False: 'major', True: 'minor'})
```

```{code-cell} ipython3
fig = px.bar(maj_min_ratio_per_dataset.reset_index(), 
       x="corpus_name", 
       y="duration_qb", 
       color="mode", 
       text='fraction',
       labels=dict(dataset='', duration_qb="duration in 𝅘𝅥", corpus_name='Key segments grouped by corpus'),
       category_orders=dict(dataset=chronological_order)
    )
fig.update_layout(**STD_LAYOUT)
fig.show()
```

## Harmony labels
### Unigrams
For computing unigram statistics, the tokens need to be grouped by their occurrence within a major or a minor key because this changes their meaning. To that aim, the annotated corpus needs to be sliced into contiguous localkey segments which are then grouped into a major (`is_minor=False`) and a minor group.

```{code-cell} ipython3
root_durations = all_chords[all_chords.root.between(-5,6)].groupby(['root', 'chord_type']).duration_qb.sum()
# sort by stacked bar length:
#root_durations = root_durations.sort_values(key=lambda S: S.index.get_level_values(0).map(S.groupby(level=0).sum()), ascending=False)
bar_data = root_durations.reset_index()
bar_data.root = bar_data.root.map(ms3.fifths2iv)
px.bar(bar_data, x='root', y='duration_qb', color='chord_type')
```

```{code-cell} ipython3
relative_roots = all_chords[['numeral', 'duration_qb', 'relativeroot', 'localkey_is_minor', 'chord_type']].copy()
relative_roots['relativeroot_resolved'] = transform(relative_roots, ms3.resolve_relative_keys, ['relativeroot', 'localkey_is_minor'])
has_rel = relative_roots.relativeroot_resolved.notna()
relative_roots.loc[has_rel, 'localkey_is_minor'] = relative_roots.loc[has_rel, 'relativeroot_resolved'].str.islower()
relative_roots['root'] = transform(relative_roots, roman_numeral2fifths, ['numeral', 'localkey_is_minor'])
chord_type_frequency = all_chords.chord_type.value_counts()
replace_rare = ms3.map_dict({t: 'other' for t in chord_type_frequency[chord_type_frequency < 500].index})
relative_roots['type_reduced'] = relative_roots.chord_type.map(replace_rare)
#is_special = relative_roots.chord_type.isin(('It', 'Ger', 'Fr'))
#relative_roots.loc[is_special, 'root'] = -4
```

```{code-cell} ipython3
root_durations = relative_roots.groupby(['root', 'type_reduced']).duration_qb.sum().sort_values(ascending=False)
bar_data = root_durations.reset_index()
bar_data.root = bar_data.root.map(ms3.fifths2iv)
root_order = bar_data.groupby('root').duration_qb.sum().sort_values(ascending=False).index.to_list()
fig = px.bar(bar_data, x='root', y='duration_qb', color='type_reduced', barmode='group', log_y=True,
             color_discrete_map=TYPE_COLORS, 
             category_orders=dict(root=root_order,
                                  type_reduced=relative_roots.type_reduced.value_counts().index.to_list(),
                                 ),
            labels=dict(root="intervallic difference between chord root to the local or secondary tonic",
                        duration_qb="duration in quarter notes",
                        type_reduced="chord type",
                       ),
             width=1000,
             height=400,
            )
fig.update_layout(**STD_LAYOUT,
                  legend=dict(
                      orientation='h',
                      xanchor="right",
                      x=1,
                      y=1,
                  )
                 )
fig.update_yaxes(gridcolor='lightgrey')
fig.show()
```

```{code-cell} ipython3
print(f"Reduced to {len(set(bar_data.iloc[:,:2].itertuples(index=False, name=None)))} types. Paper cites the sum of types in major and types in minor (see below), treating them as distinct.")
```

```{code-cell} ipython3
dim_or_aug = bar_data[bar_data.root.str.startswith("a") | bar_data.root.str.startswith("d")].duration_qb.sum()
complete = bar_data.duration_qb.sum()
print(f"On diminished or augmented scale degrees: {dim_or_aug} / {complete} = {dim_or_aug / complete}")
```

```{code-cell} ipython3
mode_slices = dc.ModeGrouper().process_data(keys_segmented)
```

### Whole dataset

```{code-cell} ipython3
mode_slices.get_slice_info()
```

```{code-cell} ipython3
unigrams = dc.ChordSymbolUnigrams(once_per_group=True).process_data(mode_slices)
```

```{code-cell} ipython3
unigrams.group2pandas = "group_of_series2series"
```

```{code-cell} ipython3
unigrams.get(as_pandas=True)
```

```{code-cell} ipython3
k = 20
modes = {True: 'MINOR', False: 'MAJOR'}
for (is_minor,), ugs in unigrams.iter():
    print(f"TOP {k} {modes[is_minor]} UNIGRAMS\n{ugs.shape[0]} types, {ugs.sum()} tokens")
    print(ugs.head(k).to_string())
```

```{code-cell} ipython3
ugs_dict = {modes[is_minor].lower(): (ugs/ugs.sum() * 100).round(2).rename('%').reset_index() for (is_minor,), ugs in unigrams.iter()}
ugs_df = pd.concat(ugs_dict, axis=1)
ugs_df.columns = ['_'.join(map(str, col)) for col in ugs_df.columns]
ugs_df.index = (ugs_df.index + 1).rename('k')
ugs_df.iloc[:50]
```

```{code-cell} ipython3
chords_by_localkey = mode_slices.get_facet('expanded')
chords_by_localkey
```

```{code-cell} ipython3
for is_minor, df in chords_by_localkey.groupby(level=0, group_keys=False):
    df = df.droplevel(0)
    df = df[df.bass_note.notna()]
    sd = ms3.fifths2sd(df.bass_note).rename('sd')
    sd.index = df.index
    sd_progression = df.groupby(level=[0,1,2], group_keys=False).bass_note.apply(lambda S: S.shift(-1) - S).rename('sd_progression')
    if is_minor:
        chords_by_localkey_minor = pd.concat([df, sd, sd_progression], axis=1)
    else:
        chords_by_localkey_major = pd.concat([df, sd, sd_progression], axis=1)
```

## Scale degrees

```{code-cell} ipython3
chords_by_localkey_minor
```

```{code-cell} ipython3
import plotly.graph_objects as go
from collections import Counter, defaultdict

def make_sunburst(chords, mode):
    in_scale = []
    for sd, sd_prog in chords[['sd', 'sd_progression']].itertuples(index=False):
        if len(sd) == 1:
            in_scale.append(sd)
    label_counts = Counter(in_scale)
    labels, values = list(label_counts.keys()), list(label_counts.values())
    #labels, values = zip(*list((sd, label_counts[sd]) for sd in sorted(label_counts)))
    parents = [mode] * len(labels)
    labels = [mode] + labels
    parents = [""] + parents
    values = [len(chords)] + values
    fig =go.Figure(go.Sunburst(
        labels=labels,
        parents=parents,
        values=values,
        branchvalues="total"
    ))
    fig.update_layout(margin = dict(t=0, l=0, r=0, b=0))
    return fig

make_sunburst(chords_by_localkey_minor, 'minor')
```

```{code-cell} ipython3
def make_sunburst(chords, mode):
    in_scale = []
    sd2prog = defaultdict(Counter)
    for sd, sd_prog in chords[['sd', 'sd_progression']].itertuples(index=False):
        if len(sd) == 1:
            in_scale.append(sd)
            sd2prog[sd].update(["∎"] if pd.isnull(sd_prog) else [str(sd_prog)])
    label_counts = Counter(in_scale)
    labels, values = list(label_counts.keys()), list(label_counts.values())
    #labels, values = zip(*list((sd, label_counts[sd]) for sd in sorted(label_counts)))
    parents = [mode] * len(labels)
    labels = [mode] + labels
    parents = [""] + parents
    values = [len(chords)] + values
    #print(sd2prog)
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
    
    fig =go.Figure(go.Sunburst(
        labels=labels,
        parents=parents,
        values=values,
        branchvalues="total"
    ))
    fig.update_layout(margin = dict(t=0, l=0, r=0, b=0))
    return fig

make_sunburst(chords_by_localkey_minor, 'minor')
```

```{code-cell} ipython3
fig =go.Figure(go.Sunburst(
    labels=["Eve", "Cain", "Seth", "Enos", "Noam", "Abel", "Awan", "Enoch", "Azura"],
    parents=["", "Eve", "Eve", "Seth", "Seth", "Eve", "Eve", "Awan", "Eve" ],
    values=[10, 14, 12, 10, 2, 6, 6, 4, 4],
))
fig.update_layout(margin = dict(t=0, l=0, r=0, b=0))

fig.show()
```

```{code-cell} ipython3
fig =go.Figure(go.Sunburst(
    labels=["major", "Cain", "1", "Enos", "Noam", "Abel", "Awan", "Enoch", "Azura"],
    parents=["", "major", "major", "1", "1", "major", "major", "Awan", "major" ],
    values=[10, 14, 12, 10, 2, 6, 6, 4, 4],
))
fig.update_layout(margin = dict(t=0, l=0, r=0, b=0))

fig.show()
```

```{code-cell} ipython3
df
```

```{code-cell} ipython3
df = px.data.tips()
fig = px.sunburst(df, path=['sex', 'day', 'time'], values='total_bill', color='time')
fig.show()
```

```{code-cell} ipython3
#localkey_major_no_repeats = ms3.segment_by_adjacency_groups(chords_by_localkey_major, ['sd', 'figbass'], )
#localkey_major_no_repeats
```

```{code-cell} ipython3
def safe_interval(fifths):
    if pd.isnull(fifths):
        return "∎"
    return ms3.fifths2iv(fifths, smallest=True)
```

```{code-cell} ipython3
def prepare_sunburst_data(chords):
    chord_data = chords[chords.sd.str.len() == 1].copy()
    chord_data["interval"] = ms3.transform(chord_data.sd_progression, safe_interval).fillna("∎")
    chord_data.figbass.fillna('3', inplace=True)
    chord_data["following_figbass"] = chord_data.groupby(level=[0,1,2],).figbass.shift(-1).fillna("∎")
    return chord_data

column2name = dict(
    sd="scale degree",
    figbass="bass figure",
    interval="bass progression",
    following_figbass="subsequent figure"
)

def rectangular_sunburst(
    chords,
    path = ['sd', 'figbass', 'interval'],
    height = 1500,
    title = "Sunburst",
):
    chord_data = prepare_sunburst_data(chords)
    title = f"{title} ({' - '.join(column2name[col] for col in path)})"
    return px.sunburst(
        chord_data, 
        path=path, 
        height=height,
        title=title,
    )

rectangular_sunburst(chords_by_localkey_major, title="MAJOR")
```

```{code-cell} ipython3
rectangular_sunburst(chords_by_localkey_major, ['sd', 'interval', 'figbass', 'following_figbass'], title="MAJOR")
```

```{code-cell} ipython3
rectangular_sunburst(chords_by_localkey_minor, title="MINOR")
```

```{code-cell} ipython3
rectangular_sunburst(chords_by_localkey_minor, ['sd', 'interval', 'figbass'], title="MINOR")
```

```{code-cell} ipython3

```