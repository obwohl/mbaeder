import pytest
from unittest.mock import patch, MagicMock
import urllib.error
import json
import csv
import io
import os
from http.client import HTTPMessage
import swm_auslastung

@pytest.fixture
def mock_locations():
    return {
        '30195': {'name': 'Bad Giesing-Harlaching', 'type': 'swim'},
        '30190': {'name': 'Cosimawellenbad', 'type': 'swim'}
    }

@patch('urllib.request.urlopen')
@patch('logging.info')
def test_get_auslastung_happy_path(mock_log_info, mock_urlopen, tmp_path, mock_locations):
    # Setup
    csv_file = tmp_path / "auslastung_raw.csv"

    # We need to patch where 'os.path.exists' and 'open' are used in swm_auslastung.py
    # and also ensure the filename used in the 'with open(...)' call is our temp file.

    with patch('swm_auslastung.LOCATIONS', mock_locations), \
         patch('swm_auslastung.os.path.exists') as mock_exists, \
         patch('swm_auslastung.open', MagicMock(side_effect=open)) as mock_open_swm:

        # Force the filename inside the function to be our temp path
        # Since it's a local variable, we have to mock 'open' to redirect if the filename matches
        original_open = open
        def side_effect(file, *args, **kwargs):
            if file == "auslastung_raw.csv":
                return original_open(csv_file, *args, **kwargs)
            return original_open(file, *args, **kwargs)

        mock_open_swm.side_effect = side_effect
        mock_exists.return_value = False # Force header writing

        mock_response = MagicMock()
        mock_response.getcode.return_value = 200
        mock_response.read.return_value = json.dumps([
            {'organizationUnitId': '30195', 'personCount': 50, 'maxPersonCount': 100}
        ]).encode('utf-8')
        mock_urlopen.return_value = mock_response

        # Execute
        swm_auslastung.get_auslastung()

        # Verify CSV content
        assert csv_file.exists()
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 1
            assert rows[0]['item_id'] == 'bad_giesing-harlaching_swim'
            assert float(rows[0]['person_count']) == 50.0
            assert float(rows[0]['max_person_count']) == 100.0
            assert float(rows[0]['utilization_percentage']) == 50.0

@patch('urllib.request.urlopen')
def test_get_auslastung_writes_header(mock_urlopen, tmp_path, mock_locations):
    # Setup
    csv_file = tmp_path / "auslastung_raw.csv"
    with patch('swm_auslastung.LOCATIONS', mock_locations), \
         patch('swm_auslastung.os.path.exists') as mock_exists, \
         patch('swm_auslastung.open', MagicMock(side_effect=open)) as mock_open_swm:

        def side_effect(file, *args, **kwargs):
            if file == "auslastung_raw.csv":
                return open(csv_file, *args, **kwargs)
            return open(file, *args, **kwargs)

        mock_open_swm.side_effect = side_effect
        mock_exists.return_value = False # Force header writing

        mock_response = MagicMock()
        mock_response.getcode.return_value = 200
        mock_response.read.return_value = json.dumps([
            {'organizationUnitId': '30195', 'personCount': 10, 'maxPersonCount': 100}
        ]).encode('utf-8')
        mock_urlopen.return_value = mock_response

        # Execute
        swm_auslastung.get_auslastung()

        # Verify header
        with open(csv_file, 'r', encoding='utf-8') as f:
            first_line = f.readline().strip()
            assert first_line == "timestamp,item_id,person_count,max_person_count,utilization_percentage"

@patch('urllib.request.urlopen')
@patch('logging.info')
def test_get_auslastung_edge_cases(mock_log_info, mock_urlopen, tmp_path, mock_locations):
    # Setup
    csv_file = tmp_path / "auslastung_raw.csv"
    with patch('swm_auslastung.LOCATIONS', mock_locations), \
         patch('swm_auslastung.os.path.exists') as mock_exists, \
         patch('swm_auslastung.open', MagicMock(side_effect=open)) as mock_open_swm:

        def side_effect(file, *args, **kwargs):
            if file == "auslastung_raw.csv":
                return open(csv_file, *args, **kwargs)
            return open(file, *args, **kwargs)

        mock_open_swm.side_effect = side_effect
        mock_exists.return_value = False

        # Scenario 1: Unknown organization ID
        # Scenario 2: maxPersonCount is zero
        # Scenario 3: personCount is negative (should be treated as 0.0 utilization per current implementation)
        mock_response = MagicMock()
        mock_response.getcode.return_value = 200
        mock_response.read.return_value = json.dumps([
            {'organizationUnitId': '99999', 'personCount': 50, 'maxPersonCount': 100},  # Unknown ID
            {'organizationUnitId': '30195', 'personCount': 50, 'maxPersonCount': 0},    # Zero max
            {'organizationUnitId': '30190', 'personCount': -1, 'maxPersonCount': 100}  # Negative personCount
        ]).encode('utf-8')
        mock_urlopen.return_value = mock_response

        # Execute
        swm_auslastung.get_auslastung()

        # Verify results
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            # Only two records should be written (99999 is skipped)
            assert len(rows) == 2

            # Record for 30195 (Zero max)
            assert rows[0]['item_id'] == 'bad_giesing-harlaching_swim'
            assert float(rows[0]['utilization_percentage']) == 0.0

            # Record for 30190 (Negative personCount)
            assert rows[1]['item_id'] == 'cosimawellenbad_swim'
            assert float(rows[1]['utilization_percentage']) == 0.0

@patch('urllib.request.urlopen')
@patch('logging.error')
def test_get_auslastung_http_error(mock_log_error, mock_urlopen):
    # Setup
    error_response = MagicMock()
    error_response.read.return_value = b"Internal Server Error"

    # Create a more realistic HTTPMessage for headers
    headers = HTTPMessage()
    headers.add_header('Content-Type', 'text/plain')
    headers.add_header('Server', 'MockServer')

    http_error = urllib.error.HTTPError(
        url="http://example.com",
        code=500,
        msg="Internal Server Error",
        hdrs=headers,
        fp=error_response
    )
    mock_urlopen.side_effect = http_error

    # Execute
    swm_auslastung.get_auslastung()

    # Verify
    mock_urlopen.assert_called_once()
    mock_log_error.assert_any_call("HTTPError fetching API: 500 - Internal Server Error")

    log_calls = [call.args[0] for call in mock_log_error.call_args_list]
    headers_log = [log for log in log_calls if "Error headers:" in log][0]
    assert "Content-Type: text/plain" in headers_log
    assert "Server: MockServer" in headers_log
    mock_log_error.assert_any_call("Error body: Internal Server Error")

@patch('urllib.request.urlopen')
@patch('logging.error')
def test_get_auslastung_generic_exception(mock_log_error, mock_urlopen):
    # Setup
    mock_urlopen.side_effect = Exception("Something went wrong")

    # Execute
    swm_auslastung.get_auslastung()

    # Verify
    mock_urlopen.assert_called_once()
    mock_log_error.assert_called_once_with("Error fetching API: Something went wrong")
