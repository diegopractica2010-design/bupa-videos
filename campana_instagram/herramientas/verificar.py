#!/usr/bin/env python3
"""QA técnico de los archivos exactos entregados; no certifica escucha ni publicidad.
Uso: python herramientas/verificar.py [--root RUTA] [--expected-count 10]
"""
from __future__ import annotations
import argparse, concurrent.futures, hashlib, importlib.util, json, math, re, struct, subprocess
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
spec=importlib.util.spec_from_file_location('bupa_render',Path(__file__).with_name('renderizar.py'));render=importlib.util.module_from_spec(spec);spec.loader.exec_module(render)


def atoms(path):
 found=[]
 with Path(path).open('rb') as f:
  while data:=f.read(8):
   assert len(data)==8,'Átomo MP4 truncado';size,kind=struct.unpack('>I4s',data);header=8
   if size==1:size=struct.unpack('>Q',f.read(8))[0];header=16
   found.append(kind.decode('ascii','replace'))
   if size==0:break
   assert size>=header,'Tamaño de átomo inválido';f.seek(size-header,1)
 return found

def ass_seconds(value):
 m=re.fullmatch(r'(\d+):([0-5]\d):([0-5]\d)\.(\d{2})',value)
 assert m,('Timestamp ASS inválido',value)
 h,mn,s,f=map(int,m.groups());return h*3600+mn*60+s+f/100

def subtitle_checks(root,v,timings):
 ass=root/'subtitulos'/f'{v["slug"]}.ass';srt=root/'subtitulos'/f'{v["slug"]}.srt';assert ass.exists() and srt.exists()
 events=[];previous=0;texts=[]
 for line in ass.read_text().splitlines():
  if not line.startswith('Dialogue:'):continue
  parts=line.split(',',9);a,b=ass_seconds(parts[1]),ass_seconds(parts[2]);assert b>a and a>=previous-.011 and b<=v['duration']+.011,(v['id'],'orden de subtítulos')
  previous=b;payload=re.sub(r'\{[^}]*\}','',parts[9]);lines=payload.split('\\N');assert 1<=len(lines)<=2 and all(len(x)<=32 for x in lines),(v['id'],'layout subtítulos')
  texts.extend(' '.join(lines).split());events.append((a,b,lines))
 assert texts==' '.join(s['voice'] for s in v['scenes']).split(),(v['id'],'texto perdido o agregado en ASS')
 srt_texts=[];srt_times=[]
 for block in srt.read_text().strip().split('\n\n'):
  lines=block.splitlines();assert len(lines)>=3
  m=re.fullmatch(r'(\d{2,}):([0-5]\d):([0-5]\d),(\d{3}) --> (\d{2,}):([0-5]\d):([0-5]\d),(\d{3})',lines[1]);assert m,lines[1]
  fields=list(map(int,m.groups()));a=fields[0]*3600+fields[1]*60+fields[2]+fields[3]/1000;b=fields[4]*3600+fields[5]*60+fields[6]+fields[7]/1000;assert b>a
  srt_times.append((a,b));srt_texts.extend(' '.join(lines[2:]).split())
 assert texts==srt_texts and len(events)==len(srt_times),'ASS y SRT difieren'
 assert all(abs(e[0]-s[0])<=.006 and abs(e[1]-s[1])<=.006 for e,s in zip(events,srt_times)),'Relojes ASS/SRT difieren'
 # El modelo propone los tiempos. Comprobarlos aquí no sustituye una escucha.
 font=render.ImageFont.truetype(str(root/'recursos/fuentes/Montserrat-Bold.ttf'),48)
 expected=render.subtitle_events(v,timings,font)
 assert len(events)==len(expected)
 for actual,e in zip(events,expected):assert abs(actual[0]-e['start'])<=.006 and abs(actual[1]-e['end'])<=.006
 return {'events':len(events),'text_literal':True,'format_and_order':True,'matches_voice_model_times':True,'human_sync':'PENDIENTE'}

def rect_overlap(a,b):return min(a['x']+a['w'],b['x']+b['w'])>max(a['x'],b['x'])+.5 and min(a['y']+a['h'],b['y']+b['h'])>max(a['y'],b['y'])+.5

