"""Dirección gráfica original para las seis escenas de cada pieza.

Entrada: contenido/guiones_v3.json. Salidas: PNG RGBA + SVG editables y
revision/layout_graficos.json. No necesita stock, logos ni el proyecto anterior.
Ejecutar: python campana_instagram/herramientas/graficos.py
No reduce fuentes para acomodar texto ni modifica la fuente de contenido.
"""
from __future__ import annotations
from pathlib import Path
import argparse
import html
import hashlib
import json
import math
import re
import unicodedata
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
W, H = 1080, 1920
BG, INK, BLUE = '#F4F8FA', '#15384F', '#0079B8'
MUTED, BORDER, TINT = '#536F80', '#C8DCE7', '#E6F1F7'
LEFT, RIGHT, WIDTH = 96, 960, 864
SUBTITLE_ZONE = (96, 930, 864, 140)


def normalize(value):
    if isinstance(value, dict):
        value = value.get('type', value.get('kind', value.get('icon', str(value))))
    return ''.join(c for c in unicodedata.normalize('NFKD', str(value or ''))
                   if not unicodedata.combining(c)).lower()


def font_path(weight=700, root=ROOT):
    name = 'Montserrat-ExtraBold.ttf' if weight >= 800 else 'Montserrat-Bold.ttf'
    path = root / 'recursos' / 'fuentes' / name
    if not path.is_file():
        raise FileNotFoundError(f'Falta la fuente requerida: {path}')
    return path


def text_lines(text, font, width):
    """Ajusta por palabras, conservando saltos editoriales explícitos."""
    result = []
    for paragraph in str(text).split('\n'):
        line = ''
        for word in paragraph.split():
            if font.getlength(word) > width:
                raise ValueError(f'Una palabra no cabe sin reducir fuente: {word!r}')
            attempt = f'{line} {word}'.strip()
            if line and font.getlength(attempt) > width:
                result.append(line)
                line = word
            else:
                line = attempt
        if line:
            result.append(line)
    return result


