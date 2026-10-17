from pathlib import Path
from html import escape
import io, json, math
import numpy as np
import pandas as pd
import streamlit as st
from core import parse_observations, statistics, percentiles, cvl, time_comparison, environment_metrics
from legacy import render_legacy

BASE=Path(__file__).parent
DATA=json.loads((BASE/'assets/module_data.json').read_text())
RATINGS=json.loads((BASE/'assets/ratings.json').read_text())
TITLES=['Fisiologi','Postur Kerja','Pengukuran Waktu Kerja','Antropometri','Antropometri Lanjutan','Temperatur','Kebisingan','Pencahayaan']
DESCRIPTIONS=[
    'Dua operator, kondisi normal dan setelah aktivitas, nadi kerja serta perhitungan CVL.',
    'RULA dan OWAS per operator dan aktivitas, bukti postur, perbandingan serta rekomendasi.',
    'Tujuh elemen kerja, tiga metode rating, rincian allowance dan uji data pengamatan.',
    '32 dimensi tubuh, pengukuran stasiun kerja, normalitas, persentil dan usulan desain.',
    'Tiga dimensi untuk sepuluh sampel, keseragaman, kecukupan dan rancangan stasiun kerja.',
    'Perbandingan kondisi dingin/panas dalam tiga percobaan per kondisi.',
    'Perbandingan kondisi normal/bising dalam tiga percobaan per kondisi.',
    'Perbandingan kondisi normal/gelap dalam tiga percobaan per kondisi.'
]


def initialize():
    for k,v in {'tables':{},'bases':{},'reports':{},'notes':{},'evidence':{},'records':[],'revision':0}.items():
        st.session_state.setdefault(k,v)
    for k,v in st.session_state.get('_widget_shadow',{}).items():
        if k not in st.session_state:
            st.session_state[k]=v


def remember_widgets():
    shadow=st.session_state.setdefault('_widget_shadow',{})
    for k,v in list(st.session_state.items()):
        if k.startswith('w_') and not k.startswith(('w_upload_','w_ed_')) and '_download_button_' not in k:
            shadow[k]=v


def commit_tables():
    st.session_state["bases"]={k:v.copy() for k,v in st.session_state["tables"].items()}
    st.session_state["revision"]+=1


def editor(key, initial, disabled=None, config=None, dynamic=False):
    rev=st.session_state['revision']
    st.session_state['bases'].setdefault(key,initial.copy())
    result=st.data_editor(st.session_state['bases'][key],key=f'w_ed_{key}_{rev}',hide_index=True,
                          num_rows='dynamic' if dynamic else 'fixed',use_container_width=True,
                          disabled=disabled or [],column_config=config or {})
    st.session_state['tables'][key]=result.copy()
    return result


def numeric_columns(names,minimum=0):
    return {n:st.column_config.NumberColumn(n,min_value=minimum,format='%.2f') for n in names}


def save_report(key,df):
    st.session_state['reports'][key]=df.copy()


def excel_bytes(tables):
    buffer=io.BytesIO()
    with pd.ExcelWriter(buffer,engine='openpyxl') as writer:
        for i,(name,df) in enumerate(tables.items(),1):
            safe=''.join(c if c.isalnum() or c=='_' else '_' for c in name)[:25]
            df=df.copy()
            for col in df.columns:
                if df[col].dtype=='object':
                    df[col]=df[col].map(lambda x: "'"+x if isinstance(x,str) and x.startswith(('=','+','-','@')) else x)
            df.to_excel(writer,sheet_name=f'{i}_{safe}'[:31],index=False)
    return buffer.getvalue()


