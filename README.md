Backend for https://citeas.org

Run with docker
============

Run the project with docker using the following commands:

1. Download the repo: `$ git clone https://github.com/ourresearch/citeas-api.git`
2. Move into the repo directory: `$ cd citeas-api`
3. Build the docker image: `$ docker build --tag citeas-api .`
4. Run the docker image: `$ docker run -p 8000:8000 citeas-api`
5. Test the API on your local machine with: [http://0.0.0.0:8000/product/http://yt-project.org](http://0.0.0.0:8000/product/http://yt-project.org)
6. View additional citations by entering addresses or text with the following format: http://0.0.0.0:8000/product/<address or keyword>

Cool Examples
=============

- via codemeta
  - https://citeas.org/cite/https://github.com/datacite/maremma
  - https://citeas.org/cite/https://fftw.org/
- via doi
  - https://citeas.org/cite/10.5281/zenodo.160400
  - https://citeas.org/cite/https://doi.org/10.5281/zenodo.160400
- from github url to CITATION file to bibtex
  - https://citeas.org/cite/https://github.com/nicholasricci/DDM_Framework
- from webpage url to CITATION file to bibtex
  - https://citeas.org/cite/https://yt-project.org
- from github url to README to DOI
  - https://citeas.org/cite/https://github.com/CeON/CERMINE
- github metadata input, no further clues
  - https://citeas.org/cite/https://github.com/jasonpriem/FeedVis
- the same project, inputted multiple ways (github, pypi, readthedocs)
  - https://citeas.org/cite/https://github.com/xolox/python-executor
  - https://citeas.org/cite/https://pypi.python.org/pypi/executor
  - https://citeas.org/cite/https://executor.readthedocs.io/en/latest/#api-documentation
- the same project, inputted via github url or a file within github repo
  - https://citeas.org/cite/https://github.com/tidyverse/ggplot2
  - https://citeas.org/cite/https://github.com/tidyverse/ggplot2/blob/master/man/borders.Rd
- the same project, inputted via cran or a cran vignette file 
  - https://citeas.org/cite/https://cran.r-project.org/web/packages/stringr
  - https://citeas.org/cite/https://cran.r-project.org/web/packages/stringr/vignettes/stringr.html
- via arXiv ID
  - https://citeas.org/cite/arXiv:1802.02689