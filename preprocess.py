import os
import sys
from PIL import Image
import logging
import traceback

logging.basicConfig(
    filename='preprocess.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def resize_image(img, max_size):
    #redimensiona img
    if max(img.size) > max_size:
        ratio = max_size / max(img.size)
        new_size = tuple(int(dim * ratio) for dim in img.size)
        img = img.resize(new_size, Image.LANCZOS)
        logging.info(f"Imagem redimensionada para: {new_size}")
    return img

def optimize_image(img, quality):
    #preto e branco
    if img.mode == 'RGBA':
        background = Image.new('RGB', img.size, (255, 255, 255))
        background.paste(img, mask=img.split()[3])
        img = background
    
    if img.mode != 'P':
        img = img.convert('P', palette=Image.ADAPTIVE, colors=256)
    
    return img

def main():
    try:
        if len(sys.argv) < 3:
            raise ValueError("Argumentos insuficientes")
        
        input_path = sys.argv[1]
        output_path = sys.argv[2]
        max_size = int(sys.argv[3]) if len(sys.argv) > 3 else 1200
        quality = int(sys.argv[4]) if len(sys.argv) > 4 else 65

        logging.info(f"Iniciando pré-processamento: {input_path}")
        
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Arquivo não encontrado: {input_path}")
        
        img = Image.open(input_path)
        logging.info(f"Dimensões originais: {img.size}")
    
        img = resize_image(img, max_size)
        img = optimize_image(img, quality)
        
        img.save(output_path, 'PNG', optimize=True, quality=quality)
        logging.info(f"Arquivo salvo em: {output_path}")
        
        print(os.path.abspath(output_path))
        
    except Exception as e:
        logging.error(f"ERRO: {str(e)}\n{traceback.format_exc()}")
        sys.exit(1)

if __name__ == "__main__":
    main()