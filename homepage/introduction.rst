**********
How to use
**********

.. contents:: Contents
   :local:

Getting the data
================

With full version history
-------------------------

The dataset is version-controlled via `git <https://git-scm.com/>`__. In order to download the files with all revisions they have gone through, git needs to be installed on your machine.
Then you can clone this repository using the command

.. code:: bash


   git clone https://github.com/DCMLab/ABC.git


Without full version history
----------------------------


If you are only interested in the current version of the corpus, you can download and unpack:

* `The Annotated Beethoven Corpus (ABC) <https://github.com/DCMLab/ABC/archive/refs/heads/main.zip>`__


Data Formats
============

Each piece in this corpus is represented by five files with identical names, each in its own folder. For example, the first movement of the first quartet, op. 18/1, has the following files:

-  ``MS3/n01op18-1_01.mscx``: Uncompressed MuseScore 3.6.2 file including the music and annotation labels.
-  ``notes/n01op18-1_01.notes.tsv``: A table of all note heads contained in the score and their relevant features (not each of them represents an onset, some are tied together)
-  ``measures/n01op18-1_01.measures.tsv``: A table with relevant information about the measures in the score.
-  ``chords/n01op18-1_01.chords.tsv``: A table containing layer-wise unique onset positions with the musical markup (such as dynamics, articulation, lyrics, figured bass, etc.).
-  ``harmonies/n01op18-1_01.harmonies.tsv``: A table of the included harmony labels (including cadences and phrases) with their positions in the score.

Opening Scores
--------------

After navigating to your local copy, you can open the scores in the folder ``MS3`` with the free and open source score editor `MuseScore <https://musescore.org>`__. Please note that the scores have been edited, annotated and tested with `MuseScore 3.6.2 <https://github.com/musescore/MuseScore/releases/tag/v3.6.2>`__. MuseScore 4 has since been released and preliminary tests suggest that it renders them correctly.

Opening TSV files in a spreadsheet
----------------------------------

Tab-separated value (TSV) files are like Comma-separated value (CSV) files and can be opened with most modern text editors. However, for correctly displaying the columns, you might want to use a spreadsheet or an addon for your favourite text editor. When you use a spreadsheet such as Excel, it might annoy you by interpreting fractions as dates. This can be circumvented by using ``Data --> From Text/CSV`` or the free alternative `LibreOffice Calc <https://www.libreoffice.org/download/download/>`__. Other than that, TSV data can be loaded with every modern programming language.

Loading TSV files in Python
---------------------------

Since the TSV files contain null values, lists, fractions, and numbers that are to be treated as strings, you may want to use this code to load any TSV files related to this repository (provided you’re doing it in Python). After a quick ``pip install -U ms3`` (requires Python 3.10) you’ll be able to load any TSV like this:

.. code:: python

   import ms3

   labels = ms3.load_tsv('harmonies/n01op18-1_01.tsv')
   notes = ms3.load_tsv('notes/n01op18-1_01.tsv')

How to read ``metadata.tsv``
============================

This section explains the meaning of the columns contained in ``metadata.tsv``.

File information
----------------

+------------------------+------------------------------------------------------------+
| column                 | content                                                    |
+========================+============================================================+
| **fname**              | name without extension (for referencing related files)     |
+------------------------+------------------------------------------------------------+
| **rel_path**           | relative file path of the score, including extension       |
+------------------------+------------------------------------------------------------+
| **subdirectory**       | folder where the score is located                          |
+------------------------+------------------------------------------------------------+
| **last_mn**            | last measure number                                        |
+------------------------+------------------------------------------------------------+
| **last_mn_unfolded**   | number of measures when playing all repeats                |
+------------------------+------------------------------------------------------------+
| **length_qb**          | length of the piece, measured in quarter notes             |
+------------------------+------------------------------------------------------------+
| **length_qb_unfolded** | length of the piece when playing all repeats               |
+------------------------+------------------------------------------------------------+
| **volta_mcs**          | measure counts of first and second endings                 |
+------------------------+------------------------------------------------------------+
| **all_notes_qb**       | summed up duration of all notes, measured in quarter notes |
+------------------------+------------------------------------------------------------+
| **n_onsets**           | number of note onsets                                      |
+------------------------+------------------------------------------------------------+
| **n_onset_positions**  | number of unique note onsets (“slices”)                    |
+------------------------+------------------------------------------------------------+

