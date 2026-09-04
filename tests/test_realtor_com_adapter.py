from realtor_scraper.sites.realtor_com import RealtorComAdapter

SAMPLE_HTML = """
<html><body>
  <div data-testid="agent-card">
    <span data-testid="agent-name">Jane Smith</span>
    <a data-testid="agent-phone" href="tel:+17025551234">(702) 555-1234</a>
    <span data-testid="agent-group">Vegas Realty Group</span>
    <a href="/realestateagent/janesmith_nv">Profile</a>
  </div>
  <div data-testid="agent-card">
    <span data-testid="agent-name">John Doe</span>
    <span data-testid="agent-group">Desert Homes</span>
    <a href="/realestateagent/johndoe_nv">Profile</a>
  </div>
  <a aria-label="Go to next page" href="/realestateagents/las-vegas_nv/pg-2">Next</a>
</body></html>
"""


def test_parse_listing_page_extracts_name_and_phone():
    adapter = RealtorComAdapter(city="Las Vegas", state="NV", selectors={})
    leads = adapter.parse_listing_page(SAMPLE_HTML)

    assert len(leads) == 2
    assert leads[0].name == "Jane Smith"
    assert leads[0].phone == "+17025551234"
    assert leads[0].brokerage == "Vegas Realty Group"
    assert leads[0].profile_url.endswith("/realestateagent/janesmith_nv")

    # Second agent has no phone element -> empty phone, not a crash.
    assert leads[1].name == "John Doe"
    assert leads[1].phone == ""


def test_has_next_page():
    adapter = RealtorComAdapter(city="Las Vegas", state="NV", selectors={})
    assert adapter.has_next_page(SAMPLE_HTML) is True
    assert adapter.has_next_page("<html><body>no next here</body></html>") is False


def test_build_search_url():
    adapter = RealtorComAdapter(city="Las Vegas", state="NV", selectors={})
    assert adapter.build_search_url(1) == "https://www.realtor.com/realestateagents/las-vegas_nv"
    assert adapter.build_search_url(2).endswith("/pg-2")
