"""
Unit tests for multilingual language and script detection.
"""

import pytest
from backend.app.services.nlp.language import LanguageDetector, LanguageResult


@pytest.fixture
def detector():
    return LanguageDetector()


def test_empty_and_whitespace_input(detector):
    res_empty = detector.detect("")
    assert res_empty.language == "und"
    assert res_empty.confidence == 0.0
    assert not res_empty.is_reliable

    res_spaces = detector.detect("   \t\n  ")
    assert res_spaces.language == "und"
    assert res_spaces.confidence == 0.0


def test_punctuation_only_input(detector):
    res = detector.detect("... ??? !!! ---")
    assert res.language == "und"
    assert res.confidence == 0.0


def test_english_detection(detector):
    text = "The government announced a new economic stimulus package to support local businesses across the nation."
    res = detector.detect(text)
    assert res.language == "en"
    assert res.script == "Latin"
    assert res.confidence >= 0.70
    assert res.is_reliable


def test_hindi_devanagari_detection(detector):
    text = "सरकार ने कल सभी नागरिकों के लिए एक नई स्वास्थ्य नीति की घोषणा की।"
    res = detector.detect(text)
    assert res.language == "hi"
    assert res.script == "Devanagari"
    assert res.confidence >= 0.80
    assert res.is_reliable


def test_spanish_detection(detector):
    text = "El presidente confirmo que las elecciones nacionales se celebraran el proximo ano con nuevos protocolos."
    res = detector.detect(text)
    assert res.language == "es"
    assert res.script == "Latin"
    assert res.confidence >= 0.65
    assert res.is_reliable


def test_french_detection(detector):
    text = "Le ministre de la sante a declare que les mesures de securite sanitaire restent en vigueur dans tout le pays."
    res = detector.detect(text)
    assert res.language == "fr"
    assert res.script == "Latin"
    assert res.confidence >= 0.65
    assert res.is_reliable


def test_german_detection(detector):
    text = "Die Bundesregierung hat gestern einen neuen Gesetzentwurf zur Reform des Arbeitsmarktes verabschiedet."
    res = detector.detect(text)
    assert res.language == "de"
    assert res.script == "Latin"
    assert res.confidence >= 0.65
    assert res.is_reliable


def test_arabic_detection(detector):
    text = "أعلنت وزارة الصحة عن بدء حملة تطعيم شاملة في جميع المحافظات."
    res = detector.detect(text)
    assert res.language == "ar"
    assert res.script == "Arabic"
    assert res.confidence >= 0.80


def test_cyrillic_russian_detection(detector):
    text = "Министерство финансов опубликовало официальный отчет о состоянии государственного бюджета."
    res = detector.detect(text)
    assert res.language == "ru"
    assert res.script == "Cyrillic"
    assert res.confidence >= 0.80


def test_cjk_chinese_detection(detector):
    text = "国家统计局今天发布了关于第三季度经济增长的统计公报和宏观分析数据。"
    res = detector.detect(text)
    assert res.language == "zh"
    assert res.script == "CJK"
    assert res.confidence >= 0.80


def test_hinglish_code_switching(detector):
    text = "Yeh news bilkul fake hai aur sarkar ne koi naya tax nahi lagaya hai."
    res = detector.detect(text)
    assert res.language == "hi"
    assert res.script == "Latin"
    assert res.is_code_switched


def test_short_string_uncertainty_penalty(detector):
    res = detector.detect("Hello")
    assert res.confidence <= 0.75
    assert not res.is_reliable
