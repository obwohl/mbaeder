import pytest
from unittest.mock import patch, MagicMock, mock_open
import urllib.error
import json
import os
import swm_auslastung

@patch('urllib.request.urlopen')
@patch('builtins.open', new_callable=mock_open)
@patch('os.path.exists')
@patch('logging.info')
def test_get_auslastung_happy_path(mock_log_info, mock_exists, mock_file, mock_urlopen):
    # Setup
    mock_exists.return_value = True

    mock_response = MagicMock()
    mock_response.getcode.return_value = 200
    mock_response.read.return_value = json.dumps([
        {'organizationUnitId': '30195', 'personCount': 50, 'maxPersonCount': 100}
    ]).encode('utf-8')
    mock_urlopen.return_value = mock_response

    # Execute
    swm_auslastung.get_auslastung()

    # Verify
    mock_urlopen.assert_called_once()
    mock_file.assert_called_once_with("auslastung_raw.csv", 'a', newline='', encoding='utf-8')
    mock_log_info.assert_any_call("Successfully wrote 1 records to auslastung_raw.csv")

@patch('urllib.request.urlopen')
@patch('logging.error')
def test_get_auslastung_http_error(mock_log_error, mock_urlopen):
    # Setup
    error_response = MagicMock()
    error_response.read.return_value = b"Internal Server Error"
    headers = {'Content-Type': 'text/plain'}

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
    mock_log_error.assert_any_call(f"Error headers: {headers}")
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
