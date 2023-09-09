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
import plotly.express as px
import plotly.graph_objects as go

from utils import STD_LAYOUT, CADENCE_COLORS, CORPUS_COLOR_SCALE, TYPE_COLORS, chronological_corpus_order, color_background, corpus_mean_composition_years, get_corpus_display_name, get_repo_name, resolve_dir, value_count_df, get_repo_name, print_heading, resolve_dir
```

```{code-cell} ipython3
:tags: [hide-input]

CORPUS_PATH = os.path.abspath(os.path.join('..', '..'))
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

## Phrases
### Presence of phrase annotation symbols per dataset:

```{code-cell} ipython3
all_annotations.groupby(["corpus"]).phraseend.value_counts()
```

### Presence of legacy phrase endings

```{code-cell} ipython3
legacy = all_annotations[all_annotations.phraseend == r'\\']
legacy.groupby(level=0).size()
```

### A table with the extents of all annotated phrases
**Relevant columns:**
* `quarterbeats`: start position for each phrase
* `duration_qb`: duration of each phrase, measured in quarter notes 
* `phrase_slice`: time interval of each annotated phrases (for segmenting chord progressions and notes)

```{code-cell} ipython3
phrase_segmented = dc.PhraseSlicer().process_data(dataset)
phrases = phrase_segmented.get_slice_info()
print(f"Overall number of phrases is {len(phrases.index)}")
phrases.head(10).style.apply(color_background, subset=["quarterbeats", "duration_qb"])
```

### A table with the chord sequences of all annotated phrases

```{code-cell} ipython3
phrase_segments = phrase_segmented.get_facet('expanded')
phrase_segments
```

```{code-cell} ipython3
:tags: [hide-input]

phrase2timesigs = phrase_segments.groupby(level=[0,1,2]).timesig.unique()
n_timesignatures_per_phrase = phrase2timesigs.map(len)
uniform_timesigs = phrase2timesigs[n_timesignatures_per_phrase == 1].map(lambda l: l[0])
more_than_one = n_timesignatures_per_phrase > 1
print(f"Filtered out the {more_than_one.sum()} phrases incorporating more than one time signature.")
n_timesigs = n_timesignatures_per_phrase.value_counts()
display(n_timesigs.reset_index().rename(columns=dict(index='#time signatures', timesig='#phrases')))
uniform_timesig_phrases = phrases.loc[uniform_timesigs.index]
timesig_in_quarterbeats = uniform_timesigs.map(Fraction) * 4
exact_measure_lengths = uniform_timesig_phrases.duration_qb / timesig_in_quarterbeats
uniform_timesigs = pd.concat([exact_measure_lengths.rename('duration_measures'), uniform_timesig_phrases], axis=1)
fig = px.histogram(uniform_timesigs, x='duration_measures', log_y=True,
                   labels=dict(duration_measures='phrase length bin in number of measures'),
                   color_discrete_sequence=CORPUS_COLOR_SCALE,
                  )
fig.update_traces(xbins=dict( # bins used for histogram
        #start=0.0,
        #end=100.0,
        size=1
    ))
fig.update_layout(**STD_LAYOUT)
fig.update_xaxes(dtick=4, gridcolor='lightgrey')
fig.update_yaxes(gridcolor='lightgrey')
fig.show()
```

### Local keys per phrase

```{code-cell} ipython3
local_keys_per_phrase = phrase_segments.groupby(level=[0,1,2]).localkey.unique().map(tuple)
n_local_keys_per_phrase = local_keys_per_phrase.map(len)
phrases_with_keys = pd.concat([n_local_keys_per_phrase.rename('n_local_keys'),
                               local_keys_per_phrase.rename('local_keys'),
                               phrases], axis=1)
phrases_with_keys.head(10).style.apply(color_background, subset=['n_local_keys', 'local_keys'])
```

#### Number of unique local keys per phrase

```{code-cell} ipython3
count_n_keys = phrases_with_keys.n_local_keys.value_counts().rename("#phrases").to_frame()
count_n_keys.index.rename("unique keys", inplace=True)
count_n_keys
```

