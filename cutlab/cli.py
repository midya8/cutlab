import argparse
import json
from pathlib import Path
from .core import audit, loads


def main():
    p=argparse.ArgumentParser(description='Exact finite submodular graph-cut witness')
    p.add_argument('input',type=Path);p.add_argument('--output',type=Path);p.add_argument('--path',action='store_true',help='exact affine unary response path')
    a=p.parse_args()
    try:
        text=a.input.read_text(encoding='utf-8')
        if a.path:
            from .path import loads_path,response_path
            report=response_path(loads_path(text))
        else: report=audit(loads(text))
    except (ValueError, OSError) as e:p.exit(2,str(e)+'\n')
    text=json.dumps(report,indent=2)+'\n'
    if a.output:a.output.write_text(text,encoding='utf-8')
    else:print(text,end='')
