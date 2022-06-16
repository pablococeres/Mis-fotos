import streamlit as st
from persist import persist, load_widget_state
import sqlite3
import numpy as np
import cv2
from  PIL import Image
import datetime
import io
import base64
import io
from st_clickable_images import clickable_images


# Quitar el menú por defecto y la marca Streamlit del pie de página
st.set_page_config(
   page_title="Mis mejores Fotos",
   page_icon="🧊",
   layout="wide",
   initial_sidebar_state="expanded",
)
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# Quitar espacio en blanco de la parte superior
st.markdown("""
        <style>
               .css-18e3th9 {
                    padding-top: 0rem;
                    padding-bottom: 10rem;
                    padding-left: 5rem;
                    padding-right: 5rem;
                }
               .css-1d391kg {
                    padding-top: 3.5rem;
                    padding-right: 1rem;
                    padding-bottom: 3.5rem;
                    padding-left: 1rem;
                }
        </style>
        """, unsafe_allow_html=True)

#Crear la base de dato y establecer la conexión
conn = sqlite3.connect('data.db')
c = conn.cursor()

# Si no existe crea la tabla donde almacenar las fotos
def tabla_fotos():
	c.execute('CREATE TABLE IF NOT EXISTS tablafotos(ID INTEGER PRIMARY KEY AUTOINCREMENT, foto BLOB, fecha TEXT)')

# Agrega la foto a la base de datos en bormato binario connservando los colores
def agregar_foto(fotoguardar, fecha):
	encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 100]
	result, encimg = cv2.imencode('.jpg', fotoguardar, encode_param)
	c.execute("INSERT INTO tablafotos(foto, fecha) VALUES (?,?)",(encimg, fecha))
	conn.commit()

# Selecciona todas las filas de la tabla de fotos
def todas_fotos():
	c.execute('SELECT * FROM tablafotos')
	data = c.fetchall()
	return data

# Actualiza una foto editada
def update(photo, id):
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 100]
    result, encimg = cv2.imencode('.jpg', photo, encode_param)
    c.execute('UPDATE tablafotos SET foto = ? WHERE id = ?', (encimg, id,))
    conn.commit()

# Borra definitivamente una foto de la tabla
def borrar(id):
	c.execute('DELETE FROM tablafotos WHERE id = ?', (id,))
	conn.commit()

# Lista las fotos en pantalla y las hace clicables
def lista_fotos():
	tabla_fotos()
	fotos = todas_fotos()
	if len(fotos) > 0:
		st.session_state.listado_fotos = []
		st.session_state.elegida_fotos = []
		st.session_state.elnumero = []
		for f in fotos:
			photo = f[1]
			numero = f[0]
			st.session_state.elegida_fotos.append(f[1])
			encoded = base64.b64encode(photo).decode()
            #st.image(photo, width=400)
			st.session_state.listado_fotos.append(f"data:image/jpeg;base64,{encoded}")
			st.session_state.elnumero.append(numero)
    
		clicked = clickable_images(st.session_state.listado_fotos,
        titles=[f"Image #{str(i)}" for i in range(4)],
        div_style={"display": "flex", "justify-content": "center", "flex-wrap": "wrap"},
        img_style={"margin": "5px", "height": "200px"},key=persist("lafoto"))
	else:
		st.subheader("Debes subir al menos una foto para poder editarla")

