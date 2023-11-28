import pytest

from reactions.slack_utils import text_to_reactions


class TestPolls:
    @pytest.mark.parametrize(
        "prompt, expected",
        [
            ("Dogs or cats?", {"dog", "cat"}),
            ("Dogs or cats or wild boars?", {"dog", "cat", "boar"}),
            (
                "tengo una pregunta sobre una botella de agua para hacer deporte",
                {"droplet"},
            ),
            ("good morning how is it going today?", {"sunny"}),
            ("ai learns to walk (deep reinforcement learning)", {"robot_face"}),
        ],
    )
    def test_prompt(self, prompt, expected):
        reactions = set(text_to_reactions(prompt))
        assert reactions == expected
