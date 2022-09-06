import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from collections import namedtuple

import logging
import sys
from main import *

try:
    from urllib.request import urlopen
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse
    from urllib import urlopen

from xml.dom.minidom import parse
from rdflib.graph import ConjunctiveGraph
from rdflib.namespace import RDF, RDFS, OWL, XSD
from rdflib.parser import Parser
from rdflib.serializer import Serializer

import microdata

from rdflib import URIRef, Literal, BNode, Namespace, RDF
from rdflib.plugin import register
from rdflib.parser import Parser
import rdflib_microdata


def get_internal_links(page_url:str, baseURL:str, base_url) -> set:
    '''
   Прима Beautiful Soup објект и базно URL како аргументи
   Враќа листа со адекватни внатрешни линкови
   '''
    # Иницијализација на повратна вредност
    rtn_value = set()
    # regex за наоѓање на внатрешни линкови
    regex = re.compile(r'^(' + baseURL + '\/|\/).+')
    response = requests.get(page_url)
    soup = BeautifulSoup(response.content, 'html.parser')
    links = soup.find_all('a', {'href':regex})
    for link in links:
        try:
            href = link['href']
            # Го трга query string-от од самиот линк
            url_path = urlparse(href).path
            # Се добива валиден url
            fully_qualified_url = urljoin(base_url,url_path)
            rtn_value.add(fully_qualified_url)
        except AttributeError as e:
            pass
    return rtn_value

# Се тестира со 10 страници
def traverse(page_url: str, base_url: str, visited: set, depth: int, f, parser, serializer):
    '''
   Зема url на страница, базичен на вебсајт, множество на броеви како аргументи, како и длабочина
   Ги прегледува сите внатреѓни линкови на сајт
   '''
    # Со цел порано запирање на рекурзијата
    print(len(visited))
    if len(visited) > 10:
        sys.stdout = original_stdout
        return True
    else:
        visited.add(page_url)
        # Ги наоѓа сите непрегледани url на таа страница
        for link in get_internal_links(page_url, base_url, base_url):
            if link not in visited:
                print('Depth: {} URL: {}'.format(depth, link))
                extract_rdfa(link, f, parser, serializer)
                traverse(link, base_url, visited, depth + 1, f, parser, serializer)
                return True
    return True

def extract_rdfa(url, f, parser, serializer):
    """
    Екстракција на rdfa (или други формати, во зависност од парсерот)

    Парсери https://rdflib.readthedocs.org/en/4.1.0/plugin_parsers.html
    Serializers https://rdflib.readthedocs.org/en/4.1.0/plugin_serializers.html
    """
    store = None
    graph = ConjunctiveGraph()
    graph.parse(url, format=parser)
   # f.write(graph.print(format=parser, encoding="utf-8"))
    print(graph.serialize(format=serializer))
    print('\n')

if __name__ == '__main__':  
    page_url = "https://www.crnobelo.com/"
    base_url = "https://www.crnobelo.com"
    parser = "rdfa"
    serializer = "turtle"
    visited = set()
    depth = 0
    original_stdout = sys.stdout
    f = open("document.txt", encoding="utf-8", mode="w")
    sys.stdout = f
    value = traverse(page_url, base_url, visited, depth + 1, f, parser, serializer)
    print(value)
