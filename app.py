from pathlib import Path
from html import escape
from datetime import date, datetime
import base64, io, json
import pandas as pd
import streamlit as st
from modules import initialize, remember_widgets, identity, render_module, TITLES, DESCRIPTIONS, excel_bytes, commit_tables
from legacy import render_legacy

BASE=Path(__file__).parent
st.set_page_config(page_title='IE Toolkit | Praktikum Ergonomi',page_icon='◆',layout='wide',initial_sidebar_state='collapsed')
st.markdown('<style>'+ (BASE/'styles.css').read_text()+'</style>',unsafe_allow_html=True)


def encode(obj):
    if isinstance(obj,pd.DataFrame):
        return {'__dataframe__':obj.to_json(orient='split',date_format='iso')}
    if isinstance(obj,bytes):
        return {'__bytes__':base64.b64encode(obj).decode('ascii')}
    if isinstance(obj,(date,datetime)):return obj.isoformat()
    if hasattr(obj,'item'):return obj.item()
    raise TypeError(f'Jenis data tidak didukung: {type(obj).__name__}')


def decode(obj):
    if set(obj)=={'__dataframe__'}:
        return pd.read_json(io.StringIO(obj['__dataframe__']),orient='split')
    if set(obj)=={'__bytes__'}:
        return base64.b64decode(obj['__bytes__'],validate=True)
    return obj


def backup_bytes():
    keys=['tables','reports','notes','evidence','records']
    payload={k:st.session_state[k] for k in keys}
    all_widgets={**st.session_state.get('_widget_shadow',{}),**{k:v for k,v in st.session_state.items() if k.startswith('w_')}}
    payload['widgets']={k:v for k,v in all_widgets.items() if k.startswith('w_') and not k.startswith(('w_ed_','w_upload_')) and '_download_button_' not in k and k not in ['w_route','w_module_num','w_search']}
    return json.dumps({'schema':'ie-toolkit-1','exported_at':datetime.now().isoformat(),'payload':payload},default=encode,ensure_ascii=False,allow_nan=False).encode('utf-8')


def validate_backup(data):
    if not isinstance(data,dict) or data.get('schema')!='ie-toolkit-1':raise ValueError('Format cadangan tidak dikenal.')
    p=data.get('payload',{})
    if not isinstance(p,dict):raise ValueError('Isi cadangan tidak valid.')
    for k in ['tables','reports']:
        if not isinstance(p.get(k),dict) or not all(isinstance(df,pd.DataFrame) for df in p[k].values()):raise ValueError(f'Bagian {k} tidak valid.')
    for k in ['notes','evidence','widgets']:
        if not isinstance(p.get(k),dict):raise ValueError(f'Bagian {k} tidak valid.')
    if not isinstance(p.get('records'),list):raise ValueError('Catatan postur tidak valid.')
    if not all(isinstance(k,str) and k.startswith('w_') and not k.startswith(('w_ed_','w_upload_')) and k not in ['w_route','w_module_num','w_search'] for k in p['widgets']):raise ValueError('Kunci formulir tidak valid.')
    for ev in p['evidence'].values():
        if not isinstance(ev,dict) or not isinstance(ev.get('data'),bytes) or not isinstance(ev.get('name'),str):raise ValueError('Bukti gambar tidak valid.')
    return p


if '_pending_import' in st.session_state:
    p=st.session_state.pop('_pending_import')
    for k in list(st.session_state):
        if k.startswith('w_'):del st.session_state[k]
    for k in ['tables','reports','notes','evidence','records']:st.session_state[k]=p[k]
    st.session_state['bases']={k:v.copy() for k,v in p['tables'].items()}
    st.session_state['_widget_shadow']=p['widgets']
    st.session_state['revision']=st.session_state.get('revision',0)+1
    st.session_state['_import_success']=True
initialize()


def go(number):
    commit_tables()
    st.session_state['w_route']='Modul Praktikum'
    st.session_state['w_module_num']=number