Composition information
-----------------------

+--------------------+---------------------------+
| column             | content                   |
+====================+===========================+
| **composer**       | composer name             |
+--------------------+---------------------------+
| **workTitle**      | work title                |
+--------------------+---------------------------+
| **composed_start** | earliest composition date |
+--------------------+---------------------------+
| **composed_end**   | latest composition date   |
+--------------------+---------------------------+
| **workNumber**     | Catalogue number(s)       |
+--------------------+---------------------------+
| **movementNumber** | 1, 2, or 3                |
+--------------------+---------------------------+
| **movementTitle**  | title of the movement     |
+--------------------+---------------------------+

Score information
-----------------

+-----------------+--------------------------------------------------------+
| column          | content                                                |
+=================+========================================================+
| **label_count** | number of chord labels                                 |
+-----------------+--------------------------------------------------------+
| **KeySig**      | key signature(s) (negative = flats, positive = sharps) |
+-----------------+--------------------------------------------------------+
| **TimeSig**     | time signature(s)                                      |
+-----------------+--------------------------------------------------------+
| **musescore**   | MuseScore version                                      |
+-----------------+--------------------------------------------------------+
| **source**      | URL to the first typesetter’s file                     |
+-----------------+--------------------------------------------------------+
| **typesetter**  | first typesetter                                       |
+-----------------+--------------------------------------------------------+
| **annotators**  | creator(s) of the chord labels                         |
+-----------------+--------------------------------------------------------+
| **reviewers**   | reviewer(s) of the chord labels                        |
+-----------------+--------------------------------------------------------+

Identifiers
-----------

These columns provide a mapping between multiple identifiers for the sonatas (not for individual movements).

+-----------------+------------------------------------------------------------------------------------------------------------+
| column          | content                                                                                                    |
+=================+============================================================================================================+
| **wikidata**    | URL of the `WikiData <https://www.wikidata.org/>`__ item                                                   |
+-----------------+------------------------------------------------------------------------------------------------------------+
| **viaf**        | URL of the Virtual International Authority File (`VIAF <http://viaf.org/>`__) entry                        |
+-----------------+------------------------------------------------------------------------------------------------------------+
| **musicbrainz** | `MusicBrainz <https://musicbrainz.org/>`__ identifier                                                      |
+-----------------+------------------------------------------------------------------------------------------------------------+
| **imslp**       | URL to the wiki page within the International Music Score Library Project (`IMSLP <https://imslp.org/>`__) |
+-----------------+------------------------------------------------------------------------------------------------------------+

Generating all TSV files from the scores
========================================

When you have made changes to the scores and want to update the TSV files accordingly, you can use the following command (provided you have pip-installed `ms3 <https://github.com/johentsch/ms3>`__):

.. code:: python

   ms3 extract -M -N -X -F -D # for measures, notes, expanded harmony labels, form labels, and metadata

If, in addition, you want to generate the reviewed scores with out-of-label notes colored in red, you can do

.. code:: python

   ms3 review -M -N -X -F -D # for extracting measures, notes, expanded harmony labels, form labels, and metadata

By adding the flag ``-c`` to the review command, it will additionally compare the (potentially modified) annotations in the score with the ones currently present in the harmonies TSV files and reflect the comparison in the reviewed scores.

Questions, Suggestions, Corrections, Bug Reports
================================================

For questions, remarks etc., please `create an issue <https://github.com/DCMLab/ABC/issues>`__ and feel free to fork and submit pull requests.

License
=======

Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License (`CC BY-NC-SA 4.0 <https://creativecommons.org/licenses/by-nc-sa/4.0/>`__).