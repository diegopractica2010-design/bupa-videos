"""Descarga verificable de modelos públicos; respeta proxy y TLS del entorno."""
from pathlib import Path
import argparse, hashlib, json, os, tarfile, urllib.request

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        while b:=f.read(1024*1024): h.update(b)
    return h.hexdigest()

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--models-dir',type=Path,default=Path(os.environ.get('BUPA_TTS_MODELS','/workspace/bupa-tts-models')))
    ap.add_argument('--asr',action='store_true'); a=ap.parse_args(); a.models_dir.mkdir(parents=True,exist_ok=True)
    licenses=Path(__file__).resolve().parents[1]/'recursos/licencias'
    records=json.loads((licenses/'modelos_procedencia.json').read_text())
    if a.asr:
        r=json.loads((licenses/'modelos_asr_procedencia.json').read_text())
        records['sherpa-onnx-whisper-base.tar.bz2']=r['sherpa-onnx-whisper-base.tar.bz2']
    for name,record in records.items():
        p=a.models_dir/name
        if not p.exists() or sha(p)!=record['sha256']:
            tmp=p.with_name(name+'.part')
            try:
                with urllib.request.urlopen(record['url'],timeout=90) as src, tmp.open('wb') as dst:
                    while chunk:=src.read(1024*1024): dst.write(chunk)
                assert sha(tmp)==record['sha256'],f'Hash inesperado: {name}'
                os.replace(tmp,p)
            finally:
                if tmp.exists(): tmp.unlink()
        print(name,'SHA256 correcto',flush=True)
        if name.endswith('.tar.bz2'):
            with tarfile.open(p) as tar: tar.extractall(a.models_dir,filter='data')

if __name__=='__main__': main()
