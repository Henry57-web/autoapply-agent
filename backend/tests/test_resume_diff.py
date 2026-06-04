import unittest

from app.services.resume_diff import build_resume_diff


class ResumeDiffTests(unittest.TestCase):
    def test_build_resume_diff_tracks_added_removed_and_unchanged_lines(self) -> None:
        diff = build_resume_diff(
            "Summary\nBuilt Python APIs\nEducation",
            "Summary\nBuilt production FastAPI services\nEducation\nSkills: Python",
        )

        self.assertEqual(diff["added_lines"], 2)
        self.assertEqual(diff["removed_lines"], 1)
        self.assertEqual(diff["unchanged_lines"], 2)
        self.assertEqual(
            [line["kind"] for line in diff["lines"]],
            ["unchanged", "removed", "added", "unchanged", "added"],
        )

    def test_build_resume_diff_handles_identical_resumes(self) -> None:
        diff = build_resume_diff("Summary\nPython", "Summary\nPython")

        self.assertEqual(diff["added_lines"], 0)
        self.assertEqual(diff["removed_lines"], 0)
        self.assertEqual(diff["unchanged_lines"], 2)


if __name__ == "__main__":
    unittest.main()
