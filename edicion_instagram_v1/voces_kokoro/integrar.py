"""Integra locución local y mezcla; no publica ni cambia originales."""
from pathlib import Path
import json,math,copy,subprocess,importlib.util,sys,hashlib
import numpy as np,soundfile as sf
from scipy.signal import resample_poly
from concurrent.futures import ThreadPoolExecutor
R=Path(__file__).resolve().parent;P=R.parent
spec=importlib.util.spec_from_file_location('base',P/'editables/producir.py');base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
D={r['id']:r for r in json.loads((R/'comprobaciones/locuciones_y_tiempos.json').read_text())}
V=copy.deepcopy(base.V);changes=[]
for v in V:
 scenes=v['scenes'];dur=[round((s['end']-s['start'])*30) for s in scenes]
 needed=[math.ceil((D[s['id']]['duration']+.04)*30) for s in scenes]
 for i in range(5):
  if needed[i]>dur[i]:
   extra=needed[i]-dur[i]
   for j in sorted((j for j in range(5) if j!=i),key=lambda j:abs(j-i)):
    take=min(extra,max(0,dur[j]-needed[j]-3));dur[j]-=take;dur[i]+=take;extra-=take
    if extra==0:break
   assert extra==0,scenes[i]['id']
 at=0
 for s,n in zip(scenes,dur):
  old=copy.deepcopy(s);s['start']=at/30;s['end']=(at+n)/30;at+=n
  if s['internal_cut']:
   fraction=(old['internal_cut']-old['start'])/(old['end']-old['start']);s['internal_cut']=round((s['start']+fraction*(s['end']-s['start']))*30)/30
  if s['start']!=old['start'] or s['end']!=old['end']:changes.append({'id':s['id'],'antes':[old['start'],old['end']],'ahora':[s['start'],s['end']],'motivo':'Ajuste de respiración de voz sin cortar palabras ni superar 1.05x; duración total y cierre 5s conservados.'})
 assert at==round(v['duration']*30) and dur[-1]==150
(R/'secuencias_con_voz_v2.json').write_text(json.dumps({'videos':V,'ajustes_temporales':changes},ensure_ascii=False,indent=2))

def word_times(s):
 r=D[s['id']];groups=[];group=[]
 for t in r['timings']:
  if t['phoneme']==' ':
   if group:groups.append(group);group=[]
  else:group.append(t)
 if group:groups.append(group)
 result=[];j=0
 for word in r['text'].split():
  count=2 if word.lower().strip('.,;:!?') in ['integramédica','multisalud','whatsapp'] else 1
  chunk=groups[j:j+count];assert len(chunk)==count,(r['id'],word)
  result.append((chunk[0][0]['start'],chunk[-1][-1]['end']));j+=count
 assert j==len(groups),(r['id'],j,len(groups))
 return result

def subtitles(v):
 events=[];srt=[]
 for s in v['scenes']:
  times=word_times(s);chunks=base.subtitle_chunks(s['voice']);j=0
  for chunk in chunks:
   count=len(' '.join(chunk).split());a=s['start']+.02+times[j][0];b=s['start']+.02+times[j+count-1][1]+.07
   if j+count<len(times):b=min(b,s['start']+.02+times[j+count][0])
   b=min(b,s['end']);assert a<b
   events.append((a,b,'\\N'.join(chunk)));srt.append((a,b,'\n'.join(chunk)));j+=count
 return events,srt

def ass(p,events,duration):
 base.write_ass(p,events,duration)
 p.write_text(p.read_text().replace('Sin voz autorizada · marca pendiente','Voz sintética · marca pendiente'))

def mix(v):
 voice=np.zeros(round(v['duration']*48000),dtype='float64');music,sr=sf.read(P/'recursos/campana_salud_112bpm.wav');music=music[:len(voice)].astype('float64');assert sr==48000
 music[-14400:]*=np.linspace(1,0,14400)[:,None]
 gains=[];ranges=[]
 for s in v['scenes']:
  a,sr=sf.read(R/'escenas'/f'{s["id"]}.wav');assert sr==24000
  a=resample_poly(a,2,1);start=round((s['start']+.02)*48000);assert start+len(a)<=round(s['end']*48000)
  voice[start:start+len(a)]+=a
  vm=np.sqrt(np.mean(a*a));mm=np.sqrt(np.mean(music[start:start+len(a)]**2));gains.append(vm/(mm+1e-12)*10**(-21/20));ranges.append((s['id'],start,len(a)))
 gain=min(gains);music*=gain
 close=round((v['duration']-5)*48000);music[close:]*=10**(-3/20)
 report=[]
 for oid,start,n in ranges:
  vr=np.sqrt(np.mean(voice[start:start+n]**2));mr=np.sqrt(np.mean(music[start:start+n]**2));diff=20*np.log10(vr/(mr+1e-12));assert diff>=20.99
  report.append({'id':oid,'voz_sobre_musica_rms_db':float(diff)})
 stereo=music+voice[:,None];p=R/f'{v["slug"]}_mezcla_previa.wav';assert np.max(np.abs(stereo))<1
 sf.write(R/f'{v["slug"]}_locucion_ajustada.wav',voice,48000,subtype='PCM_24');sf.write(p,stereo,48000,subtype='PCM_24')
 (R/'comprobaciones'/f'{v["slug"]}_mezcla.json').write_text(json.dumps(report,indent=2));return p

