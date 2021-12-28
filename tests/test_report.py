# -*- coding: utf-8 -*-

import datetime as dt

import pandas as pd
import pytest

from snl_d3d_cec_verify.report import (Line,
                                       WrappedLine,
                                       Paragraph,
                                       WrappedParagraph,
                                       MetaLine,
                                       Content,
                                       Report)


@pytest.fixture
def text():
    return "a" * 24 + " " + "a" * 24


def test_Line(text):
    
    test = Line(text, 25)
    result = test()
    lines = result.split("\n")
    
    assert len(lines) == 1
    assert len(lines[0]) == 49


def test_WrappedLine(text):
    
    test = WrappedLine(text, 25)
    result = test()
    lines = result.split("\n")
    
    assert len(lines) == 2
    assert len(lines[0]) == 24


def test_WrappedLine_width_none(text):
    
    test = WrappedLine(text)
    result = test()
    lines = result.split("\n")
    
    assert len(lines) == 1
    assert len(lines[0]) == 49


def test_Paragraph(text):
    
    test = Paragraph(text, 25)
    result = test()
    lines = result.split("\n")
    
    assert len(lines) == 2
    assert len(lines[0]) == 49


def test_WrappedParagraph(text):
    
    test = WrappedParagraph(text, 25)
    result = test()
    lines = result.split("\n")
    
    assert len(lines) == 3
    assert len(lines[0]) == 24


def test_WrappedParagraph_width_none(text):
    
    test = WrappedParagraph(text)
    result = test()
    lines = result.split("\n")
    
    assert len(lines) == 2
    assert len(lines[0]) == 49


@pytest.fixture
def metaline():
    return MetaLine()


def test_MetaLine_defined_false(metaline):
    assert not metaline.defined


def test_MetaLine_defined_true(metaline, text):
    metaline.add_line(text)
    assert metaline.defined


def test_MetaLine_add_line(metaline, text):
    
    metaline.add_line(text)
    
    assert metaline.defined
    assert isinstance(metaline.line, Line)
    
    metaline.add_line(None)
    assert not metaline.defined


def test_MetaLine_call_empty(metaline):
    assert metaline() == "%"


def test_MetaLine_call_text(metaline, text):
    metaline.add_line(text)
    assert metaline() == "% " + text


@pytest.fixture
def content():
    return Content()


def test_content_add_text(content, text):
    
    content.add_text(text)
    
    assert len(content.body) == 1
    assert content.body[0][0] == text
    assert content.body[0][1] is WrappedParagraph


def test_content_add_text_no_wrap(content, text):
    
    content.add_text(text, wrapped=False)
    
    assert len(content.body) == 1
    assert content.body[0][0] == text
    assert content.body[0][1] is Paragraph


def test_content_add_heading(content):
    
    title = "Test"
    level = 2
    
    content.add_heading(title, level=level)
    
    assert len(content.body) == 1
    assert content.body[0][1] is Paragraph
    
    text = content.body[0][0]
    assert text == '#' * level + ' ' + title


def test_content_add_table(content):
    
    data = {"a": [1, 2, 3],
            "b": [4, 5, 6]}
    df = pd.DataFrame(data)
    
    caption = "test"
    content.add_table(df, caption=caption)
    
    assert len(content.body) == 2
    assert content.body[0][1] is Paragraph
    assert content.body[1][1] is Paragraph
    
    table_text = content.body[0][0]
    assert table_text == df.to_markdown(index=True)
    
    caption_text = content.body[1][0]
    assert caption_text == "Table:  " + caption


def test_content_add_image(content):
    
    fake_path = "some_image.jpg"
    content.add_image(fake_path)
    
    assert len(content.body) == 1
    assert content.body[0][1] is Paragraph
    
    image_text = content.body[0][0]
    assert image_text == f"![{fake_path}]({fake_path})\\"


def test_content_add_image_with_caption(content):
    
    fake_path = "some_image.jpg"
    caption = "my caption"
    content.add_image(fake_path, caption)
    
    assert len(content.body) == 1
    assert content.body[0][1] is Paragraph
    
    image_text = content.body[0][0]
    assert image_text == f"![{caption}]({fake_path})"


@pytest.mark.parametrize("width, height, expected_attrs", [
                        ("5in", None, "width=5in"),
                        (None, "10px", "height=10px"),
                        ("5in", "10px", "width=5in height=10px")])
def test_content_add_image_with_dimensions(content,
                                           width,
                                           height,
                                           expected_attrs):
    
    fake_path = "some_image.jpg"
    content.add_image(fake_path, width=width, height=height)
    
    assert len(content.body) == 1
    assert content.body[0][1] is Paragraph
    
    image_text = content.body[0][0]
    assert image_text == (f"![{fake_path}]({fake_path}){{ {expected_attrs} "
                          "}\\")


def test_content_clear(content, text):
    
    title = "Test"
    content.add_heading(title)
    content.add_text(text)
    
    assert len(content.body) == 2
    
    content.clear()
    
    assert len(content.body) == 0


