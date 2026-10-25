"""ink-or-hallucination: point-and-click front end.   Run:  streamlit run app.py

Pick a segment folder that holds, for each model, NAME.tif and NAME_reverse.tif (the same model with the layers in
the other order), and optionally mask.npy. The app runs segment.py (alignment, triangle, windowed check) and shows
the report. Nothing leaves your computer.
"""
import glob, io, json, os, sys
import streamlit as st

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import segment as sg

st.set_page_config(page_title='ink-or-hallucination', layout='wide')
st.title('ink or hallucination?')
st.caption('Label-free checks for 2.5D ink maps: do several models see the same strokes, in the right layer order?')

with st.sidebar:
    st.header('Segment')
    seg = st.text_input('Folder with the maps', value=st.session_state.get('seg', ''), placeholder='/path/to/segment')
    found = []
    if seg and os.path.isdir(seg):
        for p in sorted(glob.glob(os.path.join(seg, '*'))):
            b, e = os.path.splitext(os.path.basename(p))
            if e.lower() in ('.tif', '.tiff', '.npy', '.png') and not b.endswith('_reverse') and b != 'mask' \
                    and sg.find(seg, b + '_reverse'):
                found.append(b)
        if found:
            st.success(f'{len(found)} models with both orders: {", ".join(found)}')
        else:
            st.warning('No NAME + NAME_reverse pairs found here.')
    models = st.multiselect('Models (3 or more; the less related, the stronger the check)', found, default=found[:3])
    order = st.radio('Which file is the right layer order?', ['forward', 'reverse'], horizontal=True,
                     help='forward = NAME.tif, reverse = NAME_reverse.tif. Use the layer-order rule '
                          '(scripts/curvatura.py + scripts/ordem_camadas.py) to decide, before looking at the maps.')
    st.header('Window')
    how = st.radio('Window size from', ['pixel size', 'pixels'], horizontal=True)
    if how == 'pixel size':
        px_um = st.number_input('Pixel size of the maps (µm)', 1.0, 50.0, 9.6, 0.1)
        win = int(round(2500 / px_um)); st.caption(f'2.5 mm window = {win} px')
    else:
        win = st.number_input('Window (px, about one letter)', 32, 2000, 260, 2)
    mask = st.text_input('Mask (optional)', value=(sg.find(seg, 'mask') or '') if seg and os.path.isdir(seg) else '')
    go = st.button('Run checks', type='primary', disabled=len(models) < 3)

if go:
    st.session_state['seg'] = seg
    box = st.status('Running…', expanded=True)
    try:
        R = sg.run(seg, models, order, mask or None, int(win), log=box.write)
        box.update(label=f'Done in {R["seconds"]} s', state='complete')
        st.session_state['R'] = R
    except SystemExit as e:
        box.update(label='Stopped', state='error'); st.error(str(e))

R = st.session_state.get('R')
if R:
    out = os.path.join(R['segment'], 'inkcheck_report')
    st.subheader('In short')
    for kind, text in sg.summary(R):
        {'good': st.success, 'warn': st.warning, 'bad': st.error}[kind](text)
    st.caption('Green windows: strokes the other models also see. Red: strokes only this map shows. '
               'An alarm means "the other models do not see this", not "this is fake".')
    cols = st.columns(len(R['local']))
    for c, (m, L) in zip(cols, R['local'].items()):
        with c:
            st.metric(m, f'{L["unsupported"]} / {L["judged"]}', help='windows NOT supported / windows with strokes')
            st.image(os.path.join(out, f'windows_{m}.png'), width='stretch')
    with st.expander('Triangle: verdicts and pairs'):
        st.table({'map': list(R['triangle']['verdict']), 'verdict': list(R['triangle']['verdict'].values())})
        st.table({'pair': list(R['triangle']['pairs']),
                  'corr': [round(p['corr'], 3) for p in R['triangle']['pairs'].values()],
                  'null max': [round(p['null_max'], 3) for p in R['triangle']['pairs'].values()]})
    with st.expander('Alignment between maps'):
        st.json(R['alignment'])
    with st.expander('What these checks can and cannot tell'):
        st.markdown(open(os.path.join(HERE, 'LIMITS.md'), encoding='utf-8').read() if os.path.exists(os.path.join(HERE, 'LIMITS.md')) else '')
    st.download_button('Download report (HTML)', open(os.path.join(out, 'report.html'), 'rb'), 'inkcheck_report.html', 'text/html')
