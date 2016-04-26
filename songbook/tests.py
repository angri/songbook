import unittest

from songbook.jinja2env import textdiff


class TextdiffTestCase(unittest.TestCase):
    maxDiff = None
    def test_by_lines(self):
        prev = "foo\nbar\nbaz\nquuxer\n"
        new = "foo\nbaz\nquuxer\nrab"
        res = textdiff(prev, new)
        self.assertEqual(str(res), """\
<span class="same">foo
</span><span class="removed">bar
</span><span class="same">baz
quuxer
</span><span class="added">rab
</span>""")

    def test_intraline_changes(self):
        prev = "foo\nbar\nbaz\nquuxer word\n"
        new = "foo\nbar\nbaz\nquuxer another word\n"
        res = textdiff(prev, new)
        self.assertEqual(str(res), """\
<span class="same">foo
bar
baz
</span><span class="same">quuxer</span><span class="added"> another</span><span class="same"> word
</span>""")

        prev = "foo\nbar\nbaz\nquuxer fuuxer quux\ngor\nhhoa"
        new = "foo\nbar\nbaz\nquuxer fuuxer mooxer\nquux\ngor\nhhoa"
        res = textdiff(prev, new)
        self.assertEqual(str(res), """\
<span class="same">foo
bar
baz
</span><span class="same">quuxer fuuxer </span><span class="added">mooxer
</span><span class="same">quux
</span><span class="same">gor
hhoa
</span>""")

    def test_too_many_word_changes(self):
        prev = "По возможности подзвучиваем только клавиши и бас."
        new = "Пока предположительно на дальнем кофепойнте третьего этажа."
        res = textdiff(prev, new)
        self.assertEqual(str(res), """\
<span class="removed">По возможности подзвучиваем только клавиши и бас.
</span><span class="added">Пока предположительно на дальнем кофепойнте третьего этажа.
</span>""")

    def test_added_line(self):
        prev = "foo bar baz"
        new = prev + "\nquux muux fuux"
        res = textdiff(prev, new)
        self.assertEqual(str(res), """\
<span class="same">foo bar baz
</span><span class="added">quux muux fuux
</span>""")

    def test_prev_was_empty(self):
        prev = ""
        new = "something"
        res = textdiff(prev, new)
        self.assertEqual(str(res), """\
<span class="added">something
</span>""")

    def test_new_is_empty(self):
        prev = "something"
        new = ""
        res = textdiff(prev, new)
        self.assertEqual(str(res), """\
<span class="removed">something
</span>""")
