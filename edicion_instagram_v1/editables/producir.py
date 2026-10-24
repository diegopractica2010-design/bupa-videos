"""Produce pruebas internas. Nunca usa ni modifica el audio/video original.
Requiere Python 3, Pillow, numpy, scipy, FFmpeg (libx264/libass) y fuentes incluidas.
Ejecutar desde cualquier carpeta: python producir.py [--prepare-only].
JSON reconstruido del informe, no sustituto de los JSON fuente pendientes.
"""
from pathlib import Path
import json, math, re, textwrap, subprocess, hashlib, html, sys, shutil
import numpy as np
from scipy.io.wavfile import write as wavwrite
from PIL import Image, ImageDraw, ImageFont
from concurrent.futures import ThreadPoolExecutor
R=Path(__file__).resolve().parents[1]
V=json.loads((R/'editables/secuencias_reconstruidas_del_informe.json').read_text())['videos']
BG='#F4F8FA'; INK='#15384F'; ACC='#0079B8'
font=lambda s,b=False:ImageFont.truetype(str(R/'recursos'/('Montserrat-ExtraBold.ttf' if b else 'Montserrat-Bold.ttf')),s)
layout_checks=[]
def wrap(text,size,width=864,maxlines=3,chars=None,bold=False):
 words=text.split();lines=[];line='';f=font(size,bold)
 for w in words:
  test=(line+' '+w).strip()
  if f.getlength(test)>width or (chars and len(test)>chars):
   if line:lines.append(line)
   line=w
  else:line=test
 if line:lines.append(line)
 assert len(lines)<=maxlines,(text,lines)
 return lines
class Canvas:
 def __init__(self):
  self.im=Image.new('RGBA',(1080,1920));self.d=ImageDraw.Draw(self.im);self.svg=[]
 def line(self,points,color=ACC,width=4):
  self.d.line(points,fill=color,width=width,joint='curve');self.svg.append(f'<polyline points="'+ ' '.join(f'{x},{y}' for x,y in points)+f'" fill="none" stroke="{color}" stroke-width="{width}"/>')
 def box(self,xy,outline=ACC,fill=None,width=4,radius=0):
  self.d.rounded_rectangle(xy,radius,fill=fill,outline=outline,width=width)
  x,y,x2,y2=xy;self.svg.append(f'<rect x="{x}" y="{y}" width="{x2-x}" height="{y2-y}" rx="{radius}" fill="{fill or "none"}" stroke="{outline}" stroke-width="{width}"/>')
 def ellipse(self,xy,outline=ACC,width=4):
  self.d.ellipse(xy,outline=outline,width=width);x,y,x2,y2=xy
  self.svg.append(f'<ellipse cx="{(x+x2)/2}" cy="{(y+y2)/2}" rx="{(x2-x)/2}" ry="{(y2-y)/2}" fill="none" stroke="{outline}" stroke-width="{width}"/>')
 def text(self,text,x,y,size=40,color=INK,bold=False,width=864,maxlines=3,spacing=None):
  lines=wrap(text,size,width,maxlines,bold=bold);spacing=spacing or int(size*1.17)
  for i,line in enumerate(lines):
   self.d.text((x,y+i*spacing),line,font=font(size,bold),fill=color,anchor='lt')
   self.svg.append(f'<text x="{x}" y="{y+i*spacing}" dominant-baseline="text-before-edge" font-family="Montserrat" font-size="{size}" font-weight="{800 if bold else 700}" fill="{color}">{html.escape(line)}</text>')
  layout_checks.append(dict(text=text,x=x,y=y,width=max(font(size,bold).getlength(l) for l in lines),bottom=y+(len(lines)-1)*spacing+size,lines=len(lines)))
 def save(self,p):
  self.im.save(p.with_suffix('.png'))
  p.with_suffix('.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="1920" viewBox="0 0 1080 1920">'+''.join(self.svg)+'</svg>')
def document(c,x=540,y=680):
 c.box((x-55,y-72,x+55,y+72));
 for d in [-35,0,35]:c.line([(x-32,y+d),(x+32,y+d)])
