from src.utils.load_predictor import LoadPredictor

def test_moving_average():

    predictor = LoadPredictor(window=3)

    predictor.add_measurement(5)
    predictor.add_measurement(10)
    predictor.add_measurement(15)

    predicted = predictor.predict()

    assert predicted == (5 + 10 + 15) / 3


def test_overload_detection():

    predictor = LoadPredictor(window=3)

    predictor.add_measurement(10)
    predictor.add_measurement(12)
    predictor.add_measurement(14)

    assert predictor.is_overloaded(8) == True