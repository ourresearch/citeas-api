#!/usr/bin/python
# -*- coding: utf-8 -*-

import pytest
import requests_cache

from software import Software

requests_cache.install_cache(
    "my_requests_cache", expire_after=60 * 60 * 24 * 7
)  # expire_after is in seconds

# run tests with pytest
# Use harvard1 citation style

arxiv_urls = [
    (
        "arXiv:1802.02689",
        "Borgman, C., Scharnhorst, A. & Golshan, M., 2018. Digital Data Archives as Knowledge Infrastructures: Mediating Data Sharing and Reuse. <i>arXiv</i>. Available at: http://arxiv.org/abs/1802.02689v2.",
    ),
    (
        "1807.09464",
        "Duchene, J. et al., 2018. Specification-Based Protocol Obfuscation. <i>arXiv</i>. Available at: http://arxiv.org/abs/1807.09464v1.",
    ),
    (
        "https://freud.readthedocs.io/en/stable/",
        "Ramasubramani, V. et al., 2020. freud: A software suite for high throughput analysis of particle simulation data. <i>Computer Physics Communications</i>, 254, p.107275. Available at: https://doi.org/10.1016/j.cpc.2020.107275.",
    ),
]

cran_urls = [
    (
        "CRAN.R-project.org/package=surveillance",
        "Salmon, M., Schumacher, D. & H\xf6hle, M., 2016. Monitoring Count Time Series inR: Aberration Detection in Public Health Surveillance. <i>Journal of Statistical Software</i>, 70(10). Available at: https://doi.org/10.18637/jss.v070.i10.",
    ),
    (
        "CRAN.R-project.org/package=changepoint",
        "Killick, R., Haynes, K. & Eckley, I., 2016. changepoint: Methods for Changepoint Detection. <i>R package version 2.2.2</i>. Available at: https://CRAN.R-project.org/package=changepoint.",
    ),
    (
        "CRAN.R-project.org/package=tidyverse",
        "Wickham, H. et al., 2019. Welcome to the Tidyverse. <i>Journal of Open Source Software</i>, 4(43), p.1686. Available at: https://doi.org/10.21105/joss.01686.",
    ),
    (
        "https://cran.r-project.org/web/packages/BDP2/",
        "Kopp-Schneider, A., Wiesenfarth, M. & Abel, U., 2018. BDP2: Bayesian Adaptive Designs for Phase II Trials with Binary. <i>R package version 0.1.3</i>. Available at: https://CRAN.R-project.org/package=BDP2.",
    ),
    (
        "https://cran.r-project.org/web/packages/vistime/index.html",
        "Raabe, S., 2021. vistime: Pretty Timelines in R. <i>R package version 1.2.1</i>. Available at: https://CRAN.R-project.org/package=vistime.",
    ),
    (
        "http://cran.r-project.org/package=abcrf",
        "Marin, J.-M., 2019. abcrf: Approximate Bayesian Computation via Random Forests. <i>R package version 1.8.1</i>. Available at: https://CRAN.R-project.org/package=abcrf.",
    ),
    (
        "https://cran.r-project.org/web/packages/stringr",
        "Hadley, W., 2019. stringr: Simple, Consistent Wrappers for Common String Operations. <i>R package version 1.4.0</i>. Available at: https://CRAN.R-project.org/package=stringr.",
    ),
]

doi_urls = [
    (
        "10.1109/5.771073",
        "Paskin, N., 1999. Toward unique identifiers. <i>Proceedings of the IEEE</i>, 87(7), pp.1208–1227. Available at: https://doi.org/10.1109/5.771073.",
    ),
    (
        "10.1093/ajae/aaq063",
        "Shi, G., Chavas, J.-. paul . & Stiegert, K., 2010. An Analysis of the Pricing of Traits in the U.S. Corn Seed Market. <i>American Journal of Agricultural Economics</i>, 92(5), pp.1324–1338. Available at: https://doi.org/10.1093/ajae/aaq063.",
    ),
]