def icon(c,kind,x=540,y=680):
 if kind=='shield':c.line([(x-60,y-65),(x,y-85),(x+60,y-65),(x+52,y+25),(x,y+80),(x-52,y+25),(x-60,y-65)])
 elif kind=='consult':
  c.box((x-70,y-55,x+70,y+40),radius=16);c.line([(x-45,y+40),(x-45,y+65),(x-15,y+40)])
  c.line([(x,y-28),(x,y+14)]);c.line([(x-21,y-7),(x+21,y-7)])
 elif kind=='test':
  c.line([(x-30,y-70),(x+30,y-70)]);c.line([(x-20,y-70),(x-20,y+48),(x,y+70),(x+20,y+48),(x+20,y-70)]);c.line([(x-20,y+10),(x+20,y+10)])
 elif kind=='bed':
  c.line([(x-72,y-45),(x-72,y+65)]);c.line([(x+72,y-20),(x+72,y+65)]);c.line([(x-72,y+30),(x+72,y+30)]);c.box((x-64,y-15,x-18,y+20));c.box((x-10,y-5,x+65,y+20))
 elif kind=='network':
  for a,b in [((-65,-40),(65,-40)),((-65,-40),(0,65)),((65,-40),(0,65))]:c.line([(x+a[0],y+a[1]),(x+b[0],y+b[1])])
  for dx,dy in [(-65,-40),(65,-40),(0,65)]:c.ellipse((x+dx-18,y+dy-18,x+dx+18,y+dy+18))
 elif kind=='tooth':c.line([(x,y-45),(x-45,y-65),(x-65,y-35),(x-50,y+25),(x-30,y+75),(x-10,y+20),(x+10,y+20),(x+30,y+75),(x+50,y+25),(x+65,y-35),(x+45,y-65),(x,y-45)])
 elif kind=='calendar':
  c.box((x-65,y-60,x+65,y+65));c.line([(x-65,y-25),(x+65,y-25)])
  for dx in [-35,35]:c.line([(x+dx,y-78),(x+dx,y-45)])
 elif kind=='world':
  # Original stylized continental silhouette, no countries or travel/evacuation arrows.
  shapes=[[(-140,-50),(-90,-70),(-45,-55),(-35,-25),(-60,-5),(-48,15),(-70,30),(-85,5),(-110,-5),(-140,-50)],[(-67,27),(-30,35),(-22,60),(-50,100),(-65,75),(-67,27)],[(-5,-45),(25,-65),(65,-60),(100,-70),(145,-40),(135,-10),(95,5),(80,-10),(55,10),(20,-10),(-5,-45)],[(0,-10),(40,0),(35,50),(10,75),(-10,35),(0,-10)],[(100,55),(135,45),(155,65),(125,80),(100,55)]]
  for pts in shapes:c.line([(x+a,y+b) for a,b in pts])
 else:document(c,x,y)
def graphics(c,s,y=680):
 g=s['graphic'] or ''
 if 'Isapre →' in g:
  labels=['Isapre','Copago','Complemento según plan'];w=252
  for i,label in enumerate(labels):
   x=96+i*306;c.box((x,y-55,x+w,y+60),radius=12);c.text(label,x+12,y-28,26,width=w-24,maxlines=3)
   if i<2:c.line([(x+w+8,y),(x+w+44,y),(x+w+34,y-10)]);c.line([(x+w+44,y),(x+w+34,y+10)])
 elif 'Dos tarjetas' in g:
  labels=['Clínica Bupa Santiago','IntegraMédica'] if 'Clínica' in g else ['Base','Adicionales']
  for i,l in enumerate(labels):
   x=96+i*444;c.box((x,y-55,x+414,y+65),radius=12);c.text(l,x+16,y-25,30,width=382,maxlines=2)
 elif 'Cinco círculos' in g:
  for i in range(5):c.ellipse((180+i*160,y-35,250+i*160,y+35))
 else:
  kinds=[]
  if 'Consulta' in g:kinds.append('consult')
  if 'Examen' in g:kinds.append('test')
  if 'Cama' in g:kinds.append('bed')
  if 'Escudo' in g:kinds=['shield']
  if 'Red de prestadores' in g:kinds=['network']
  if 'Diente' in g:kinds=['tooth']
  if 'Calendario' in g:kinds=['calendar']
  if 'Silueta mundial' in g:kinds=['world']
  if not kinds:kinds=['document']
  for i,k in enumerate(kinds):icon(c,k,540+(i-(len(kinds)-1)/2)*240,y)
  if 'Calendario' in g:c.text('Carencias según prestación',190,550,32,width=700,maxlines=1)
