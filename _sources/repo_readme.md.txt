![Version](https://img.shields.io/github/v/release/DCMLab/ABC?display_name=tag)
[![DOI](https://zenodo.org/badge/127907867.svg)](https://zenodo.org/badge/latestdoi/127907867)
![GitHub repo size](https://img.shields.io/github/repo-size/DCMLab/ABC)
![License](https://img.shields.io/badge/license-CC%20BY--NC--SA%204.0-9cf)


This is a README file for a data repository originating from the [DCML corpus initiative](https://github.com/DCMLab/dcml_corpora)
and serves as welcome page for both 

* the GitHub repo [https://github.com/DCMLab/ABC](https://github.com/DCMLab/ABC) and the corresponding
* documentation page [https://dcmlab.github.io/ABC](https://dcmlab.github.io/ABC)

For information on how to obtain and use the dataset, please refer to [this documentation page](https://dcmlab.github.io/ABC/introduction).


# ABC - The Annotated Beethoven Corpus (v2.4)

The ABC dataset consists of expert harmonic analyses of all Beethoven string quartets 
(opp. 18, 59, 74, 95, 127, 130, 131, 132, 135, composed between 1800 and 1826), encoded in a human- and 
machine-readable format (MuseScore format). 
Using a modified Roman Numeral notation (the [DCML harmony annotation standard](https://github.com/DCMLab/standards)), 
the dataset includes the common music-theoretical set of harmonic features such as key, chordal root, 
chord inversion, chord extensions, suspensions, and others.


## Cite as

> Neuwirth, M., Harasim, D., Moss, F. C., & Rohrmeier, M. (2018). The Annotated Beethoven Corpus (ABC): A Dataset of Harmonic Analyses of All Beethoven String Quartets. Frontiers in Digital Humanities, 5(July), 1–5. https://doi.org/10.3389/fdigh.2018.00016


## Publications

* The accompanying Data Report has been published in [Neuwirth, M., Harasim, D., Moss, F. & Rohrmeier M. (2018)](https://www.frontiersin.org/articles/10.3389/fdigh.2018.00016/full).
* An evaluation of the dataset can be found in  this [Moss, F., Neuwirth M., Harasim, D. & Rohrmeier, M. (2019)](https://doi.org/10.1371/journal.pone.0217242).
* The latest version of the annotation standard has been described in [Hentschel, J., Neuwirth, M. & Rohrmeier, M. (2021)](http://doi.org/10.5334/tismir.63 )  

## Version history

See the [GitHub releases](https://github.com/DCMLab/ABC/releases).

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

## License

Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License ([CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/)).

## File naming convention

```regex
n(?P<quartet>\d{2})  # quartet number, e.g. n01
op(?P<op>\d{2,3})    # opus number, e.g. op18
(?:-(?P<no>\d))?     # (optional) number within the opus, e.g. -1
_(?P<mvt>\d{2})      # movement number, e.g. _01
```

## Overview
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
|n06op18-6_04|     296|   465|1.0.0   |Markus Neuwirth|          |
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


*Overview table automatically updated using [ms3](https://ms3.readthedocs.io/).*