github_urls = [
    (
        "https://github.com/pvlib/pvlib-python",
        "Holmgren, W. et al., 2020. <i>pvlib/pvlib-python: v0.7.2</i>, Zenodo. Available at: https://doi.org/10.5281/zenodo.3762635.",
    ),
    (
        "https://github.com/gcowan/hyperk",
        "Cowan, G., 2016. Gcowan/Hyperk: Mcp Data Processing Code. Available at: https://doi.org/10.5281/zenodo.160400.",
    ),
    (
        "https://github.com/NSLS-II-XPD/xpdView",
        "Duff, C. & Kaming-Thanassi, J., 2016. Xpdview: Xpdview Initial Release. Available at: https://doi.org/10.5281/zenodo.60479.",
    ),
    (
        "https://github.com/impactstory/depsy",
        "OurResearch, 2015. depsy. Available at: https://github.com/ourresearch/depsy.",
    ),
    (
        "https://github.com/abianchetti/blick",
        "Bianchetti, A., 2012. blick. Available at: https://github.com/abianchetti/blick.",
    ),
    (
        "https://github.com/jasonpriem/FeedVis",
        "Priem, J., 2011. FeedVis. Available at: https://github.com/jasonpriem/FeedVis.",
    ),
    (
        "https://github.com/vahtras/loprop",
        "Vahtras, O., 2014. Loprop For Dalton. Available at: https://doi.org/10.5281/zenodo.13276.",
    ),
    (
        "https://github.com/cvitolo/r_BigDataAnalytics",
        "Vitolo, C., 2015. R_Bigdataanalytics V.0.0.1. Available at: https://doi.org/10.5281/zenodo.15722.",
    ),
    (
        "https://github.com/dfm/emcee",
        "Foreman-Mackey, D. et al., 2013. emcee: The MCMC Hammer. <i>Publications of the Astronomical Society of the Pacific</i>, 125(925), pp.306\u2013312. Available at: https://doi.org/10.1086/670067.",
    ),
    (
        "https://github.com/robintw/Py6S",
        "Wilson, R.T., 2013. Py6S: A Python interface to the 6S radiative transfer model. <i>Computers & Geosciences</i>, 51, pp.166–171. Available at: https://doi.org/10.1016/j.cageo.2012.08.002.",
    ),
    (
        "https://github.com/nicholasricci/DDM_Framework",
        "Marzolla, M., D'Angelo, G. & Mandrioli, M., 2013. A Parallel Data Distribution Management Algorithm.",
    ),
    (
        "https://gist.github.com/vegaasen/157fbc6dce8545b7f12c",
        "Aasen, V., 2015. supress-warning-idea.md. Available at: https://gist.github.com/157fbc6dce8545b7f12c.",
    ),
    (
        "https://github.com/cboettig/noise-phenomena",
        'Boettiger, C., 2018. Cboettig/Noise-Phenomena: Supplement To: "From Noise To Knowledge: How Randomness Generates Novel Phenomena And Reveals Information". Available at: https://doi.org/10.5281/zenodo.1219780.',
    ),
    (
        "https://dbdp.org/",
        "Bent, B. et al., 2020. The digital biomarker discovery pipeline: An open-source software platform for the development of digital biomarkers using mHealth and wearables data. <i>Journal of Clinical and Translational Science</i>, 5(1). Available at: https://doi.org/10.1017/cts.2020.511.",
    ),
]

