#!/usr/bin/env python3
"""Render reproducible de pruebas internas. No publica ni modifica originales.
Uso: python herramientas/renderizar.py [--root RUTA] [--only slug ...]
Entradas: contenido/secuencias.json, revision/tiempos_voz.json, audio/escenas,
recursos/graficos, recursos/fuentes y recursos/audio. Caché fuera del checkout.
"""
from __future__ import annotations
import argparse, concurrent.futures, fcntl, hashlib, json, math, os, re, subprocess, tempfile
from xml.sax.saxutils import escape as xml_escape
from pathlib import Path
import numpy as np
import soundfile as sf
from scipy.signal import resample_poly
from PIL import Image, ImageFont
FPS=30; VOICE_OFFSET=.03; BG='#F4F8FA'; CACHE_SCHEMA=4

def digest(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  while block:=f.read(1024*1024):h.update(block)
 return h.hexdigest()

def atomic_text(path,text):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
 fd,tmp=tempfile.mkstemp(prefix=path.name+'.',dir=path.parent)
 try:
  with os.fdopen(fd,'w') as f:f.write(text)
  os.replace(tmp,path)
 finally:
  if os.path.exists(tmp):os.unlink(tmp)

def save_json(path,value):atomic_text(path,json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def ass_time(t):
 units=round(t*100);seconds,fraction=divmod(units,100);minutes,seconds=divmod(seconds,60);hours,minutes=divmod(minutes,60)
 return f'{hours}:{minutes:02}:{seconds:02}.{fraction:02}'
def srt_time(t):
 units=round(t*1000);seconds,fraction=divmod(units,1000);minutes,seconds=divmod(seconds,60);hours,minutes=divmod(minutes,60)
 return f'{hours:02}:{minutes:02}:{seconds:02},{fraction:03}'

def read_inputs(root):
 manifest=json.loads((root/'contenido/secuencias.json').read_text());videos=manifest['videos']
 raw=json.loads((root/'revision/tiempos_voz.json').read_text())
 if isinstance(raw,dict):raw=raw.get('escenas',raw.get('records',raw.get('voices',raw.get('scenes'))))
 assert isinstance(raw,list),'tiempos_voz.json debe ser una lista de escenas'
 timings={r['id']:r for r in raw};assert len(timings)==len(raw),'IDs de voz duplicados'
 assert len({v['slug'] for v in videos})==len(videos),'Slugs duplicados'
 seen=set()
 for v in videos:
  assert Path(v['slug']).name==v['slug'] and v['slug'] not in ('','.'),'Slug inseguro'
  at=0
  for s in v['scenes']:
   assert s['id'] not in seen,'IDs de escena duplicados';seen.add(s['id'])
   a,b=s['start'],s['end'];assert abs(a-at)<1e-6 and b>a,(s['id'],'hueco o solapamiento')
   assert abs(a*FPS-round(a*FPS))<1e-5 and abs(b*FPS-round(b*FPS))<1e-5,(s['id'],'tiempo fuera de fotograma')
   at=b;r=timings[s['id']];assert r['text']==s['voice'],(s['id'],'texto de voz distinto')
   assert 0<float(r.get('speed',1))<=1.05,(s['id'],'velocidad no permitida')
   assert ' '.join(w['word'] for w in r['words']).split()==s['voice'].split(),(s['id'],'palabras no coinciden')
   previous=0
   for w in r['words']:
    assert 0<=w['start']<w['end']<=float(r['duration'])+.001,(s['id'],w)
    assert w['start']>=previous-.001,(s['id'],'palabras no ordenadas');previous=w['end']
   assert VOICE_OFFSET+float(r['duration'])<=b-a+.00005,(s['id'],'voz fuera de ventana')
  assert abs(at-v['duration'])<1e-6 and abs(v['scenes'][-1]['end']-v['scenes'][-1]['start']-5)<1e-6,(v['slug'],'duración o cierre distinto')
 return manifest,videos,timings

def balanced_lines(words,font):
 def fits(ws):
  t=' '.join(ws);return len(t)<=32 and font.getlength(t)<=832
 if fits(words):return [' '.join(words)]
 candidates=[]
 for k in range(1,len(words)):
  a,b=words[:k],words[k:]
  if fits(a) and fits(b):
   penalty=abs(len(' '.join(a))-len(' '.join(b)))+30*(len(a)==1 or len(b)==1)
   candidates.append((penalty,[' '.join(a),' '.join(b)]))
 return min(candidates,key=lambda x:x[0])[1] if candidates else None

def subtitle_chunks(words,font):
 """Partición por palabras y ancho real; evita un bloque final de una palabra."""
 n=len(words);dp=[None]*(n+1);dp[n]=(0,[])
 for i in range(n-1,-1,-1):
  best=None
  for j in range(i+1,n+1):
   tokens=[w['word'] for w in words[i:j]]
   if len(' '.join(tokens))>65:break
   lines=balanced_lines(tokens,font)
   if lines is None or dp[j] is None:continue
   orphan=100 if j-i==1 and n>1 else 0
   cost=4+(len(' '.join(tokens))-45)**2/120+orphan+dp[j][0]
   candidate=(cost,[(i,j,lines)]+dp[j][1])
   if best is None or cost<best[0]:best=candidate
  dp[i]=best
 assert dp[0] is not None,'Texto imposible a 48px/32 caracteres sin reducir tipografía'
 return dp[0][1]

def subtitle_events(v,timings,font):
 events=[]
 for s in v['scenes']:
  words=timings[s['id']]['words']
  for i,j,lines in subtitle_chunks(words,font):
   a=s['start']+VOICE_OFFSET+words[i]['start']
   b=min(s['end'],s['start']+VOICE_OFFSET+words[j-1]['end']+.07)
   if j<len(words):b=min(b,s['start']+VOICE_OFFSET+words[j]['start'])
   assert round(b*100)>round(a*100),(s['id'],'subtítulo nulo al redondear')
   events.append({'scene':s['id'],'start':a,'end':b,'lines':lines,'first_word':i,'last_word':j-1})
 return events

ASS_HEADER='''[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\nWrapStyle: 2\n[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\nStyle: Sub,Montserrat,48,&H00FFFFFF,&H00FFFFFF,&H263F2B10,&H263F2B10,-1,0,0,0,100,100,0,0,3,16,0,7,112,112,930,1\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n'''
def write_ass(path,events,a=0,b=None):
 text=ASS_HEADER
 for e in events:
  start=max(e['start'],a)-a;end=min(e['end'],b) -a if b is not None else e['end']-a
  if end<=start or round(end*100)<=round(start*100):continue
  payload='\\N'.join(e['lines']).replace('{','(').replace('}',')')
  text+=f'Dialogue: 0,{ass_time(start)},{ass_time(end)},Sub,,0,0,0,,{{\\pos(112,946)}}{payload}\n'
 atomic_text(path,text)

def command(cmd,log):
 with Path(log).open('w') as f:result=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT)
 if result.returncode:raise RuntimeError(f'Falló comando ({result.returncode}): {log}')
def json_from_ffmpeg(text):
 at=text.rfind('{');assert at>=0,'FFmpeg no produjo medición JSON'
 return json.JSONDecoder().raw_decode(text[at:])[0]
def verify_font_selection(log,has_subtitles):
 selections=[line.split('fontselect: ',1)[1] for line in Path(log).read_text().splitlines() if 'fontselect: ' in line]
 assert selections or not has_subtitles,('No se comprobó la fuente real de subtítulos',str(log))
 for line in selections:
  assert re.search(r'\(Montserrat,\s*700,\s*0\)',line) and line.rsplit(', ',1)[-1]=='Montserrat-Bold',('Fuente inesperada/fallback',line)
  assert 'OpenAI' not in line and '/usr/share/fonts/' not in line,('Fuente del host no autorizada',line)
 return selections
def ffprobe(path,count=False):
 cmd=['ffprobe','-v','error']+(['-count_frames'] if count else [])+['-show_streams','-show_format','-of','json',str(path)]
 return json.loads(subprocess.run(cmd,capture_output=True,text=True,check=True).stdout)
def atomically_encode(cmd,target,log):
 target=Path(target);target.parent.mkdir(parents=True,exist_ok=True)
 tmp=target.with_name(target.stem+'.partial.mp4')
 try:
  command(cmd+[str(tmp)],log)
  probe=ffprobe(tmp);assert any(s['codec_type']=='video' for s in probe['streams'])
  os.replace(tmp,target)
 finally:
  if tmp.exists():tmp.unlink()

def assemble_audio(root,v,timings,work):
 sr=48000;n=round(v['duration']*sr);voice=np.zeros(n,dtype='float64')
 music,rate=sf.read(root/'recursos/audio/campana_salud_112bpm.wav',always_2d=True)
 assert rate==sr and music.shape[1]==2 and len(music)>=n,'Música requiere estéreo 48 kHz y duración suficiente'
 music=music[:n].astype('float64').copy();ranges=[];gains=[]
 # Fade de pieza, independiente de la longitud de la composición maestra.
 music[:round(.08*sr)]*=np.linspace(0,1,round(.08*sr))[:,None]
 music[-round(.3*sr):]*=np.linspace(1,0,round(.3*sr))[:,None]
 for s in v['scenes']:
  a,rate=sf.read(root/'audio/escenas'/f'{s["id"]}.wav');assert rate==24000 and a.ndim==1,'Voz debe ser mono 24 kHz'
  assert abs(len(a)/rate-float(timings[s['id']]['duration']))<1/rate+.000001,(s['id'],'duración WAV difiere')
  a=resample_poly(a,2,1);start=round((s['start']+VOICE_OFFSET)*sr)
  assert start+len(a)<=round(s['end']*sr),(s['id'],'audio fuera de escena')
  assert np.isfinite(a).all() and np.max(np.abs(a))<1,'Voz inválida o saturada'
  voice[start:start+len(a)]+=a
  vr=float(np.sqrt(np.mean(a*a)));mr=float(np.sqrt(np.mean(music[start:start+len(a)]**2)))
  assert vr>1e-8 and mr>1e-10,(s['id'],'voz/música vacía')
  gains.append(vr/mr*10**(-21/20));ranges.append((s,start,len(a)))
 music*=min(gains)
 close=round((v['duration']-5)*sr);ramp=min(round(.02*sr),close)
 music[close-ramp:close]*=np.linspace(1,10**(-3/20),ramp)[:,None]
 music[close:]*=10**(-3/20)
 balance=[]
 for s,start,count in ranges:
  vr=float(np.sqrt(np.mean(voice[start:start+count]**2)));mr=float(np.sqrt(np.mean(music[start:start+count]**2)))
  db=20*math.log10(vr/(mr+1e-15));minimum=24 if s==v['scenes'][-1] else 21
  assert db>=minimum-.001,(s['id'],'balance de mezcla')
  balance.append({'scene':s['id'],'voice_over_music_rms_db':db,'required_db':minimum})
 narration=root/'audio/locuciones'/f'{v["slug"]}.wav';narration.parent.mkdir(parents=True,exist_ok=True)
 tmp=narration.with_name(narration.stem+'.partial.wav');sf.write(tmp,voice,sr,subtype='PCM_24');os.replace(tmp,narration)
 # WAV float evita recorte antes de loudnorm incluso si la suma supera 0 dBFS.
 mix=work/'mezcla_float.wav';sf.write(mix,music+voice[:,None],sr,subtype='FLOAT')
 save_json(work/'balance.json',balance)
 return mix,balance

def source_fingerprint(root,v,timings):
 paths=[root/'recursos/audio/campana_salud_112bpm.wav']+sorted((root/'recursos/fuentes').glob('*.ttf'))
 for scene in v['scenes']:
  paths.append(root/'audio/escenas'/f'{scene["id"]}.wav')
  image=root/'recursos/graficos'/f'{scene["id"]}.png';paths.append(image)
  detail=image.with_name(image.stem+'_detalle.png')
  if detail.exists():paths.append(detail)
 return {'sequence':hashlib.sha256(json.dumps(v,ensure_ascii=False,sort_keys=True).encode()).hexdigest(),'timings':hashlib.sha256(json.dumps([timings[s['id']] for s in v['scenes']],ensure_ascii=False,sort_keys=True).encode()).hexdigest(),'files':{str(p.relative_to(root)):digest(p) for p in paths},'renderer_code':digest(Path(__file__))}

def render_video(root,v,timings,work,fonts_hash,ffmpeg_version,font):
 source_before=source_fingerprint(root,v,timings)
 work.mkdir(parents=True,exist_ok=True);events=subtitle_events(v,timings,font)
 subtitles=root/'subtitulos';subtitles.mkdir(exist_ok=True)
 write_ass(subtitles/f'{v["slug"]}.ass',events)
 atomic_text(subtitles/f'{v["slug"]}.srt','\n\n'.join(f'{i}\n{srt_time(e["start"])} --> {srt_time(e["end"])}\n'+ '\n'.join(e['lines']) for i,e in enumerate(events,1))+'\n')
 save_json(work/'subtitulos_eventos.json',events);parts=[];segment_records=[]
 for s in v['scenes']:
  png=root/'recursos/graficos'/f'{s["id"]}.png';detail=png.with_name(png.stem+'_detalle.png')
  for image in [png]+([detail] if detail.exists() else []):
   with Image.open(image) as im:assert im.size==(1080,1920) and im.mode=='RGBA',(image,'requiere RGBA1080×1920')
  a,b=s['start'],s['end'];phases=[(a,b,png)]
  if detail.exists() and b-a>=5:
   cut=round((a+b)/2*FPS)/FPS;phases=[(a,cut,png),(cut,b,detail)]
  for index,(a,b,image) in enumerate(phases):
   stem=f'{s["id"]}_{index}';part=work/f'{stem}.mp4';ap=work/f'{stem}.ass';duration=b-a
   write_ass(ap,[e for e in events if e['start']<b and e['end']>a],a,b)
   fades=(',fade=t=in:st=0:d=0.18:alpha=1' if a==s['start'] else '')+(f',fade=t=out:st={duration-.1}:d=0.1:alpha=1' if b==s['end'] else '')
   motion='12*max(0,1-t/0.18)' if a==s['start'] else '0'
   # RGB permanece en rango completo hasta la conversión real a YUV709 limitado.
   vf=f"format=rgba{fades}[fg];color=c={BG}:s=1080x1920:r=30:d={duration},format=rgba[bg];[bg][fg]overlay=x=0:y='{motion}':shortest=1:format=rgb,subtitles={ap}:fontsdir={root/'recursos/fuentes'},scale=iw:ih:in_range=pc:out_range=tv:out_color_matrix=bt709,format=yuv420p"
   cmd=['ffmpeg','-hide_banner','-y','-loop','1','-framerate','30','-i',str(image),'-filter_complex',vf,'-t',str(duration),'-an','-c:v','libx264','-threads','2','-preset','veryfast','-profile:v','high','-b:v','10M','-maxrate','14M','-bufsize','20M','-r','30','-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709','-color_range','tv']
   key=hashlib.sha256(json.dumps({'schema':CACHE_SCHEMA,'png':digest(image),'ass':digest(ap),'cmd':cmd,'fonts':fonts_hash,'ffmpeg':ffmpeg_version},sort_keys=True).encode()).hexdigest();stamp=work/f'{stem}.json'
   cached=json.loads(stamp.read_text()) if stamp.exists() else {}
   valid=part.exists() and cached.get('key')==key and cached.get('output_sha256')==digest(part)
   if not valid:
    atomically_encode(cmd,part,work/f'{stem}.log');save_json(stamp,{'key':key,'output_sha256':digest(part)})
   font_selection=verify_font_selection(work/f'{stem}.log','Dialogue:' in ap.read_text())
   parts.append(part);segment_records.append({'scene':s['id'],'phase':index,'start':a,'end':b,'cache_key':key,'reused':valid,'has_subtitles':'Dialogue:' in ap.read_text(),'font_selection':font_selection})
 listing=work/'concat.txt';atomic_text(listing,'\n'.join("file '"+str(p).replace("'","'\\''")+"'" for p in parts)+'\n')
 mix,balance=assemble_audio(root,v,timings,work)
 measurement=subprocess.run(['ffmpeg','-hide_banner','-i',str(mix),'-af','loudnorm=I=-16:TP=-2.2:LRA=7:print_format=json','-f','null','-'],capture_output=True,text=True,check=True)
 atomic_text(work/'loudnorm_pasada1.log',measurement.stderr);m=json_from_ffmpeg(measurement.stderr)
 af='loudnorm=I=-16:TP=-2.2:LRA=7:measured_I='+m['input_i']+':measured_TP='+m['input_tp']+':measured_LRA='+m['input_lra']+':measured_thresh='+m['input_thresh']+':offset='+m['target_offset']+':linear=true:print_format=json'
 output=root/'videos'/f'{v["slug"]}.mp4'
 cmd=['ffmpeg','-hide_banner','-y','-f','concat','-safe','0','-i',str(listing),'-i',str(mix),'-map','0:v','-map','1:a','-af',af,'-c:v','copy','-bsf:v','h264_metadata=colour_primaries=1:transfer_characteristics=1:matrix_coefficients=1','-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709','-c:a','aac','-b:a','192k','-ar','48000','-ac','2','-t',str(v['duration']),'-movflags','+faststart']
 atomically_encode(cmd,output,work/'mux.log')
 assert source_before==source_fingerprint(root,v,timings),'Las entradas cambiaron durante el render'
 result={'source_inputs':source_before,'id':v['id'],'file':str(output.relative_to(root)),'sha256':digest(output),'segments':segment_records,'voice_music_balance':balance,'subtitle_events':events,'publication':'BLOQUEADA_FICHAS_MARCA_ESCUCHA_MOVIL'}
 save_json(root/'revision/qa'/f'{v["slug"]}_render.json',result)
 print(f'RENDER {v["id"]} {output.name}',flush=True);return result

def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);parser.add_argument('--only',nargs='+');parser.add_argument('--cache',type=Path,default=Path('/tmp/bupa_v3_render'));args=parser.parse_args()
 root=args.root.resolve();manifest,videos,timings=read_inputs(root)
 if args.only:
  requested=set(args.only);videos=[v for v in videos if v['slug'] in requested or v['id'] in requested];assert len(videos)==len(requested),'Selector --only desconocido'
 fonts=sorted((root/'recursos/fuentes').glob('*.ttf'));assert fonts,'Faltan fuentes TTF'
 fonts_hash={p.name:digest(p) for p in fonts};bold=next((p for p in fonts if p.name=='Montserrat-Bold.ttf'),None);assert bold,'Falta Montserrat-Bold.ttf';font=ImageFont.truetype(str(bold),48)
 ffmpeg_version=subprocess.run(['ffmpeg','-version'],capture_output=True,text=True,check=True).stdout
 cache=args.cache.resolve();assert not cache.is_relative_to(root),'La caché debe estar fuera del checkout';cache.mkdir(parents=True,exist_ok=True)
 lock=(cache/'ejecucion.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 namespace=hashlib.sha256(str(root).encode()).hexdigest()[:12]
 # Fontconfig queda limitado a fuentes entregadas: no heredar aliases del host.
 config=cache/namespace/'fonts.conf';font_cache=cache/namespace/'fontconfig_cache';font_cache.mkdir(parents=True,exist_ok=True)
 atomic_text(config,'<?xml version="1.0"?><!DOCTYPE fontconfig SYSTEM "urn:fontconfig:fonts.dtd"><fontconfig><dir>'+xml_escape(str(root/'recursos/fuentes'))+'</dir><cachedir>'+xml_escape(str(font_cache))+'</cachedir></fontconfig>')
 os.environ['FONTCONFIG_FILE']=str(config);os.environ['FONTCONFIG_PATH']=str(config.parent)
 # Un render nuevo invalida el QA anterior hasta revisar de nuevo los MP4.
 save_json(root/'revision/qa/resumen.json',{'technical_pass':False,'status':'PENDING_QA_AFTER_RENDER','render_final_publicable':False})
 save_json(root/'revision/qa/renderizado.json',{'status':'IN_PROGRESS','selected':[v['id'] for v in videos],'publication':'NO_AUTORIZADA'})
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
  results=list(pool.map(lambda v:render_video(root,v,timings,cache/namespace/v['slug'],fonts_hash,ffmpeg_version,font),videos))
 save_json(root/'revision/qa/renderizado.json',{'status':'COMPLETE','selected':[v['id'] for v in videos],'results':results,'inputs':{'sequences_sha256':digest(root/'contenido/secuencias.json'),'voice_timings_sha256':digest(root/'revision/tiempos_voz.json'),'fonts':fonts_hash,'music_sha256':digest(root/'recursos/audio/campana_salud_112bpm.wav')},'ffmpeg':ffmpeg_version,'fontconfig':{'scope':'Solo fuentes entregadas; sin configuración ni aliases del host','config_sha256':digest(config)},'human_review':'PENDIENTE','publication':'NO_AUTORIZADA'})
 print('Render terminado. Ejecutar verificar.py; este resultado no acredita revisión humana ni publicación.',flush=True)
if __name__=='__main__':main()
