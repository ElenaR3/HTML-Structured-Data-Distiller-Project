
from pprint import pprint
import extruct
from extruct import MicrodataExtractor, JsonLdExtractor, RDFaExtractor
from flask import Flask, request
from pyRdfa import VocabReferenceError, URIOpener, HTTPError, RDFaError, MediaTypes
from pyRdfa.rdfs import err_unreachable_vocab, err_outdated_cache, err_unparsable_Turtle_vocab, \
    err_unparsable_rdfa_vocab, err_unrecognised_vocab_type
from pyRdfa.rdfs.cache import xml_application_media_type
from rdflib import Graph
from w3lib.html import get_base_url
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import microdata
import rdflib_microdata

import sys

try:
    from urllib.request import urlopen
    # from urllib.parse import urlparse
except ImportError:
    # from urlparse import urlparse
    from urllib import urlopen

from rdflib.graph import ConjunctiveGraph

app = Flask(__name__)


@app.route("/result", methods=['POST'])
def result():
    output = request.json.get("url")
    r = requests.get(output)
    flag = True
    f = open("document.txt", encoding="utf-8", mode="w")
    data = scrape(r.url, r.text, flag, f)
    return data


@app.route("/resultFromHtmlMicrodata", methods=['POST'])
def resultFromHtmlMicrodata():
    html = request.json.get("html")
    microdataRes = scrapeFromHtml(html, "Microdata")

    return str(microdataRes)


@app.route("/resultFromHtmlJson", methods=['POST'])
def resultFromHtmlJson():
    html = request.json.get("html")
    jsonRes = scrapeFromHtml(html, "JSON-LD")

    return str(jsonRes)


@app.route("/resultFromHtmlRdfa", methods=['POST'])
def resultFromHtmlRdfa():
    html = request.json.get("html")
    rdfaRes = scrapeFromHtml(html, "rdfa")

    return str(rdfaRes)


@app.route("/crawlingResult", methods=['POST'])
def crawlingResult():
    url = request.json.get("url")
    r = requests.get(url)
    serializer = request.json.get("serializer")
    parser = request.json.get("parser")
    page_url = url
    base_url = url[:-1]
    f = open("document.txt", encoding="utf-8", mode="w")

    visited = set()
    depth = 0
    value = traverse(page_url, base_url, visited, depth + 1, f, parser, serializer, r)
    f.close()
    text_file = open("C:\\Users\\elena\\PycharmProjects\\vbs-project-extruct\\document.txt", encoding="utf-8")

    # read whole file to a string
    data = text_file.read()

    print(data)
    return data

@app.route("/crawlForJson", methods=['POST'])
def crawlForJson():
    url = request.json.get("url")

    r = requests.get(url)

    serializer = request.json.get("serializer")
    parser = request.json.get("parser")
    page_url = url
    base_url = url[:-1]  # bez kosa crta da e
    f = open("document.txt", encoding="utf-8", mode="w")
    visited = set()
    depth = 0
    value = traverse(page_url, base_url, visited, depth + 1, f, parser, serializer, r)
    f.close()
    text_file = open("C:\\Users\\elena\\PycharmProjects\\vbs-project-extruct\\document.txt", encoding="utf-8")

    # read whole file to a string
    data = text_file.read()

    print(data)
    return data


@app.route("/getData", methods=['POST'])
def getData():
    with open('document.txt') as f:
        lines = f.readlines()
    return lines


@app.route("/turtle", methods=['POST'])
def turtle_result():
    output = request.json.get("url")
    output_format = request.json.get("outputFormat")
    r = requests.get(output)
    flag = False
    res_turtle = return_turtle(r.url, any, output_format, flag)
    if res_turtle is None:
        res_turtle = ''
    return res_turtle


@app.route("/turtleFromHtml", methods=['POST'])
def turtleFromHtml_result():
    html = request.json.get("html")
    output_format = request.json.get("outputFormat")
    f = open("turtle.txt", encoding="utf-8", mode="w")
    f.write(repr(html))
    location = f.name
    f.close()
    flag = True
    res_turtle = return_turtle(location, any, output_format, flag)
    if res_turtle is None:
        res_turtle = ''
    return res_turtle


@app.route("/rdfa", methods=['POST'])
def rdfa_result():
    output = request.json.get("url")
    output_format = request.json.get("outputFormat")
    r = requests.get(output)
    res_rdfa = extract_data_from_html(r.url, "rdfa", output_format)
    if res_rdfa is None:
        res_rdfa = ''
    return res_rdfa


@app.route("/microdata", methods=['POST'])
def microdata_result():
    output = request.json.get("url")
    output_format = request.json.get("outputFormat")
    r = requests.get(output)
    res_microdata = extract_data_from_html(r.url, "microdata", output_format)
    if res_microdata is None:
        res_microdata = ''
    return res_microdata


def get_internal_links(page_url: str, baseURL: str, base_url) -> set:
    rtn_value = set()

    regex = re.compile(r'^(' + baseURL + '\/|\/).+')
    response = requests.get(page_url)
    soup = BeautifulSoup(response.content, 'html.parser')
    links = soup.find_all('a', {'href': regex})
    for link in links:
        try:
            href = link['href']

            url_path = urlparse(href).path

            fully_qualified_url = urljoin(base_url, url_path)
            rtn_value.add(fully_qualified_url)
        except AttributeError as e:
            pass
    return rtn_value


