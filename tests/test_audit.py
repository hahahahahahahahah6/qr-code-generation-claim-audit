import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from qr_code_generation_claim_audit.audit import audit, evidence
from qr_code_generation_claim_audit.phrases import QRCODEGENERATION, NOQRCODEGENERATION, GENERIC_NAMES

class AuditTests(unittest.TestCase):
    def test_phrases(self):
        self.assertEqual((len(QRCODEGENERATION), len(NOQRCODEGENERATION), len(GENERIC_NAMES)), (50, 24, 24))
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); doc = root / 'README.md'; src = root / 'app.py'
            for phrase in QRCODEGENERATION:
                with self.subTest(phrase=phrase):
                    doc.write_text(phrase); src.unlink(missing_ok=True)
                    self.assertEqual(audit(root)['verdict'], 'FAIL')
                    src.write_text('x.generate_qr_code()'); self.assertEqual(audit(root)['verdict'], 'PASS')
            for phrase in NOQRCODEGENERATION:
                with self.subTest(phrase=phrase):
                    doc.write_text(phrase); src.unlink(missing_ok=True)
                    self.assertEqual(audit(root)['verdict'], 'PASS')
                    src.write_text('x.generate_qr_code()'); r = audit(root)
                    self.assertEqual(len(r['findings']), 1); self.assertEqual(r['findings'][0]['rule'], 'documented-no-qr-code-generation-claim-false')

    def test_routes(self):
        sources = ['import qrcode as q; q.make()', 'from qrcode import make as m; m()', 'import qrcode as q; x=q.QRCode(); x.make()', 'from qrcode import QRCode as Q; x=Q(); x.make_image()', 'import pyqrcode as p; p.create()', 'from pyqrcode import create as c; c()']
        for name in ('make', 'make_qr', 'make_micro', 'make_sequence'):
            sources += ['import segno as s; s.%s()' % name, 'from segno import %s as f; f()' % name]
        for name in ('encode_text', 'encode_binary', 'encode_segments'):
            sources += ['import qrcodegen as q; q.QrCode.%s()' % name, 'from qrcodegen import QrCode as Q; Q.%s()' % name]
        sources += ['x.%s()' % n for n in GENERIC_NAMES] + ['from lib import %s as f; f()' % n for n in GENERIC_NAMES]
        for source in sources:
            with self.subTest(source=source): self.assertTrue(evidence(source))

    def test_non_routes(self):
        sources = ['import '+n for n in ('qrcode', 'segno', 'qrcodegen', 'pyqrcode')]
        sources += ['make()', 'import qrcode; qrcode.QRCode()', 'x.make()', 'x.make_image()', 'import qrcode; qrcode.QRCode(); x.add_data()', 'import segno; segno.QRCode()', 'import qrcodegen; qrcodegen.QrCode', 'create()', 'invalid syntax !!!', 'import subprocess; subprocess.run(["qrencode"])', 'from pyzbar import decode; decode()', 'import cv2; cv2.QRCodeDetector().detectAndDecode()', 'import zxingcpp; zxingcpp.read_barcode()', 'import barcode; barcode.get()']
        sources += [n+'()' for n in ('make_qr','make_micro','make_sequence','encode_text','encode_binary','encode_segments')]
        sources += ['import pyqrcode; pyqrcode.'+n+'()' for n in ('png','svg','eps','terminal')]
        sources += ['generate_qr_code()', 'def generate_qr_code(): pass\nx.generate_qr_code()', 'import qrcode\nwith obj as qrcode: pass\nqrcode.make()']
        for source in sources:
            with self.subTest(source=source): self.assertFalse(evidence(source))

    def test_findings(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); doc=root/'README.md'; doc.write_text("doesn't generate qr code")
            self.assertEqual(audit(root)['verdict'], 'PASS')
            (root/'app.py').write_text('x.generate_qr_code()'); self.assertEqual(len(audit(root)['findings']),1)
            (root/'app.py').unlink(); doc.write_text('generate qr code'); self.assertEqual(audit(root)['findings'][0]['severity'],'HIGH')
            (root/'tests').mkdir(); (root/'tests/test_x.py').write_text('x.generate_qr_code()')
            self.assertEqual(audit(root)['findings'][0]['severity'],'MEDIUM'); self.assertEqual(audit(root)['verdict'],'PASS'); self.assertEqual(audit(root,fail_on='medium')['verdict'],'FAIL')
            doc.write_text('```\ngenerate qr code\n```'); self.assertEqual(audit(root)['verdict'],'PASS')
            doc.write_text('`generate qr code`'); self.assertEqual(audit(root,fail_on='medium')['verdict'],'FAIL')

    def test_split_ignore(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); (root/'README.md').write_text('generate qr code'); (root/'a.py').write_text('import qrcode; qrcode.QRCode()'); (root/'b.py').write_text('x.make_image()')
            self.assertEqual(audit(root)['verdict'],'FAIL')
            (root/'b.py').write_text('x.generate_qr_code()'); (root/'link.py').symlink_to(root/'b.py')
            self.assertEqual(audit(root,ignore=['b.py'])['verdict'],'FAIL')

    def test_cli(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp,'README.md').write_text('generate qr code')
            cmd=[sys.executable,'-m','qr_code_generation_claim_audit']
            p=subprocess.run(cmd+['audit',tmp,'--json'],capture_output=True,text=True); self.assertEqual(p.returncode,2); self.assertEqual(set(json.loads(p.stdout)),{'verdict','findings'})
            self.assertEqual(subprocess.run(cmd+['audit',tmp,'--ignore','README.md'],capture_output=True).returncode,0)
            self.assertEqual(subprocess.run(cmd+['audit',tmp+'/missing'],capture_output=True).returncode,1)
            self.assertEqual(subprocess.run(cmd+['--version'],capture_output=True,text=True).stdout.strip(),'0.1.0')
        root=Path(__file__).resolve().parents[1]
        self.assertEqual(audit(root)['verdict'],'PASS')
        self.assertEqual(subprocess.run([sys.executable,'-m','qr_code_generation_claim_audit','audit',str(root)],capture_output=True).returncode,0)

if __name__ == '__main__': unittest.main()