class Canvas:
    def __init__(self, scene, variant, root, blocks, errors):
        self.root, self.scene, self.variant = root, scene, variant
        self.blocks, self.errors = blocks, errors
        self.image = Image.new('RGBA', (W, H), BG)
        self.draw = ImageDraw.Draw(self.image)
        self.svg = [f'<rect width="{W}" height="{H}" fill="{BG}"/>']

    def line(self, points, color=BLUE, width=4):
        self.draw.line(points, fill=color, width=width, joint='curve')
        values = ' '.join(f'{x:.2f},{y:.2f}' for x, y in points)
        self.svg.append(f'<polyline points="{values}" fill="none" stroke="{color}" '
                        f'stroke-width="{width}" stroke-linecap="round" stroke-linejoin="round"/>')

    def rect(self, box, fill=None, stroke=BORDER, width=2, radius=0):
        self.draw.rounded_rectangle(box, radius=radius, fill=fill,
                                    outline=stroke, width=width)
        x, y, r, b = box
        self.svg.append(f'<rect x="{x}" y="{y}" width="{r-x}" height="{b-y}" '
                        f'rx="{radius}" fill="{fill or "none"}" '
                        f'stroke="{stroke or "none"}" stroke-width="{width}"/>')

    def ellipse(self, box, fill=None, stroke=BLUE, width=4):
        self.draw.ellipse(box, fill=fill, outline=stroke, width=width)
        x, y, r, b = box
        self.svg.append(f'<ellipse cx="{(x+r)/2}" cy="{(y+b)/2}" rx="{(r-x)/2}" '
                        f'ry="{(b-y)/2}" fill="{fill or "none"}" '
                        f'stroke="{stroke or "none"}" stroke-width="{width}"/>')

    def path(self, commands, stroke=BLUE, width=4, fill=None):
        """Pequeño trazador Bézier original: SVG y raster con la misma geometría."""
        svg, points, first, current = [], [], None, None
        for item in commands:
            op, *v = item
            svg.append(op + ' '.join(str(n) for n in v))
            if op == 'M':
                current = (v[0], v[1]); first = current; points.append(current)
            elif op == 'L':
                current = (v[0], v[1]); points.append(current)
            elif op == 'C':
                p0 = current
                p1, p2, p3 = (v[0], v[1]), (v[2], v[3]), (v[4], v[5])
                for j in range(1, 33):
                    t = j / 32; u = 1 - t
                    points.append(tuple(u**3*p0[k] + 3*u*u*t*p1[k] +
                                        3*u*t*t*p2[k] + t**3*p3[k] for k in (0, 1)))
                current = p3
            elif op == 'Z' and first is not None:
                points.append(first); current = first
        if fill and points:
            self.draw.polygon(points, fill=fill)
        if points:
            self.draw.line(points, fill=stroke, width=width, joint='curve')
        self.svg.append(f'<path d="{" ".join(svg)}" fill="{fill or "none"}" '
                        f'stroke="{stroke}" stroke-width="{width}" '
                        'stroke-linecap="round" stroke-linejoin="round"/>')

    def text(self, value, role, x, y, size, width=WIDTH, max_lines=3,
             weight=700, color=INK, leading=None, max_bottom=None):
        text = str(value or '').strip()
        if not text:
            return y
        face = ImageFont.truetype(str(font_path(weight, self.root)), size)
        leading = leading or round(size * 1.2)
        try:
            lines = text_lines(text, face, width)
        except ValueError as exc:
            self.errors.append({'scene': self.scene, 'variant': self.variant,
                                'role': role, 'error': str(exc), 'text': text})
            lines = [text]
        if len(lines) > max_lines:
            self.errors.append({'scene': self.scene, 'variant': self.variant,
                                'role': role, 'error': f'{len(lines)} líneas; máximo {max_lines}',
                                'text': text})
        boxes = []
        for i, line in enumerate(lines):
            top = y + i * leading
            self.draw.text((x, top), line, font=face, fill=color, anchor='lt')
            boxes.append(self.draw.textbbox((x, top), line, font=face, anchor='lt'))
            self.svg.append(f'<text x="{x}" y="{top}" dominant-baseline="text-before-edge" '
                            f'font-family="Montserrat" font-weight="{weight}" font-size="{size}" '
                            f'fill="{color}">{html.escape(line)}</text>')
        # Conservative text rectangles include font-size height, even for short glyphs.
        box = (x, y, max(face.getlength(l) for l in lines),
               (len(lines) - 1) * leading + size)
        record = {'escena': self.scene, 'variante': self.variant, 'rol': role,
                  'scene': self.scene, 'variant': self.variant, 'role': role,
                  'x': box[0], 'y': box[1], 'w': box[2], 'h': box[3],
                  'text': text, 'lines': lines, 'font_px': size, 'weight': weight}
        self.blocks.append(record)
        if max_bottom is not None and box[1] + box[3] > max_bottom:
            self.errors.append({'scene': self.scene, 'variant': self.variant,
                                'role': role, 'error': f'El bloque excede y={max_bottom}',
                                'text': text})
        return box[1] + box[3]

    def save(self, target):
        self.image.save(target.with_suffix('.png'))
        target.with_suffix('.svg').write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="1920" '
            'viewBox="0 0 1080 1920">\n' + '\n'.join(self.svg) + '\n</svg>\n',
            encoding='utf-8')