def editable_concordance(root,videos):
 # Los editables deben describir la misma entrega que la secuencia renderizada.
 source=root/'contenido/guiones_v3.json';raw=json.loads(source.read_text())['videos']
 assert len(raw)==len(videos) and len({v['id'] for v in raw})==len(raw),'Cantidad o IDs de guiones distintos'
 by_id={v['id']:v for v in videos}
 for original in raw:
  current=by_id[original['id']]
  for key,value in original.items():
   if key=='scenes':
    assert len(value)==len(current['scenes']),(original['id'],'cantidad de escenas distinta')
    for a,b in zip(value,current['scenes']):
     assert all(b.get(k)==val for k,val in a.items()),(a['id'],'guion editable y secuencia no concuerdan')
   else:assert current.get(key)==value,(original['id'],key,'guion editable y secuencia no concuerdan')
 layout=json.loads((root/'revision/layout_graficos.json').read_text())
 assert isinstance(layout,dict) and layout.get('source_sha256')==render.digest(source),'Layout corresponde a otra versión del guion'
 return {'pass':True,'videos':len(raw),'scenes':sum(len(v['scenes']) for v in raw),'script_sha256':render.digest(source),'graphic_layout_matches_script':True}

def geometry(root,scene_ids):
 path=root/'revision/layout_graficos.json';data=json.loads(path.read_text())
 if isinstance(data,dict):data=data.get('items',data.get('elements',data.get('boxes',data.get('layout'))))
 assert isinstance(data,list),'layout_graficos debe ser lista o items/elements/boxes/layout'
 errors=[];text_boxes=[];present=set()
 for raw in data:
  if raw.get('scene') not in scene_ids:continue
  b=dict(raw);present.add(b['scene']);role=str(b.get('role','')).lower()
  if not all(k in b for k in ['x','y','w','h']):errors.append({'scene':b['scene'],'error':'faltan dimensiones','box':b});continue
  if not all(isinstance(b[k],(int,float)) and math.isfinite(b[k]) for k in ['x','y','w','h']):errors.append({'scene':b['scene'],'error':'dimensiones no finitas'});continue
  if b['w']<0 or b['h']<0 or b['x']<0 or b['y']<0 or b['x']+b['w']>1080+.5 or b['y']+b['h']>1920+.5:errors.append({'scene':b['scene'],'error':'fuera del lienzo','box':b})
  is_text=bool(b.get('text')) or bool(re.search(r'title|headline|product|note|caption|cta|phone|footer|text|label|identity|titulo|nota|texto',role))
  if is_text:
   if b['x']<96-.5 or b['x']+b['w']>960+.5:errors.append({'scene':b['scene'],'error':'texto fuera de margen horizontal seguro','box':b})
   if not re.search(r'footer|pie|revision|revisión',role) and (b['y']<300-.5 or b['y']+b['h']>1220+.5):errors.append({'scene':b['scene'],'error':'texto fuera de zona vertical de contenido','box':b})
   text_boxes.append(b)
   if not re.search(r'subtitle|subtitulo|subtítulo',role) and rect_overlap(b,{'x':96,'y':930,'w':864,'h':140}):errors.append({'scene':b['scene'],'error':'invade reserva subtítulos','box':b})
 overlaps=[]
 for i,a in enumerate(text_boxes):
  for b in text_boxes[i+1:]:
   if a['scene']==b['scene'] and a.get('variant','base')==b.get('variant','base') and rect_overlap(a,b):overlaps.append({'scene':a['scene'],'roles':[a.get('role'),b.get('role')],'texts':[a.get('text'),b.get('text')]})
 missing=sorted(scene_ids-present)
 return {'checked_items':len(data),'missing_scenes':missing,'errors':errors,'text_overlaps':overlaps,'pass':not(errors or overlaps or missing)}

