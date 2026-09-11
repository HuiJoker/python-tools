from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "split_images_by_count.py"
SPEC = importlib.util.spec_from_file_location("split_images", SCRIPT)
assert SPEC and SPEC.loader
split_images = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(split_images)


class SplitImagesTests(unittest.TestCase):
    def test_small_remainder_is_merged_into_final_batch(self) -> None:
        images = [Path(f"image_{index}.jpg") for index in range(425)]
        batches = split_images.group_images(images, 200)
        self.assertEqual([len(batch) for batch in batches], [200, 225])

    def test_output_folders_are_created_inside_source(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            source = Path(temporary_directory) / "images"
            source.mkdir()
            for index in range(4):
                (source / f"image_{index}.jpg").touch()

            result = split_images.split_images(source, 3, copy_files=False, dry_run=False, recursive=False)

            target = source / "images_1"
            self.assertEqual(result["batch_sizes"], [4])
            self.assertEqual(result["output_dirs"], [str(target)])
            self.assertEqual(len(list(target.glob("*.jpg"))), 4)
            self.assertEqual(len(list(source.glob("*.jpg"))), 0)


if __name__ == "__main__":
    unittest.main()
