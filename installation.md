Installation and Usage
=====================

To install citeas-api on your local machine, clone the repository into a folder of your choice:

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