def render(v):
 work=R/'trabajo'/v['slug'];work.mkdir(parents=True,exist_ok=True);events,srt=subtitles(v)
 ass(R/f'{v["slug"]}.ass',events,v['duration'])
 (R/f'{v["slug"]}.srt').write_text('\n\n'.join(f'{i}\n{base.srt_time(a)} --> {base.srt_time(b)}\n{t}' for i,(a,b,t) in enumerate(srt,1)))
 parts=[]
 for s in v['scenes']:
  chunks=[(s['start'],s['end'],False)]
  if s['internal_cut'] and s['graphic'] and not s['missing_stock']:chunks=[(s['start'],s['internal_cut'],False),(s['internal_cut'],s['end'],True)]
  for a,b,var in chunks:
   stem=s['id']+('_texto' if var else '');png=P/'recursos'/v['slug']/f'{stem}.png';out=work/f'{stem}.mp4';d=b-a
   ap=work/f'{stem}.ass';ev=[(max(x,a)-a,min(y,b)-a,t) for x,y,t in events if x<b and y>a];ass(ap,ev,d)
   fades=(',fade=t=in:st=0:d=0.18:alpha=1' if a==s['start'] else '')+(f',fade=t=out:st={d-.1}:d=0.1:alpha=1' if b==s['end'] else '')
   motion='12*max(0,1-t/0.18)' if a==s['start'] else '0'
   vf=f"format=rgba{fades}[fg];color=c=#F4F8FA:s=1080x1920:r=30:d={d},format=rgba[bg];[bg][fg]overlay=x=0:y='{motion}':shortest=1:format=rgb,subtitles={ap}:fontsdir={P/'recursos'},scale=iw:ih:in_range=pc:out_range=tv:out_color_matrix=bt709,format=yuv420p"
   cmd=['ffmpeg','-hide_banner','-y','-loop','1','-framerate','30','-i',str(png),'-filter_complex',vf,'-t',str(d),'-an','-c:v','libx264','-threads','2','-preset','veryfast','-profile:v','high','-b:v','10M','-maxrate','14M','-bufsize','20M','-r','30','-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709','-color_range','tv',str(out)]
   key=hashlib.sha256(png.read_bytes()+ap.read_bytes()+json.dumps(cmd).encode()).hexdigest();stamp=out.with_suffix('.sha256')
   if not out.exists() or not stamp.exists() or stamp.read_text()!=key:base.run(cmd,work/f'{stem}.log');stamp.write_text(key)
   parts.append(out)
 listing=work/'concat.txt';listing.write_text('\n'.join("file '"+str(p)+"'" for p in parts));mixfile=mix(v)
 first=subprocess.run(['ffmpeg','-hide_banner','-i',str(mixfile),'-af','loudnorm=I=-16:TP=-2.2:LRA=7:print_format=json','-f','null','-'],capture_output=True,text=True,check=True)
 (work/'loudnorm_pasada1.log').write_text(first.stderr);m=json.JSONDecoder().raw_decode(first.stderr[first.stderr.rfind('{'):])[0]
 af='loudnorm=I=-16:TP=-2.2:LRA=7:measured_I='+m['input_i']+':measured_TP='+m['input_tp']+':measured_LRA='+m['input_lra']+':measured_thresh='+m['input_thresh']+':offset='+m['target_offset']+':linear=true:print_format=json'
 output=P/'renders_con_voz'/f'{v["slug"]}_instagram_whatsapp_voz_v2_REVISION.mp4';output.parent.mkdir(exist_ok=True)
 base.run(['ffmpeg','-hide_banner','-y','-f','concat','-safe','0','-i',str(listing),'-i',str(mixfile),'-map','0:v','-map','1:a','-af',af,'-c:v','copy','-bsf:v','h264_metadata=colour_primaries=1:transfer_characteristics=1:matrix_coefficients=1','-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709','-c:a','aac','-b:a','192k','-ar','48000','-ac','2','-t',str(v['duration']),'-movflags','+faststart',str(output)],work/'mux.log')
 print('RENDER CON VOZ',v['id'],flush=True)
if __name__=='__main__':
 with ThreadPoolExecutor(max_workers=2) as ex:list(ex.map(render,V))
