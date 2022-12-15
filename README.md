<!-- TOC -->
* [ABC - The Annotated Beethoven Corpus (v2.0)](#abc---the-annotated-beethoven-corpus--v20-)
  * [Publications](#publications)
  * [Version 2.0](#version-20)
    * [Upgrade to MuseScore 3](#upgrade-to-musescore-3)
    * [New folder and file structure](#new-folder-and-file-structure)
    * [Changes to the data](#changes-to-the-data)
  * [Remarks](#remarks)
* [Overview](#overview)
<!-- TOC -->

![Version](https://img.shields.io/github/v/release/DCMLab/ABC?display_name=tag)
[![DOI](https://zenodo.org/badge/127907867.svg)](https://zenodo.org/badge/latestdoi/127907867)
![GitHub repo size](https://img.shields.io/github/repo-size/DCMLab/ABC)
![License](https://img.shields.io/badge/license-CC%20BY--NC--SA%204.0-9cf)

# ABC - The Annotated Beethoven Corpus (v2.0)

The ABC dataset consists of expert harmonic analyses of all Beethoven string quartets 
(opp. 18, 59, 74, 95, 127, 130, 131, 132, 135, composed between 1800 and 1826), encoded in a human- and 
machine-readable format (MuseScore format). 
Using a modified Roman Numeral notation (the [DCML harmony annotation standard](https://github.com/DCMLab/standards)), 
the dataset includes the common music-theoretical set of harmonic features such as key, chordal root, 
chord inversion, chord extensions, suspensions, and others.

**A full diff of all changes applied with version 2.0 can be seen [here](https://github.com/DCMLab/ABC/commit/8bd699a9b5b00dba3214c6626575f8368279b965).** 

## Publications

* The accompanying Data Report has been published in [Neuwirth, M., Harasim, D., Moss, F. & Rohrmeier M. (2018)](https://www.frontiersin.org/articles/10.3389/fdigh.2018.00016/full).
* An evaluation of the dataset can be found in  this [Moss, F., Neuwirth M., Harasim, D. & Rohrmeier, M. (2019)](https://doi.org/10.1371/journal.pone.0217242).
* The latest version of the annotation standard has been described in [Hentschel, J., Neuwirth, M. & Rohrmeier, M. (2021)](http://doi.org/10.5334/tismir.63 )  

## Version 2.0

4.5 years after its first publication (see below), this is the first revised version of the ABC. 
In the meantime, the [DCML corpus initiative](https://www.epfl.ch/labs/dcml/projects/corpus-project/) has advanced
and this update has as a main goal to harmonize the ABC with all other annotated corpora that have been and
will be published. This includes the following changes:

### Upgrade to MuseScore 3

* All scores have been converted to [MuseScore](https://musescore.org/download) 3.6.2 format and can be found in the folder `MS3`.
* The harmony labels have been moved to MuseScore's "Roman Numeral Analysis" layer of the left-hand staff.

### New folder and file structure

* The `code` folder was removed since the old Julia code has been replaced by the Python library [ms3](https://pypi.org/project/ms3/).
* The MuseScore files are contained in `MS3` and for each movement there are a couple of other files available, identified by their file names:
  * The folder `notes` contains one TSV file per movement with all note heads (not every note head represents an onset).
  * The folder `measures` contains one TSV file per movement with all measure-like units 
  * The folder `harmonies` contains one TSV file per movement with all harmony annotation labels
  * The folder `reviewed` contains two files per movement:
    * A copy of the score where all out-of-label notes have been colored in red; additionally, modified labels ( w.r.t. v1.0) are shown in these files in a diff-like manner (removed in red, added in green).
    * A copy of the harmonies TSV with six added columns that reflect the coloring of out-of-label notes ("coloring reports")
  * The file `warnings.log` lists those labels where over 60 % of notes within the label's segment are not expressed
    by the label. Potentially, most of them are semantically incorrect. 

The folders are automatically kept up to date by the [dcml_corpus_workflow](https://github.com/DCMLab/dcml_corpus_workflow)
which calls the command `ms3 review -M -N -X -D` on every change.

Information on what the columns in the TSV files contain can be found in the [documentation for ms3](https://johentsch.github.io/ms3/columns).

### Changes to the data

**A full diff of all changes applied with version 2.0 can be seen [here](https://github.com/DCMLab/ABC/commit/8bd699a9b5b00dba3214c6626575f8368279b965).**

* The scores have been aligned by [tunescribers.com](https://tunescribers.com/) with the Henle and Breitkopf editions
  provided in the `pdf` folder and indicated in its README.
* Systematic changes to the harmony labels:
  * With the harmony labels moved to the Roman Numeral Analysis layer, no initial `.` are needed anymore.
  * `V9` is not part of the DCML harmony annotation standard and has been replaced by `V7(9)` or `V7(+9)`.
  * Corrected `vii` chords in major keys that had often been wrongly labeled as `#vii`.
* Obvious errors have been corrected in many places. Thanks to @craigsapp, @lancioni, @malcolmsailor, @MarkGotham, @napulen and @tymoczko
  for reporting quite a few of them!

## Remarks

**Hybrid version of annotations**

v1.0 of this dataset used version 1.0.0 of the [DCML harmony annotation standard](https://github.com/DCMLab/standards),
with the version number attributed only in hindsight. Some of the labels that were corrected in the meantime, however,
use features available only in later versions, such as recursive reference to a secondary ('tertiary') key as in `V7/V/V`.
However, changes have been applied conservatively in order to keep the data as homogeneous as possible.

**Possible annotation errors**

While the annotation process (as detailed in the Data Report) was conducted very carefully, and all annotated symbols have been automatically checked for syntactic correctness, the authors cannot entirely rule out the possibility of typograpical errors or misinterpretations (e.g., due to ambiguities in the score or underspecification in the musical texture). After all, music analysis is not a deterministic process but involves interpretation. If you encounter anything that seems not right to you, please create an issue [here](https://github.com/DCMLab/ABC/issues).

**Missing bars**

The original XML file for Op. 132 No. 15, mov. 5 from Project Gutenberg did not contain measures 194-241. We added them manually.


# Overview
| file_name  |measures|labels|standard|  annotators   |reviewers |
|------------|-------:|-----:|--------|---------------|----------|
|n01op18-1_01|     313|   405|1.0.0   |Markus Neuwirth|          |
|n01op18-1_02|     110|   263|1.0.0   |Markus Neuwirth|          |
|n01op18-1_03|     145|   203|1.0.0   |Markus Neuwirth|          |
|n01op18-1_04|     381|   598|1.0.0   |Markus Neuwirth|          |
|n02op18-2_01|     249|   486|1.0.0   |Markus Neuwirth|          |
|n02op18-2_02|      86|   177|1.0.0   |Markus Neuwirth|          |
|n02op18-2_03|      87|   138|1.0.0   |Markus Neuwirth|          |
|n02op18-2_04|     412|   468|1.0.0   |Markus Neuwirth|          |
|n03op18-3_01|     269|   383|1.0.0   |Markus Neuwirth|          |
|n03op18-3_02|     151|   394|1.0.0   |Markus Neuwirth|          |
|n03op18-3_03|     168|   278|1.0.0   |Markus Neuwirth|          |
|n03op18-3_04|     364|   569|1.0.0   |Markus Neuwirth|          |
|n04op18-4_01|     219|   554|1.0.0   |Markus Neuwirth|          |
|n04op18-4_02|     261|   369|1.0.0   |Markus Neuwirth|          |
|n04op18-4_03|      98|   145|1.0.0   |Markus Neuwirth|          |
|n04op18-4_04|     217|   386|1.0.0   |Markus Neuwirth|          |
|n05op18-5_01|     225|   430|1.0.0   |Markus Neuwirth|          |
|n05op18-5_02|     105|   168|1.0.0   |Markus Neuwirth|          |
|n05op18-5_03|     139|   247|1.0.0   |Markus Neuwirth|          |
|n05op18-5_04|     300|   567|1.0.0   |Markus Neuwirth|          |
|n06op18-6_01|     264|   374|1.0.0   |Markus Neuwirth|          |
|n06op18-6_02|      79|   265|1.0.0   |Markus Neuwirth|          |
|n06op18-6_03|      68|   168|1.0.0   |Markus Neuwirth|          |
|n06op18-6_04|     296|   464|1.0.0   |Markus Neuwirth|          |
|n07op59-1_01|     400|   482|1.0.0   |Markus Neuwirth|          |
|n07op59-1_02|     476|   635|1.0.0   |Markus Neuwirth|          |
|n07op59-1_03|     132|   374|1.0.0   |Markus Neuwirth|          |
|n07op59-1_04|     327|   605|1.0.0   |Markus Neuwirth|          |
|n08op59-2_01|     255|   445|1.0.0   |Markus Neuwirth|          |
|n08op59-2_02|     157|   326|1.0.0   |Markus Neuwirth|          |
|n08op59-2_03|     134|   262|1.0.0   |Markus Neuwirth|          |
|n08op59-2_04|     409|   567|1.0.0   |Markus Neuwirth|          |
|n09op59-3_01|     269|   515|1.0.0   |Markus Neuwirth|          |
|n09op59-3_02|     207|   481|1.0.0   |Markus Neuwirth|          |
|n09op59-3_03|      96|   177|1.0.0   |Markus Neuwirth|          |
|n09op59-3_04|     428|   699|1.0.0   |Markus Neuwirth|          |
|n10op74_01  |     262|   446|1.0.0   |Markus Neuwirth|          |
|n10op74_02  |     169|   304|1.0.0   |Markus Neuwirth|          |
|n10op74_03  |     467|   447|1.0.0   |Markus Neuwirth|          |
|n10op74_04  |     195|   322|1.0.0   |Markus Neuwirth|          |
|n11op95_01  |     151|   245|1.0.0   |Markus Neuwirth|          |
|n11op95_02  |     192|   353|1.0.0   |Markus Neuwirth|          |
|n11op95_03  |     207|   364|1.0.0   |Markus Neuwirth|          |
|n11op95_04  |     175|   326|1.0.0   |Markus Neuwirth|          |
|n12op127_01 |     282|   558|1.0.0   |Markus Neuwirth|          |
|n12op127_02 |     126|   542|1.0.0   |Markus Neuwirth|          |
|n12op127_03 |     289|   428|1.0.0   |Markus Neuwirth|          |
|n12op127_04 |     299|   689|1.0.0   |Markus Neuwirth|          |
|n13op130_01 |     236|   723|1.0.0   |Markus Neuwirth|          |
|n13op130_02 |     107|   181|1.0.0   |Markus Neuwirth|          |
|n13op130_03 |      89|   450|1.0.0   |Markus Neuwirth|          |
|n13op130_04 |     150|   295|1.0.0   |Markus Neuwirth|          |
|n13op130_05 |      66|   189|1.0.0   |Markus Neuwirth|          |
|n13op130_06 |     493|   626|1.0.0   |Markus Neuwirth|          |
|n14op131_01 |     120|   334|1.0.0   |Markus Neuwirth|          |
|n14op131_02 |     197|   354|1.0.0   |Markus Neuwirth|          |
|n14op131_03 |      10|    30|1.0.0   |Markus Neuwirth|          |
|n14op131_04 |     276|   659|1.0.0   |Markus Neuwirth|          |
|n14op131_05 |     499|   599|1.0.0   |Markus Neuwirth|          |
|n14op131_06 |      27|    68|1.0.0   |Markus Neuwirth|          |
|n14op131_07 |     387|   522|1.0.0   |Markus Neuwirth|          |
|n15op132_01 |     264|   622|1.0.0   |Markus Neuwirth|          |
|n15op132_02 |     238|   479|1.0.0   |Markus Neuwirth|          |
|n15op132_03 |     211|   506|1.0.0   |Markus Neuwirth|          |
|n15op132_04 |      46|   113|1.0.0   |Markus Neuwirth|          |
|n15op132_05 |     404|   732|1.0.0   |Markus Neuwirth|JH (1.0.0)|
|n16op135_01 |     193|   398|1.0.0   |Markus Neuwirth|          |
|n16op135_02 |     272|   376|1.0.0   |Markus Neuwirth|          |
|n16op135_03 |      54|   178|1.0.0   |Markus Neuwirth|          |
|n16op135_04 |     282|   562|1.0.0   |Markus Neuwirth|          |


*Overview table updated using [ms3](https://johentsch.github.io/ms3/) 1.0.2.*
