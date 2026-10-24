"""Genera WAV locales y secuencias nuevas; no publica ni modifica originales."""
from pathlib import Path
import argparse,os,json,math,hashlib,dataclasses
import numpy as np,soundfile as sf
from kokoro_onnx import Kokoro

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);ap.add_argument('--only');args=ap.parse_args();root=args.root.resolve()
 modeldir=Path(os.environ.get('BUPA_TTS_MODELS','/workspace/bupa-tts-models'))
 expected=json.loads((root/'recursos/licencias/modelos_procedencia.json').read_text())
 for name,record in expected.items():assert hashlib.sha256((modeldir/name).read_bytes()).hexdigest()==record['sha256'],name
 k=Kokoro(str(modeldir/'kokoro-v1.0.onnx'),str(modeldir/'voices-v1.0.bin'))
 raw=json.loads((root/'contenido/guiones_v3.json').read_text());videos=raw['videos'];records=[];adjustments=[]
 for v in videos:
  windows=[]
  for s in v['scenes']:
   dest=root/'audio/escenas'/f'{s["id"]}.wav';dest.parent.mkdir(parents=True,exist_ok=True)
   key=hashlib.sha256((s['voice']+'|ef_dora|es-419|1.0|model:'+expected['kokoro-v1.0.onnx']['sha256']).encode()).hexdigest();side=dest.with_suffix('.json')
   if dest.exists() and side.exists() and json.loads(side.read_text()).get('cache_key')==key:
    rec=json.loads(side.read_text());audio,sr=sf.read(dest)
   else:
    speed=1.0;audio,sr,t=k.create_timed(s['voice'],voice='ef_dora',lang='es-419',speed=speed,sentence_pause=.10,clause_pause=.06)
    if s.get('purpose')=='cta' and len(audio)/sr>4.8:
     speed=1.05;audio,sr,t=k.create_timed(s['voice'],voice='ef_dora',lang='es-419',speed=speed,sentence_pause=.04,clause_pause=.025)
    groups=[];g=[]
    for token in t:
     if token.phoneme==' ':
      if g:groups.append(g);g=[]
     else:g.append(token)
    if g:groups.append(g)
    words=s['voice'].split();counts=[]
    for w in words:
     normalized=w.lower().strip('.,;:!?¿¡')
     counts.append(2 if normalized in ['integramédica','multisalud','whatsapp'] else max(1,len(k.tokenizer.phonemize(w,'es-419').split())))
    assert sum(counts)==len(groups),(s['id'],list(zip(words,counts)),len(groups),k.tokenizer.phonemize(s['voice'],'es-419'))
    wordtimes=[];j=0
    for w,n in zip(words,counts):
     chunk=groups[j:j+n];wordtimes.append({'word':w,'start':chunk[0][0].start,'end':chunk[-1][-1].end});j+=n
    rec={'id':s['id'],'text':s['voice'],'voice':'ef_dora','language':'es-419','speed':speed,'duration':len(audio)/sr,'sample_rate':sr,'words':wordtimes,'timings':[dataclasses.asdict(x) for x in t],'phonemes':k.tokenizer.phonemize(s['voice'],'es-419'),'cache_key':key}
    sf.write(dest,audio,sr,subtype='PCM_24');side.write_text(json.dumps(rec,ensure_ascii=False,indent=2))
   assert sr==24000 and rec['speed']<=1.05 and np.max(np.abs(audio))<1
   records.append(rec);duration=rec['duration']
   if s.get('purpose')=='cta':assert duration<=4.90,(s['id'],'Acortar CTA sin cortar palabras',duration)
   reading=len(s.get('note','').split())/3.2
   minimum=max(3.0,duration+.20,reading)
   if s.get('cards'):minimum=max(minimum,3.8)
   windows.append(150 if s.get('purpose')=='cta' else math.ceil(minimum*30))
   print(s['id'],f'{duration:.2f}s','voz completa',flush=True)
  target=max(round(v.get('target_duration',28)*30),sum(windows));remaining=target-sum(windows)
  # Give spare time to the blocks with the longest voice/condition reading demand.
  order=sorted(range(5),key=lambda i:len(v['scenes'][i]['note'])+len(v['scenes'][i]['voice']),reverse=True)
  for n in range(remaining):windows[order[n%5]]+=1
  at=0
  for s,n in zip(v['scenes'],windows):s['start']=at/30;s['end']=(at+n)/30;at+=n
  v['duration']=at/30;assert windows[-1]==150
  adjustments.append({'id':v['id'],'target_duration':v.get('target_duration'),'duration':v['duration'],'criterion':'Voz sin recortes; lectura de condiciones; cierre cinco segundos; 30fps.'})
 out={'videos':videos,'timing_policy':adjustments,'status':'REVISION_INTERNA_BLOQUEADA_PARA_PUBLICACION'}
 (root/'contenido/secuencias.json').write_text(json.dumps(out,ensure_ascii=False,indent=2));(root/'revision/tiempos_voz.json').write_text(json.dumps(records,ensure_ascii=False,indent=2))
 print('60 locuciones y 10 secuencias completas.',flush=True)
if __name__=='__main__':main()
