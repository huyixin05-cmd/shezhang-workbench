import io
import zipfile
import av
import pytest
from test_api import client, wait_job


@pytest.fixture
def clip(tmp_path):
    path=tmp_path/'clip.mp4'
    with av.open(str(path),'w') as output:
        stream=output.add_stream('libx264',rate=10)
        stream.width=64;stream.height=64;stream.pix_fmt='yuv420p'
        for i in range(10):
            frame=av.VideoFrame(64,64,'yuv420p')
            for plane in frame.planes: plane.update(bytes(plane.buffer_size))
            for packet in stream.encode(frame): output.mux(packet)
        for packet in stream.encode(): output.mux(packet)
    return path.read_bytes()


def test_import_real_mp4_and_export_without_secrets(client,clip):
    bad=client.post('/api/import-video?title=test',content=b'not a video')
    assert bad.status_code==400
    r=client.post('/api/import-video?title=Existing%20animation',content=clip)
    assert r.status_code==200,r.text
    data=r.json();vid=data['version']['id']
    assert data['version']['report']['source']=='imported'
    assert client.get('/api/versions/'+vid+'/download?format=video').content==clip
    archive=zipfile.ZipFile(io.BytesIO(client.get('/api/versions/'+vid+'/download?format=zip').content))
    assert set(archive.namelist())=={'index.html','report.json','THIRD_PARTY_NOTICES.txt','assets/clip.mp4'}


def test_attach_video_creates_new_combined_version(client,clip):
    created=client.post('/api/projects',json={'request':'力','kind':'interactive'}).json()
    wait_job(client,created['job']['id']);pid=created['project']['id']
    j=client.post(f'/api/projects/{pid}/confirm',json={'revision':1}).json()
    vid=wait_job(client,j['id'])['version_id']
    r=client.post('/api/versions/'+vid+'/video',content=clip)
    assert r.status_code==200,r.text
    v=r.json()['version'];assert v['kind']=='combined'
    assert v['id']!=vid
    assert client.get('/api/versions/'+vid+'/download?format=html').status_code==200
    assert client.get('/api/versions/'+v['id']+'/download?format=html').status_code==400
    assert '<video ' in client.get('/api/versions/'+v['id']+'/html').text
