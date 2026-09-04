from unittest.mock import MagicMock, patch

from realtor_scraper.google_places import fetch_leads

PAGE_1 = {
    "places": [
        {
            "displayName": {"text": "Jane Smith - Vegas Realty"},
            "nationalPhoneNumber": "(702) 555-1234",
            "formattedAddress": "123 Main St, Las Vegas, NV",
            "googleMapsUri": "https://maps.google.com/?cid=1",
        },
        {
            "displayName": {"text": "Desert Homes Group"},
            "internationalPhoneNumber": "+1 702-555-5678",
            "formattedAddress": "456 Desert Ave, Las Vegas, NV",
        },
    ],
    "nextPageToken": "token-abc",
}

PAGE_2 = {
    "places": [
        {
            "displayName": {"text": "No Phone Realty"},
            "formattedAddress": "789 Sunset Rd, Las Vegas, NV",
        },
    ],
}


def _mock_response(payload, status=200):
    resp = MagicMock()
    resp.status_code = status
    resp.json.return_value = payload
    return resp


@patch("realtor_scraper.google_places.time.sleep")
@patch("realtor_scraper.google_places.requests.post")
def test_fetch_leads_paginates_and_maps_fields(mock_post, mock_sleep):
    mock_post.side_effect = [_mock_response(PAGE_1), _mock_response(PAGE_2)]

    leads = fetch_leads(
        query="real estate agents in Las Vegas, NV",
        api_key="fake-key",
        city="Las Vegas",
        state="NV",
        max_results=60,
    )

    assert len(leads) == 3
    assert leads[0].name == "Jane Smith - Vegas Realty"
    assert leads[0].phone == "(702) 555-1234"
    assert leads[1].phone == "+1 702-555-5678"
    assert leads[2].name == "No Phone Realty"
    assert leads[2].phone == ""
    assert mock_post.call_count == 2
    assert mock_sleep.called


@patch("realtor_scraper.google_places.requests.post")
def test_fetch_leads_respects_max_results(mock_post):
    mock_post.return_value = _mock_response(PAGE_1)

    leads = fetch_leads(query="q", api_key="fake-key", max_results=1)

    assert len(leads) == 1
    assert mock_post.call_count == 1
