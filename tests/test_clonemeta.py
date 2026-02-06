import unittest
import os
import shutil
import pikepdf
from datetime import datetime
from clonemeta import clone_pdf_attributes

class TestCloneMeta(unittest.TestCase):
    def setUp(self):
        self.test_dir = "test_data"
        os.makedirs(self.test_dir, exist_ok=True)
        
        # Paths
        self.source_path = os.path.join(self.test_dir, "source.pdf")
        self.target_path = os.path.join(self.test_dir, "target.pdf")
        self.output_path = os.path.join(self.test_dir, "source (edit).pdf")

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def create_pdf(self, path, info=None, xmp=None):
        with pikepdf.new() as pdf:
            if info:
                for k, v in info.items():
                    pdf.docinfo[k] = v
            
            if xmp:
                with pdf.open_metadata() as meta:
                    for k, v in xmp.items():
                        meta[k] = v
            pdf.save(path)

    def test_basic_cloning_and_spoofing(self):
        """Test basic metadata cloning and Producer spoofing."""
        src_info = {
            '/Title': 'Original Title',
            '/Author': 'Original Author',
            '/Producer': 'Legacy Producer v1.0'
        }
        dst_info = {
            '/Title': 'Garbage Title',
            '/Producer': 'New Producer v2.0'
        }
        
        self.create_pdf(self.source_path, info=src_info)
        self.create_pdf(self.target_path, info=dst_info)
        
        clone_pdf_attributes(self.source_path, self.target_path)
        
        with pikepdf.open(self.output_path) as pdf:
            self.assertEqual(str(pdf.docinfo['/Title']), 'Original Title')
            self.assertEqual(str(pdf.docinfo['/Author']), 'Original Author')
            self.assertEqual(str(pdf.docinfo['/Producer']), 'Legacy Producer v1.0')

    def test_unicode_support(self):
        """Test cloning of Unicode characters in metadata."""
        src_info = {'/Title': 'Title with Üñîçø∂é 🚀'}
        self.create_pdf(self.source_path, info=src_info)
        self.create_pdf(self.target_path)
        
        clone_pdf_attributes(self.source_path, self.target_path)
        
        with pikepdf.open(self.output_path) as pdf:
            self.assertEqual(str(pdf.docinfo['/Title']), 'Title with Üñîçø∂é 🚀')

    def test_xmp_sync_and_clearing(self):
        """Test that XMP is synced and extra target XMP is cleared."""
        # Source has XMP title
        self.create_pdf(self.source_path, xmp={'dc:title': 'Source XMP Title'})
        # Target has different XMP description
        self.create_pdf(self.target_path, xmp={'dc:description': 'Old Target Desc'})
        
        clone_pdf_attributes(self.source_path, self.target_path)
        
        with pikepdf.open(self.output_path) as pdf:
            with pdf.open_metadata() as meta:
                # Should show source XMP
                self.assertEqual(meta['dc:title'], 'Source XMP Title')
                # Should NOT have target's old XMP
                self.assertIsNone(meta.get('dc:description'))

    def test_source_without_xmp(self):
        """Test that if source has NO XMP, target XMP is fully stripped."""
        # Source has NO XMP (just basic info)
        self.create_pdf(self.source_path, info={'/Title': 'No XMP'})
        # Target HAS XMP
        self.create_pdf(self.target_path, xmp={'dc:title': 'I should be deleted'})
        
        clone_pdf_attributes(self.source_path, self.target_path)
        
        with pikepdf.open(self.output_path) as pdf:
            # pikepdf might initialize a minimal XMP on open, but our specific keys should be gone
            # checking simple property: checking if we can find the old key
            with pdf.open_metadata() as meta:
                self.assertIsNone(meta.get('dc:title'))

    def test_date_preservation(self):
        """Test strict preservation of CreationDate and ModDate strings."""
        # PDF Dates are strings like D:20230101000000+00'00'
        date_str = "D:20231231235959+00'00'"
        src_info = {'/CreationDate': date_str, '/ModDate': date_str}
        
        self.create_pdf(self.source_path, info=src_info)
        self.create_pdf(self.target_path)
        
        clone_pdf_attributes(self.source_path, self.target_path)
        
        with pikepdf.open(self.output_path) as pdf:
            self.assertEqual(str(pdf.docinfo['/CreationDate']), date_str)
            self.assertEqual(str(pdf.docinfo['/ModDate']), date_str)

if __name__ == '__main__':
    unittest.main()
