"""Descarga reproducible por HTTPS y verificación con huellas archivadas.
SHA256 registrados en la primera descarga confiable por TLS, no firmas del autor.
"""
from pathlib import Path
from urllib.request import urlopen
import json,hashlib,os,sys,tarfile
R=Path(__file__).resolve().parent;M=Path(os.environ.get('BUPA_TTS_MODELS','/workspace/bupa-tts-models'));M.mkdir(parents=True,exist_ok=True)
models=json.loads((R/'licencias/modelos_procedencia.json').read_text())
if '--asr' in sys.argv:models.update(json.loads((R/'licencias/modelos_asr_procedencia.json').read_text()))
for name,d in models.items():
 p=M/name
 if not p.exists():
  temp=p.with_suffix(p.suffix+'.part')
  with urlopen(d['url'],timeout=120) as source,temp.open('wb') as out:
   while chunk:=source.read(1024*1024):out.write(chunk)
  assert hashlib.sha256(temp.read_bytes()).hexdigest()==d['sha256'],name
  temp.replace(p)
 assert hashlib.sha256(p.read_bytes()).hexdigest()==d['sha256'],name
 if name.endswith('.tar.bz2'):
  with tarfile.open(p) as archive:archive.extractall(M,filter='data')
 print('SHA256 OK',name,flush=True)
