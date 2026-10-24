"""Locuciones sintéticas locales, sin clonación; modelo Kokoro Apache-2.0.
Modelos fuera del repositorio: /workspace/bupa-tts-models. Requiere kokoro-onnx.
"""
from pathlib import Path
import json,dataclasses,hashlib,shutil,time,os
import numpy as np,soundfile as sf
from kokoro_onnx import Kokoro
R=Path(__file__).resolve().parent;P=R.parent
vs=json.loads((P/'editables/secuencias_reconstruidas_del_informe.json').read_text())['videos']
M=Path(os.environ.get('BUPA_TTS_MODELS','/workspace/bupa-tts-models'))
k=Kokoro(str(M/'kokoro-v1.0.onnx'),str(M/'voices-v1.0.bin'))
records=[]
for v in vs:
 narration=np.zeros(round(v['duration']*24000),dtype='float32')
 for s in v['scenes']:
  a,sr,t=k.create_timed(s['voice'],voice='ef_dora',lang='es-419',speed=1.0,sentence_pause=.12,clause_pause=.07)
  speed=1.0;budget=s['end']-s['start']-.1
  if len(a)/sr>budget:
   speed=min(1.05,len(a)/sr/budget+.005)
   a,sr,t=k.create_timed(s['voice'],voice='ef_dora',lang='es-419',speed=speed,sentence_pause=.05,clause_pause=.03)
  fits=len(a)/sr<=budget
  record=dict(id=s['id'],text=s['voice'],voice='ef_dora',language='es-419',speed=speed,duration=len(a)/sr,window=[s['start'],s['end']],fits=fits,timings=[dataclasses.asdict(x) for x in t],phonemes=k.tokenizer.phonemize(s['voice'],'es-419'))
  records.append(record);sf.write(R/'escenas'/f'{s["id"]}.wav',a,sr,subtype='PCM_24')
  if fits:
   start=round((s['start']+.05)*sr);narration[start:start+len(a)]+=a
  print(s['id'],round(len(a)/sr,3),'window',s['end']-s['start'],'speed',speed,'OK' if fits else 'EXCEDE',flush=True)
 # El ensamblaje se realiza después en integrar.py, que ajusta las ventanas.
(R/'comprobaciones/locuciones_y_tiempos.json').write_text(json.dumps(records,ensure_ascii=False,indent=2))
for n in ['README_upstream.md','README_model_provenance.md','LICENSE_runtime.txt','LICENSE_upstream.txt']:
 if not (R/'licencias'/n).exists():shutil.copy2(M/n,R/'licencias'/n)
meta={}
for n in ['kokoro-v1.0.onnx','voices-v1.0.bin']:
 p=M/n;meta[n]={'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'url':'https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.1/'+n}
(R/'licencias/modelos_procedencia.json').write_text(json.dumps(meta,indent=2))
print('Frases que requieren retiming en integrar.py:',sum(not r['fits'] for r in records),flush=True)