def dashboard():
    st.markdown('<div class="welcome-box"><div class="section-kicker">Universitas Pelita Bangsa · Teknik Industri</div><h2>Ruang Praktikum Ergonomi</h2><div class="muted">Isi pengamatan, periksa hasil perhitungan, lalu susun analisis untuk setiap modul.</div></div>',unsafe_allow_html=True)
    left,right=st.columns([1,2.05],gap='medium')
    with left:
        today=date.today()
        st.markdown(f'<div class="sidebox"><h3>Ringkasan Praktikum</h3><div class="muted">{today:%d-%m-%Y} · waktu server</div><div class="side-row">8 modul praktikum<small>Fisiologi, postur, waktu kerja, antropometri dan lingkungan kerja</small></div><div class="side-row">{len(st.session_state["records"])} hasil postur dicatat<small>RULA dan OWAS per operator / aktivitas</small></div><div class="side-row">{len(st.session_state["evidence"])} bukti gambar<small>Hasil tulisan, postur dan sketsa</small></div></div>',unsafe_allow_html=True)
        st.markdown('<div class="sidebox"><h3>Urutan Pengisian</h3><div class="side-row">01 · Lengkapi identitas<small>Kelas, kelompok, anggota, dua operator</small></div><div class="side-row">02 · Isi lembar pengamatan<small>Gunakan data hasil praktikum</small></div><div class="side-row">03 · Periksa hasil dan analisis<small>Hasil otomatis tidak menggantikan pengamatan</small></div><div class="side-row">04 · Unduh laporan dan cadangan<small>Excel untuk laporan, JSON untuk pemulihan data</small></div></div>',unsafe_allow_html=True)
        st.info('Penyimpanan sesi, bukan database. Cadangkan sebelum menutup atau menyegarkan browser.')
    with right:
        st.subheader('Modul Akademik')
        search=st.text_input('Cari modul',placeholder='Cari berdasarkan nama atau nomor modul',key='w_search',label_visibility='collapsed')
        matched=[i for i,t in enumerate(TITLES,1) if search.lower() in (str(i)+' '+t+' '+DESCRIPTIONS[i-1]).lower()]
        for start in range(0,len(matched),2):
            cols=st.columns(2,gap='small')
            for col,n in zip(cols,matched[start:start+2]):
                with col:
                    status='Draft tersedia' if any(k.startswith(f'm{n}_') for k in st.session_state['tables']) else 'Belum ada input'
                    st.markdown(f'<div class="course-card"><span class="tag">Modul {n:02d}</span><div class="title">{escape(TITLES[n-1])}</div><div class="desc">{escape(DESCRIPTIONS[n-1])}</div><div class="meta">Teknik Industri · {status}</div></div>',unsafe_allow_html=True)
                    st.button('Buka lembar kerja',key=f'open_module_{n}',on_click=go,args=(n,),use_container_width=True)
        if not matched:st.info('Tidak ada modul yang cocok.')


