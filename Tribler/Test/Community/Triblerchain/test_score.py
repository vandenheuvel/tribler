from unittest import TestCase

from Tribler.community.triblerchain.score import calculate_score, BOUNDARY_VALUE


class TestScore(TestCase):
    @staticmethod
    def create_node(public_key="TEST", total_up=0, total_down=0):
        return {"public_key": public_key, "total_up": total_up, "total_down": total_down}

    def test_calculate_score_below(self):
        self.assertEqual(0, calculate_score(self.create_node(total_down=BOUNDARY_VALUE + 1)))

    def test_calculate_score_above(self):
        self.assertEqual(1, calculate_score(self.create_node(total_up=BOUNDARY_VALUE + 1)))

    def test_calculate_score_between(self):
        self.assertEqual(0.75, calculate_score(self.create_node(total_up=BOUNDARY_VALUE / 2)))