def test_content_undo(content, text):
    
    title = "Test"
    content.add_heading(title)
    content.add_text(text)
    
    assert len(content.body) == 2
    
    content.undo()
    
    assert len(content.body) == 1


def test_content_call(content, text):
    
    content.width = 25
    long_title = "Test " * 5 + "Test"
    
    content.add_heading(long_title)
    content.add_text(text)
    
    result = content()
    
    assert len(result) == 2
    assert result[0].count("\n") == 1
    assert result[1].count("\n") == 2


@pytest.fixture
def report():
    return Report()


def test_report_get_width(report):
    assert report.width is None


def test_report_set_width(report):
    value = 79
    report.width = value
    assert report.width == value
    assert report.content.width == value


def test_report_get_title(report):
    assert report.title is None


def test_report_set_title(report):
    
    value = "Test"
    report.title = value
    assert report.title == value
    
    report.title = None
    assert report.title is None


def test_report_get_authors(report):
    assert report.authors is None


def test_report_set_authors(report):
    
    values = ["Me", "You"]
    report.authors = values
    assert report.authors == "; ".join(values)
    
    report.authors = None
    assert report.authors is None


def test_report_get_date(report):
    assert report.date is None


def test_report_set_date_today(report):
    
    report.date = "today"
    today = dt.date.today()
    
    assert report.date == str(today)
    assert report._date == today
    
    report.date = None
    
    assert report.date is None
    assert report._date is None


def test_report_set_date_iso(report):
    
    iso_date = "1919-01-21"
    report.date = iso_date
    
    assert report.date == iso_date
    assert report._date == dt.date.fromisoformat(iso_date)
    
    report.date = None
    
    assert report.date is None
    assert report._date is None


def test_report_set_date_iso_formatted(report):
    
    report.date_format = "%d %B %Y"
    iso_date = "1919-01-21"
    report.date = iso_date
    
    assert report.date == "21 January 1919"
    assert report._date == dt.date.fromisoformat(iso_date)
    
    report.date = None
    
    assert report.date is None
    assert report._date is None


def test_report_get_date_format(report):
    assert report.date_format is None


def test_report_set_date_format(report):
    value = "%d %B %Y"
    report.date_format = value
    assert report.date_format == value


def test_report_set_date_format_with_date(report):
    
    iso_date = "1919-01-21"
    report.date = iso_date
    
    assert report.date == iso_date
    
    value = "%d %B %Y"
    report.date_format = value
    
    assert report.date_format == value
    assert report.date == "21 January 1919"


def test_report_get_meta_none(report):
    assert not report._get_meta()


def test_report_get_meta_single(report):
    
    title = "Test"
    report.title = title
    lines = report._get_meta()
    
    assert len(lines) == 2
    assert lines[0] == f"% {title}"
    assert lines[1] == ""


@pytest.mark.parametrize("title, expected_title", [
                                (None, "%"),
                                ("Test", "% Test")])
def test_report_get_meta_double(report,
                                title,
                                expected_title):
    
    authors = ["You", "Me"]
    report.title = title
    report.authors = authors
    lines = report._get_meta()
    
    assert len(lines) == 3
    assert lines[0] == expected_title
    assert lines[1] == f'% {"; ".join(authors)}'
    assert lines[2] == ""


@pytest.mark.parametrize("title, expected_title", [
                                (None, "%"),
                                ("Test", "% Test")])
@pytest.mark.parametrize("authors, expected_authors", [
                                (None, "%"),
                                (["You", "Me"], "% You; Me")])
def test_report_get_meta_triple(report,
                                title,
                                authors,
                                expected_title,
                                expected_authors):
    
    iso_date = "1919-01-21"
    report.title = title
    report.authors = authors
    report.date = iso_date
    lines = report._get_meta()
    
    assert len(lines) == 4
    assert lines[0] == expected_title
    assert lines[1] == expected_authors
    assert lines[2] == f'% {iso_date}'
    assert lines[3] == ""


def test_report_repr(report):
    
    width = 79
    date_format = "%d %B %Y"
    title = "Test"
    authors = ["You", "Me"]
    date = "1919-01-21"
    
    report.width = width
    report.date_format = date_format
    report.title = title
    report.authors = authors
    report.date = date
    
    test = repr(report)
    
    assert str(width) in test
    assert date_format in test
    assert title in test
    assert "; ".join(authors) in test
    assert date in test


@pytest.fixture
def filled_report(text):
    report = Report()
    report.width = 25
    report.title = "Test"
    report.content.add_text(text)
    return report


def test_filled_report_length(filled_report):
    assert len(filled_report) == 5


def test_filled_report_getitem_(filled_report):
    assert filled_report[0] == "% Test\n"
    assert filled_report[1] == "\n"
    assert len(filled_report[2]) == 25
    assert filled_report[4] == "\n"


def test_filled_report_str(filled_report):
    
    test = str(filled_report)
    lines = test.split("\n")
    
    assert len(lines) == len(filled_report) + 1
    assert lines[4][:2] == "5:"
    assert not lines[5]