def reports():
    st.title('Laporan dan Cadangan')
    st.caption('Excel memuat tabel dan analisis. Cadangan JSON memuat tabel, pilihan formulir, catatan postur, serta bukti gambar untuk dipulihkan.')
    if st.session_state.pop('_import_success',False):st.success('Cadangan berhasil dipulihkan.')
    frames={**st.session_state['tables'],**st.session_state['reports']}
    notes_rows=[{'Modul':m,'Bagian':part,'Isi':value} for m,items in st.session_state['notes'].items() for part,value in items.items()]
    frames['Analisis_semua_modul']=pd.DataFrame(notes_rows)
    frames['Bukti_gambar']=pd.DataFrame([{'ID':k,'Nama berkas':v['name'],'Disimpan dalam':'Cadangan JSON; tidak disematkan dalam Excel'} for k,v in st.session_state['evidence'].items()])
    a,b=st.columns(2)
    with a:
        st.subheader('Ekspor')
        st.download_button('Unduh seluruh tabel dan analisis (.xlsx)',excel_bytes(frames),file_name='Laporan_Praktikum_IE_Toolkit.xlsx',mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',use_container_width=True)
        try:st.download_button('Unduh cadangan lengkap (.json)',backup_bytes(),file_name='Cadangan_IE_Toolkit.json',mime='application/json',use_container_width=True)
        except (TypeError,ValueError) as e:st.error(f'Cadangan belum dapat dibuat: {e}')
        st.warning('Cadangan dapat berisi identitas dan data fisiologis. Simpan di lokasi yang aksesnya dibatasi.')
    with b:
        st.subheader('Pulihkan cadangan')
        uploaded=st.file_uploader('Pilih cadangan JSON dari aplikasi ini',type=['json'],key='backup_import')
        confirm=st.checkbox('Saya memahami pemulihan akan mengganti seluruh draft sesi ini.',key='backup_confirm')
        if st.button('Pulihkan cadangan',disabled=uploaded is None or not confirm,type='primary'):
            try:
                data=json.loads(uploaded.getvalue().decode('utf-8'),object_hook=decode)
                st.session_state['_pending_import']=validate_backup(data);st.rerun()
            except (ValueError,TypeError,KeyError,UnicodeDecodeError) as e:st.error(f'Cadangan gagal dibaca: {e}')
    st.subheader('Daftar data yang tersedia')
    st.dataframe(pd.DataFrame([{'Tabel':k,'Baris':len(v),'Kolom':len(v.columns)} for k,v in frames.items()]),hide_index=True,use_container_width=True)
    with st.expander('Panduan dan batasan perhitungan'):
        st.markdown('''
- OWAS memakai tabel modul, bukan tebakan atau penjumlahan skor postur.
- CVL memakai nadi istirahat dan nadi saat kerja; nadi setelah aktivitas disimpan terpisah.
- ECPT/ECPM dan efisiensi resmi modul 6–8 disediakan sebagai isian manual karena rumus berada pada gambar yang belum diverifikasi.
- Metode Schummard dan Obyektif mengikuti rumus teks modul. Rating Westinghouse serta RULA/REBA dipertahankan dari aplikasi awal dan belum diaudit ulang terhadap publikasi asli.
- Uji antropometri memakai SD sampel, Shapiro-Wilk (3–5000 nilai tidak konstan), dan persentil empiris atau parametrik. Tidak ada penghapusan outlier otomatis pada modul 4–5.
- Tidak ada autentikasi, database bersama, ataupun sinkronisasi antarperangkat. Unduhan JSON merupakan mekanisme simpan/muat permanen.
- UI mengikuti susunan kartu dan panel pada contoh Edlink, tanpa memakai merek, logo, jadwal, atau data kehadiran Edlink.
''')
        st.download_button('Unduh dokumen modul sumber (.docx)',(BASE/'assets/MODUL-1-8.docx').read_bytes(),file_name='MODUL-1-8.docx',mime='application/vnd.openxmlformats-officedocument.wordprocessingml.document')


name='Praktikan'
ops=st.session_state['tables'].get('operators')
if isinstance(ops,pd.DataFrame) and len(ops) and str(ops.iloc[0].get('Nama','')).strip():name=str(ops.iloc[0]['Nama'])
st.markdown(f'<div class="navbar"><div class="navbrand">◆ IE Toolkit <small>Universitas Pelita Bangsa</small></div><div class="navlinks">Praktikum · Teknik Industri</div><div class="navuser">{escape(name)}<br>Ruang kerja praktikum</div></div>',unsafe_allow_html=True)
route=st.radio('Menu utama',['Beranda','Identitas','Modul Praktikum','REBA Tambahan','Laporan'],horizontal=True,key='w_route',label_visibility='collapsed',on_change=commit_tables)
if route=='Beranda':dashboard()
elif route=='Identitas':identity()
elif route=='Modul Praktikum':
    n=st.selectbox('Pilih modul',list(range(1,9)),format_func=lambda n:f'Modul {n} · {TITLES[n-1]}',key='w_module_num',on_change=commit_tables)
    render_module(n)
elif route=='REBA Tambahan':
    st.title('REBA Assessment')
    st.caption('Fitur tambahan dari aplikasi awal. Modul 2 mewajibkan RULA dan OWAS; REBA tidak menggantikan OWAS.')
    render_legacy('REBA Assessment','w_reba_extra')
else:reports()
remember_widgets()
