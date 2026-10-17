import math
import numpy as np
from scipy.stats import shapiro, norm


def parse_observations(text, minimum=2):
    vals = [float(v.strip()) for v in str(text).replace(';', ',').split(',') if v.strip()]
    if len(vals) < minimum:
        raise ValueError(f'Masukkan minimal {minimum} pengamatan, dipisahkan koma; gunakan titik untuk desimal.')
    if not all(math.isfinite(x) and x > 0 for x in vals):
        raise ValueError('Semua pengamatan harus berupa angka hingga yang lebih besar dari nol.')
    return vals


def statistics(values, k=2., precision=.05, sample=True):
    a=np.asarray(values,dtype=float)
    if len(a)<2 or not np.isfinite(a).all() or (a<=0).any():
        raise ValueError('Statistik memerlukan minimal dua nilai positif dan hingga.')
    n=len(a); mean=float(a.mean()); sd=float(a.std(ddof=1 if sample else 0))
    upper=mean+k*sd; lower=mean-k*sd
    needed=((k/precision)*math.sqrt(max(n*float((a*a).sum())-float(a.sum())**2,0))/float(a.sum()))**2
    return {'N':n,'Jumlah':float(a.sum()),'Jumlah kuadrat':float((a*a).sum()),'Rata-rata':mean,'SD':sd,
            'BKA':upper,'BKB':lower,"N'":needed,'N minimum':math.ceil(needed),
            'Keseragaman':'Seragam' if ((a>=lower)&(a<=upper)).all() else 'Tidak seragam',
            'Kecukupan':'Cukup' if needed<=n else 'Belum cukup'}


def percentiles(values, mode='Empiris'):
    a=np.asarray(values,dtype=float)
    if len(a)<2 or not np.isfinite(a).all() or (a<=0).any():
        raise ValueError('Persentil memerlukan minimal dua nilai positif dan hingga.')
    normality=None
    if 3<=len(a)<=5000 and np.ptp(a)>0:
        normality=float(shapiro(a).pvalue)
    use_normal=mode=='Normal parametrik' or (mode=='Otomatis' and normality is not None and normality>=.05)
    result={f'P{p}':float(a.mean()+norm.ppf(p/100)*a.std(ddof=1)) if use_normal else float(np.percentile(a,p)) for p in [5,10,50,90,95]}
    result.update({'p Shapiro-Wilk':normality,'Metode persentil':'Normal parametrik' if use_normal else 'Empiris (interpolasi linear)'})
    return result


def cvl(rest, work, maximum):
    if any(x is None or not math.isfinite(float(x)) or x<=0 for x in [rest,work,maximum]):
        raise ValueError('Isi nadi istirahat, nadi saat kerja, dan nadi maksimum dengan angka positif.')
    if maximum<=rest:
        raise ValueError('Nadi maksimum harus lebih besar dari nadi istirahat.')
    if work<rest or work>maximum:
        raise ValueError('Periksa nadi kerja: harus berada antara nadi istirahat dan maksimum estimasi; sesuaikan maksimum manual jika perlu.')
    return 100*(work-rest)/(maximum-rest)


def time_comparison(ws, score, west, difficulty, allowance, basis):
    numbers=[ws,score,west,difficulty,allowance]
    if any(v is None or not math.isfinite(float(v)) for v in numbers):
        raise ValueError('Lengkapi waktu, rating, kesulitan, dan allowance.')
    if ws<=0 or score<=0 or west<=0 or difficulty<0 or not 0<=allowance<100:
        raise ValueError('Waktu/rating harus positif, kesulitan tidak negatif, allowance 0–<100%.')
    factors={'Schummard':score/60,'Westinghouse':west,'Obyektif':score/60*(1+difficulty/100)}
    ans=[]
    for method,p in factors.items():
        wn=ws*p
        wb=wn*(1+allowance/100) if basis=='Waktu normal' else wn/(1-allowance/100)
        ans.append({'Metode':method,'Ws (detik)':ws,'p':p,'Wn (detik)':wn,'Allowance (%)':allowance,'Wb (detik)':wb,'Output (unit/jam)':3600/wb})
    return ans


def environment_metrics(target, completed, errors, seconds):
    vals=[target,completed,errors,seconds]
    if any(v is None or not math.isfinite(float(v)) for v in vals):
        raise ValueError('Lengkapi target, selesai, salah, dan durasi.')
    if target<=0 or seconds<=0 or min(completed,errors)<0 or errors>completed:
        raise ValueError('Target/durasi harus positif; 0 ≤ salah ≤ selesai.')
    return {'Selesai (%)':100*completed/target,'Kesalahan (%)':100*errors/completed if completed else 0,
            'Baik terhadap target (%)':100*(completed-errors)/target,
            'Output baik (unit/jam)':3600*(completed-errors)/seconds}
