# ABC - The Annotated Beethoven Corpus (v2.0)
## Upgrade to MuseScore 3

Two years after its first publication (see below), this is the revised version of the ABC. It comes with the following changes:

* The repo's folder structure has been changed and scores have been renamed.
* All scores have been converted to [MuseScore 3](https://musescore.org/download) format and can be found in the folder `MS3`.
* The tables in TSV format have been recreated with a new parser. The meaning of the columns can be found in each folder's README:
  - The folder `harmonies` contains the chord labels of one movement each but with additional features such as the common chord type notation (e.g. `Mm7`) and chord tones.
  - The folder `notes` contains one note list per movement.
  - The folder `measures` contains tables of each movement's measures' features.
* The chord labels have been completely revised and adapted to version XY of the [DCML annotation standard](https://github.com/DCMLab/standards) (annotation guidelines under this link, too).

# ABC - The Annotated Beethoven Corpus (v1.0)

*Markus Neuwirth (markus.neuwirth@epfl.ch), Daniel Harasim (daniel.harasim@epfl.ch), Fabian C. Moss (fabian.moss@epfl.ch), Martin Rohrmeier (martin.rohrmeier@epfl.ch)*

The ABC dataset consists of expert harmonic analyses of all Beethoven string quartets (opp. 18, 59, 74, 95, 127, 130, 131, 132, 135, composed between 1800 and 1826), encoded in a human- and machine-readable format (MuseScore format). Using a modified Roman Numeral notation, the dataset includes the common music-theoretical set of harmonic features such as key, chordal root, chord inversion, chord extensions, suspensions, and others.

The accompanying Data Report has been published by [Frontiers in Digital Humanities](https://www.frontiersin.org/articles/10.3389/fdigh.2018.00016/full).

## Remarks

**Possible annotation errors**

While the annotation process (as detailed in the Data Report) was conducted very carefully, and all annotated symbols have been automatically checked for syntactic correctness, the authors cannot entirely rule out the possibility of typograpical errors or misinterpretations (e.g., due to ambiguities in the score or underspecification in the musical texture). After all, music analysis is not a deterministic process but involves interpretation. If you encounter anything that seems not right to you, please create an issue [here](https://github.com/DCMLab/ABC/issues).

**Missing bars**

The original XML file for Op. 132 No. 15, mov. 5 from Project Gutenberg did not contain measures 194-241. We added them manually.


# Overview
| file_name  |measures|labels|standard|  annotators   |reviewers|
|------------|-------:|-----:|--------|---------------|---------|
|n01op18-1_01|     313|   405|1.0.0   |Markus Neuwirth|         |
|n01op18-1_02|     110|   263|1.0.0   |Markus Neuwirth|         |
|n01op18-1_03|     145|   203|1.0.0   |Markus Neuwirth|         |
|n01op18-1_04|     381|   598|1.0.0   |Markus Neuwirth|         |
|n02op18-2_01|     249|   486|1.0.0   |Markus Neuwirth|         |
|n02op18-2_02|      86|   177|1.0.0   |Markus Neuwirth|         |
|n02op18-2_03|      87|   138|1.0.0   |Markus Neuwirth|         |
|n02op18-2_04|     412|   466|1.0.0   |Markus Neuwirth|         |
|n03op18-3_01|     271|   381|1.0.0   |Markus Neuwirth|         |
|n03op18-3_02|     151|   394|1.0.0   |Markus Neuwirth|         |
|n03op18-3_03|     172|   278|1.0.0   |Markus Neuwirth|         |
|n03op18-3_04|     372|   567|1.0.0   |Markus Neuwirth|         |
|n04op18-4_01|     219|   554|1.0.0   |Markus Neuwirth|         |
|n04op18-4_02|     261|   369|1.0.0   |Markus Neuwirth|         |
|n04op18-4_03|      98|   145|1.0.0   |Markus Neuwirth|         |
|n04op18-4_04|     226|   387|1.0.0   |Markus Neuwirth|         |
|n05op18-5_01|     228|   431|1.0.0   |Markus Neuwirth|         |
|n05op18-5_02|     105|   168|1.0.0   |Markus Neuwirth|         |
|n05op18-5_03|     152|   247|1.0.0   |Markus Neuwirth|         |
|n05op18-5_04|     304|   567|1.0.0   |Markus Neuwirth|         |
|n06op18-6_01|     264|   374|1.0.0   |Markus Neuwirth|         |
|n06op18-6_02|      79|   265|1.0.0   |Markus Neuwirth|         |
|n06op18-6_03|      68|   168|1.0.0   |Markus Neuwirth|         |
|n06op18-6_04|     297|   466|1.0.0   |Markus Neuwirth|         |
|n07op59-1_01|     400|   482|1.0.0   |Markus Neuwirth|         |
|n07op59-1_02|     476|   635|1.0.0   |Markus Neuwirth|         |
|n07op59-1_03|     132|   374|1.0.0   |Markus Neuwirth|         |
|n07op59-1_04|     327|   605|1.0.0   |Markus Neuwirth|         |
|n08op59-2_01|     255|   445|1.0.0   |Markus Neuwirth|         |
|n08op59-2_02|     157|   326|1.0.0   |Markus Neuwirth|         |
|n08op59-2_03|     135|   262|1.0.0   |Markus Neuwirth|         |
|n08op59-2_04|     409|   567|1.0.0   |Markus Neuwirth|         |
|n09op59-3_01|     270|   515|1.0.0   |Markus Neuwirth|         |
|n09op59-3_02|     207|   483|1.0.0   |Markus Neuwirth|         |
|n09op59-3_03|      96|   177|1.0.0   |Markus Neuwirth|         |
|n09op59-3_04|     428|   699|1.0.0   |Markus Neuwirth|         |
|n10op74_01  |     262|   446|1.0.0   |Markus Neuwirth|         |
|n10op74_02  |     169|   304|1.0.0   |Markus Neuwirth|         |
|n10op74_03  |     467|   447|1.0.0   |Markus Neuwirth|         |
|n10op74_04  |     195|   322|1.0.0   |Markus Neuwirth|         |
|n11op95_01  |     151|   245|1.0.0   |Markus Neuwirth|         |
|n11op95_02  |     192|   353|1.0.0   |Markus Neuwirth|         |
|n11op95_03  |     207|   364|1.0.0   |Markus Neuwirth|         |
|n11op95_04  |     175|   327|1.0.0   |Markus Neuwirth|         |
|n12op127_01 |     282|   558|1.0.0   |Markus Neuwirth|         |
|n12op127_02 |     126|   542|1.0.0   |Markus Neuwirth|         |
|n12op127_03 |     289|   430|1.0.0   |Markus Neuwirth|         |
|n12op127_04 |     299|   689|1.0.0   |Markus Neuwirth|         |
|n13op130_01 |     236|   723|1.0.0   |Markus Neuwirth|         |
|n13op130_02 |     107|   186|1.0.0   |Markus Neuwirth|         |
|n13op130_03 |      89|   450|1.0.0   |Markus Neuwirth|         |
|n13op130_04 |     150|   295|1.0.0   |Markus Neuwirth|         |
|n13op130_05 |      66|   189|1.0.0   |Markus Neuwirth|         |
|n13op130_06 |     498|   631|1.0.0   |Markus Neuwirth|         |
|n14op131_01 |     120|   334|1.0.0   |Markus Neuwirth|         |
|n14op131_02 |     197|   354|1.0.0   |Markus Neuwirth|         |
|n14op131_03 |      10|    30|1.0.0   |Markus Neuwirth|         |
|n14op131_04 |     277|   657|1.0.0   |Markus Neuwirth|         |
|n14op131_05 |     499|   599|1.0.0   |Markus Neuwirth|         |
|n14op131_06 |      27|    68|1.0.0   |Markus Neuwirth|         |
|n14op131_07 |     387|   523|1.0.0   |Markus Neuwirth|         |
|n15op132_01 |     264|   622|1.0.0   |Markus Neuwirth|         |
|n15op132_02 |     246|   479|1.0.0   |Markus Neuwirth|         |
|n15op132_03 |     211|   506|1.0.0   |Markus Neuwirth|         |
|n15op132_04 |      46|   113|1.0.0   |Markus Neuwirth|         |
|n15op132_05 |     404|   715|1.0.0   |Markus Neuwirth|         |
|n16op135_01 |     193|   398|1.0.0   |Markus Neuwirth|         |
|n16op135_02 |     274|   376|1.0.0   |Markus Neuwirth|         |
|n16op135_03 |      54|   178|1.0.0   |Markus Neuwirth|         |
|n16op135_04 |     283|   562|1.0.0   |Markus Neuwirth|         |
