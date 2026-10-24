"""Contraste ASR local por bloques<30s; no certificación de pronunciación."""
from pathlib import Path
import json,subprocess,sys,os
import numpy as np,sherpa_onnx
R=Path(__file__).resolve().parent;P=R.parent;model=sys.argv[1] if len(sys.argv)>1 else 'base';M=Path(os.environ.get('BUPA_TTS_MODELS','/workspace/bupa-tts-models'))/('sherpa-onnx-whisper-'+model)
recognizer=sherpa_onnx.OfflineRecognizer.from_whisper(encoder=str(M/(model+'-encoder.int8.onnx')),decoder=str(M/(model+'-decoder.int8.onnx')),tokens=str(M/(model+'-tokens.txt')),language='es',num_threads=2)
V=json.loads((R/'secuencias_con_voz_v2.json').read_text())['videos'];out=R/f'comprobaciones/asr_{model}_independiente.json'
results=json.loads(out.read_text()) if '--only' in sys.argv and out.exists() else []
for v in V:
 if '--only' in sys.argv and v['id']!=sys.argv[sys.argv.index('--only')+1]:continue
 path=P/'renders_con_voz'/f'{v["slug"]}_instagram_whatsapp_voz_v2_REVISION.mp4'
 raw=subprocess.run(['ffmpeg','-v','error','-i',str(path),'-f','f32le','-ac','1','-ar','16000','-'],capture_output=True,check=True).stdout
 samples=np.frombuffer(raw,dtype=np.float32).copy()[:round(v['duration']*16000)]
 cuts=[(0,v['duration'])] if v['duration']<30 else [(0,v['scenes'][-1]['start']),(v['scenes'][-1]['start'],v['duration'])]
 segments=[]
 for a,b in cuts:
  assert b-a<30
  s=recognizer.create_stream();s.accept_waveform(16000,samples[round(a*16000):round(b*16000)]);recognizer.decode_stream(s)
  segments.append({'start':a,'end':b,'asr':s.result.text})
 expected=' '.join(x['voice'] for x in v['scenes']);text=' '.join(s['asr'] for s in segments)
 r={'id':v['id'],'esperado':expected,'asr':text,'segmentos':segments,'nota':'Reconocimiento automático; puede confundir marcas, cifras o alucinar. No sustituye escucha humana ni certifica cada palabra.'}
 results=[x for x in results if x['id']!=v['id']]+[r];results.sort(key=lambda x:x['id']);out.write_text(json.dumps(results,ensure_ascii=False,indent=2))
 print(v['id'],text,flush=True)
