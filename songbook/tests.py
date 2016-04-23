import unittest

from songbook.jinja2env import textdiff


class TextdiffTestCase(unittest.TestCase):
    def test_by_lines(self):
        prev = "foo\nbar\nbaz\nquuxer\n"
        new = "foo\nbaz\nquuxer\nrab"
        res = textdiff(prev, new)
        self.assertEqual(res, """\
<span class="same">foo
</span><span class="removed">bar
</span><span class="same">baz
quuxer
</span><span class="added">rab</span>""")

    def test_intraline_changes(self):
        prev = "foo\nbar\nbaz\nquuxer\n"
        new = "foo\nbar\nbaz\nquuxer another word\n"
        res = textdiff(prev, new)
        self.assertEqual(res, """\
<span class="same">foo
bar
baz
</span><span class="same">quuxer</span><span class="added"> another word</span><span class="same">
</span>""")

        prev = "foo\nbar\nbaz\nquuxer\ngor\nhhoa"
        new = "foo\nbar\nbaz\nquuxer mooxer\nquux\ngor\nhhoa"
        res = textdiff(prev, new)
        self.assertEqual(res, """\
<span class="same">foo
bar
baz
</span><span class="same">quuxer</span><span class="added"> mooxer</span><span class="same">
</span><span class="added">quux
</span><span class="same">gor
hhoa</span>""")
