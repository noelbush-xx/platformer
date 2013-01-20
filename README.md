This is a re-implementation of [Platformer](http://platformer.org), a "political
technology" project itself very much under conceptual development, in Python,
using [Flask](http://flask.pocoo.org/).  The old, aborted, Erlang-based
implementation can be found in the
[platformer-old](https://github.com/noelbush/platformer-old) repo.

Work on this project is currently being planned and tracked
[using Pivotal](https://www.pivotaltracker.com/projects/734017).

Basic steps to get going:

	git clone https://github.com/noelbush/platformer.git
	cd platformer
	mkvirtualenv platformer
	pip install -r requirements.txt
	python src/platformer/node.py

Then go to http://localhost:5000.  You should get a *Method Not Allowed* page. :)

Run the tests:

    nosetests

So far there's a grand total of one:

	.
	----------------------------------------------------------------------
	Ran 1 test in 0.178s

	OK
