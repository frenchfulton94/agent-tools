from weather.app import forecast


def test_forecast_stub():
    assert forecast("oslo")["city"] == "oslo"
