#!/usr/bin/env python3
from __future__ import annotations
import json, subprocess, sys, tempfile
from pathlib import Path

PLUGIN=Path(__file__).resolve().parents[1]
ENGINE=PLUGIN/'engine'

def run(*args,cwd=None,ok=(0,)):
    p=subprocess.run([str(x) for x in args],cwd=cwd,capture_output=True,text=True)
    if p.returncode not in ok:
        print(p.stdout); print(p.stderr,file=sys.stderr); raise AssertionError(f'command failed {p.returncode}: {args}')
    return p.stdout

def main():
    with tempfile.TemporaryDirectory() as td:
        r=Path(td)
        (r/'src/auth').mkdir(parents=True); (r/'tests').mkdir()
        (r/'src/auth/session.py').write_text('def refresh_session(token):\n    return {"token": token}\n')
        (r/'src/notifications.py').write_text('def send_email(order_id):\n    return order_id\n')
        (r/'tests/test_session.py').write_text('from src.auth.session import refresh_session\n\ndef test_refresh_session():\n    assert refresh_session("x")["token"] == "x"\n')
        run('git','init','-q',cwd=r); run('git','config','user.email','fixture@example.com',cwd=r); run('git','config','user.name','Fixture',cwd=r); run('git','add','.',cwd=r); run('git','commit','-qm','initial',cwd=r)
        run(sys.executable,ENGINE/'project_brain.py','--root',r,'init')
        assert (r/'.codemium/model-profile.json').exists()
        out=json.loads(run(sys.executable,ENGINE/'project_brain.py','--root',r,'add-decision','--text','Auth sessions rotate in the auth module','--source','src/auth/session.py'))
        assert out['id']=='D0001'
        run(sys.executable,ENGINE/'repo_graph.py','build','--root',r)
        graph=json.loads((r/'.codemium/repository/graph.json').read_text())
        assert graph['file_count']==3
        assert any('refresh_session' in f['symbols'] for f in graph['files'])
        run(sys.executable,ENGINE/'test_map.py','build','--root',r)
        task=json.loads(run(sys.executable,ENGINE/'task_compiler.py','--root',r,'--request','Fix auth refresh bug that logs users out'))
        assert task['type']=='FIX' and task['risk']=='high'
        ws=json.loads(run(sys.executable,ENGINE/'working_set.py','--root',r,'--query','auth refresh session','--top','5'))
        assert any(x['path']=='src/auth/session.py' for x in ws['files'])
        (r/'src/auth/session.py').write_text('def refresh_session(token):\n    if not token:\n        raise ValueError("token required")\n    return {"token": token}\n')
        impact=json.loads(run(sys.executable,ENGINE/'impact.py','--root',r,'--git-diff'))
        assert 'src/auth/session.py' in impact['changed_files'] and impact['blast_radius']=='high'
        scope=json.loads(run(sys.executable,ENGINE/'scope_guard.py','--root',r,'--strict'))
        assert scope['status']=='pass'
        miss=json.loads(run(sys.executable,ENGINE/'cache.py','--root',r,'check','--kind','search','--key','refresh_session callers'))
        assert miss['hit'] is False
        run(sys.executable,ENGINE/'cache.py','--root',r,'record','--kind','search','--key','refresh_session callers','--result-ref','E0001')
        hit=json.loads(run(sys.executable,ENGINE/'cache.py','--root',r,'check','--kind','search','--key','refresh_session callers'))
        assert hit['hit'] is True
        health=json.loads(run(sys.executable,ENGINE/'health.py','--root',r)); assert health['initialized'] is True
        tel=json.loads(run(sys.executable,ENGINE/'telemetry.py','--root',r)); assert 'approx_text_tokens_if_all_loaded' in tel
    print('PASS: Codemium fixture')
if __name__=='__main__': main()
