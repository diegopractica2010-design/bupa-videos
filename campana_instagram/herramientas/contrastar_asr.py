"""Contraste auxiliar ASR local del audio MP4 completo; no certifica pronunciación."""
from pathlib import Path
import argparse, hashlib, json, os, subprocess
import numpy as np
import sherpa_onnx

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    ap.add_argument('--only', nargs='+')
    args = ap.parse_args(); root = args.root.resolve()
    modelroot = Path(os.environ.get('BUPA_TTS_MODELS', '/workspace/bupa-tts-models'))
    modeldir = modelroot / 'sherpa-onnx-whisper-base'
    license_data = json.loads((root/'recursos/licencias/modelos_asr_procedencia.json').read_text())
    archive = modelroot/'sherpa-onnx-whisper-base.tar.bz2'
    assert sha(archive) == license_data[archive.name]['sha256'], 'Archivo de modelo distinto al documentado'
    files = [modeldir/'base-encoder.int8.onnx', modeldir/'base-decoder.int8.onnx', modeldir/'base-tokens.txt']
    recognizer = sherpa_onnx.OfflineRecognizer.from_whisper(
        encoder=str(files[0]), decoder=str(files[1]), tokens=str(files[2]), language='es', num_threads=2)
    videos = json.loads((root/'contenido/secuencias.json').read_text())['videos']
    if args.only:
        videos = [v for v in videos if v['id'] in args.only or v['slug'] in args.only]
        assert len(videos) == len(set(args.only))
    out = root/'revision/asr_independiente.json'; results = []
    report = {'status':'IN_PROGRESS', 'model_files':{p.name:sha(p) for p in files}, 'videos':results,
              'scope':'Reconocimiento automático auxiliar. Puede confundir marcas, cifras o alucinar. No acredita escucha humana, naturalidad, acento ni sincronía perceptiva.'}
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2))
    for v in videos:
        path = root/'videos'/f'{v["slug"]}.mp4'; before = sha(path)
        raw = subprocess.run(['ffmpeg','-v','error','-i',str(path),'-f','f32le','-ac','1','-ar','16000','-'],capture_output=True,check=True).stdout
        samples = np.frombuffer(raw,dtype=np.float32).copy()[:round(v['duration']*16000)]
        # Partir solamente entre escenas para no cortar palabras, siempre <30 s.
        cuts = []; start = 0; scene_ids = []
        for scene in v['scenes']:
            if scene['end']-start > 28.5 and scene_ids:
                cuts.append((start,scene['start'],scene_ids)); start=scene['start']; scene_ids=[]
            scene_ids.append(scene['id'])
        cuts.append((start,v['duration'],scene_ids)); segments=[]
        for a,b,ids in cuts:
            assert 0 < b-a < 30
            stream=recognizer.create_stream(); stream.accept_waveform(16000,samples[round(a*16000):round(b*16000)])
            recognizer.decode_stream(stream)
            segments.append({'start':a,'end':b,'scenes':ids,'asr':stream.result.text,
                             'expected':' '.join(s['voice'] for s in v['scenes'] if s['id'] in ids)})
        assert sha(path) == before
        results.append({'id':v['id'],'sha256_mp4':before,'segments':segments,
                        'audio_covered_seconds':v['duration'],'audio_pcm_f32_16khz_sha256':hashlib.sha256(raw).hexdigest(),'human_review':'PENDIENTE'})
        out.write_text(json.dumps(report,ensure_ascii=False,indent=2)); print(v['id'],' | '.join(s['asr'] for s in segments),flush=True)
    report['status']='COMPLETE'; out.write_text(json.dumps(report,ensure_ascii=False,indent=2))

if __name__ == '__main__': main()