# El editor de las fotos, y donde pueden ser borradas
def editar(foto, id):

    image = Image.open(foto)

    if st.button('Borrar'):
            borrar(id)
    
    colu1, colu2 = st.columns( [0.5, 0.5])
    with colu1:
        st.markdown('<p style="text-align: left;">Antes</p>',unsafe_allow_html=True)
        st.image(st.session_state.listado_fotos[st.session_state.lafoto], width=300)

    with colu2:
        binfoto = ""
        converted_img = image
        st.markdown('<p style="text-align: left;">Después</p>',unsafe_allow_html=True)
        filter = st.sidebar.radio('Editar tu foto con:', ['Original','Gray Image','Black and White', 'Pencil Sketch', 'Blur Effect'], key = id)
        if filter == 'Gray Image':
                converted_img = np.array(image.convert('RGB'))
                gray_scale = cv2.cvtColor(converted_img, cv2.COLOR_RGB2GRAY)
                binfoto = gray_scale
                st.image(gray_scale, width=300)
        elif filter == 'Black and White':
                converted_img = np.array(image.convert('RGB'))
                gray_scale = cv2.cvtColor(converted_img, cv2.COLOR_RGB2GRAY)
                slider = st.sidebar.slider('Adjust the intensity', 1, 255, 127, step=1)
                (thresh, blackAndWhiteImage) = cv2.threshold(gray_scale, slider, 255, cv2.THRESH_BINARY)
                binfoto = blackAndWhiteImage
                st.image(blackAndWhiteImage, width=300)
        elif filter == 'Pencil Sketch':
                converted_img = np.array(image.convert('RGB'))
                gray_scale = cv2.cvtColor(converted_img, cv2.COLOR_RGB2GRAY)
                inv_gray = 255 - gray_scale
                slider = st.sidebar.slider('Adjust the intensity', 25, 255, 125, step=2)
                blur_image = cv2.GaussianBlur(inv_gray, (slider,slider), 0, 0)
                sketch = cv2.divide(gray_scale, 255 - blur_image, scale=256)
                binfoto = sketch
                st.image(sketch, width=300) 
        elif filter == 'Blur Effect':
                converted_img = np.array(image.convert('RGB'))
                slider = st.sidebar.slider('Adjust the intensity', 5, 81, 33, step=2)
                converted_img = cv2.cvtColor(converted_img, cv2.COLOR_RGB2BGR)
                blur_image = cv2.GaussianBlur(converted_img, (slider,slider), 0, 0)
                binfoto = blur_image
                st.image(blur_image, channels='BGR', width=300) 
        else: 
                binfoto = st.session_state.listado_fotos[st.session_state.lafoto]
                st.image(binfoto, width=300)
		
        if st.button('Guardar'):
            e = datetime.datetime.now()
            hoy = (e.day, e.month, e.year)
            update(binfoto, id)
            st.text('Foto editada')
        
# Declara las páginas y las hace accesibles, establece el valor inicial del selector de fotos            
def main():
    if "page" not in st.session_state:
        st.session_state.update({
            "page": "home",
            "lafoto": -1,
        })
    page = st.sidebar.radio("Elige qué quieres hacer", tuple(PAGES.keys()), format_func=str.capitalize)
    PAGES[page]()

# La página Editar
def page_editar():

    if st.session_state.lafoto > -1 and st.session_state.lafoto <= len(st.session_state.listado_fotos):
        st.image(st.session_state.listado_fotos[st.session_state.lafoto])
        sele = 0
        con = 0
        for i in st.session_state.elegida_fotos: 
            if con == int(st.session_state.lafoto):
                sele = io.BytesIO(i)
                elid = st.session_state.elnumero[con]     
            con += 1
        editar(sele, elid)      
    else:
        st.text('Debes hacer click en una imagen en "Mis Fotos" para poder editarla o borrarla')

# La página de inicio
def page_home():
    st.header("Mis Fotos")
    st.text("Haz click en la imagen que quieras editar y ve a la página Editar")
    lista_fotos()

# La página donde se cargan las fotos
def page_subir():
    st.header("Subir una foto")
    uploaded_file = st.file_uploader("", type=['jpg','png','jpeg'], key = 'subir')
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, width=400)
        e = datetime.datetime.now()
        hoy = (e.day, e.month, e.year)
        bin_img = np.array(image.convert('RGB'))
        img_reconv = cv2.cvtColor(bin_img, cv2.COLOR_RGB2BGR)
        agregar_foto(img_reconv, str(hoy))
        st.text('Foto subida')

# diccionario de páginas
PAGES = {
    "Mis fotos": page_home,
    "Editar": page_editar,
    "Subir Foto": page_subir,  
}

# Inicio de la aplicación
if __name__ == "__main__":
    load_widget_state()
    main()