website_urls = [
    (
        "http://yt-project.org",
        "Turk, M.J. et al., 2010. Yt: A Multi-Code Analysis Toolkit For Astrophysical Simulation Data. <i>The Astrophysical Journal Supplement Series</i>, 192(1), p.9. Available at: https://doi.org/10.1088/0067-0049/192/1/9.",
    ),
    (
        "http://fftw.org/",
        "Frigo, M. & Johnson, S.G., 2005. The Design and Implementation of FFTW3. <i>Proceedings of the IEEE</i>, 93(2), pp.216–231. Available at: https://doi.org/10.1109/jproc.2004.840301.",
    ),
    (
        "www.simvascular.org",
        " 2015. SimVascular. Available at: https://github.com/SimVascular/SimVascular.",
    ),
    (
        "https://bioconductor.org/packages/release/bioc/html/edgeR.html",
        "Yunshun Chen <Yuchen@Wehi.Edu.Au>, A., Davis McCarthy <Dmccarthy@Wehi.Edu.Au>, Xiaobei Zhou <Xiaobei.Zhou@Uzh.Ch>, Mark Robinson<Mark.Robinson@Imls.Uzh.Ch>, Gordon Smyth <Smyth@Wehi.Edu.Au>, 2017. edgeR. Available at: https://doi.org/10.18129/b9.bioc.edger.",
    ),
    (
        "https://slicer.org/",
        "Punzo, D. et al., 2017. SlicerAstro: A 3-D interactive visual analytics tool for HI data. <i>Astronomy and Computing</i>, 19, pp.45–59. Available at: https://doi.org/10.1016/j.ascom.2017.03.004.",
    ),
    (
        "https://vhub.org/resources/puffin",
        "Bursik, M.I. et al., 2013. puffin. Available at: https://vhub.org/resources/puffin.",
    ),
    (
        "https://ccdproc.readthedocs.io/en/latest/",
        "Craig, M. et al., 2017. Astropy/Ccdproc: V1.3.0.Post1. Available at: https://doi.org/10.5281/zenodo.1069648.",
    ),
    (
        "https://photutils.readthedocs.io/",
        "Bradley, L. et al., 2021. <i>astropy/photutils: 1.1.0</i>, Zenodo. Available at: https://doi.org/10.5281/zenodo.596036.",
    ),
    (
        "https://www.thelancet.com/journals/laninf/article/PIIS1473-3099(20)30120-1/fulltext",
        "Dong, E., Du, H. & Gardner, L., 2020. An interactive web-based dashboard to track COVID-19 in real time. <i>The Lancet Infectious Diseases</i>, 20(5), pp.533–534. Available at: https://doi.org/10.1016/s1473-3099(20)30120-1.",
    ),
    (
        "freud.readthedocs.io",
        "Anon, freud — freud 2.6.2 documentation. Available at: http://freud.readthedocs.io.",
    ),
    (
        "nullhttps://www.nytimes.com/2021/04/22/climate/biden-emissions-target-economy.html",
        "Anon, Biden Wants to Slash Emissions. Success Would Mean a Very Different America. - The New York Times. Available at: https://www.nytimes.com/2021/04/22/climate/biden-emissions-target-economy.html.",
    ),
    (
        "https://www.thebalancecareers.com/constructive-feedback-to-help-employees-grow-4120943",
        "Anon, How to Provide Feedback to Help Employees Grow Their Skills. Available at: https://www.thebalancecareers.com/constructive-feedback-to-help-employees-grow-4120943.",
    ),
]

key_word_urls = [
    (
        "Clarke%20J.I.,%20(1966)%20Morphometry%20from%20maps,%20Essays%20in%20geomorphology",
        "Holmgren, W. et al., 2020. <i>pvlib/pvlib-python: v0.7.2</i>, Zenodo. Available at: https://doi.org/10.5281/zenodo.3762635.",
    )
]

urls_to_test = (
    arxiv_urls + cran_urls + doi_urls + github_urls + key_word_urls + website_urls
)


@pytest.mark.parametrize("url,expected", urls_to_test)
def test_citations(url, expected):
    my_software = Software(url)
    my_software.find_metadata()
    assert my_software.citation_plain == expected