def download_module(key):
    report={**{k:v for k,v in st.session_state['tables'].items() if k.startswith((key, 'w_'+key))},
            **{k:v for k,v in st.session_state['reports'].items() if k.startswith((key, 'w_'+key))}}
    if not report:
        return
    report['Identitas']=st.session_state['tables'].get('identity',pd.DataFrame())
    report['Operator']=st.session_state['tables'].get('operators',pd.DataFrame())
    report['Anggota']=st.session_state['tables'].get('members',pd.DataFrame())
    report['Analisis']=pd.DataFrame([{'Bagian':k,'Isi':v} for k,v in st.session_state['notes'].get(key,{}).items()])
    st.download_button('Unduh lembar kerja modul (.xlsx)',excel_bytes(report),file_name=f'{key}_IE_Toolkit.xlsx',mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',key='dl_'+key,use_container_width=True)


def notes(key,labels=None):
    st.subheader('Analisis dan pembahasan')
    labels=labels or ['Analisis hasil','Usulan perbaikan','Kesimpulan','Saran']
    store=st.session_state['notes'].setdefault(key,{})
    for i,label in enumerate(labels):
        value=st.text_area(label,value=store.get(label,''),key=f'w_note_{key}_{i}',height=95)
        store[label]=value


def evidence(key,label):
    file=st.file_uploader(label,type=['png','jpg','jpeg','webp'],key=f'w_upload_{key}')
    if file is not None:
        st.session_state['evidence'][key]={'name':file.name,'mime':file.type,'data':file.getvalue()}
    saved=st.session_state['evidence'].get(key)
    if saved:
        st.image(saved['data'],caption=saved['name'],width=340)
        if st.button('Hapus bukti ini',key='del_evidence_'+key):
            del st.session_state['evidence'][key]
            st.rerun()


def identity():
    st.subheader('Identitas praktikum')
    fields=['Kelas','Kelompok','Batch','Tanggal praktikum','Mata kuliah','Dosen / asisten']
    default=['J253B','','','','Perancangan Sistem Kerja dan Ergonomi + Praktek','']
    editor('identity',pd.DataFrame({'Isian':fields,'Nilai':default}),disabled=['Isian'])
    st.caption('Isi tanggal dalam format YYYY-MM-DD. Identitas ini digunakan bersama oleh seluruh modul.')
    st.subheader('Anggota kelompok')
    editor('members',pd.DataFrame({'Nama':['']*7,'NIM':['']*7,'Pembagian tugas':['']*7}),dynamic=True)
    st.subheader('Operator pengamatan')
    ops=pd.DataFrame({'ID':['Operator 1','Operator 2'],'Nama':['',''],'Jenis kelamin':['Laki-laki','Perempuan'],
                      'Usia (tahun)':[None,None],'Berat badan (kg)':[None,None]})
    editor('operators',ops,disabled=['ID'],config={'Jenis kelamin':st.column_config.SelectboxColumn(options=['Laki-laki','Perempuan']),**numeric_columns(['Usia (tahun)','Berat badan (kg)'])})
    st.info('Isian disimpan dalam sesi browser. Unduh cadangan JSON melalui menu Laporan untuk menyimpan permanen dan memulihkannya kembali.')


def physiology():
    key='m1'
    st.caption('Lengkapi identitas dua operator terlebih dahulu. Bedakan nadi saat bekerja dari nadi sesudah berhenti.')
    rows=[{'Operator':f'Operator {o}','Kondisi':c,'Sistolik (mmHg)':None,'Diastolik (mmHg)':None,
           'Nadi (denyut/menit)':None,'Suhu badan (°C)':None,'Waktu menulis (detik)':None}
          for o in [1,2] for c in ['Normal','Setelah aktivitas']]
    frame=editor(key+'_pengukuran',pd.DataFrame(rows),disabled=['Operator','Kondisi'],config=numeric_columns(list(rows[0])[2:]))
    st.subheader('Nadi kerja dan pemulihan')
    extra=pd.DataFrame({'Operator':['Operator 1','Operator 2'],'Nadi saat kerja (bpm)':[None,None],
                        'Nadi maksimum manual (bpm)':[None,None],'P1 pemulihan (bpm)':[None,None],
                        'P2 pemulihan (bpm)':[None,None],'P3 pemulihan (bpm)':[None,None],
                        'ECPT hasil manual':[None,None],'ECPM hasil manual':[None,None],'Satuan ECPT/ECPM':['','']})
    recovery=editor(key+'_pemulihan',extra,disabled=['Operator'],config=numeric_columns(list(extra.columns[1:-1])))
    st.caption('Nadi maksimum manual boleh kosong: gunakan estimasi 220−usia (laki-laki) atau 200−usia (perempuan). ECPT/ECPM dicatat manual; rumus gambar dalam modul belum ditranskripsi/diverifikasi. Jangan menganggap hasil ini diagnosis medis.')
    result=[]
    operators=st.session_state['tables'].get('operators',pd.DataFrame())
    for _,r in recovery.iterrows():
        op=r['Operator']
        normal=frame[(frame.Operator==op)&(frame.Kondisi=='Normal')].iloc[0]
        after=frame[(frame.Operator==op)&(frame.Kondisi=='Setelah aktivitas')].iloc[0]
        maximum=r['Nadi maksimum manual (bpm)']
        if pd.isna(maximum) and not operators.empty:
            data=operators[operators.ID==op]
            if len(data) and pd.notna(data.iloc[0]['Usia (tahun)']):
                age=float(data.iloc[0]['Usia (tahun)'])
                maximum=(220 if data.iloc[0]['Jenis kelamin']=='Laki-laki' else 200)-age
        if any(pd.isna(x) for x in [maximum,normal['Nadi (denyut/menit)'],r['Nadi saat kerja (bpm)']]):
            continue
        try:
            value=cvl(float(normal['Nadi (denyut/menit)']),float(r['Nadi saat kerja (bpm)']),float(maximum))
            delta=after['Waktu menulis (detik)']-normal['Waktu menulis (detik)'] if all(pd.notna(x) for x in [after['Waktu menulis (detik)'],normal['Waktu menulis (detik)']]) else None
            result.append({'Operator':op,'Nadi maksimum (bpm)':maximum,'CVL (%)':value,'Perubahan waktu menulis (detik)':delta})
        except ValueError as e:
            st.warning(f'{op}: {e}')
    with st.expander('Gambar rumus asli dari Modul 1'):
        for i,label in [(1,'CVL'),(2,'Rumus fisiologi berikutnya — gambar sumber 2'),(3,'Rumus fisiologi berikutnya — gambar sumber 3')]:
            st.image(str(BASE/'assets'/f'image{i}.jpg'),caption=label)
    st.latex(r'CVL=100\frac{DN_{kerja}-DN_{istirahat}}{DN_{maks}-DN_{istirahat}}')
    st.caption('Acuan CVL: https://ejournal.akprind.ac.id/index.php/rekavasi/article/download/4182/3025/7040')
    res=pd.DataFrame(result); save_report(key+'_hasil_CVL',res)
    if len(res):
        st.dataframe(res,hide_index=True,use_container_width=True)
    else:
        st.info('Hasil CVL muncul setelah usia atau nadi maksimum manual, nadi normal, dan nadi saat kerja dilengkapi.')
    with st.expander('Bukti hasil tulisan sebelum dan setelah aktivitas'):
        for o in [1,2]:
            for c in ['Normal','Setelah aktivitas']:
                evidence(f'm1_{o}_{c}',f'Operator {o} — {c}')
    notes(key,['Analisis Operator 1 normal','Analisis Operator 1 setelah aktivitas','Analisis Operator 2 normal','Analisis Operator 2 setelah aktivitas','Perhitungan / acuan ECPT dan ECPM','Kesimpulan','Saran'])
    download_module(key)


def posture():
    key='m2'
    a,b,c=st.columns(3)
    op=a.selectbox('Operator',['Operator 1','Operator 2'],key='w_m2_operator')
    activity=b.selectbox('Aktivitas',['Menulis','Berlari di treadmill','Naik turun tangga'],key='w_m2_activity')
    method=c.selectbox('Metode',['RULA','OWAS'],key='w_m2_method')
    st.caption('Modul menyebut treadmill dan naik-turun tangga pada bagian berbeda. Pilih aktivitas yang benar-benar diamati; keduanya tidak disamakan.')
    ctx=f'w_m2_{op}_{activity}_{method}'
    if method=='RULA':
        render_legacy('RULA Assessment',ctx)
        df=st.session_state['reports'].get(ctx+'_df_rula')
        score=int(df.loc[df['Komponen Evaluasi RULA']=='Skor Akhir RULA (Tabel C)','Nilai / Skor'].iloc[0]) if df is not None else None
        category=df.iloc[-1,1] if df is not None else ''
    else:
        labels=[['Lurus / tegak','Bungkuk ke depan','Miring ke samping','Bungkuk dan miring'],
                ['Kedua tangan di bawah bahu','Satu tangan pada / di atas bahu','Kedua tangan pada / di atas bahu'],
                ['Duduk','Dua kaki lurus','Satu kaki lurus','Kedua lutut menekuk','Satu lutut menekuk','Berlutut','Berjalan / bergerak'],
                ['<10 kg','10–20 kg','>20 kg']]
        codes=[]
        for i,(name,options) in enumerate(zip(['Punggung','Lengan','Kaki','Beban'],labels)):
            choice=st.selectbox(name,range(1,len(options)+1),format_func=lambda x,opts=options:f'{x} · {opts[x-1]}',key=ctx+str(i))
            codes.append(choice)
        code=''.join(map(str,codes)); score=DATA['owas'][code]
        category={1:'Aman',2:'Perbaikan beberapa waktu ke depan',3:'Perbaikan dalam waktu dekat',4:'Perbaikan sekarang juga'}[score]
        st.metric('Kategori tindakan OWAS',score)
        st.info(f'Kode postur {code} · {category}')
        st.caption('Lookup 252 kombinasi disalin dari tabel OWAS dalam MODUL-1-8.docx. Nilai tabel sumber belum diaudit terhadap publikasi OWAS asli.')
        save_report(ctx+'_detail',pd.DataFrame({'Komponen':['Punggung','Lengan','Kaki','Beban','Kategori'],'Skor':codes+[score]}))
    st.caption('Periksa seluruh pilihan sebelum mencatat hasil. Skor awal bukan data pengamatan tersimpan.')
    if st.button('Catat hasil operator dan aktivitas',key='record_'+ctx,type='primary') and score is not None:
        record={'Operator':op,'Aktivitas':activity,'Metode':method,'Skor':score,'Kategori':category}
        records=st.session_state['records']
        records[:]=[r for r in records if (r['Operator'],r['Aktivitas'],r['Metode'])!=(op,activity,method)]
        records.append(record); st.success('Hasil dicatat. Mengubah pilihan tidak menimpa catatan sebelum tombol ini ditekan kembali.')
    with st.expander('Foto postur yang diamati'):
        evidence(ctx,op+' — '+activity)
    st.subheader('Perbandingan hasil postur')
    compare=pd.DataFrame(st.session_state['records']); save_report('m2_perbandingan',compare)
    if not compare.empty:
        st.dataframe(compare,hide_index=True,use_container_width=True)
        st.dataframe(compare.pivot_table(index=['Metode','Aktivitas'],columns='Operator',values='Skor',aggfunc='last'),use_container_width=True)
    notes(key,['Analisis perbandingan postur','Usulan perbaikan postur kerja','Kesimpulan','Saran'])
    download_module(key)


def work_time():
    key='m3'
    mode=st.radio('Tampilan',['Lembar praktikum tiga metode','Kalkulator cepat sebelumnya'],horizontal=True,key='w_m3_mode',on_change=commit_tables)
    if mode=='Kalkulator cepat sebelumnya':
        st.caption('Kalkulator cepat mempertahankan data contoh dari aplikasi awal. Ganti seluruh data contoh dengan pengamatan Anda. Allowance berbasis waktu normal.')
        render_legacy('Waktu Baku','w_m3_quick')
        return
    st.caption('Waktu dan rating diisi per elemen, bukan menjumlahkan faktor penyesuaian atau persentase allowance antar-elemen.')
    elements=['Mengukur suhu badan (sebelum)','Mengukur tensi (sebelum)','Menulis (sebelum)','Lari','Menulis (setelah)','Mengukur suhu badan (setelah)','Mengukur tensi (setelah)']
    base=[{'ID':f'O{o}-E{i+1}','Operator':f'Operator {o}','Elemen kerja':el} for o in [1,2] for i,el in enumerate(elements)]
    t1,t2,t3=st.tabs(['1 · Waktu observasi','2 · Rating tiga metode','3 · Rincian allowance'])
    with t1:
        timing=editor(key+'_waktu',pd.DataFrame([{**r,'Pengamatan (detik, pisah koma)':''} for r in base]),disabled=['ID','Operator','Elemen kerja'])
        st.caption('Minimal dua pengamatan per elemen. Gunakan titik untuk desimal: 12.5, 13.0, 12.8. Data asli tetap disimpan.')
    factor_keys=['skill_dict','effort_dict','cond_dict','cons_dict']
    factor_cols=['Skill','Effort','Condition','Consistency']
    with t2:
        rating_rows=[]
        for r in base:
            rating_rows.append({**r,'Score Schummard':None,
                **{c:next(k for k,v in RATINGS[d].items() if v==0) for c,d in zip(factor_cols,factor_keys)},
                **{c:None for c in ['ABT','PK','PT','KMT','PERLT','BB']}})
        config={'Score Schummard':st.column_config.NumberColumn(min_value=1),
                **{c:st.column_config.SelectboxColumn(options=list(RATINGS[d])) for c,d in zip(factor_cols,factor_keys)},
                **numeric_columns(['ABT','PK','PT','KMT','PERLT','BB'])}
        rating=editor(key+'_rating',pd.DataFrame(rating_rows),disabled=['ID','Operator','Elemen kerja'],config=config)
        st.caption('Schummard: p=score/60. Westinghouse: p=1+jumlah empat faktor. Obyektif: p=(score/60)×[1+(ABT+PK+PT+KMT+PERLT+BB)/100]. Isi 0 jika faktor kesulitan memang bernilai nol; kolom kosong tidak dianggap nol.')
    with t3:
        acols=['Tenaga (%)','Sikap kerja (%)','Gerakan kerja (%)','Kelelahan mata (%)','Suhu (%)']
        allowance=editor(key+'_allowance',pd.DataFrame([{**r,**{c:None for c in acols}} for r in base]),disabled=['ID','Operator','Elemen kerja'],config=numeric_columns(acols))
        st.caption('Angka 4%, 1%, 0.5%, 5%, 5% pada modul adalah contoh. Isi hasil pengamatan sendiri. Total 108.50% lintas tujuh baris tidak dipakai sebagai allowance satu siklus.')
    c1,c2,c3=st.columns(3)
    basis=c1.selectbox('Basis allowance',['Waktu normal','Waktu kerja total'],key='w_m3_basis')
    k=c2.selectbox('k (keseragaman/kecukupan)',[2.,3.,1.],key='w_m3_k')
    precision=c3.number_input('Ketelitian (%)',min_value=1.,max_value=25.,value=5.,key='w_m3_precision')/100
    st.caption('Waktu normal: Wb=Wn×(1+a). Waktu kerja total: Wb=Wn/(1−a). Pilih definisi allowance yang ditetapkan pengampu.')
    results=[]; stats_rows=[]; issues=[]
    for idx,r in timing.iterrows():
        if not str(r['Pengamatan (detik, pisah koma)']).strip():
            continue
        try:
            vals=parse_observations(r['Pengamatan (detik, pisah koma)'])
            stats=statistics(vals,k,precision)
            stats_rows.append({'ID':r['ID'],'Operator':r['Operator'],'Elemen kerja':r['Elemen kerja'],**stats})
            rr=rating.iloc[idx]; aa=allowance.iloc[idx]
            required=[rr[c] for c in ['Score Schummard','ABT','PK','PT','KMT','PERLT','BB']]+[aa[c] for c in acols]
            if any(pd.isna(v) for v in required):
                issues.append(r['ID']+': waktu tersimpan; lengkapi rating dan lima komponen allowance.');continue
            west=1+sum(RATINGS[d][rr[c]] for c,d in zip(factor_cols,factor_keys))
            difficulty=sum(float(rr[c]) for c in ['ABT','PK','PT','KMT','PERLT','BB'])
            allow=sum(float(aa[c]) for c in acols)
            for res in time_comparison(stats['Rata-rata'],float(rr['Score Schummard']),west,difficulty,allow,basis):
                results.append({'ID':r['ID'],'Operator':r['Operator'],'Elemen kerja':r['Elemen kerja'],'Basis allowance':basis,**res})
        except (ValueError,KeyError,TypeError) as e:
            issues.append(f'{r["ID"]}: {e}')
    sdf=pd.DataFrame(stats_rows); rdf=pd.DataFrame(results)
    save_report(key+'_uji_statistik',sdf);save_report(key+'_perbandingan',rdf)
    if issues:
        with st.expander(f'{len(issues)} baris perlu dilengkapi / diperiksa',expanded=True):
            for msg in issues:st.warning(msg)
    if not sdf.empty:
        st.subheader('Uji keseragaman dan kecukupan per elemen');st.dataframe(sdf,hide_index=True,use_container_width=True)
        chosen=st.selectbox('Peta kontrol elemen',sdf.ID.tolist(),key='w_m3_chart')
        vals=parse_observations(timing.loc[timing.ID==chosen,'Pengamatan (detik, pisah koma)'].iloc[0])
        stats=statistics(vals,k,precision)
        st.line_chart(pd.DataFrame({'Waktu':vals,'BKA':[stats['BKA']]*len(vals),'Rata-rata':[stats['Rata-rata']]*len(vals),'BKB':[stats['BKB']]*len(vals)},index=range(1,len(vals)+1)))
    totals=pd.DataFrame()
    if not rdf.empty:
        st.subheader('Perbandingan tiga metode');st.dataframe(rdf,hide_index=True,use_container_width=True)
        totals=rdf.groupby(['Operator','Metode'],as_index=False).agg(**{'Elemen lengkap':('ID','nunique'),'Total Wn (detik)':('Wn (detik)','sum'),'Total Wb (detik)':('Wb (detik)','sum')})
        totals['Output satu siklus (unit/jam)']=np.where(totals['Elemen lengkap']==7,3600/totals['Total Wb (detik)'],np.nan)
        st.dataframe(totals,hide_index=True,use_container_width=True)
        st.caption('Output satu siklus hanya muncul ketika ketujuh elemen operator sudah lengkap. Hasil belum final jika uji data belum memenuhi.')
    save_report(key+'_total',totals)
    notes(key,['Analisis metode Schummard','Analisis metode Westinghouse','Analisis metode Obyektif','Perbandingan output standar','Kesimpulan','Saran'])
    download_module(key)


def anthropometry(advanced=False):
    key='m5' if advanced else 'm4'
    count=10 if advanced else 7
    dimensions=['Dimensi 1','Dimensi 2','Dimensi 3'] if advanced else DATA['dimensions']
    cols=[f'S{i+1} (cm)' for i in range(count)]
    initial=pd.DataFrame([{'Dimensi tubuh':d,**{c:None for c in cols}} for d in dimensions])
    st.caption('Satu kolom untuk satu responden. Sel kosong tidak dihitung sebagai nol. Semua ukuran tubuh memakai cm.')
    values=editor(key+'_dimensi',initial,disabled=[] if advanced else ['Dimensi tubuh'],config=numeric_columns(cols))
    with st.expander('Identitas responden'):
        editor(key+'_responden',pd.DataFrame({'ID':[f'S{i+1}' for i in range(count)],'Nama / kode':['']*count,'Jenis kelamin':['']*count,'Usia (tahun)':[None]*count}),disabled=['ID'],config={'Jenis kelamin':st.column_config.SelectboxColumn(options=['','Laki-laki','Perempuan']),**numeric_columns(['Usia (tahun)'])})
    a,b,c=st.columns(3)
    k=a.selectbox('Koefisien k',[2.,3.,1.],key='w_'+key+'_k')
    precision=b.number_input('Ketelitian (%)',min_value=1.,max_value=25.,value=5.,key='w_'+key+'_precision')/100
    mode=c.selectbox('Metode persentil',['Otomatis','Empiris','Normal parametrik'],key='w_'+key+'_percentile')
    st.caption('Otomatis: parametrik jika p Shapiro-Wilk ≥0.05, empiris jika tidak atau uji tak dapat dilakukan. p≥0.05 bukan bukti pasti distribusi normal. SD sampel dipakai; outlier hanya ditandai, tidak dihapus otomatis.')
    results=[]
    for _,row in values.iterrows():
        data=pd.to_numeric(row[cols],errors='coerce').dropna().tolist()
        if not data:continue
        if len(data)<2:
            st.warning(f'{row["Dimensi tubuh"]}: minimal dua pengukuran untuk statistik.');continue
        try:
            results.append({'Dimensi tubuh':row['Dimensi tubuh'],'Min':min(data),'Max':max(data),**statistics(data,k,precision),**percentiles(data,mode)})
        except ValueError as e:st.warning(f'{row["Dimensi tubuh"]}: {e}')
    report=pd.DataFrame(results);save_report(key+'_statistik',report)
    if len(report):
        st.subheader('Statistik, validasi dan persentil');st.dataframe(report,hide_index=True,use_container_width=True)
        chosen=st.selectbox('Dimensi untuk peta kontrol',report['Dimensi tubuh'].tolist(),key='w_'+key+'_chart')
        raw=values[values['Dimensi tubuh']==chosen].iloc[0]
        nums=pd.to_numeric(raw[cols],errors='coerce').dropna()
        stats=statistics(nums.tolist(),k,precision)
        st.line_chart(pd.DataFrame({'Ukuran (cm)':nums.to_numpy(),'BKA':[stats['BKA']]*len(nums),'Rata-rata':[stats['Rata-rata']]*len(nums),'BKB':[stats['BKB']]*len(nums)},index=nums.index))
    if not advanced:
        st.subheader('Ukuran stasiun kerja saat ini')
        measures=[('Pintu','Panjang'),('Pintu','Lebar'),('Pintu','Tinggi'),('Pintu','Tebal'),('Meja','Panjang'),('Meja','Lebar'),('Meja','Tinggi'),('Meja','Tebal'),('Kursi','Tinggi'),('Kursi','Lebar'),('Kursi','Tinggi sandaran tangan'),('Kursi','Sudut sandaran punggung'),('Kursi','Tinggi sandaran kaki')]
        editor(key+'_stasiun',pd.DataFrame([{'Stasiun':s,'Parameter':p,'Ukuran saat ini':None,'Satuan':'derajat' if 'Sudut' in p else 'cm'} for s,p in measures]),disabled=['Stasiun','Parameter','Satuan'],config=numeric_columns(['Ukuran saat ini']))
    st.subheader('Usulan rancangan stasiun kerja')
    plan=editor(key+'_rancangan',pd.DataFrame({'Komponen':['Pintu','Meja','Kursi'],'Parameter':['','',''],'Dimensi acuan':['','',''],
                    'Persentil dipilih':['P95','P50','P5'],'Ukuran usulan (cm)':[None]*3,'Allowance desain (cm)':[None]*3,'Alasan pemilihan':['']*3}),
                dynamic=True,config={'Persentil dipilih':st.column_config.SelectboxColumn(options=['P5','P10','P50','P90','P95']),**numeric_columns(['Ukuran usulan (cm)','Allowance desain (cm)'])})
    st.caption('Pemilihan persentil dan ukuran usulan harus mempertimbangkan fungsi ukuran serta populasi sasaran; aplikasi tidak otomatis menyamakan semua ukuran dengan P95.')
    with st.expander('Bukti pengukuran / sketsa rancangan'):
        evidence(key+'_sketsa','Unggah foto atau sketsa')
    notes(key,['Analisis keseragaman dan kecukupan','Analisis normalitas dan persentil','Kesesuaian dimensi stasiun kerja','Usulan redesign','Kesimpulan','Saran'])
    download_module(key)


def environment(number):
    key=f'm{number}'
    conditions={6:['Dingin','Panas'],7:['Normal','Bising'],8:['Normal','Gelap']}[number]
    unit={6:'°C',7:'dBA',8:'lux'}[number]
    level={6:'Temperatur (°C)',7:'Kebisingan (dBA)',8:'Pencahayaan (lux)'}[number]
    st.caption('Tiga percobaan per kondisi; durasi awal 120 detik sesuai modul. Isikan hasil nyata, bukan estimasi kondisi semata.')
    a,b=st.columns(2)
    operator=a.text_input('Operator',key='w_'+key+'_operator')
    timer=b.text_input('Pencatat waktu',key='w_'+key+'_timer')
    initial=pd.DataFrame([{'Kondisi':c,'Percobaan':p,level:None,'Durasi (detik)':120.,'Target (unit)':None,'Selesai (unit)':None,'Salah (unit)':None} for c in conditions for p in [1,2,3]])
    raw=editor(key+'_percobaan',initial,disabled=['Kondisi','Percobaan'],config=numeric_columns([level,'Durasi (detik)','Target (unit)','Selesai (unit)','Salah (unit)']))
    results=[]
    for _,r in raw.iterrows():
        required=[r[c] for c in ['Durasi (detik)','Target (unit)','Selesai (unit)','Salah (unit)']]
        if any(pd.isna(v) for v in required):continue
        try:
            if any(float(r[c])%1 for c in ['Target (unit)','Selesai (unit)','Salah (unit)']):
                raise ValueError('Jumlah unit harus bilangan bulat.')
            metrics=environment_metrics(*map(float,[r['Target (unit)'],r['Selesai (unit)'],r['Salah (unit)'],r['Durasi (detik)']]))
            results.append({'Operator':operator,'Pencatat waktu':timer,**r.to_dict(),**metrics})
        except ValueError as e:st.warning(f'{r["Kondisi"]} P{r["Percobaan"]}: {e}')
    st.info('Definisi operasional aplikasi: selesai%=selesai/target×100; kesalahan%=salah/selesai×100; baik terhadap target%=(selesai−salah)/target×100. Efisiensi pada modul tidak memiliki rumus teks yang terbaca; nilai baik terhadap target tidak otomatis dianggap efisiensi resmi modul.')
    result=pd.DataFrame(results);save_report(key+'_hasil',result)
    summary=pd.DataFrame()
    if len(result):
        st.subheader('Hasil per percobaan');st.dataframe(result,hide_index=True,use_container_width=True)
        metrics=['Selesai (%)','Kesalahan (%)','Baik terhadap target (%)','Output baik (unit/jam)']
        summary=result.groupby('Kondisi')[metrics].mean().reset_index()
        summary['Percobaan lengkap']=summary.Kondisi.map(result.groupby('Kondisi').size())
        st.subheader('Rata-rata per kondisi');st.dataframe(summary,hide_index=True,use_container_width=True)
        st.bar_chart(summary.set_index('Kondisi')[metrics[:3]])
        st.caption('Rata-rata adalah rata-rata aritmetika persentase tiap percobaan; hasil kondisi lengkap membutuhkan tiga percobaan. Kondisi dengan jumlah percobaan berbeda belum sebanding penuh.')
    save_report(key+'_ringkasan',summary)
    manual=editor(key+'_efisiensi_manual',pd.DataFrame({'Kondisi':conditions,'Efisiensi menurut pengampu (%)':[None,None],'Rumus / acuan':['','']}),disabled=['Kondisi'],config=numeric_columns(['Efisiensi menurut pengampu (%)']))
    notes(key,[f'Analisis kondisi {conditions[0].lower()}',f'Analisis kondisi {conditions[1].lower()}','Perbandingan hasil','Rekomendasi lingkungan kerja','Kesimpulan','Saran'])
    download_module(key)


def render_module(number):
    st.markdown(f'<div class="section-kicker">Lembar kerja praktikum · Modul {number:02d}</div>',unsafe_allow_html=True)
    st.title(TITLES[number-1]);st.caption(DESCRIPTIONS[number-1])
    if number==1:physiology()
    elif number==2:posture()
    elif number==3:work_time()
    elif number in [4,5]:anthropometry(number==5)
    else:environment(number)
