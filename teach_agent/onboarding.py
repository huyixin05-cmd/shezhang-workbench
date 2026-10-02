"""Local setup wizard. Credentials never pass through the conversation or MCP JSON."""
import argparse
import getpass
import json
import sys
from pathlib import Path

from .__main__ import default_data
from .config import Settings


def write_mcp_config(source_root, data_root):
    source_root=Path(source_root).resolve()
    data_root=Path(data_root).resolve()
    data_root.mkdir(parents=True,exist_ok=True)
    config={'mcpServers':{'teach-agent':{
        'command':str(Path(sys.executable).resolve()),
        'args':['-m','teach_agent.mcp_server'],
        'env':{'PYTHONPATH':str(source_root),'TEACH_DATA_DIR':str(data_root),'PYTHONUTF8':'1'}
    }}}
    path=data_root/'workbuddy-mcp.json'
    path.write_text(json.dumps(config,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return path


def configure(settings):
    public=settings.public()
    print('制作流程需要一个兼容 Chat Completions 的模型 API。不会自动使用 WorkBuddy 的模型额度。')
    if public['configured']:
        print('已有模型：'+public['model'])
        if input('重新配置？[y/N] ').strip().lower()!='y':
            return
    values={}
    for key,label in [('base_url','模型地址（通常以 /v1 结尾）'),('model','模型名称')]:
        previous=public.get(key,'')
        value=input(f'{label} [{previous}]：').strip() or previous
        if not value:
            raise ValueError('模型地址和名称不能为空；可重新运行向导。')
        values[key]=value
    key=getpass.getpass('API 密钥（输入不显示；留空保留原密钥，本地无密钥模型可留空）：').strip()
    if key:
        values['api_key']=key
    elif public['has_key']:
        values['clear_key']=input('清除原密钥？[y/N] ').strip().lower()=='y'
    manim=input('已有 Manim 环境的 Python 路径（暂不制作动画可留空）：').strip().strip('"')
    if manim:
        if not Path(manim).is_file():
            raise ValueError('Manim Python 路径不存在，请确认后重新运行向导。')
        values['manim_python']=manim
    settings.save(values)


def main():
    parser=argparse.ArgumentParser(description='舍长工作台：接入 WorkBuddy / MCP')
    parser.add_argument('--data-dir',type=Path,default=default_data())
    parser.add_argument('--config-only',action='store_true',help='只生成 MCP 配置，不运行模型设置向导')
    args=parser.parse_args()
    settings=Settings(args.data_dir)
    if not args.config_only:
        try:
            print('WorkBuddy 对话制作默认使用当前对话模型，无需单独 API 密钥。')
            if input('也配置独立网页使用的模型 API？[y/N] ').strip().lower()=='y':
                configure(settings)
            else:
                manim=input('已有 Manim 环境的 Python 路径（暂不制作动画可留空）：').strip().strip('"')
                if manim:
                    if not Path(manim).is_file():
                        raise ValueError('Manim Python 路径不存在')
                    settings.save({'manim_python':manim})
        except (ValueError,EOFError,KeyboardInterrupt) as error:
            print('\n设置未完成：'+str(error),file=sys.stderr)
            raise SystemExit(1)
    path=write_mcp_config(Path(__file__).resolve().parent.parent,settings.root)
    print('\n配置文件：'+str(path))
    print('在 WorkBuddy 的「插件 → MCP 服务器 → 配置 MCP」添加以下 teach-agent 配置。保留已有服务。')
    print(path.read_text(encoding='utf-8'))
    print('连接成功后直接对话：用舍长工作台，做一个让初二学生理解浮力的互动演示。')
    print('无需先开网页。制作期间保持 WorkBuddy 的 MCP 连接；断开由它启动的服务会停止未完成任务，已有版本保留。')


if __name__=='__main__':
    main()