def draw_icon(c, kind, x=540, y=766, radius=80):
    """Iconos originales; sin monedas, flechas de transporte ni cifras implícitas."""
    s = radius / 80
    def p(dx, dy): return (x + dx*s, y + dy*s)
    def line(points): c.line([p(*a) for a in points])
    def box(a,b,r=0): c.rect((*p(*a),*p(*b)), stroke=BLUE, width=4, radius=r)
    def ellipse(a,b): c.ellipse((*p(*a),*p(*b)),stroke=BLUE,width=4)
    def path(items):
        converted=[]
        for op,*coords in items:
            values=[]
            for j in range(0,len(coords),2): values.extend(p(coords[j],coords[j+1]))
            converted.append((op,*values))
        c.path(converted)
    if kind == 'shield':
        path([('M',0,-74),('C',20,-70,41,-60,62,-58),('L',57,7),
              ('C',52,38,26,59,0,77),('C',-26,59,-52,38,-57,7),
              ('L',-62,-58),('C',-41,-60,-20,-70,0,-74),('Z',)])
    elif kind == 'consult':
        box((-67,-50),(67,44),18)
        line([(-42,44),(-42,66),(-13,44)])
        line([(0,-26),(0,20)]);line([(-23,-3),(23,-3)])
    elif kind == 'exam':
        line([(-32,-68),(32,-68)])
        path([('M',-22,-68),('L',-22,39),('C',-22,74,22,74,22,39),('L',22,-68)])
        line([(-22,7),(22,7)])
    elif kind == 'bed':
        line([(-72,-43),(-72,66)]);line([(72,-18),(72,66)])
        line([(-72,30),(72,30)]);box((-61,-13),(-21,18),6);box((-12,-4),(60,18),4)
    elif kind == 'network':
        for a,b in [((-57,-38),(57,-38)),((-57,-38),(0,57)),((57,-38),(0,57))]:line([a,b])
        for dx,dy in [(-57,-38),(57,-38),(0,57)]:ellipse((dx-18,dy-18),(dx+18,dy+18))
    elif kind == 'copago':
        for dx,dy in [(-55,-30),(0,0),(55,30)]:box((dx-30,dy-30),(dx+30,dy+30),8)
    elif kind == 'group':
        for dx in [-56,0,56]:
            ellipse((dx-16,-55),(dx+16,-23))
            path([('M',dx-29,44),('L',dx-29,9),('C',dx-29,-19,dx+29,-19,dx+29,9),('L',dx+29,44)])
    elif kind == 'dental':
        path([('M',0,-51),('C',-21,-62,-45,-72,-58,-47),
              ('C',-73,-20,-50,11,-43,47),('C',-36,89,-21,65,-13,22),
              ('C',-8,1,8,1,13,22),('C',21,65,36,89,43,47),
              ('C',50,11,73,-20,58,-47),('C',45,-72,21,-62,0,-51),('Z',)])
    elif kind == 'calendar':
        box((-64,-57),(64,66),12);line([(-64,-20),(64,-20)])
        for dx in [-32,32]:line([(dx,-76),(dx,-43)])
        for dx in [-28,9,46]:
            for dy in [7,36]:c.ellipse((*p(dx-4,dy-4),*p(dx+4,dy+4)),fill=BLUE,stroke=None)
    elif kind == 'world':
        # Silueta esquemática original. No países ni rutas de evacuación.
        shapes=[ [(-139,-40),(-109,-66),(-73,-60),(-38,-41),(-51,-17),(-73,-6),(-69,17),(-97,9),(-109,-15),(-139,-40)],
                 [(-72,20),(-37,31),(-29,52),(-50,91),(-64,69),(-72,20)],
                 [(-7,-39),(24,-62),(59,-54),(96,-64),(140,-35),(128,-6),(95,5),(70,-11),(54,12),(23,-4),(-7,-39)],
                 [(1,-8),(33,-1),(32,38),(9,65),(-9,27),(1,-8)],
                 [(96,49),(125,38),(148,59),(123,76),(96,49)] ]
        for poly in shapes:line(poly)
    else:
        box((-53,-68),(53,68),10)
        for dy in [-31,0,31]:line([(-29,dy),(29,dy)])


def icon_kinds(scene):
    hint=normalize(scene.get('visual',scene.get('icon','documento')))
    result=[]
    for terms,name in [(['consulta','consult','ambulator'],'consult'),(['examen','exam','tubo'],'exam'),
                       (['hospital','cama','bed'],'bed')]:
        if any(t in hint for t in terms):result.append(name)
    if result:return result[:3]
    for terms,name in [(['calend','carencia'],'calendar'),(['dental','diente','tooth'],'dental'),
                       (['mund','global','world','internacional'],'world'),(['escudo','shield'],'shield'),
                       (['equipo','grupo','titular','person','team'],'group'),(['copago','isapre','complement'],'copago'),
                       (['red','network','prestador'],'network')]:
        if any(t in hint for t in terms):return [name]
    return ['document']


def cards_for(scene):
    data=scene.get('cards') or []
    result=[]
    for card in data:
        if isinstance(card,str):result.append({'title':'','body':card})
        elif isinstance(card,dict):result.append({'title':str(card.get('title') or ''),
                                               'body':str(card.get('body') or '')})
        else:raise TypeError(f'Tarjeta no válida en {scene.get("id")}: {card!r}')
    return result


