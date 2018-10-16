Backend for http://citeas.org

Installation and Usage
=====================

Clone the repository into a folder of your choice:

`$ git clone https://github.com/Impactstory/citeas-api.git`

Move into the folder

`$ cd citeas-api`

Create a virtual environment with Python 2.7:

`$ virtualenv --python=python2.7 venv`

_Note: cite-as API currently runs on Python 2.7.15, which can be downloaded and installed [here](https://www.python.org/downloads/). Virtualenv can be installed with `pip install virtualenv`._

Activate the virtual environment:

`$ source venv/bin/activate`

Install the dependencies:

`$ pip install -r requirements.txt`

Run the app with:

`$ heroku local`

The API is now available at the following URL:

`http://0.0.0.0:5000/product/`

Add a software DOI or project and view the results, such as:

`http://0.0.0.0:5000/product/10.5281/zenodo.160400`

_Note: for best results, view in an API browser such as [Postman](https://www.getpostman.com/)._

Install on Heroku
=================

To install on [heroku](https://www.heroku.com/), while in the citeas-api directory from previous steps run [heroku create](https://devcenter.heroku.com/articles/creating-apps), replacing 'my_app_name' with a unique name of your choice.

`$ heroku create my_app_name`

Then push your code to Heroku with:

`$ git push heroku master`

You can now view the previous example DOI on your Heroku app at:

`https://my_app_name.herokuapp.com/products/10.5281/zenodo.160400`

Cool Examples
=============

- via codemeta
  - http://citeas.org/cite/https://github.com/datacite/maremma
  - http://citeas.org/cite/http://fftw.org/
- via doi
  - http://citeas.org/cite/10.5281/zenodo.160400
  - http://citeas.org/cite/http://doi.org/10.5281/zenodo.160400
- from github url to CITATION file to bibtex
  - http://citeas.org/cite/https://github.com/nicholasricci/DDM_Framework
- from webpage url to CITATION file to bibtex
  - http://citeas.org/cite/http://yt-project.org
- from github url to README to DOI
  - http://citeas.org/cite/https://github.com/CeON/CERMINE
- github metadata input, no further clues
  - http://citeas.org/cite/https://github.com/jasonpriem/FeedVis
- the same project, inputted multiple ways (github, pypi, readthedocs)
  - http://citeas.org/cite/https://github.com/xolox/python-executor
  - http://citeas.org/cite/https://pypi.python.org/pypi/executor
  - http://citeas.org/cite/https://executor.readthedocs.io/en/latest/#api-documentation
- the same project, inputted via github url or a file within github repo
  - http://citeas.org/cite/https://github.com/tidyverse/ggplot2
  - http://citeas.org/cite/https://github.com/tidyverse/ggplot2/blob/master/man/borders.Rd
- the same project, inputted via cran or a cran vignette file 
  - http://citeas.org/cite/https://cran.r-project.org/web/packages/stringr
  - http://citeas.org/cite/https://cran.r-project.org/web/packages/stringr/vignettes/stringr.html
- via arXiv ID
  - http://citeas.org/cite/arXiv:1802.02689