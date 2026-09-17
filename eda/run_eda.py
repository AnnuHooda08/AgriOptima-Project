from pathlib import Path
import argparse, json, math, re, warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
warnings.filterwarnings("ignore")

def safe(x):
    return re.sub(r"[^A-Za-z0-9._-]+", "_", str(x))[:140]

def norm(x):
    return re.sub(r"[^a-z0-9]+", "_", str(x).strip().lower()).strip("_")

def find_col(cols, keys):
    for c in cols:
        n = norm(c)
        if n in [norm(k) for k in keys]:
            return c
    for c in cols:
        n = norm(c)
        if any(norm(k) in n for k in keys):
            return c
    return None

def reservoir_sample(path, n, chunksize):
    rng = np.random.default_rng(42)
    rows, seen, cols = [], 0, None
    for chunk in pd.read_csv(path, chunksize=chunksize, low_memory=False):
        cols = list(chunk.columns)
        for row in chunk.itertuples(index=False, name=None):
            seen += 1
            if len(rows) < n:
                rows.append(row)
            else:
                j = rng.integers(0, seen)
                if j < n:
                    rows[j] = row
    return pd.DataFrame(rows, columns=cols) if cols else pd.DataFrame()

def full_profile(path, chunksize):
    header = pd.read_csv(path, nrows=0, low_memory=False)
    cols = list(header.columns)
    missing = pd.Series(0, index=cols, dtype="int64")
    total = 0
    uniques = {c:set() for c in cols}
    max_unique = 100000
    for ch in pd.read_csv(path, chunksize=chunksize, low_memory=False):
        total += len(ch)
        missing = missing.add(ch.isna().sum(), fill_value=0).astype("int64")
        for c in cols:
            if len(uniques[c]) <= max_unique:
                vals = ch[c].dropna().astype(str).unique()
                uniques[c].update(vals[:max_unique-len(uniques[c])])
    return cols, total, missing, uniques, {c:str(header[c].dtype) for c in cols}

def numeric_stats(path, cols, chunksize):
    if not cols: return pd.DataFrame()
    st = {c: [0,0,0.0,0.0,None,None] for c in cols}
    for ch in pd.read_csv(path, usecols=cols, chunksize=chunksize, low_memory=False):
        for c in cols:
            s = pd.to_numeric(ch[c], errors="coerce")
            v = s.dropna().to_numpy(float)
            st[c][0] += len(v); st[c][1] += int(s.isna().sum())
            if len(v):
                st[c][2] += v.sum(); st[c][3] += np.square(v).sum()
                st[c][4] = float(v.min()) if st[c][4] is None else min(st[c][4],float(v.min()))
                st[c][5] = float(v.max()) if st[c][5] is None else max(st[c][5],float(v.max()))
    out=[]
    for c,(n,miss,sm,ss,mn,mx) in st.items():
        mean=sm/n if n else np.nan
        var=max(ss/n-mean**2,0) if n else np.nan
        out.append([c,n,miss,mean,math.sqrt(var) if n else np.nan,mn,mx])
    return pd.DataFrame(out,columns=["column","count","missing","mean","std","min","max"])

def plot_numeric(df, cols, out):
    out.mkdir(parents=True,exist_ok=True)
    for c in cols:
        s=pd.to_numeric(df[c],errors="coerce").dropna()
        if len(s)<2: continue
        fig=plt.figure(figsize=(8,5)); plt.hist(s,bins=30); plt.title(f"Distribution: {c}"); plt.xlabel(c); plt.ylabel("Frequency"); plt.tight_layout()
        fig.savefig(out/f"{safe(c)}_hist.png",dpi=140); plt.close(fig)
        fig=plt.figure(figsize=(8,3.5)); plt.boxplot(s,vert=False); plt.title(f"Boxplot: {c}"); plt.xlabel(c); plt.tight_layout()
        fig.savefig(out/f"{safe(c)}_box.png",dpi=140); plt.close(fig)

def plot_cat(df, cols, out):
    out.mkdir(parents=True,exist_ok=True)
    for c in cols:
        vc=df[c].astype("string").fillna("<MISSING>").value_counts().head(15)
        if vc.empty: continue
        fig=plt.figure(figsize=(9,5)); plt.barh(vc.index.astype(str)[::-1],vc.values[::-1]); plt.title(f"Top categories: {c}"); plt.xlabel("Count in sample"); plt.tight_layout()
        fig.savefig(out/f"{safe(c)}_top.png",dpi=140); plt.close(fig)

