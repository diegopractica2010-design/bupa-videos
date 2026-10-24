"""Comprobaciones técnicas de las pruebas internas; no aprueba publicación."""
from pathlib import Path
import json,subprocess,hashlib,re,struct,csv,io
from PIL import Image,ImageDraw
from concurrent.futures import ThreadPoolExecutor
R=Path(__file__).resolve().parents[1]
V=json.loads((R/'editables/secuencias_reconstruidas_del_informe.json').read_text())['videos']
def hashfile(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  while chunk:=f.read(1024*1024):h.update(chunk)
 return h.hexdigest()
def atoms(p):
 result=[]
 with p.open('rb') as f:
  while True:
   data=f.read(8)
   if len(data)<8:break
   size,kind=struct.unpack('>I4s',data)
   if size==1:size=struct.unpack('>Q',f.read(8))[0];extra=16
   else:extra=8
   result.append(kind.decode('ascii','replace'))
   if size<extra:break
   f.seek(size-extra,1)
 return result

def check(v):
 p=R/'renders_revision'/f'{v["slug"]}_instagram_whatsapp_v1_REVISION_SIN_VOZ.mp4'
 out=R/'comprobaciones'/v['slug'];out.mkdir(exist_ok=True)
 probe=subprocess.run(['ffprobe','-v','error','-count_frames','-show_streams','-show_format','-of','json',str(p)],capture_output=True,text=True,check=True)
 data=json.loads(probe.stdout);(out/'ffprobe.json').write_text(probe.stdout)
 video=next(s for s in data['streams'] if s['codec_type']=='video');audio=next(s for s in data['streams'] if s['codec_type']=='audio')
 checks=dict(dimensions=video['width']==1080 and video['height']==1920,fps=video['avg_frame_rate']=='30/1',frames=int(video['nb_read_frames'])==round(v['duration']*30),duration=abs(float(data['format']['duration'])-v['duration'])<1/30,video_codec=video['codec_name']=='h264' and video['profile']=='High' and video['pix_fmt']=='yuv420p',rec709=all(video.get(k)=='bt709' for k in ['color_space','color_transfer','color_primaries']),audio=audio['codec_name']=='aac' and audio['profile']=='LC' and audio['sample_rate']=='48000' and audio['channels']==2)
 aa=atoms(p);checks['faststart']=aa.index('moov')<aa.index('mdat')
 decode=subprocess.run(['ffmpeg','-hide_banner','-v','error','-xerror','-i',str(p),'-map','0:v','-map','0:a','-f','null','-'],capture_output=True,text=True)
 (out/'decodificacion.log').write_text(decode.stderr or 'Decodificación íntegra sin errores; exit 0.\n');checks['full_decode']=decode.returncode==0
 loud=subprocess.run(['ffmpeg','-hide_banner','-i',str(p),'-af','loudnorm=I=-16:TP=-1.5:LRA=7:print_format=json','-f','null','-'],capture_output=True,text=True,check=True)
 (out/'loudness.log').write_text(loud.stderr);lm=json.JSONDecoder().raw_decode(loud.stderr[loud.stderr.rfind('{'):])[0];checks['music_only_lufs']=abs(float(lm['input_i'])+16)<=1;checks['music_only_truepeak']=float(lm['input_tp'])<=-1.5
 sheet=Image.new('RGB',(1080,1320),'white');d=ImageDraw.Draw(sheet);bg_samples=[]
 for i,s in enumerate(v['scenes']):
  img=out/(s['id']+'.png');t=(s['start']+s['end'])/2
  if s['internal_cut'] and abs(t-s['internal_cut'])<.3:t+=.35
  subprocess.run(['ffmpeg','-v','error','-y','-ss',str(t),'-i',str(p),'-vf','scale=360:640','-frames:v','1',str(img)],check=True)
  bg_samples.append(Image.open(img).getpixel((5,5)))
  x=(i%3)*360;y=(i//3)*660;sheet.paste(Image.open(img),(x,y));d.text((x+5,y+642),f'{s["id"]} - {t:g}s',fill='black')
 sheet.save(out/'contacto_6_escenas.jpg',quality=92)
 checks['background_conversion']=all(max(abs(a-b) for a,b in zip(rgb,(244,248,250)))<=4 for rgb in bg_samples)
 result=dict(id=v['id'],file=str(p.relative_to(R)),sha256=hashfile(p),checks=checks,loudness_music_only=lm,background_rgb_samples=bg_samples,missing_stock=[s['id'] for s in v['scenes'] if s['missing_stock']],publication='BLOQUEADA',voice='AUSENTE_AUTORIZACION_PENDIENTE',subtitle_sync='PROVISIONAL_SIN_VOZ_NO_VERIFICABLE')
 (out/'resultado.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
 print(v['id'],'PASS' if all(checks.values()) else checks,flush=True);return result
if __name__=='__main__':
 with ThreadPoolExecutor(max_workers=2) as ex:results=list(ex.map(check,V))
 before=json.loads((R/'comprobaciones/originales_sha256_antes.json').read_text());after={p.name:hashfile(p) for p in (R.parent/'output').glob('*.mp4')};assert before==after
 (R/'comprobaciones/originales_sha256_despues.json').write_text(json.dumps(after,indent=2))
 layouts=json.loads((R/'comprobaciones/layout.json').read_text());overflow=[x for x in layouts if x['x']+x['width']>960 or x['bottom']>1220]
 overlaps=[]
 for i,a in enumerate(layouts):
  for b in layouts[i+1:]:
   if (a.get('scene'),a.get('variant'))!=(b.get('scene'),b.get('variant')):continue
   if a['x']<b['x']+b['width'] and b['x']<a['x']+a['width'] and a['y']<b['bottom'] and b['y']<a['bottom']:overlaps.append([a,b])
 summary=dict(videos=results,originales_intactos=before==after,layout_overflow=overflow,text_box_overlaps=overlaps,render_final_publicable=False,checks_pendientes=['12 tomas limpias','Logos y conformidad de marca B01','Procedencia y licencias del stock B02','Vigencia comercial y voz autorizada B03','Locución y mezcla con ducking de voz','Sincronía real de subtítulos ±100ms','Escucha humana y revisión móvil B04','Apertura WhatsApp y conexión al anuncio sin enviar mensajes B05','Validación Meta B07','Contraste con plan_maestro.json, ordenes_ejecucion.json y enlaces_whatsapp.json fuente ausentes'])
 (R/'comprobaciones/resumen_qa.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
 assert not overflow
 assert not overlaps
 assert all(all(v['checks'].values()) for v in results)
 print('10/10 pruebas técnicas completadas. Originales intactos. Publicación bloqueada.',flush=True)
