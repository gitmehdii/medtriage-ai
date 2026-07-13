from datetime import date

import httpx

from medical_knowledge_mcp.models import SearchRequest
from medical_knowledge_mcp.sources import OfficialWebSearchAdapter


def test_official_web_adapter_parses_search_results_and_page_metadata():
    search_html = '''
    <html><body><a href="/guidance/stroke">Stroke warning signs</a></body></html>
    '''
    detail_html = '''
    <html><head>
      <meta property="og:title" content="Stroke warning signs">
      <meta name="description" content="Recognise warning signs and act quickly.">
    </head><body><time datetime="2025-12-19">Updated 19 December 2025</time></body></html>
    '''

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/search":
            assert request.url.params["q"] == "chest pain"
            assert "patient" not in str(request.url)
            return httpx.Response(200, text=search_html, request=request)
        return httpx.Response(200, text=detail_html, request=request)

    adapter = OfficialWebSearchAdapter(
        "nhs",
        "https://www.nhs.uk/search",
        "nhs.uk",
        "National Health Service",
        "GB",
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    results = adapter.search(SearchRequest(query="patient chest pain"))

    assert len(results) == 1
    assert results[0].title == "Stroke warning signs"
    assert results[0].publication_date == date(2025, 12, 19)
    assert results[0].last_update_date == date(2025, 12, 19)
    assert str(results[0].citation.url) == "https://www.nhs.uk/guidance/stroke"
