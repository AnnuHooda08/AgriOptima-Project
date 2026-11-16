from pathlib import Path
import requests,hashlib,json,pandas as pd
repo='DHIVAKARNAIDUSUNKARI/mandi-india-daily-prices-2001-2026'
revision='62ad5b49bc00c60b6303ddf3d74ea0718addb59b'  # pinned source revision
out=Path(__file__).resolve().parent
out.mkdir(exist_ok=True)
manifest=[]
for year in [2024,2025,2026]:
 name=f'mandi_daily_{year}.parquet';cache=Path('/tmp')/name
 url=f'https://huggingface.co/datasets/{repo}/resolve/{revision}/data/mandi_daily_by_year/{name}'
 print('DOWNLOAD',year,flush=True)
 if not cache.exists():
  r=requests.get(url,stream=True,timeout=(30,120));r.raise_for_status()
  with cache.open('wb') as f:
   for chunk in r.iter_content(1024*1024):f.write(chunk)
 frame=pd.read_parquet(cache,filters=[('Commodity','==','Maize')])
 print(year,len(frame),frame.Arrival_Date.min(),frame.Arrival_Date.max(),frame.columns.tolist(),flush=True)
 path=out/f'maize_{year}.csv';frame.to_csv(path,index=False)
 manifest.append({'year':year,'url':url,'revision':revision,'rows':len(frame),'first_date':str(frame.Arrival_Date.min()),'last_date':str(frame.Arrival_Date.max()),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'file':path.name})
(out/'source_manifest.json').write_text(json.dumps(manifest,indent=2))
