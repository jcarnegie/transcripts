install: clean
	brew install ffmpeg
	pip install --editable .

clean:
	python setup.py clean
	rm -rf build dist .mypy_cache
	find . \
		-type f -name "*.py[co]" -delete \
		-o -type d -name __pycache__ -delete;
	find . -type d -name "*.egg-info" -exec rm -rf {} +