def traverse(page_url: str, base_url: str, visited: set, depth: int, f, parser, serializer, r):
    if len(visited) > 4:
        return True
    else:
        visited.add(page_url)

        for link in get_internal_links(page_url, base_url, base_url):
            if link not in visited:
                print('Depth: {} URL: {}'.format(depth, link), file=f)
                if parser != "json-ld":
                    extract_rdfa(link, f, parser, serializer)
                else:
                    data = scrape(r.url, r.text, False, f)

                traverse(link, base_url, visited, depth + 1, f, parser, serializer, r)
                return True
    return True


def extract_rdfa(url, f, parser, serializer):
    store = None
    graph = ConjunctiveGraph()
    graph.parse(url, format=parser)

    print(graph.serialize(format=serializer), file=f)
    print('\n', file=f)


def get_html(url: str):
    """Get raw HTML from a URL."""
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Max-Age': '3600',
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0'
    }
    req = requests.get(url, headers=headers)
    return req.text


def get_metadata(html: str, url: str):
    r = requests.get(url)
    base_url = get_base_url(r.text, r.url)
    metadata = extruct.extract(
        html,
        base_url=base_url,
        syntaxes=['microdata', 'json-ld', 'rdfa', 'opengraph'],
        uniform=True
    )
    if bool(metadata) and isinstance(metadata, list):
        metadata = metadata[0]
    return metadata


def get_metadata_json(html: str, url: str):
    r = requests.get(url)
    base_url = get_base_url(r.text, r.url)
    metadata = extruct.extract(
        html,
        base_url=base_url,
        syntaxes=['json-ld'],
        uniform=True
    )
    if bool(metadata) and isinstance(metadata, list):
        metadata = metadata[0]
    return metadata


def scrape(url: str, html: str, flag, f):
    """Parse structured data from a target page."""
    if flag:
        metadata = get_metadata(html, url)
        pprint(metadata, indent=2, width=150)
    else:  # json e
        metadata = get_metadata_json(html, url)
        print(metadata, file=f)
        print('\n', file=f)
    return metadata


def scrapeFromHtml(html: str, format: str):
    if format == "Microdata":
        mde = MicrodataExtractor()
        microdatares = mde.extract(html)
        return microdatares
    if format == "JSON-LD":
        jslde = JsonLdExtractor()
        jsonres = jslde.extract(html)
        return jsonres
    if format == "rdfa":
        rdfae = RDFaExtractor()
        rdfares = rdfae.extract(html)
        return rdfares


def return_turtle(uri, options, serializer, flag, newCache=False):
    def return_to_cache(msg):
        if newCache:
            options.add_warning(err_unreachable_vocab % uri, warning_type=VocabReferenceError)
        else:
            options.add_warning(err_outdated_cache % uri, warning_type=VocabReferenceError)

    retval = None
    expiration_date = None
    content = None
    text = None

    if not flag:
        try:
            content = URIOpener(uri,
                                {
                                    'Accept': 'text/html;q=0.8, application/xhtml+xml;q=0.8, text/turtle;q=1.0, application/rdf+xml;q=0.9'})
        except HTTPError:
            (type, value, traceback) = sys.exc_info()
            return_to_cache(value)
            return (None, None)
        except RDFaError:
            (type, value, traceback) = sys.exc_info()
            return_to_cache(value)
            return (None, None)
        except Exception:
            (type, value, traceback) = sys.exc_info()
            return_to_cache(value)
            return (None, None)

        # Store the expiration date of the newly accessed data
        expiration_date = content.expiration_date

        if content.content_type == MediaTypes.turtle:
            try:
                retval = Graph()
                retval.parse(content.data, format="turtle")
                if serializer == "rdf/xml":
                    serializer = "pretty-xml"
                elif serializer == "n-triples":
                    serializer = "n3"
                text = str(retval.serialize(format=serializer))
            except:
                (type, value, traceback) = sys.exc_info()
                options.add_warning(err_unparsable_Turtle_vocab % (uri, value))

            return text
    else:
        try:
            retval = Graph()
            retval.parse(uri, format="turtle")
            if serializer == "rdf/xml":
                serializer = "pretty-xml"
            elif serializer == "n-triples":
                serializer = "n3"
            text = str(retval.serialize(format=serializer))
        except:
            (type, value, traceback) = sys.exc_info()
            options.add_warning(err_unparsable_Turtle_vocab % (uri, value))
        return text


def extract_data_from_html(html, parser, serializer):  # parser: rdfa, microdata; ser: turtle, n3, xml

    if serializer == "rdf/xml":
        serializer = "xml"
    elif serializer == "n-triples":
        serializer = "n3"
    store = None
    graph = ConjunctiveGraph()
    graph.parse(html, format=parser)
    try:
        text = str(graph.serialize(format=serializer))
        print(text)
        return text
    except ValueError as e:
        return "The data cannot be represented in this format due to its invalidity. Please choose another format."


if __name__ == '__main__':
    app.run(debug=True, port=2000)
