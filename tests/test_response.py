from app import response


def test_response_parses():

    assert response.parse("*1\r\n$4\r\nping\r\n") == ["ping"]
