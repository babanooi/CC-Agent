"""测试意图分类器"""
import pytest


@pytest.fixture(scope="module")
def classifier():
    from agent.intent import IntentClassifier
    return IntentClassifier()


class TestIntentClassifier:
    def test_prompt_build(self, classifier):
        prompt = classifier._build_prompt()
        assert "product_query" in prompt
        assert "product_compare" in prompt
        assert "troubleshoot" in prompt
        assert "purchase_advice" in prompt
        assert "chitchat" in prompt

    def test_parse_valid_json(self, classifier):
        result = classifier._parse_response('{"intent":"chitchat","confidence":0.95}')
        assert result["intent"] == "chitchat"
        assert result["confidence"] == 0.95

    def test_parse_json_with_text(self, classifier):
        result = classifier._parse_response('一些文字 {"intent":"product_query","confidence":0.8}')
        assert result["intent"] == "product_query"

    def test_parse_invalid_fallback(self, classifier):
        result = classifier._parse_response("not json at all")
        assert result["intent"] == "product_query"
        assert result["confidence"] == 0.5

    def test_unknown_intent_fallback(self, classifier):
        result = classifier._parse_response('{"intent":"unknown_type","confidence":0.9}')
        assert result["intent"] == "product_query"
