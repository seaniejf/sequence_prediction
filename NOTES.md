# ToDo

* Find a way to audit to find files that are incorrectly categorized.
* Is there a way to get a "confidence" score for each match?   (gui selects > x%)

# Design

* Caching:
	- We only need to extract documents once, but anytime the training cache changes, we need to retrain.  Split these steps?
	- If we have already have a cache file for the requested directory, do we use it?

* Avoid having to redo steps.
	- If a doc has already been reduced to a clean set of tokens, cache the set.
	- Adding a new doc should not require redoing existing docs.
	- If the cleaning changes, all docs should be reprocessed.
	- Save the model.

# ToDo

* multi-threading
	- Currently, it dives into each category and extracts text one directory at a time.
	- If we take the first directory after the training_lib path as a label, we can process the next doc no matter where it is.

* GUI
	- save settings
	- integrate with textractor
	- include file suffixes in textractor
	- set fixed widths for checkbox and category
	- Should the UI move to a dir, add keywords, or both?

* move orig docs to training_lib
	- when a file is moved, the list has to be updated.
	- if a file exists, don't overwrite it!
	- Need to associate with a person.

* Find a way to audit to find files that are incorrectly categorized.
	- Is there a way to get a "confidence" score for each match?   (gui selects > x%)
* Extra cleaning is 3min vs >1hr.
	- Estimate time?
	- Allow selection?
* Caching:
	- We only need to extract docs once, but anytime the training cache changes, we need to retrain.  Split these steps?
	- If we have already have a cache file for the requested directory, do we use it?

* Tagging
	-