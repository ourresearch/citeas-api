#!/usr/bin/python
 # -*- coding: utf-8 -*-

import pytest
import requests_cache

from software import Software

requests_cache.install_cache('my_requests_cache', expire_after=60*60*24*7)  # expire_after is in seconds

# run tests with pytest
# Use harvard1 citation style

arxiv_urls = [
    ("arXiv:1802.02689", "Borgman, C., Scharnhorst, A. & Golshan, M., 2018. Digital Data Archives as Knowledge Infrastructures: Mediating Data Sharing and Reuse. <i>arXiv</i>. Available at: http://arxiv.org/abs/1802.02689v2.")
]

cran_urls = [
    ("CRAN.R-project.org/package=surveillance", "Salmon, M., Schumacher, D. & H\xf6hle, M., 2016. Monitoring Count Time Series inR: Aberration Detection in Public Health Surveillance. <i>Journal of Statistical Software</i>, 70(10). Available at: https://doi.org/10.18637/jss.v070.i10."),
    ("CRAN.R-project.org/package=changepoint", "Killick, R., Haynes, K. & Eckley, I., 2016. changepoint: Methods for Changepoint Detection. <i>R package version 2.2.2</i>. Available at: https://CRAN.R-project.org/package=changepoint."),
    ("CRAN.R-project.org/package=tidyverse", "Wickham, H. et al., 2019. Welcome to the Tidyverse. <i>Journal of Open Source Software</i>, 4(43), p.1686. Available at: https://doi.org/10.21105/joss.01686."),
    ("https://cran.r-project.org/web/packages/BDP2/", "Kopp-Schneider, A., Wiesenfarth, M. & Abel, U., 2018. BDP2: Bayesian Adaptive Designs for Phase II Trials with Binary. <i>R package version 0.1.3</i>. Available at: https://CRAN.R-project.org/package=BDP2."),
    ("https://cran.r-project.org/web/packages/vistime/index.html", "Raabe, S., 2020. vistime: Pretty Timelines. <i>R package version 1.0.0</i>. Available at: https://CRAN.R-project.org/package=vistime."),
    ("https://cran.r-project.org/web/packages/afCEC/index.html", "Byrski, K., 2018. afCEC: Active Function Cross-Entropy Clustering. <i>R package version 1.0.2</i>. Available at: https://CRAN.R-project.org/package=afCEC."),
    ("http://cran.r-project.org/package=abcrf", "Marin, J.-M., 2019. abcrf: Approximate Bayesian Computation via Random Forests. <i>R package version 1.8.1</i>. Available at: https://CRAN.R-project.org/package=abcrf."),
]

doi_urls = [
    ("1807.09464", "Duchene, J. et al., 2018. Specification-Based Protocol Obfuscation. <i>arXiv</i>. Available at: http://arxiv.org/abs/1807.09464v1."),
]

