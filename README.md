# Yousician Music Searcher

**Programming language:**

- Python 3.9 (3.9.6)

**Dependencies:**

- Selenium 4.1.3
- WebDriverManager 3.5.4

**Configuration:**

- `pip3 install -r requirements.txt`

**Arguments:**

- `-i, --input - search input`

**Running:**

- `python3 search_music.py --input {search_input}`
- `python3 search_music.py`

Script tested on MacBook (Intel) with macOS Monterey 12.1 on browsers:

- **Google Chrome**
- **Firefox**
- **Opera**
- **Safari**

If --input argument is not passed script will ask for search input.

The script will detect installed browsers in OS and will ask to select one of them. The second request of the script
will ask to specify the path to the webdriver. These parameters are optional and can be leaved blank by pressing "Enter"
button. Script will use (1) detected browser and will download webdriver for this browser. Downloaded webdriver will be
placed in {script.dir}/.wdm