def build_art(v,s,variant=False):
 layout_start=len(layout_checks);c=Canvas();close=s['id'].endswith('06');presentation=s['id'].endswith('02')
 c.box((96,300,356,390),outline='#B7C9D4',width=2)
 c.text('Logo pendiente',108,328,24,width=240,maxlines=1)
 if not close and not presentation:c.text(v['product'],96,420,40,maxlines=2)
 if close:
  c.text(v['product'],96,530,64,bold=True,maxlines=3,spacing=72)
  c.text('Cotiza por WhatsApp',96,758,56,bold=True,maxlines=1)
  c.text('+56 9 8612 1803',96,840,44,maxlines=1)
 elif s['missing_stock']:
  c.box((96,545,960,735),outline='#B7C9D4',width=2,radius=12)
  c.text('TOMA FUENTE PENDIENTE',120,565,32,width=816,maxlines=1)
  c.text(re.split(r'[\\/]',s['resource'])[-1],120,625,26,width=816,maxlines=2)
  c.text(s['headline'],96,780,56,bold=True,maxlines=2)
 elif presentation:
  c.text(s['headline'],96,530,64,bold=True,maxlines=3,spacing=72)
  if not variant:graphics(c,s,820)
 else:
  if not variant:graphics(c,s,680)
  c.text(s['headline'],96,780,56,bold=True,maxlines=2)
 c.text(s['note'],96,1100,32,maxlines=3,spacing=38)
 p=R/'recursos'/v['slug']/s['id'];p.parent.mkdir(exist_ok=True)
 if variant:p=p.with_name(p.name+'_texto')
 
 for item in layout_checks[layout_start:]:item['scene']=s['id'];item['variant']=variant
 c.save(p);return p.with_suffix('.png')
def ass_time(t):
 units=round(t*100);seconds,fraction=divmod(units,100);minutes,seconds=divmod(seconds,60);hours,minutes=divmod(minutes,60)
 return f'{hours}:{minutes:02}:{seconds:02}.{fraction:02}'
def srt_time(t):
 units=round(t*1000);seconds,fraction=divmod(units,1000);minutes,seconds=divmod(seconds,60);hours,minutes=divmod(minutes,60)
 return f'{hours:02}:{minutes:02}:{seconds:02},{fraction:03}'
def subtitle_chunks(txt):
 lines=textwrap.wrap(txt,width=32,break_long_words=False,break_on_hyphens=False)
 return [lines[i:i+2] for i in range(0,len(lines),2)]
HEADER='''[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\nWrapStyle: 2\n[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\nStyle: Sub,Montserrat,48,&H00FFFFFF,&H00FFFFFF,&H263F2B10,&H263F2B10,-1,0,0,0,100,100,0,0,3,16,0,7,112,112,930,1\nStyle: Review,Montserrat,28,&H00404090,&H00404090,&H00FAF8F4,&H00FAF8F4,-1,0,0,0,100,100,0,0,1,0,0,7,96,96,1300,1\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n'''
def subtitles(v):
 events=[];srt=[]
 for s in v['scenes']:
  chunks=subtitle_chunks(s['voice']);weights=[len(' '.join(c)) for c in chunks];a=s['start']
  for chunk,w in zip(chunks,weights):
   b=a+(s['end']-s['start'])*w/sum(weights)
   events.append((a,b,'\\N'.join(chunk)));srt.append((a,b,'\n'.join(chunk)));a=b
 return events,srt
