#!/usr/bin/python
 # -*- coding: utf-8 -*-

import unittest
from nose.tools import assert_equals
from ddt import ddt, data
import requests_cache

from software import Software

requests_cache.install_cache('my_requests_cache', expire_after=60*60*24*7)  # expire_after is in seconds

# run it like this:
# nosetests --processes=10 test/

test_urls = [
    ("http://cnn.com", "", u'Anon, CNN - Breaking News, Latest News and Videos. Available at: http://cnn.com.'),
    ("https://github.com/pvlib/pvlib-python", "10.5281/zenodo.1420548", "Holmgren, W. et al., 2018. Pvlib/Pvlib-Python: V0.6.0. Available at: https://doi.org/10.5281/zenodo.1420548."),
    ("https://github.com/gcowan/hyperk", "10.5281/zenodo.160400", "Cowan, G., 2016. Gcowan/Hyperk: Mcp Data Processing Code. Available at: https://doi.org/10.5281/zenodo.160400."),
    ("https://github.com/NSLS-II-XPD/xpdView", "10.5281/zenodo.60479", "Duff, C. & Kaming-Thanassi, J., 2016. Xpdview: Xpdview Initial Release. Available at: https://doi.org/10.5281/zenodo.60479."),
    ("https://github.com/impactstory/depsy", "", "Impactstory, 2015. depsy. Available at: https://github.com/Impactstory/depsy."),
    ("https://github.com/abianchetti/blick", "", u"Bianchetti, A., 2012. <i>Determinación del diámetro pupilar ocular en tiempo real</i>."),
    ("https://github.com/jasonpriem/FeedVis", "", u"Priem, J., 2011. FeedVis. Available at: https://github.com/jasonpriem/FeedVis."),
    ("https://github.com/vahtras/loprop", "", u'Vahtras, O., 2014. Loprop For Dalton. Available at: https://doi.org/10.5281/zenodo.13276.'),
    ("https://github.com/cvitolo/r_BigDataAnalytics", "", u'Vitolo, C., 2015. R_Bigdataanalytics V.0.0.1. Available at: https://doi.org/10.5281/zenodo.15722.'),
    ("https://github.com/nicholasricci/DDM_Framework", "", u"Marzolla, M., D'Angelo, G. & Mandrioli, M., 2013. A Parallel Data Distribution Management Algorithm."),
    ("http://yt-project.org", "", u"Turk, M.J. et al., 2010. Yt: A Multi-Code Analysis Toolkit For Astrophysical Simulation Data. <i>The Astrophysical Journal Supplement Series</i>, 192(1), p.9. Available at: https://doi.org/10.1088/0067-0049/192/1/9."),
    ("https://github.com/dfm/emcee", "", u'Foreman-Mackey, D. et al., 2013. emcee: The MCMC Hammer. <i>Publications of the Astronomical Society of the Pacific</i>, 125(925), pp.306\u2013312. Available at: https://doi.org/10.1086/670067.'),
    ("https://github.com/robintw/Py6S", "", u'Wilson, R.T., 2013. Py6S: A Python interface to the 6S radiative transfer model. <i>Computers & Geosciences</i>, 51, pp.166–171. Available at: https://doi.org/10.1016/j.cageo.2012.08.002.'),
    ("http://fftw.org/", "", u'Frigo, M. & Johnson, S.G., 2005. The Design and Implementation of FFTW3. <i>Proceedings of the IEEE</i>, 93(2), pp.216–231. Available at: https://doi.org/10.1109/jproc.2004.840301.'),
    ("www.simvascular.org", "", u' 2015. SimVascular. Available at: https://github.com/SimVascular/SimVascular.'),
    ("arXiv:1802.02689", "", u'Borgman, C., Scharnhorst, A. & Golshan, M., 2018. Digital Data Archives as Knowledge Infrastructures: Mediating Data Sharing and Reuse. <i>arXiv</i>. Available at: http://arxiv.org/abs/1802.02689v2.'),
    ("https://bioconductor.org/packages/release/bioc/html/edgeR.html", "", u'Yunshun Chen <Yuchen@Wehi.Edu.Au>, A., Davis McCarthy <Dmccarthy@Wehi.Edu.Au>, Xiaobei Zhou <Xiaobei.Zhou@Uzh.Ch>, Mark Robinson<Mark.Robinson@Imls.Uzh.Ch>, Gordon Smyth <Smyth@Wehi.Edu.Au>, 2017. edgeR. Available at: https://doi.org/10.18129/b9.bioc.edger.'),
    ("https://slicer.org/", "", u"Punzo, D., 2015. SlicerAstro. Available at: https://github.com/Punzo/SlicerAstro."),
    ("1807.09464", "", u"Duchene, J. et al., 2018. Specification-Based Protocol Obfuscation. <i>arXiv</i>. Available at: http://arxiv.org/abs/1807.09464v1."),
    ("CRAN.R-project.org/package=surveillance", "", u"Paul, M. et al., 2018. surveillance: Temporal and Spatio-Temporal Modeling and Monitoring of Epidemic. <i>R package version 1.16.2</i>. Available at: https://CRAN.R-project.org/package=surveillance."),
    ("CRAN.R-project.org/package=changepoint", "", u"Haynes, K., Eckley, I. & Fearnhead, P., 2016. changepoint: Methods for Changepoint Detection. <i>R package version 2.2.2</i>. Available at: https://CRAN.R-project.org/package=changepoint."),
    ("CRAN.R-project.org/package=tidyverse", "", "Wickham, H. & RStudio, 2017. tidyverse: Easily Install and Load the 'Tidyverse'. <i>R package version 1.2.1</i>. Available at: https://CRAN.R-project.org/package=tidyverse.")

    # getting the number and page wrong at the moment
    # ("http://yt-project.org", "", "Turk, M.J. et al., 2010. Yt: A Multi-Code Analysis Toolkit For Astrophysical Simulation Data. The Astrophysical Journal Supplement Series, 192(1), p.9. Available at: http://dx.doi.org/10.1088/0067-0049/192/1/9."),

    # bug.  doesn't include the proceedings title at the moment.
    # ("https://github.com/nicholasricci/DDM_Framework", "", u"Marzolla, M., D'Angelo, G. & Mandrioli, M., 2014. A Parallel Data Distribution Management Algorithm. In Proc. IEEE/ACM International Symposium on Distributed Simulation and Real Time Applications (DS-RT 2013).  Delft, the Netherlands."),

    # ("https://github.com/alvarag/LSH-IS", "", u'Arnaiz-Gonz\xe1lez, \xc1. et al., 2016. Instance selection of linear complexity for big data. Knowledge-Based Systems, 107, pp.83\u201395.'),
    # ("https://github.com/sanger-pathogens/mlst_check", "", """"Multilocus sequence typing by blast from de novo assemblies against PubMLST", Andrew J. Page, Ben Taylor, Jacqueline A. Keane, The Journal of Open Source Software, (2016). doi: http://dx.doi.org/10.21105/joss.00118"""),
    # ("https://github.com/AndrasHartmann/rtfractools", "", "Hartmann, A., Mukli, P., Nagy, Z., Kocsis, L., Hermán, P., & Eke, A. (2013). Real-time fractal signal processing in the time domain. Physica A: Statistical Mechanics and Its Applications, 392(1), 89–102. doi:10.1016/j.physa.2012.08.002"),
    # ("https://github.com/magitz/1001", "", "Mavrodiev EV. (2015) 1001 - A tool for binary representations of unordered multistate characters (with examples from genomic data) PeerJ PrePrints 3:e1403 https://dx.doi.org/10.7287/peerj.preprints.1153v1"),
    # ("https://github.com/gregmacfarlane/trucksim_disagg", "", """Macfarlane, G. and Donnelly, R. (2014). A national simulation of freight truck flows."""),
    # ("https://github.com/aimalz/chippr", "", "alz et al, in preparation\footnote{\texttt{https://github.com/aimalz/chippr}}"),
    # ("https://github.com/happynotes/NLDAS2TS", "", """PIHM Analysis Suite developed by Lele Shu, contributions by PIHM and http://www.pihm.psu.edu"""),
    ]

# We request that applications and derivative work cite this as:
# Cite this as
# If you end up using any of the code or ideas you find here in your academic research, please cite me as
# How to cite this software
# To cite this software please use the following BibTex information
# Please cite this software as
# To cite this software:
# To cite this software use:
# Please cite this software:
# Cite this software as:
# If you use this software please, cite the following paper:
# Citation: if you want to cite this software use the following bibtex entry.

@ddt
class MyTestCase(unittest.TestCase):
    _multiprocess_can_split_ = True

    @data(*test_urls)
    def test_the_urls(self, test_data):
        (url, doi, expected) = test_data
        my_software = Software(url)
        my_software.find_metadata()
        assert_equals(my_software.citation_plain, expected)

    @data(*test_urls)
    def test_the_dois(self, test_data):
        (url, doi, expected) = test_data
        if doi:
            my_software = Software(doi)
            my_software.find_metadata()
            assert_equals(my_software.citation_plain, expected)