def agri_checks(df):
    rows=[]
    for c in df.select_dtypes(include=np.number).columns:
        s=pd.to_numeric(df[c],errors="coerce").dropna()
        if s.empty: continue
        n=norm(c)
        if (s<0).any(): rows.append([c,"negative values",int((s<0).sum())])
        if (s==0).any(): rows.append([c,"zero values",int((s==0).sum())])
        if any(k in n for k in ["percent","percentage","loss_pct","loss_percent"]) and (s>100).any():
            rows.append([c,"percentage > 100",int((s>100).sum())])
        if "latitude" in n and ((s<-90)|(s>90)).any(): rows.append([c,"latitude outside -90..90",int(((s<-90)|(s>90)).sum())])
        if "longitude" in n and ((s<-180)|(s>180)).any(): rows.append([c,"longitude outside -180..180",int(((s<-180)|(s>180)).sum())])
    return pd.DataFrame(rows,columns=["column","check","count"])

def specific(path, df):
    name=path.name.lower(); cols=list(df.columns)
    if any(x in name for x in ["soil","soilgrids","nutrient"]): family="soil"
    elif any(x in name for x in ["post_harvest","food_loss","foodloss"]): family="post_harvest_loss"
    elif any(x in name for x in ["production","yield","crop"]): family="crop_production_or_yield"
    elif any(x in name for x in ["mandi","price","market"]): family="market_price"
    elif any(x in name for x in ["weather","rainfall","temperature","climate"]): family="weather"
    else: family="unknown"
    detected={}
    if family=="crop_production_or_yield":
        detected={"crop":find_col(cols,["crop","commodity"]),"area":find_col(cols,["area","harvested_area"]),"production":find_col(cols,["production"]),"yield":find_col(cols,["yield"]),"year":find_col(cols,["year","date"]),"state":find_col(cols,["state"]),"district":find_col(cols,["district"]),"season":find_col(cols,["season"])}
    elif family=="market_price":
        detected={"date":find_col(cols,["date","arrival_date"]),"crop":find_col(cols,["crop","commodity"]),"market":find_col(cols,["market","mandi"]),"state":find_col(cols,["state"]),"min_price":find_col(cols,["min_price"]),"max_price":find_col(cols,["max_price"]),"modal_price":find_col(cols,["modal_price","modal"])}
    elif family=="soil":
        detected={"ph":find_col(cols,["ph"]),"nitrogen":find_col(cols,["nitrogen"]),"organic_carbon":find_col(cols,["organic_carbon","organic carbon","oc"]),"cec":find_col(cols,["cec"]),"bulk_density":find_col(cols,["bulk_density","bulk density"]),"latitude":find_col(cols,["latitude","lat"]),"longitude":find_col(cols,["longitude","lon"])}
    elif family=="weather":
        detected={"date":find_col(cols,["date","time"]),"rainfall":find_col(cols,["rainfall","precipitation","prectot"]),"temperature":find_col(cols,["temperature","temp","t2m"]),"humidity":find_col(cols,["humidity"]),"latitude":find_col(cols,["latitude","lat"]),"longitude":find_col(cols,["longitude","lon"])}
    elif family=="post_harvest_loss":
        detected={"commodity":find_col(cols,["commodity","crop","product"]),"loss":find_col(cols,["loss","loss_percent","loss_percentage"]),"stage":find_col(cols,["stage","value_chain"]),"location":find_col(cols,["location","state","district","region"]),"year":find_col(cols,["year","date"])}
    notes=[]
    if detected.get("yield") and detected.get("production"):
        notes.append("Potential target leakage: if yield is production/area, do not use production as a predictor.")
    if family=="soil": notes.append("Check units and soil depth before merging SoilGrids layers.")
    return {"dataset_family":family,"detected_columns":detected,"notes":notes}

