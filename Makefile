prepare:
		python setup.py sdist

upload:
		pip install twine
		twine upload dist/*
