import math

from app.geo import distance_to_route_km, distance_to_segment_km, haversine_km, within_corridor

# Nairobi and Meru town centers, roughly 210km apart by road / ~180km straight-line.
NAIROBI = (-1.286389, 36.817223)
MERU = (0.047418, 37.649803)


def test_haversine_known_distance_nairobi_to_meru():
    km = haversine_km(*NAIROBI, *MERU)
    assert 170 < km < 200


def test_haversine_zero_for_identical_points():
    assert haversine_km(*NAIROBI, *NAIROBI) == 0.0


def test_distance_to_segment_is_zero_on_the_segment():
    # Midpoint of the segment should have ~0 distance to the segment itself.
    mid_lat = (NAIROBI[0] + MERU[0]) / 2
    mid_lon = (NAIROBI[1] + MERU[1]) / 2
    d = distance_to_segment_km(mid_lat, mid_lon, *NAIROBI, *MERU)
    assert d < 0.01


def test_distance_to_segment_clamps_beyond_endpoints():
    # A point far past the MERU end should measure distance to the endpoint,
    # not project backwards onto the infinite line.
    far_beyond = (1.5, 38.5)
    d = distance_to_segment_km(*far_beyond, *NAIROBI, *MERU)
    expected = haversine_km(*far_beyond, *MERU)
    assert math.isclose(d, expected, rel_tol=0.05)


def test_distance_to_route_uses_closest_segment():
    route = [NAIROBI, (-0.5, 37.2), MERU]
    # A point near the middle segment should be much closer to the route
    # than the straight Nairobi-Meru line would suggest.
    near_middle = (-0.5, 37.25)
    d = distance_to_route_km(*near_middle, route)
    assert d < 10


def test_within_corridor_true_and_false():
    route = [NAIROBI, MERU]
    on_route_ish = ((NAIROBI[0] + MERU[0]) / 2, (NAIROBI[1] + MERU[1]) / 2)
    far_away = (-4.0, 39.6)  # Mombasa, nowhere near this route
    assert within_corridor(*on_route_ish, route, buffer_km=15) is True
    assert within_corridor(*far_away, route, buffer_km=15) is False


def test_distance_to_route_empty_is_infinite():
    assert distance_to_route_km(0, 0, []) == math.inf