def draw_cards(c, cards):
    count=len(cards)
    if count>3:
        c.errors.append({'scene':c.scene,'variant':c.variant,'role':'cards','error':'Más de tres tarjetas'})
        cards=cards[:3];count=3
    if not count:return
    # Tres conceptos se organizan en filas: conserva 'Hospitalización' íntegra a36px
    # y permite comparar categorías sin convertirlas en tres columnas diminutas.
    if count==3:
        for i,card in enumerate(cards):
            x=LEFT;y=686+i*76
            c.rect((x,y,RIGHT,y+68),fill='#FFFFFF',stroke=BORDER,width=2,radius=16)
            c.line([(500,y+16),(500,y+52)],color=BORDER,width=2)
            c.text(card['title'],f'card_{i+1}_title',x+16,y+17,36,width=372,
                   max_lines=1,weight=800,color=BLUE,max_bottom=y+60)
            c.text(card['body'],f'card_{i+1}_body',520,y+17,36,width=424,
                   max_lines=1,weight=700,max_bottom=y+60)
        return
    gap=24;card_w=(WIDTH-gap*(count-1))/count
    # Tipografía mínima de tarjeta:36px. Si no cabe, se corrige copy o estructura.
    size=36
    for i,card in enumerate(cards):
        x=LEFT+i*(card_w+gap);y=686;bottom=910
        c.rect((x,y,x+card_w,bottom),fill='#FFFFFF',stroke=BORDER,width=2,radius=20)
        c.rect((x+16,y+18,x+48,y+22),fill=BLUE,stroke=None,width=0,radius=2)
        title_bottom=c.text(card['title'],f'card_{i+1}_title',x+16,y+39,size,
                            width=card_w-32,max_lines=2,weight=700 if count==3 else 800,color=BLUE,
                            leading=size+5,max_bottom=bottom-16)
        body_y=title_bottom+12 if card['title'] else y+48
        c.text(card['body'],f'card_{i+1}_body',x+16,body_y,size,
               width=card_w-32,max_lines=3,weight=700,leading=size+5,max_bottom=bottom-16)


def build_scene(video, scene, number, root, blocks, errors, detail=False):
    sceneid=str(scene['id']);variant='detalle' if detail else 'principal'
    c=Canvas(sceneid,variant,root,blocks,errors)
    # Sutil textura geométrica original fuera del área de lectura e interfaz.
    c.ellipse((792,1590,1232,2030),stroke='#E4EEF3',width=2)
    c.ellipse((872,1670,1152,1950),stroke='#E4EEF3',width=2)
    c.line([(LEFT,258),(RIGHT,258)],color=BORDER,width=2)
    # Seis hitos de montaje, sin texto promocional añadido.
    for i in range(6):
        x=LEFT+i*24
        c.ellipse((x,248,x+8,256),fill=BLUE if i==number else BORDER,stroke=None)
    product=video['product'];headline=str(scene.get('headline') or '')
    close=number==5;presentation=number==1
    if close:
        c.text(product,'producto',LEFT,450,64,weight=800,leading=74,max_lines=3,max_bottom=680)
        c.line([(LEFT,410),(LEFT+72,410)],color=BLUE,width=5)
        c.text(headline,'cta',LEFT,724,56,weight=800,leading=66,max_lines=2,max_bottom=850)
        c.text('WhatsApp: +56 9 8612 1803','numero',LEFT,868,44,max_lines=1,max_bottom=920)
    elif presentation:
        # Una sola identidad de producto; nunca se repite en una cabecera menor.
        c.text(product,'producto',LEFT,450,64,weight=800,leading=74,max_lines=3,max_bottom=680)
        c.line([(LEFT,410),(LEFT+72,410)],color=BLUE,width=5)
        cards=cards_for(scene)
        if cards:draw_cards(c,cards)
        elif not detail:
            kinds=icon_kinds(scene)
            for i,kind in enumerate(kinds):draw_icon(c,kind,540+(i-(len(kinds)-1)/2)*240,780)
    else:
        c.text(product,'producto',LEFT,300,40,leading=48,max_lines=2,max_bottom=398)
        c.line([(LEFT,420),(LEFT+72,420)],color=BLUE,width=5)
        # La variante detalle mantiene la información y convierte el espacio del icono
        # en una composición tipográfica: no elimina tarjetas ni sus condiciones.
        c.text(headline,'titular',LEFT,450,64,weight=800,leading=74,max_lines=3,max_bottom=674)
        cards=cards_for(scene)
        if cards:draw_cards(c,cards)
        elif not detail:
            kinds=icon_kinds(scene)
            for i,kind in enumerate(kinds):draw_icon(c,kind,540+(i-(len(kinds)-1)/2)*240,766)
    note=str(scene.get('note') or '')
    c.text(note,'nota',LEFT,1110,32,leading=39,max_lines=4,max_bottom=1260)
    c.line([(LEFT,1426),(RIGHT,1426)],color=BORDER,width=2)
    c.text('REVISIÓN INTERNA','revision',LEFT,1450,28,color=MUTED,max_lines=1,max_bottom=1500)
    target=root/'recursos'/'graficos'/(sceneid+('_detalle' if detail else ''))
    c.save(target)
    return target


