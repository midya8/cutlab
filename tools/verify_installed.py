from pathlib import Path
import importlib,importlib.util,json,sys
from cutlab import audit
records=json.loads(Path(sys.argv[1]).read_text());checkout=Path(sys.argv[2]).resolve()
origins={name:str(Path(importlib.util.find_spec(name).origin).resolve()) for name in ['cutlab','cutlab.core','cutlab.cli','cutlab.__main__','cutlab.path']}
for name,origin in origins.items():assert checkout not in Path(origin).parents,(name,origin)
for x in records:assert audit(x['input'])==x['report'],x['name']
print(json.dumps({'cases':len(records),'module_origins':origins}))

from cutlab.path import response_path
paths=json.loads((checkout/'docs/path-audits.json').read_text())
for x in paths:assert response_path(x['input'])==x['report'],x['name']
print(json.dumps({'path_cases':len(paths)}))
