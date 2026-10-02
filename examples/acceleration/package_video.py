"""Package the rendered film, preserving an attribution in MP4 metadata."""
from pathlib import Path
import av

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
SOURCE=HERE/'render-local/final-media/videos/animation_scene/720p30/AccelerationLesson.mp4'
OUTPUT=ROOT/'dist/examples/acceleration'


def main():
    OUTPUT.mkdir(parents=True,exist_ok=True)
    target=OUTPUT/'加速度的影响因素-讲解.mp4'
    notice='Cart geometry: Open Lab Components, phy.mechanics.cart.dynamics.\n'+(ROOT/'teach_agent/vendor/olc/LICENSE').read_text(encoding='utf-8')
    with av.open(str(SOURCE)) as source,av.open(str(target),'w',options={'movflags':'+faststart'}) as output:
        mapping={s.index:output.add_stream_from_template(s) for s in source.streams if s.type in ('video','audio')}
        output.metadata['title']='加速度的影响因素'
        output.metadata['comment']=notice
        output.metadata['description']='Manim teaching animation; Mandarin narration synthesized with Microsoft Huihui Desktop.'
        for packet in source.demux():
            if packet.dts is None or packet.stream.index not in mapping:continue
            packet.stream=mapping[packet.stream.index]
            output.mux(packet)
    with av.open(str(target)) as result:
        assert len(result.streams.audio)==1 and len(result.streams.video)==1
        assert result.streams.video[0].codec_context.width==1280
        assert 'Open Lab Components' in result.metadata.get('comment','')
        print('Video:',round(result.duration/av.time_base,2),'seconds;',target.stat().st_size,'bytes')
    (OUTPUT/'视频素材许可.txt').write_text(notice,encoding='utf-8')


if __name__=='__main__':main()