def intersects(a,b):
    return (a['x'] < b['x']+b['w'] and b['x'] < a['x']+a['w'] and
            a['y'] < b['y']+b['h'] and b['y'] < a['y']+a['h'])


def validate(blocks,errors):
    groups={}
    for b in blocks:
        groups.setdefault((b['scene'],b['variant']),[]).append(b)
        if b['x'] < LEFT-0.01 or b['x']+b['w'] > RIGHT+0.01:
            errors.append({'scene':b['scene'],'variant':b['variant'],'role':b['role'],
                           'error':'Texto fuera de zona horizontal x96–960','text':b['text']})
        zone={'x':SUBTITLE_ZONE[0],'y':SUBTITLE_ZONE[1],
              'w':SUBTITLE_ZONE[2],'h':SUBTITLE_ZONE[3]}
        if intersects(b,zone):
            errors.append({'scene':b['scene'],'variant':b['variant'],'role':b['role'],
                           'error':'Texto ocupa zona reservada de subtítulos','text':b['text']})
    for (scene,variant),items in groups.items():
        for i,a in enumerate(items):
            for b in items[i+1:]:
                if intersects(a,b):
                    errors.append({'scene':scene,'variant':variant,'role':a['role']+' / '+b['role'],
                                   'error':'Intersección entre bloques de texto',
                                   'texts':[a['text'],b['text']]})


def build_all(manifest_path=None, root=None):
    """Genera arte de las 60 escenas y variantes de detalle; devuelve diagnóstico."""
    root=Path(root) if root else ROOT
    path=Path(manifest_path) if manifest_path else root/'contenido'/'guiones_v3.json'
    manifest_bytes=path.read_bytes()
    data=json.loads(manifest_bytes)
    videos=data['videos'] if isinstance(data,dict) else data
    blocks,errors,files=[],[],[]
    (root/'recursos'/'graficos').mkdir(parents=True,exist_ok=True)
    (root/'revision').mkdir(parents=True,exist_ok=True)
    for video in videos:
        scenes=video['scenes']
        if len(scenes)!=6:raise ValueError(f'{video.get("id")}: se requieren seis escenas')
        for i,scene in enumerate(scenes):
            files.append(str(build_scene(video,scene,i,root,blocks,errors)))
            purpose=normalize(scene.get('purpose',''))
            detail=(i in (2,3,4) or any(k in purpose for k in ['beneficio','condicion','requisito']))
            if detail:files.append(str(build_scene(video,scene,i,root,blocks,errors,True)))
    validate(blocks,errors)
    report={'source':str(path.relative_to(root)) if path.is_relative_to(root) else str(path),
            'source_sha256':hashlib.sha256(manifest_bytes).hexdigest(),
            'canvas':{'width':W,'height':H,'rgba':True},
            'palette':{'background':BG,'text':INK,'accent':BLUE,
                       'status':'Decisión editorial; no manual de marca'},
            'subtitle_reserved':{'x':96,'y':930,'w':864,'h':140},
            'files':files,'items':blocks,'errors':errors,
            'publication':'NO APROBADA: faltan conformidad de producto/marca y escucha final'}
    (root/'revision'/'layout_graficos.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest',type=Path)
    parser.add_argument('--root',type=Path)
    args=parser.parse_args()
    result=build_all(args.manifest,args.root)
    print(json.dumps({'files':len(result['files']),'text_blocks':len(result['items']),
                      'errors':result['errors']},ensure_ascii=False,indent=2))
    if result['errors']:
        raise SystemExit(1)