#### The most frequent keys for non-modulating phrases

```{code-cell} ipython3
unique_key_selector = phrases_with_keys.n_local_keys == 1
phrases_with_unique_key = phrases_with_keys[unique_key_selector].copy()
phrases_with_unique_key.local_keys = phrases_with_unique_key.local_keys.map(lambda t: t[0])
value_count_df(phrases_with_unique_key.local_keys, counts="#phrases")
```

#### Most frequent modulations within one phrase

```{code-cell} ipython3
two_keys_selector = phrases_with_keys.n_local_keys > 1
phrases_with_unique_key = phrases_with_keys[two_keys_selector].copy()
value_count_df(phrases_with_unique_key.local_keys, "modulations")
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

### Tone profiles for all major and minor local keys

```{code-cell} ipython3
notes_by_keys = keys_segmented.get_facet("notes")
notes_by_keys
```

```{code-cell} ipython3
keys = keys[[col for col in keys.columns if col not in notes_by_keys]]
notes_joined_with_keys = notes_by_keys.join(keys, on=keys.index.names)
notes_by_keys_transposed = ms3.transpose_notes_to_localkey(notes_joined_with_keys)
mode_tpcs = notes_by_keys_transposed.reset_index(drop=True).groupby(['localkey_is_minor', 'tpc']).duration_qb.sum().reset_index(-1).sort_values('tpc').reset_index()
mode_tpcs['sd'] = ms3.fifths2sd(mode_tpcs.tpc)
mode_tpcs['duration_pct'] = mode_tpcs.groupby('localkey_is_minor', group_keys=False).duration_qb.apply(lambda S: S / S.sum())
mode_tpcs['mode'] = mode_tpcs.localkey_is_minor.map({False: 'major', True: 'minor'})
```

```{code-cell} ipython3
#mode_tpcs = mode_tpcs[mode_tpcs['duration_pct'] > 0.001]
#sd_order = ['b1', '1', '#1', 'b2', '2', '#2', 'b3', '3', 'b4', '4', '#4', '##4', 'b5', '5', '#5', 'b6','6', '#6', 'b7', '7']
xaxis = dict(
        tickmode = 'array',
        tickvals = mode_tpcs.tpc,
        ticktext = mode_tpcs.sd
    )
legend=dict(
    yanchor="top",
    y=0.99,
    xanchor="right",
    x=0.99
)
fig = px.bar(mode_tpcs,
       x='tpc',
       y='duration_pct',
       color='mode',
       barmode='group',
       labels=dict(duration_pct='normalized duration',
                   tpc="Notes transposed to the local key, as major-scale degrees",
                  ),
       #log_y=True,
       #category_orders=dict(sd=sd_order)
      )
fig.update_layout(**STD_LAYOUT, xaxis=xaxis, legend=legend)
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
print(ugs_df.iloc[:50].to_markdown())
```

### Per corpus

```{code-cell} ipython3
corpus_wise_unigrams = dc.Pipeline([dc.CorpusGrouper(), dc.ChordSymbolUnigrams(once_per_group=True)]).process_data(mode_slices)
```

```{code-cell} ipython3
corpus_wise_unigrams.get()
```

```{code-cell} ipython3
for (is_minor, corpus_name), ugs in corpus_wise_unigrams.iter():
    print(f"{corpus_name} {modes[is_minor]} unigrams ({ugs.shape[0]} types, {ugs.sum()} tokens)")
    print(ugs.head(5).to_string())
```

```{code-cell} ipython3
types_shared_between_corpora = {}
for (is_minor, corpus_name), ugs in corpus_wise_unigrams.iter():
    if is_minor in types_shared_between_corpora:
        types_shared_between_corpora[is_minor] = types_shared_between_corpora[is_minor].intersection(ugs.index) 
    else:
        types_shared_between_corpora[is_minor] = set(ugs.index)
