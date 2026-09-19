import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import importlib.util
import sys
MODULE_DIR = Path(__file__).resolve().parents[1] / "scripts" / "wechat"
sys.path.insert(0, str(MODULE_DIR))
SPEC = importlib.util.spec_from_file_location("qiaomu_wechat_media", MODULE_DIR / "download_media.py")
assert SPEC and SPEC.loader
dm = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(dm)

class Tests(unittest.TestCase):
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