github_urls = [
    ("https://github.com/pvlib/pvlib-python", "Holmgren, W. et al., 2020. pvlib/pvlib-python: v0.7.2. Available at: https://doi.org/10.5281/zenodo.3762635."),
    ("https://github.com/gcowan/hyperk", "Cowan, G., 2016. Gcowan/Hyperk: Mcp Data Processing Code. Available at: https://doi.org/10.5281/zenodo.160400."),
    ("https://github.com/NSLS-II-XPD/xpdView", "Duff, C. & Kaming-Thanassi, J., 2016. Xpdview: Xpdview Initial Release. Available at: https://doi.org/10.5281/zenodo.60479."),
    ("https://github.com/impactstory/depsy", "Research, O., 2015. depsy. Available at: https://github.com/ourresearch/depsy."),
    ("https://github.com/abianchetti/blick", "Bianchetti, A., 2012. blick. Available at: https://github.com/abianchetti/blick."),
    ("https://github.com/jasonpriem/FeedVis", "Priem, J., 2011. FeedVis. Available at: https://github.com/jasonpriem/FeedVis."),
    ("https://github.com/vahtras/loprop", 'Vahtras, O., 2014. Loprop For Dalton. Available at: https://doi.org/10.5281/zenodo.13276.'),
    ("https://github.com/cvitolo/r_BigDataAnalytics", 'Vitolo, C., 2015. R_Bigdataanalytics V.0.0.1. Available at: https://doi.org/10.5281/zenodo.15722.'),
    ("https://github.com/dfm/emcee", 'Foreman-Mackey, D. et al., 2013. emcee: The MCMC Hammer. <i>Publications of the Astronomical Society of the Pacific</i>, 125(925), pp.306\u2013312. Available at: https://doi.org/10.1086/670067.'),
    ("https://github.com/robintw/Py6S", 'Wilson, R.T., 2013. Py6S: A Python interface to the 6S radiative transfer model. <i>Computers & Geosciences</i>, 51, pp.166–171. Available at: https://doi.org/10.1016/j.cageo.2012.08.002.'),
    ("https://github.com/nicholasricci/DDM_Framework", "Marzolla, M., D'Angelo, G. & Mandrioli, M., 2013. A Parallel Data Distribution Management Algorithm."),
    # ("https://gist.github.com/rxaviers/7360908", "Anon, Complete list of github markdown emoji markup · GitHub. Available at: https://gist.github.com/rxaviers/7360908."),
]

website_urls = [
    ("http://yt-project.org", "Turk, M.J. et al., 2010. Yt: A Multi-Code Analysis Toolkit For Astrophysical Simulation Data. <i>The Astrophysical Journal Supplement Series</i>, 192(1), p.9. Available at: https://doi.org/10.1088/0067-0049/192/1/9."),
    ("http://fftw.org/", "Frigo, M. & Johnson, S.G., 2005. The Design and Implementation of FFTW3. <i>Proceedings of the IEEE</i>, 93(2), pp.216–231. Available at: https://doi.org/10.1109/jproc.2004.840301."),
    ("www.simvascular.org", " 2015. SimVascular. Available at: https://github.com/SimVascular/SimVascular."),
    ("https://bioconductor.org/packages/release/bioc/html/edgeR.html", "Yunshun Chen <Yuchen@Wehi.Edu.Au>, A., Davis McCarthy <Dmccarthy@Wehi.Edu.Au>, Xiaobei Zhou <Xiaobei.Zhou@Uzh.Ch>, Mark Robinson<Mark.Robinson@Imls.Uzh.Ch>, Gordon Smyth <Smyth@Wehi.Edu.Au>, 2017. edgeR. Available at: https://doi.org/10.18129/b9.bioc.edger."),
    ("https://slicer.org/", "Punzo, D., 2015. SlicerAstro. Available at: https://github.com/Punzo/SlicerAstro."),
    ("https://vhub.org/resources/puffin", "Bursik, M.I. et al., 2013. puffin. Available at: https://vhub.org/resources/puffin."),
    ("https://ccdproc.readthedocs.io/en/latest/", "Craig, M. et al., 2017. Astropy/Ccdproc: V1.3.0.Post1. Available at: https://doi.org/10.5281/zenodo.1069648."),
    ("https://photutils.readthedocs.io/", "Bradley, L. et al., 2019. astropy/photutils: v0.7.2. Available at: https://doi.org/10.5281/zenodo.596036."),
    ("https://www.thelancet.com/journals/laninf/article/PIIS1473-3099(20)30120-1/fulltext", "Dong, E., Du, H. & Gardner, L., 2020. An interactive web-based dashboard to track COVID-19 in real time. <i>The Lancet Infectious Diseases</i>, 20(5), pp.533–534. Available at: https://doi.org/10.1016/s1473-3099(20)30120-1.")
]

urls_to_test = arxiv_urls + cran_urls + doi_urls + github_urls + website_urls


@pytest.mark.parametrize("url,expected", urls_to_test)
def test_citations(url, expected):
    my_software = Software(url)
    my_software.find_metadata()
    assert my_software.citation_plain == expected