types_shared_between_corpora = {k: sorted(v, key=lambda x: unigrams.get()[(k, x)], reverse=True) for k, v in types_shared_between_corpora.items()}
n_types = {k: len(v) for k, v in types_shared_between_corpora.items()}
print(f"Chords which occur in all corpora, sorted by descending global frequency:\n{types_shared_between_corpora}\nCounts: {n_types}")
```

### Per piece

```{code-cell} ipython3
piece_wise_unigrams = dc.Pipeline([dc.PieceGrouper(), dc.ChordSymbolUnigrams(once_per_group=True)]).process_data(mode_slices)
```

```{code-cell} ipython3
piece_wise_unigrams.get()
```

```{code-cell} ipython3
types_shared_between_pieces = {}
for (is_minor, corpus_name), ugs in piece_wise_unigrams.iter():
    if is_minor in types_shared_between_pieces:
        types_shared_between_pieces[is_minor] = types_shared_between_pieces[is_minor].intersection(ugs.index) 
    else:
        types_shared_between_pieces[is_minor] = set(ugs.index)
print(types_shared_between_pieces)
```

## Bigrams

+++

### Whole dataset

```{code-cell} ipython3
bigrams = dc.ChordSymbolBigrams(once_per_group=True).process_data(mode_slices)
```

```{code-cell} ipython3
bigrams.get()
```

```{code-cell} ipython3
modes = {True: 'MINOR', False: 'MAJOR'}
for (is_minor,), ugs in bigrams.iter():
    print(f"{modes[is_minor]} BIGRAMS\n{ugs.shape[0]} transition types, {ugs.sum()} tokens")
    print(ugs.head(20).to_string())
```

### Per corpus

```{code-cell} ipython3
corpus_wise_bigrams = dc.Pipeline([dc.CorpusGrouper(), dc.ChordSymbolBigrams(once_per_group=True)]).process_data(mode_slices)
```

```{code-cell} ipython3
corpus_wise_bigrams.get()
```

```{code-cell} ipython3
for (is_minor, corpus_name), ugs in corpus_wise_bigrams.iter():
    print(f"{corpus_name} {modes[is_minor]} bigrams ({ugs.shape[0]} transition types, {ugs.sum()} tokens)")
    print(ugs.head(5).to_string())
```

```{code-cell} ipython3
normalized_corpus_unigrams = {group: (100 * ugs / ugs.sum()).round(1).rename("frequency") for group, ugs in corpus_wise_unigrams.iter()}
```

```{code-cell} ipython3
transitions_from_shared_types = {
    False: {},
    True: {}
}
for (is_minor, corpus_name), bgs in corpus_wise_bigrams.iter():
    transitions_normalized_per_from = bgs.groupby(level="from", group_keys=False).apply(lambda S: (100 * S / S.sum()).round(1))
    most_frequent_transition_per_from = transitions_normalized_per_from.rename('fraction').reset_index(level=1).groupby(level=0).nth(0)
    most_frequent_transition_per_shared = most_frequent_transition_per_from.loc[types_shared_between_corpora[is_minor]]
    unigram_frequency_of_shared = normalized_corpus_unigrams[(is_minor, corpus_name)].loc[types_shared_between_corpora[is_minor]]
    combined = pd.concat([unigram_frequency_of_shared, most_frequent_transition_per_shared], axis=1)
    transitions_from_shared_types[is_minor][corpus_name] = combined
```

```{code-cell} ipython3
pd.concat(transitions_from_shared_types[False].values(), keys=transitions_from_shared_types[False].keys(), axis=1)
```

```{code-cell} ipython3
pd.concat(transitions_from_shared_types[True].values(), keys=transitions_from_shared_types[False].keys(), axis=1)
```

### Per piece

```{code-cell} ipython3
piece_wise_bigrams = dc.Pipeline([dc.PieceGrouper(), dc.ChordSymbolBigrams(once_per_group=True)]).process_data(mode_slices)
```

```{code-cell} ipython3
piece_wise_bigrams.get()
```