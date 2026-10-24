"""Composición original por síntesis, 112BPM, sin samples ni grabaciones externas."""
from pathlib import Path
import argparse, math
import numpy as np
from scipy.io.wavfile import write as wavwrite

def music(destination, stems=False):
 destination.mkdir(parents=True,exist_ok=True)
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
  if stems: wavwrite(destination/f'{k}_112bpm.wav',sr,np.column_stack([stem,stem]).astype('float32'))
 mix=sum(tracks.values());mix*=np.minimum(t/.08,1)*np.minimum((duration-t)/.3,1)
 wavwrite(destination/'campana_salud_112bpm.wav',sr,np.column_stack([mix,mix]).astype('float32'))

if __name__ == '__main__':
 ap=argparse.ArgumentParser(description=__doc__); ap.add_argument('--destination',type=Path,default=Path(__file__).resolve().parents[1]/'recursos/audio'); ap.add_argument('--stems',action='store_true'); a=ap.parse_args(); music(a.destination,a.stems)
