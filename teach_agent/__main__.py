import argparse
import asyncio
import json
import os
from pathlib import Path
import threading
import webbrowser
import uvicorn
from .app import create_app


def default_data():
    return Path(os.environ.get('TEACH_DATA_DIR',str(Path.home()/'.teach-agent'))).expanduser().resolve()


def main():
    parser=argparse.ArgumentParser(description='Teach Agent local workbench')
    parser.add_argument('--data-dir',type=Path,default=default_data())
    parser.add_argument('--port',type=int,default=8765)
    parser.add_argument('--open',action='store_true')
    args=parser.parse_args()
    if not 1024<=args.port<=65535:
        parser.error('port must be 1024–65535')
    if args.open:
        from .local_runtime import LocalRuntime
        runtime=LocalRuntime(args.data_dir)
        existing=asyncio.run(runtime.existing_address())
        if existing:
            webbrowser.open(existing+'/#'+runtime.settings.token)
            print('舍长工作台：已打开正在运行的本地服务 '+existing)
            return
    app=create_app(args.data_dir)
    url=f'http://127.0.0.1:{args.port}'
    app.state.server_url=url
    if args.open:
        threading.Timer(1.5,lambda:webbrowser.open(url+'/#'+app.state.settings.token)).start()
    print('Teach Agent: '+url+' (open via launcher or enter the local session-token file value)')
    uvicorn.run(app,host='127.0.0.1',port=args.port,log_level='warning',access_log=False)


if __name__=='__main__':
    main()
