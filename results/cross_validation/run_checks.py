import json
from pathlib import Path
import numpy as np,pandas as pd
from sklearn.model_selection import train_test_split,StratifiedKFold,GridSearchCV
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler,OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import Ridge
from sklearn.svm import SVC
from sklearn.metrics import f1_score,accuracy_score,mean_absolute_error
R=Path.cwd();out=R/'results/cross_validation'
n=json.loads((R/'models/01_crop_suitability.ipynb').read_text());scope={'ROOT':R,'pd':pd,'np':np,'display':lambda *a:None}
exec(next(''.join(c['source']) for c in n['cells'] if c['cell_type']=='code' and 'raw = pd.read_csv' in ''.join(c['source'])),scope)
d=scope['data'];X=d[scope['features']];y=d.label
X,yunused,Y,ytest=train_test_split(X,y,test_size=.2,stratify=y,random_state=42)
rows=[]
for fold,(tr,va) in enumerate(StratifiedKFold(3,shuffle=True,random_state=42).split(X,Y),1):
 search=GridSearchCV(make_pipeline(StandardScaler(),SVC(kernel='rbf',gamma='scale')),{'svc__C':[.1,1,10]},scoring='f1_macro',cv=StratifiedKFold(3,shuffle=True,random_state=17),n_jobs=1)
 search.fit(X.iloc[tr],Y.iloc[tr]);pred=search.predict(X.iloc[va]);rows.append({'fold':fold,'C':search.best_params_['svc__C'],'macro_f1':f1_score(Y.iloc[va],pred,average='macro',zero_division=0),'accuracy':accuracy_score(Y.iloc[va],pred)})
print('SVM',rows,flush=True)
n=json.loads((R/'models/02_crop_yield.ipynb').read_text());scope={'ROOT':R,'pd':pd,'np':np,'display':lambda *a:None}
exec(next(''.join(c['source']) for c in n['cells'] if c['cell_type']=='code' and 'raw = pd.read_csv' in ''.join(c['source'])),scope)
d=scope['data'];features=scope['features'];cats=['State','District','Crop','Season'];nums=['YearStart','Area']
rrows=[]
for cutoff in [2006,2009,2012]:
 fit=d[d.YearStart<cutoff];val=d[(d.YearStart>=cutoff)&(d.YearStart<cutoff+3)]
 inner=fit[fit.YearStart<cutoff-3];iv=fit[fit.YearStart>=cutoff-3];best=None;bestmae=float('inf')
 for alpha in [.1,1,10,100]:
  pipe=make_pipeline(ColumnTransformer([('cat',OneHotEncoder(handle_unknown='ignore'),cats),('num',StandardScaler(),nums)]),Ridge(alpha=alpha,solver='lsqr'))
  pipe.fit(inner[features],inner.Yield);mae=mean_absolute_error(iv.Yield,pipe.predict(iv[features]))
  if mae<bestmae:best=pipe;bestmae=mae;choice=alpha
 best.fit(fit[features],fit.Yield);rrows.append({'validation':f'{cutoff}–{cutoff+2}','alpha':choice,'mae':mean_absolute_error(val.Yield,best.predict(val[features])),'rows':len(val)})
print('RIDGE',rrows,flush=True)
result={'svm':rows,'svm_f1_mean':float(np.mean([r['macro_f1'] for r in rows])),'svm_f1_std':float(np.std([r['macro_f1'] for r in rows],ddof=1)),'ridge':rrows,'ridge_mae_mean':float(np.mean([r['mae'] for r in rrows])),'ridge_mae_std':float(np.std([r['mae'] for r in rrows],ddof=1))}
(out/'results.json').write_text(json.dumps(result,indent=2))