def analyze(path,reports,plots,sample_size,chunksize):
    name=safe(path.stem); rd=reports/name; pdx=plots/name; rd.mkdir(parents=True,exist_ok=True); pdx.mkdir(parents=True,exist_ok=True)
    cols,total,missing,uniques,dtypes=full_profile(path,chunksize)
    sample=reservoir_sample(path,sample_size,chunksize)
    numeric=[]
    for c in sample.columns:
        if pd.to_numeric(sample[c],errors="coerce").notna().sum() >= max(10,int(.1*len(sample))): numeric.append(c)
    cats=[c for c in sample.columns if c not in numeric and sample[c].nunique(dropna=True)<=100]
    cs=pd.DataFrame([{"column":c,"dtype":dtypes[c],"rows":total,"missing_count":int(missing[c]),"missing_percent":100*missing[c]/total if total else np.nan,"unique_values_tracked":len(uniques[c])} for c in cols])
    cs.to_csv(rd/"column_summary.csv",index=False)
    cs[["column","missing_count","missing_percent"]].sort_values("missing_percent",ascending=False).to_csv(rd/"missing_values.csv",index=False)
    numeric_stats(path,numeric,chunksize).to_csv(rd/"numeric_summary.csv",index=False)
    catrows=[]
    for c in cats:
        for v,n in sample[c].astype("string").fillna("<MISSING>").value_counts().head(30).items():
            catrows.append([c,str(v),int(n),100*n/len(sample)])
    pd.DataFrame(catrows,columns=["column","value","sample_count","sample_percent"]).to_csv(rd/"categorical_summary.csv",index=False)
    out=[]
    for c in numeric:
        s=pd.to_numeric(sample[c],errors="coerce").dropna()
        if len(s)<10: continue
        q1,q3=s.quantile([.25,.75]); iqr=q3-q1
        no=int(((s<q1-1.5*iqr)|(s>q3+1.5*iqr)).sum()) if iqr else 0
        out.append([c,q1,q3,iqr,no,100*no/len(s)])
    pd.DataFrame(out,columns=["column","q1","q3","iqr","sample_outliers","outlier_percent"]).to_csv(rd/"outlier_summary.csv",index=False)
    if len(numeric)>=2:
        corr=sample[numeric].apply(pd.to_numeric,errors="coerce").corr()
        corr.to_csv(rd/"correlation_matrix.csv")
        pairs=[]
        for i in range(len(numeric)):
            for j in range(i+1,len(numeric)):
                v=corr.iloc[i,j]
                if pd.notna(v): pairs.append([numeric[i],numeric[j],v,abs(v)])
        pd.DataFrame(pairs,columns=["feature_1","feature_2","correlation","abs_correlation"]).sort_values("abs_correlation",ascending=False).to_csv(rd/"correlation_pairs.csv",index=False)
        fig=plt.figure(figsize=(10,8)); plt.imshow(corr,aspect="auto"); plt.colorbar(label="Correlation"); plt.xticks(range(len(numeric)),numeric,rotation=90); plt.yticks(range(len(numeric)),numeric); plt.title("Correlation Matrix"); plt.tight_layout(); fig.savefig(pdx/"correlation_matrix.png",dpi=140); plt.close(fig)
    plot_numeric(sample,numeric,pdx/"numeric_distributions"); plot_cat(sample,cats,pdx/"categorical_distributions")
    ag=agri_checks(sample); ag.to_csv(rd/"agriculture_checks.csv",index=False)
    sp=specific(path,sample); (rd/"dataset_specific_analysis.json").write_text(json.dumps(sp,indent=2,default=str))
    overview={"file":path.name,"size_mb":round(path.stat().st_size/1024**2,2),"rows":total,"columns":len(cols),"sample_rows":len(sample),"numeric_columns":numeric,"dataset_family":sp["dataset_family"]}
    (rd/"overview.json").write_text(json.dumps(overview,indent=2,default=str))
    (rd/"eda_summary.txt").write_text("\n".join([f"Dataset: {path.name}",f"Rows: {total:,}",f"Columns: {len(cols)}",f"Sample: {len(sample):,}",f"Family: {sp['dataset_family']}","",*["NOTE: "+x for x in sp["notes"]]]))
    return overview

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--data-dir",default="DataSets"); ap.add_argument("--reports-dir",default="reports"); ap.add_argument("--plots-dir",default="plots")
    ap.add_argument("--sample-size",type=int,default=50000); ap.add_argument("--chunksize",type=int,default=50000)
    a=ap.parse_args(); data=Path(a.data_dir); reports=Path(a.reports_dir); plots=Path(a.plots_dir); reports.mkdir(exist_ok=True); plots.mkdir(exist_ok=True)
    files=sorted(data.glob("*.csv"))
    if not files: raise SystemExit(f"No CSV files found in {data.resolve()}")
    inv=[]
    print(f"Found {len(files)} CSV files")
    for f in files:
        try: inv.append(analyze(f,reports,plots,a.sample_size,a.chunksize)); print("DONE:",f.name)
        except Exception as e: print("ERROR:",f.name,e); inv.append({"file":f.name,"error":str(e)})
    pd.DataFrame(inv).to_csv(reports/"dataset_inventory.csv",index=False)
    print("\nEDA COMPLETE")
    print("Reports:",reports.resolve()); print("Plots:",plots.resolve())

if __name__=="__main__":
    main()
