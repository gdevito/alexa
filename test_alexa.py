
import pytest
import get_sites


def test_get_sites():

    sites = get_sites.get_alexa_sites()
    assert len(sites) == 100


def test_get_words():

    url = 'google.com'
    words = get_sites.get_words(url)
    assert words['wc']

