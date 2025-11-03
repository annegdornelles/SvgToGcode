import io
import numpy as np
from PIL import Image, ImageFilter
from potrace import Bitmap, Path
import logging

MAX_POINTS = 100000
MAX_DIMENSION = 500  

def preprocess_image(png_path):
    
    try:
        img = Image.open(png_path).convert("L")

        width, height = img.size
        if max(width, height) > MAX_DIMENSION:
            scale = MAX_DIMENSION / max(width, height)
            img = img.resize(
                (int(width * scale), int(height * scale)),
                Image.LANCZOS
            )

        threshold = 128
        img = img.point(lambda p: 255 if p > threshold else 0)

        return np.array(img, dtype=np.uint8)
    except Exception as e:
        logging.error(f"Erro no pré-processamento do converter.py: {str(e)}")
        raise

def simplify_image(image_array, quality=65):
    try:
        img = Image.fromarray(image_array)

        img = img.filter(ImageFilter.GaussianBlur(radius=1))

        #binarização
        img = img.point(lambda p: 255 if p > 127 else 0)

        return np.array(img, dtype=np.uint8)
    except Exception as e:
        logging.error(f"Erro na simplificação: {str(e)}")
        return image_array 

def png_to_svg(png_path, keep_every_point=False, quality=65, simplify=True):
    #simplifica. usa potrace
    logging.info(f"Carregando imagem: {png_path}")
    img_array = preprocess_image(png_path)

    if simplify:
        img_array = simplify_image(img_array, quality)
 
    bitmap = Bitmap((img_array == 0).astype(np.uint8))
    path = bitmap.trace()

    height, width = img_array.shape
    svg_io = io.StringIO()
    svg_io.write(f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">')
    for curve in path:
        d_attr = path_to_d(curve, keep_every_point)
        svg_io.write(f'<path d="{d_attr}" fill="black"/>')
    svg_io.write('</svg>')

    return svg_io.getvalue()

def path_to_d(curve: Path, keep_every_point: bool):
    #converte curva Potrace em atributo d de path svg
    d = []
    for segment in curve:
        if segment.is_corner:
            d.append(f"L {segment.c.x} {segment.c.y} L {segment.end_point.x} {segment.end_point.y}")
        else:
            d.append(f"C {segment.c1.x} {segment.c1.y}, {segment.c2.x} {segment.c2.y}, {segment.end_point.x} {segment.end_point.y}")
    return "M " + " ".join(d) + " Z"
