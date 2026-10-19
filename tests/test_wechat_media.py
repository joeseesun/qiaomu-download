import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import importlib.util
import sys
import json
import threading
import http.server
import subprocess
from types import SimpleNamespace
MODULE_DIR = Path(__file__).resolve().parents[1] / "scripts" / "wechat"
sys.path.insert(0, str(MODULE_DIR))
SPEC = importlib.util.spec_from_file_location("qiaomu_wechat_media", MODULE_DIR / "download_media.py")
assert SPEC and SPEC.loader
dm = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(dm)

class Tests(unittest.TestCase):
    def test_media_request_bypasses_inherited_proxy_and_sends_browser_ua(self):
        payload = b'verified media fixture'
        class Handler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200 if self.headers.get('User-Agent', '').startswith('Mozilla/') else 403)
                self.send_header('Content-Length', str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)
            def log_message(self, *_args):
                pass
        server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with tempfile.TemporaryDirectory() as root, \
                    patch.object(dm.urllib.request, 'getproxies', return_value={'http': 'http://127.0.0.1:9'}), \
                    patch.object(dm.urllib.request, 'proxy_bypass', return_value=False), patch.object(dm, 'emit'):
                path = Path(root) / 'video.partial'
                dm.fetch_bytes(f'http://127.0.0.1:{server.server_port}/fixture', path, 'test')
                self.assertEqual(path.read_bytes(), payload)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_decrypt_uses_configured_capability_first(self):
        result = subprocess.CompletedProcess([], 0, '--filepath path --key key', '')
        with patch.object(dm.subprocess, 'run', return_value=result) as run:
            self.assertEqual(dm.find_decrypt_backend('/configured/backend'), '/configured/backend')
            self.assertEqual(run.call_args.args[0], ['/configured/backend', 'decrypt', '--help'])

    def test_decrypt_fallback_requires_verified_pinned_install(self):
        lock = json.loads((MODULE_DIR / 'release-lock.json').read_text())
        platform, asset = next(iter(lock['assets'].items()))
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            old = root / 'backend' / lock['tag'] / 'wx_video_download'
            old.parent.mkdir(parents=True)
            old.write_text('fixture')
            marker = old.parent / '.qiaomu-install.json'
            marker.write_text(json.dumps({'tag': lock['tag'], 'platform': platform, 'archive_sha256': asset['sha256']}))
            newer = root / 'backend' / 'v260907' / 'wx_video_download'
            def probe(command, **_kwargs):
                return subprocess.CompletedProcess(command, 0 if command[0] == str(old) else 1,
                                                   '--filepath path --key key' if command[0] == str(old) else '', 'unknown command')
            with patch.dict(dm.os.environ, {'QIAOMU_WX_VIDEO_HOME': str(root)}), patch.object(dm.subprocess, 'run', side_effect=probe) as run:
                self.assertEqual(dm.find_decrypt_backend(str(newer)), str(old))
                self.assertEqual(run.call_count, 2)
                marker.write_text(json.dumps({'tag': lock['tag'], 'platform': platform, 'archive_sha256': 'untrusted'}))
                run.reset_mock()
                self.assertIsNone(dm.find_decrypt_backend(str(newer)))
                self.assertEqual(run.call_count, 1)

    def test_no_decrypt_capability_fails_before_media_download(self):
        with tempfile.TemporaryDirectory() as root:
            args = SimpleNamespace(output=Path(root), backend=Path('/configured/backend'), config=Path('/config'), ffmpeg='ffmpeg')
            with patch.object(dm, 'find_decrypt_backend', return_value=None), patch.object(dm, 'fetch_bytes') as fetch:
                with self.assertRaisesRegex(RuntimeError, 'supports decrypt'):
                    dm.candidate({'url': 'https://example/video', 'decodeKey': '1'}, '', args)
                fetch.assert_not_called()
            self.assertEqual(list(Path(root).iterdir()), [])

    def test_signed_query_preserved(self):
        url='https://media.example/video?sign=a%2fb%2B%3d&basedata=X+Y&token=z&X-snsvideoflag=old'
        result=dm.media_url({'url':url}, 'xWT111')
        self.assertEqual(result, 'https://media.example/video?sign=a%2fb%2B%3d&basedata=X+Y&token=z&X-snsvideoflag=xWT111')
        self.assertEqual(dm.media_url({'url':url}, ''),url)

    def test_nested_error_is_not_success(self):
        with self.assertRaises(RuntimeError):
            dm.profile_from_response({'code':0,'data':{'errCode':1000,'errMsg':'unmatched key'}})
        with self.assertRaises(RuntimeError):
            dm.profile_from_response({'code':0,'data':{'errCode':0,'data':{'object':{'objectDesc':{'media':None}}}}})

    def test_minimal_metadata(self):
        d={'code':0,'data':{'errCode':0,'data':{'cookie':'secret','object':{'contact':{'username':'private'},'objectDesc':{'description':'title','media':[{'url':'https://example/x','decodeKey':'1','unrelated':'secret'}]}}}}}
        p=dm.profile_from_response(d)
        self.assertEqual(p,{'title':'title','media':[{'url':'https://example/x','decodeKey':'1'}]})

    def test_no_overwrite(self):
        with tempfile.TemporaryDirectory() as root:
            d=Path(root);(d/'video.mp4').write_bytes(b'old');tmp=d/'partial';tmp.write_bytes(b'new')
            target=dm.publish(tmp,d,'video')
            self.assertEqual(target.name,'video (1).mp4')
            self.assertEqual((d/'video.mp4').read_bytes(),b'old')
            self.assertEqual(target.read_bytes(),b'new')
            self.assertFalse(tmp.exists())

    def test_safe_transport(self):
        for url in ['http://example/video','https://user:pass@example/video']:
            with self.assertRaises(ValueError):dm.media_url({'url':url},'')
        with self.assertRaises(ValueError):dm.validate_api('http://remote.example:2022')
        with self.assertRaises(ValueError):dm.HTTPSOnly().redirect_request(None,None,302,'',{},'http://example/video')

    def test_partial_transfer_rejected(self):
        class Response(io.BytesIO):
            status=200
            headers={'Content-Length':'12'}
        class Opener:
            def open(self,*a,**k):return Response(b'abc')
        with tempfile.TemporaryDirectory() as root, patch.object(dm.urllib.request,'build_opener',return_value=Opener()), patch.object(dm,'emit'):
            with self.assertRaises(RuntimeError):dm.fetch_bytes('https://example/video',Path(root)/'partial','test')

    def test_missing_connection_emits_once(self):
        class Opener:
            def open(self,*a,**k):return io.BytesIO(b'{"code":400,"msg":"socket missing"}')
        with patch.object(dm.urllib.request,'build_opener',return_value=Opener()),patch.object(dm,'emit') as emit:
            with self.assertRaises(RuntimeError):dm.capture('https://weixin.qq.com/sph/example','http://127.0.0.1:2022',0)
            emit.assert_called_once()

if __name__=='__main__':unittest.main()
