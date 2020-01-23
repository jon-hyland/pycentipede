====================================
PyCentipede - A Python word splitter
====================================

Welcome to PyCentipede, a Python-based word splitting service.

PyCentipede splits strings of contiguous characters into separate words. It
was originally used for analyzing domain names.

The service loads a custom dictionary providing the most common English words
and word pairs, each rated by occurrence frequency. Many gigabytes of written
text were analyzed from fiction and non-fiction books, articles, and other
sources in the public domain.


Usage Examples
--------------

`<http://localhost:5000/wordsplit?input=thisisatest>`_

* Returns "this is a test" in JSON format with confidence scoring and
  other metadata.

`<http://localhost:5000/wordsplit?input=somewordstosplit&output=text>`_

* Returns "some words to split" in plain text.

`<http://localhost:5000/wordsplit?input=firstquery|secondquerytosplit|thirdletsdothisright>`_

* Multiple queries can be split at once.

`<http://localhost:5000/wordsplit?input=onceuponatimeandstuff&verbosity=1>`_

* Return more metadata with verbosity=1 (Medium).

`<http://localhost:5000/wordsplit?input=onceuponatimeandstuff&verbosity=2>`_

* Return even more metadata with verbosity=2 (High).
* Shows top 5 passes by confidence score.

`<http://localhost:5000/wordsplit?input=toiletseat>`_

* Many queries are hard to split ("toilet seat" or "toilets eat").  The
  dictionary's word frequency is important, especially for pairs.

`<http://localhost:5000/wordsplit?input=thequickbrownfoxjumpsoverthelazydog>`_

* Returns "the quick brown fox jumps over the lazy dog".  Longer queries take
  exponentially longer, with configurable limits on internal passes to prevent
  overload.
* Queries are cached for quicker response, with a configurable number of max
  items.

`<http://localhost:5000/wordsplit?input=thequickbrownfoxjumpsoverthelazydog&cache=0>`_

* Disables reading from and writing to the cache, forcing split operation to
  take place.

`<http://localhost:5000/getstats>`_

* Returns service runtime statistics in JSON format.

`<http://localhost:5000/ping>`_

* Returns plain text 'Up', 'Down', or 'LoadingData' to indicate service state.
* Can be used for load balancing 'up' test.


See usage_example.py for an example of how to use PyCentipede as a stand-alone
package within an existing Python program, without the included Flask HTTP
service.


PyCentipede - Copyright (C) 2019-2020 by John Hyland.  This program comes with
ABSOLUTELY NO WARRANTY.  This is free software, and you are welcome to
redistribute it under certain conditions:
`GNU General Public License v3 <https://www.gnu.org/licenses/gpl-3.0.html>`_
