ifeq ($(OS),Windows_NT)
    PYTHON=python
    ACTIVATE=.venv\Scripts\activate.bat
else
    PYTHON=python3
    ACTIVATE=. .venv/bin/activate
endif

run: .venv
	$(ACTIVATE) && pip install -r requirements.txt && $(PYTHON) main.py

.venv:
	$(PYTHON) -m venv .venv

clean:
	rm -rf .venv __pycache__