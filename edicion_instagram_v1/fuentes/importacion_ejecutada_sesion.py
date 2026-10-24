from pathlib import Path
import zipfile,xml.etree.ElementTree as E,json,re,hashlib,shutil
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
R=Path('/workspace/bupa-videos/edicion_instagram_v1')
doc=Path('/workspace/attachments/957bc246-ff2e-4281-bcab-868aaf09ad4e/Auditoria_videos_Instagram_WhatsApp_v1.docx')
pdf=Path('/workspace/attachments/ad986fc7-a95a-43a8-9ab5-dce38d00fea9/Auditoria_videos_Instagram_WhatsApp_v1.pdf')
for f in (doc,pdf): shutil.copy2(f,R/'fuentes'/f.name)
shutil.copy2('/tmp/bupa-auditoria.txt',R/'fuentes'/'auditoria_extraida.txt')
r=E.fromstring(zipfile.ZipFile(doc).read('word/document.xml'));ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
ps=[''.join(t.text or '' for t in p.findall('.//w:t',ns)) for p in r.findall('.//w:p',ns)]
(R/'fuentes'/'parrafos_docx.json').write_text(json.dumps(ps,ensure_ascii=False,indent=2))
tables=[]
for t in r.findall('.//w:tbl',ns):
 rows=[[' '.join(x.text or '' for x in c.findall('.//w:t',ns)) for c in row.findall('w:tc',ns)] for row in t.findall('w:tr',ns)]
 tables.append(rows)
 scripts=[t for t in tables if t and 'Locución exacta' in ' '.join(t[0])]
slugs=['bupa_adulto_mayor_70','bupa_catastrofico','bupa_complementa','bupa_cuidado_total','bupa_multisalud','bupa_proteccion','bupa_pymes','integramedica_100','mi_dental_integramedica','seguros_global']
products=['Plan IntegraMédica Adulto Mayor 70%','Seguro Bupa Catastrófico','Seguro Bupa Complementa','Seguro Bupa Cuidado Total','Seguro Bupa MultiSalud','Seguro Bupa + Protección','Seguro Bupa Pymes','Plan IntegraMédica 100%','Plan Mi Dental IntegraMédica 68%','Seguros de Salud Global Bupa']
def secs(s):
 m,v=s.split(':');return int(m)*60+float(v)
manifest=[]
for i,(slug,product,rows) in enumerate(zip(slugs,products,scripts),1):
 scenes=[]
 for j,row in enumerate(rows[1:],1):
  oid=f'ORD-V{i:02d}-S{j:02d}'; at=next(k for k,p in enumerate(ps) if p.startswith(oid+' ·'))
  para=ps[at:at+6]; impl=para[3]; start,end=map(secs,row[0].split('–'))
  resource=para[2].removeprefix('Recurso exacto: ')
  note=impl.split(' Nota: ')[-1]
  # Restore typographic spaces lost in the source document, without changing wording.
  note=re.sub(r'(?<=\d)(?=[A-Za-zÁÉÍÓÚáéíóú])|(?<=[A-Za-zÁÉÍÓÚáéíóú])(?=\d)',' ',note)
  note=note.replace('UF25','UF 25').replace('UF60','UF 60').replace('B,CyD','B, C y D').replace('CyD','C y D')
  g=re.search(r'Gráfico obligatorio: (.*?)\. No usar',impl)
  cut=re.search(r'corte interno en(\d\d:\d\d\.\d\d)',impl)
  scenes.append(dict(id=oid,start=start,end=end,voice=row[1],headline=row[2],note=note,resource=resource,graphic=g.group(1) if g else None,missing_stock=resource.startswith('C:'),internal_cut=secs(cut[1]) if cut else None,source_instructions=para))
 msg=f'Hola, quiero información y una cotización de {product}. Vi el anuncio en Instagram.'
 from urllib.parse import quote
 manifest.append(dict(id=f'V{i:02d}',slug=slug,product=product,duration=scenes[-1]['end'],scenes=scenes,whatsapp_message=msg,whatsapp_url='https://wa.me/56986121803?text='+quote(msg,safe='')))
assert len(manifest)==10 and all(len(x['scenes'])==6 for x in manifest)
(R/'editables'/'secuencias_reconstruidas_del_informe.json').write_text(json.dumps({'advertencia':'Reconstrucción del DOCX, no son los JSON originales ausentes. Sin voz autorizada ni logos. Uso interno.', 'videos':manifest},ensure_ascii=False,indent=2))
# Preserve all detailed orders separately; no fabricated order fields.
orders=[]
for k,p in enumerate(ps):
 if re.match(r'^ORD-V\d\d-[SAGCE]\d\d(?: ·| )',p):
  end=k+1
  while end<len(ps) and not ps[end].startswith('ORD-') and end<k+20: end+=1
  orders.append(ps[k:end])
(R/'editables'/'ordenes_transcritas_docx.json').write_text(json.dumps(orders,ensure_ascii=False,indent=2))
hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (R.parent/'output').glob('*.mp4')}
(R/'comprobaciones'/'originales_sha256_antes.json').write_text(json.dumps(hashes,indent=2))
for name,w in [('Montserrat-Bold.ttf',700),('Montserrat-ExtraBold.ttf',800)]:
 font=instantiateVariableFont(TTFont(R/'recursos'/'Montserrat.ttf'),{'wght':w},inplace=False);font.save(R/'recursos'/name)
print('10 guiones, 60 escenas y hashes preservados. Órdenes detalladas:',len(orders))
print('Escenas con stock ausente:',sum(s['missing_stock'] for v in manifest for s in v['scenes']))