def write_ass(path,events,duration):
 content=HEADER
 for a,b,text in events:content+=f'Dialogue: 0,{ass_time(a)},{ass_time(b)},Sub,,0,0,0,,{{\\pos(112,946)}}{text}\n'
 content+=f'Dialogue: 1,0:00:00.00,{ass_time(duration)},Review,,0,0,0,,REVISIÓN INTERNA · NO PUBLICAR\\NSin voz autorizada · marca pendiente\n'
 path.write_text(content)
def music():
 sr=48000;duration=32;n=sr*duration;t=np.arange(n)/sr;beat=60/112;rng=np.random.default_rng(112)
 tracks={k:np.zeros(n) for k in ['pluck','bajo','bombo','aro','shaker']}
 def add(name,start,x,peak):
  i=round(start*sr);m=min(len(x),n-i)
  if m<=0:return
  x=x.copy();tail=min(round(.02*sr),len(x));head=min(round(.002*sr),len(x))
  x[-tail:]*=np.linspace(1,0,tail);x[:head]*=np.linspace(0,1,head)
  peakx=np.max(np.abs(x))
  if peakx:tracks[name][i:i+m]+=x[:m]/peakx*10**(peak/20)
 chords=[([60,64,67],36),([57,60,64],33),([53,57,60],29),([55,59,62],31)]
 for b in range(math.ceil(duration/beat)):
  start=b*beat;notes,bass=chords[(b//8)%4]
  q=np.arange(round(.42*sr))/sr;env=np.minimum(q/.01,1)*np.exp(-q/.16)
  note=notes[b%3];f=440*2**((note-69)/12)
  add('pluck',start,(np.sin(2*np.pi*f*q)+.22*np.sin(4*np.pi*f*q))*env,-29)
  q=np.arange(round(.40*sr))/sr;f=440*2**((bass-69)/12)
  add('bajo',start,np.sin(2*np.pi*f*q)*np.minimum(q/.01,1)*np.exp(-q/.16),-26)
  q=np.arange(round(.18*sr))/sr
  if b%4 in (0,2):add('bombo',start,np.sin(2*np.pi*(55*q+4*(1-np.exp(-q*40))))*np.exp(-q*35),-24)
  else:add('aro',start,rng.normal(size=len(q))*np.exp(-q*100),-30)
  for off in [0,.5]:
   q=np.arange(round(.08*sr))/sr;x=rng.normal(size=len(q));x=np.r_[0,np.diff(x)]*np.exp(-q*75)
   add('shaker',start+off*beat,x,-34)
 for k,x in tracks.items():
  stem=x.copy();tail=round(.02*sr);stem[-tail:]*=np.linspace(1,0,tail)
  wavwrite(R/'recursos'/f'{k}_112bpm.wav',sr,np.column_stack([stem,stem]).astype('float32'))
 mix=sum(tracks.values());mix*=np.minimum(t/.08,1)*np.minimum((duration-t)/.3,1)
 wavwrite(R/'recursos/campana_salud_112bpm.wav',sr,np.column_stack([mix,mix]).astype('float32'))
def run(cmd,log):
 with log.open('w') as f:r=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT)
 if r.returncode:raise RuntimeError(str(log))
def render(v):
 work=R/'recursos'/v['slug'];events,srt=subtitles(v)
 write_ass(R/'editables'/f'{v["slug"]}_PROVISIONAL.ass',events,v['duration'])
 (R/'editables'/f'{v["slug"]}_PROVISIONAL.srt').write_text('\n\n'.join(f'{i}\n{srt_time(a)} --> {srt_time(b)}\n{txt}' for i,(a,b,txt) in enumerate(srt,1)))
 parts=[]
 for s in v['scenes']:
  chunks=[(s['start'],s['end'],False)]
  if s['internal_cut'] and s['graphic'] and not s['missing_stock']:
   chunks=[(s['start'],s['internal_cut'],False),(s['internal_cut'],s['end'],True)]
  for a,b,var in chunks:
   stem=s['id']+('_texto' if var else '');png=work/f'{stem}.png';out=work/f'{stem}.mp4';duration=b-a
   ass=work/f'{stem}.ass';ev=[(max(x,a)-a,min(y,b)-a,txt) for x,y,txt in events if x<b and y>a];write_ass(ass,ev,duration)
   fades=(',fade=t=in:st=0:d=0.18:alpha=1' if a==s['start'] else '')+(f',fade=t=out:st={duration-.1}:d=0.1:alpha=1' if b==s['end'] else '')
   motion="12*max(0,1-t/0.18)" if a==s['start'] else "0"
   vf=f"format=rgba{fades}[fg];color=c={BG}:s=1080x1920:r=30:d={duration},format=rgba[bg];[bg][fg]overlay=x=0:y='{motion}':shortest=1:format=rgb,subtitles={ass}:fontsdir={R/'recursos'},scale=iw:ih:in_range=pc:out_range=tv:out_color_matrix=bt709,format=yuv420p"
   cmd=['ffmpeg','-hide_banner','-y','-loop','1','-framerate','30','-i',str(png),'-filter_complex',vf,'-t',str(duration),'-an','-c:v','libx264','-threads','2','-preset','veryfast','-profile:v','high','-b:v','10M','-maxrate','14M','-bufsize','20M','-r','30','-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709','-color_range','tv',str(out)]
   
   key=hashlib.sha256(png.read_bytes()+ass.read_bytes()+json.dumps(cmd).encode()).hexdigest()
   stamp=work/f'{stem}.sha256'
   if '--reuse-segments' not in sys.argv or not out.exists() or not stamp.exists() or stamp.read_text()!=key:
    run(cmd,work/f'{stem}_render.log');stamp.write_text(key)
   parts.append(out)
 listing=work/'concat.txt';listing.write_text('\n'.join("file '"+str(p)+"'" for p in parts))
 # No narration: this is explicitly a music-only internal preview, not an approved mix.
 out=R/'renders_revision'/f'{v["slug"]}_instagram_whatsapp_v1_REVISION_SIN_VOZ.mp4'
 dur=v['duration'];audio=f'atrim=0:{dur},afade=t=in:d=0.08,afade=t=out:st={dur-.3}:d=0.3,volume=if(lt(t\\,{dur-5})\\,1\\,0.70795):eval=frame'
 measurement=subprocess.run(['ffmpeg','-hide_banner','-i',str(R/'recursos/campana_salud_112bpm.wav'),'-af',audio+',loudnorm=I=-16:TP=-2.2:LRA=7:print_format=json','-f','null','-'],capture_output=True,text=True,check=True)
 (work/'loudnorm_pasada1.log').write_text(measurement.stderr)
 measured=json.JSONDecoder().raw_decode(measurement.stderr[measurement.stderr.rfind('{'):])[0]
 audio+=',loudnorm=I=-16:TP=-2.2:LRA=7:measured_I='+measured['input_i']+':measured_TP='+measured['input_tp']+':measured_LRA='+measured['input_lra']+':measured_thresh='+measured['input_thresh']+':offset='+measured['target_offset']+':linear=true:print_format=json'
 run(['ffmpeg','-hide_banner','-y','-f','concat','-safe','0','-i',str(listing),'-i',str(R/'recursos/campana_salud_112bpm.wav'),'-map','0:v','-map','1:a','-af',audio,'-c:v','copy','-bsf:v','h264_metadata=colour_primaries=1:transfer_characteristics=1:matrix_coefficients=1','-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709','-c:a','aac','-b:a','192k','-ar','48000','-ac','2','-t',str(dur),'-movflags','+faststart',str(out)],work/'mux.log')
 print('RENDER',v['id'],out.name,flush=True)
if __name__=='__main__':
 for v in V:
  for s in v['scenes']:
   build_art(v,s)
   if s['internal_cut'] and s['graphic'] and not s['missing_stock']:build_art(v,s,True)
 music()
 (R/'comprobaciones/layout.json').write_text(json.dumps(layout_checks,ensure_ascii=False,indent=2))
 print('Gráficos editables, PNG y seis pistas musicales producidos.',flush=True)
 if '--prepare-only' not in sys.argv:
  with ThreadPoolExecutor(max_workers=2) as ex:list(ex.map(render,V))