def test_source_preview():
    my_software = Software("https://cran.r-project.org/web/packages/stringr")
    my_software.find_metadata()
    resp = my_software.to_dict()
    provenance = resp["provenance"][8]["source_preview"]
    assert (
        provenance["title"]
        == '<i>Snapshot of title data found at https://cran.r-project.org/web/packages/stringr/DESCRIPTION.</i><br>Package: stringr<br />Title: <span class="highlight">'
        "Simple, Consistent Wrappers for Common String Operations</span><br />Version: 1.4.0<br />Authors@R: <br />    c(person(given = &quot;Hadley&quot;,<br />"
        "             family = &quot;Wickham&quot;,<br />             role = c(&quot;aut&quot;, &quot;cre&quot;, &quot;cph&quot;),<br />             "
        "email = &quot;hadley@rstudio.com&quot;),<br />      person(given = &quot;RStudio&quot;,<br />             role = c(&quot;cph&quot;, &quot;fnd&quot;)))<br />"
        "Description: A consistent, simple and easy to use set of<br />    wrappers around the fantastic &#x27;stringi"
    )
    assert (
        provenance["author"]
        == "<i>Snapshot of author data found at https://cran.r-project.org/web/packages/stringr/DESCRIPTION.</i><br>Package: "
        "stringr<br />Title: Simple, Consistent Wrappers for Common String Operations<br />Version: 1.4.0<br />Authors@R: <br />    "
        'c(person(given = "<span class="highlight">Hadley</span>",<br />             family = "<span class="highlight">Wickham</span>",<br />             '
        'role = c("aut", "cre", "cph"),<br />             email = "hadley@rstudio.com"),<br />      person(given = "RStudio",<br />             '
        'role = c("cph", "fnd")))<br />Description: A consistent, simple and easy to use set of<br />    wrappers around the fantastic stringi package. All function and<br />    '
        'argument names (and positions) are consistent, all functions deal with<br />    "NA"s and zero length vectors in the same way, and the output from<br />    one function is easy t'
    )
    assert (
        provenance["year"]
        == "<i>Snapshot of year data found at https://cran.r-project.org/web/packages/stringr/DESCRIPTION.</i><br>tringr<br />BugReports: "
        "https://github.com/tidyverse/stringr/issues<br />Depends: R (&gt;= 3.1)<br />Imports: glue (&gt;= 1.2.0), magrittr, stringi (&gt;= 1.1.7)<br />Suggests: covr, htmltools, "
        "htmlwidgets, knitr, rmarkdown, testthat<br />VignetteBuilder: knitr<br />Encoding: UTF-8<br />LazyData: true<br />RoxygenNote: 6.1.1<br />"
        "NeedsCompilation: no<br />Packaged: 2019-02-09 16:03:19 UTC; hadley<br />Author: Hadley Wickham [aut, cre, cph],<br />  RStudio [cph, fnd]<br />"
        'Maintainer: Hadley Wickham &lt;hadley@rstudio.com&gt;<br />Repository: CRAN<br />Date/Publication: <span class="highlight">2019-02-10 03:40:03 UTC</span><br />'
    )


def test_provenance():
    my_software = Software("http://yt-project.org")
    my_software.find_metadata()
    resp = my_software.to_dict()
    provenance = resp["provenance"]

    steps_with_content = [
        {"step_name": "UserInputStep", "parent_step_name": "NoneType"},
        {"step_name": "WebpageStep", "parent_step_name": "UserInputStep"},
        {"step_name": "GithubRepoStep", "parent_step_name": "WebpageStep"},
        {"step_name": "GithubCitationFileStep", "parent_step_name": "GithubRepoStep"},
        {
            "step_name": "CrossrefResponseStep",
            "parent_step_name": "GithubCitationFileStep",
        },
        {
            "step_name": "CrossrefResponseMetadataStep",
            "parent_step_name": "CrossrefResponseStep",
        },
    ]

    steps_without_content = [
        {"step_name": "CrossrefResponseStep", "parent_step_name": "UserInputStep"},
        {"step_name": "ArxivResponseStep", "parent_step_name": "UserInputStep"},
        {"step_name": "GithubRepoStep", "parent_step_name": "UserInputStep"},
        {"step_name": "BitbucketRepoStep", "parent_step_name": "UserInputStep"},
        {"step_name": "CranLibraryStep", "parent_step_name": "UserInputStep"},
        {"step_name": "PypiLibraryStep", "parent_step_name": "UserInputStep"},
        {"step_name": "RelationHeaderStep", "parent_step_name": "WebpageStep"},
        {"step_name": "CrossrefResponseStep", "parent_step_name": "WebpageStep"},
        {"step_name": "GithubCodemetaFileStep", "parent_step_name": "GithubRepoStep"},
    ]

    for step in steps_with_content:
        for p in provenance:
            if (
                p["name"] == step["step_name"]
                and p["parent_step_name"] == step["parent_step_name"]
            ):
                assert p["has_content"] is True

    for step in steps_without_content:
        for p in provenance:
            if (
                p["name"] == step["step_name"]
                and p["parent_step_name"] == step["parent_step_name"]
            ):
                assert p["has_content"] is False