def check_video(root,v,timings):
 path=root/'videos'/f'{v["slug"]}.mp4';out=root/'revision/qa'/v['slug'];out.mkdir(parents=True,exist_ok=True)
 initial_hash=render.digest(path);probe=render.ffprobe(path,count=True);render.save_json(out/'ffprobe.json',probe)
 video=next(s for s in probe['streams'] if s['codec_type']=='video');audio=next(s for s in probe['streams'] if s['codec_type']=='audio')
 checks={'dimensions':video['width']==1080 and video['height']==1920,'fps':video['avg_frame_rate']=='30/1','frame_count':int(video['nb_read_frames'])==round(v['duration']*30),'duration':abs(float(probe['format']['duration'])-v['duration'])<=1/30,'video_codec':video['codec_name']=='h264' and video['profile']=='High' and video['pix_fmt']=='yuv420p','rec709':all(video.get(k)=='bt709' for k in ['color_space','color_transfer','color_primaries']) and video.get('color_range')=='tv','audio_codec':audio['codec_name']=='aac' and audio['profile']=='LC' and audio['sample_rate']=='48000' and audio['channels']==2}
 aa=atoms(path);checks['faststart']='moov' in aa and 'mdat' in aa and aa.index('moov')<aa.index('mdat')
 # Comprobar realmente la cadencia, no únicamente la media de fotogramas.
 pts=subprocess.run(['ffprobe','-v','error','-select_streams','v:0','-show_entries','frame=best_effort_timestamp_time','-of','csv=p=0',str(path)],capture_output=True,text=True,check=True).stdout
 times=[float(m[1]) for line in pts.splitlines() if (m:=re.match(r'^(-?\d+(?:\.\d+)?)',line))]
 checks['cfr_timestamps']=len(times)==round(v['duration']*30) and all(abs((b-a)-1/30)<.00002 for a,b in zip(times,times[1:]));render.atomic_text(out/'frame_timestamps.csv',pts)
 decoded=subprocess.run(['ffmpeg','-hide_banner','-xerror','-i',str(path),'-vf','blackdetect=d=0.1:pix_th=0.05','-af','loudnorm=I=-16:TP=-1.5:LRA=7:print_format=json','-f','null','-'],capture_output=True,text=True)
 render.atomic_text(out/'decodificacion_y_audio.log',decoded.stderr);checks['full_decode']=decoded.returncode==0
 loud=render.json_from_ffmpeg(decoded.stderr);checks['mix_lufs']=abs(float(loud['input_i'])+16)<=1;checks['mix_truepeak']=float(loud['input_tp'])<=-1.5;black=re.findall(r'black_start:([\d.]+) black_end:([\d.]+) black_duration:([\d.]+)',decoded.stderr);checks['no_black_intervals']=not black
 subs=subtitle_checks(root,v,timings);checks['subtitles']=True
 source_render=json.loads((root/'revision/qa'/f'{v["slug"]}_render.json').read_text());balance=source_render['voice_music_balance'];checks['voice_music_balance']=len(balance)==len(v['scenes']) and all(x['voice_over_music_rms_db']>=x['required_db']-.001 for x in balance)
 segments=source_render.get('segments',[])
 checks['subtitle_font_no_host_fallback']=bool(segments) and all('font_selection' in x and (x['font_selection'] or not x.get('has_subtitles',True)) and all(re.search(r'\(Montserrat,\s*700,\s*0\)',line) and line.rsplit(', ',1)[-1]=='Montserrat-Bold' and 'OpenAI' not in line and '/usr/share/fonts/' not in line for line in x['font_selection']) for x in segments)
 checks['render_hash_matches']=source_render['sha256']==initial_hash
 checks['source_inputs_current']=source_render.get('source_inputs')==render.source_fingerprint(root,v,timings)
 sheet=Image.new('RGB',(1080,math.ceil(len(v['scenes'])/3)*660),'white');draw=ImageDraw.Draw(sheet);contact_files=[]
 for i,s in enumerate(v['scenes']):
  t=(s['start']+s['end'])/2
  # Mostrar contenido después del posible corte interno, no su fotograma limítrofe.
  if s['end']-s['start']>=5:t=min(s['end']-.2,t+.35)
  image=out/f'{s["id"]}.png';subprocess.run(['ffmpeg','-v','error','-y','-ss',str(t),'-i',str(path),'-vf','scale=360:640','-frames:v','1',str(image)],check=True)
  with Image.open(image) as im:sheet.paste(im,((i%3)*360,(i//3)*660))
  draw.text(((i%3)*360+5,(i//3)*660+643),f'{s["id"]} · {t:.2f}s',fill='black');contact_files.append(str(image.relative_to(root)))
 sheet.save(out/'contacto_6_escenas.jpg',quality=92)
 final_hash=render.digest(path);checks['file_unchanged_during_qa']=initial_hash==final_hash
 result={'id':v['id'],'file':str(path.relative_to(root)),'sha256':final_hash,'checks':checks,'loudness_mix':loud,'black_intervals':black,'subtitle_validation':subs,'voice_music_balance_pre_loudnorm':balance,'contact_sheet':str((out/'contacto_6_escenas.jpg').relative_to(root)),'sampled_frames':contact_files,'human_review':'PENDIENTE_ESCUCHA_Y_REPRODUCCION_COMPLETA','publication':'BLOQUEADA_FICHAS_IDENTIDAD_MARCA_MOVIL'}
 render.save_json(out/'resultado.json',result);print(v['id'],'PASS' if all(checks.values()) else {k:x for k,x in checks.items() if not x},flush=True);return result

def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);parser.add_argument('--expected-count',type=int,default=10);args=parser.parse_args();root=args.root.resolve()
 render.save_json(root/'revision/qa/resumen.json',{'technical_pass':False,'status':'IN_PROGRESS','render_final_publicable':False})
 production=json.loads((root/'revision/qa/renderizado.json').read_text());assert production.get('status')=='COMPLETE','Render previo no terminó'
 manifest,videos,timings=render.read_inputs(root);assert len(videos)==args.expected_count,('Cantidad de videos inesperada',len(videos));expected={v['slug']+'.mp4' for v in videos};actual={p.name for p in (root/'videos').glob('*.mp4')};assert expected==actual,('Archivos ausentes o inesperados',sorted(expected-actual),sorted(actual-expected))
 boundary={'ass_9.999':render.ass_time(9.999)=='0:00:10.00','ass_59.999':render.ass_time(59.999)=='0:01:00.00','srt_0.9996':render.srt_time(.9996)=='00:00:01,000'};assert all(boundary.values())
 concordance=editable_concordance(root,videos)
 geom=geometry(root,{s['id'] for v in videos for s in v['scenes']});results=[];failures=[]
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
  future={pool.submit(check_video,root,v,timings):v for v in videos}
  for f in concurrent.futures.as_completed(future):
   try:results.append(f.result())
   except Exception as e:
    v=future[f];failures.append({'id':v['id'],'error':repr(e)});print(v['id'],'ERROR',repr(e),flush=True)
 results.sort(key=lambda x:x['id']);technical=not failures and len(results)==len(videos) and geom['pass'] and all(all(v['checks'].values()) for v in results)
 summary={'status':'COMPLETE','technical_pass':technical,'videos':results,'errors':failures,'geometry':geom,'editable_concordance':concordance,'timestamp_boundary_tests':boundary,'source_inputs_sha256':{'sequences':render.digest(root/'contenido/secuencias.json'),'voice_timings':render.digest(root/'revision/tiempos_voz.json'),'graphic_layout':render.digest(root/'revision/layout_graficos.json')},'scope':'Archivos exportados exactos; comprobaciones automáticas y muestreo visual, no revisión humana continua. No se modifican ni borran originales.','render_final_publicable':False,'pending':['Validación de fichas y vigencia comercial','Identidad y conformidad de marca','Escucha humana: naturalidad, pronunciación, acento y sincronía perceptiva','Reproducción completa y vista móvil con interfaz de Instagram','Prueba de enlaces y cuenta WhatsApp sin enviar mensajes','Autorización separada de cualquier publicación o inversión'],'sales_or_performance_validated':False}
 render.save_json(root/'revision/qa/resumen.json',summary)
 if not technical:raise SystemExit('QA técnico incompleto o fallido; consultar revision/qa/resumen.json')
 print(f'{len(results)}/{len(videos)} MP4 pasan QA técnico. Revisión humana/comercial pendiente; no habilita publicación.',flush=True)
if __name__=='__main__':main()
