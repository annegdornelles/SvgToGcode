import os
import sys
import re
import time
import logging
import traceback
import multiprocessing
from PIL import Image
from svg_to_gcode.svg_parser import parse_file
from svg_to_gcode.compiler import Compiler, interfaces
import converter

MAX_COMPLEXITY = 4000
MAX_IMG_SIZE = 500  
LOG_FILE = 'gcode_converter.log'

def info_print(*args, **kwargs):
    print(*args, **kwargs)
    sys.stdout.flush()

class GCodeConverter:
    def __init__(self, use_multiprocessing=True):
        self.use_multiprocessing = use_multiprocessing
        self.setup_logging()
        self.validate_environment()

    def setup_logging(self):
        logging.basicConfig(
            filename=LOG_FILE,
            level=logging.INFO,
            format='%(asctime)s | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        logging.info("Inicializando GCodeConverter")

    def validate_environment(self):
        try:
            import PIL
            import numpy
            logging.info("Dependências validadas com sucesso")
        except Exception as e:
            logging.critical(f"Falta dependência: {str(e)}")
            raise

    def preprocess_image(self, input_png):
        try:
            info_print(f"[preprocess] abrindo: {input_png}")
            img = Image.open(input_png).convert("L")  # escala de cinza

            width, height = img.size
            info_print(f"[preprocess] dimensão original: {width}x{height}")

            if max(width, height) > MAX_IMG_SIZE:
                scale = MAX_IMG_SIZE / max(width, height)
                new_w = int(width * scale)
                new_h = int(height * scale)
                img = img.resize((new_w, new_h), Image.LANCZOS)
                info_print(f"[preprocess] redimensionado para: {new_w}x{new_h}")

            # threshold fixo, mas permite ajuste futuro
            threshold = 128
            img = img.point(lambda p: 255 if p > threshold else 0)

            temp_path = os.path.splitext(input_png)[0] + "_pre.png"
            img.save(temp_path)
            info_print(f"[preprocess] salvo temporário: {temp_path} (size {os.path.getsize(temp_path)} bytes)")
            return temp_path
        except Exception as e:
            logging.error(f"Erro no pré-processamento: {e}")
            info_print("[preprocess] ERRO:", str(e))
            return input_png

    def optimize_svg(self, svg_path):
        try:
            with open(svg_path, 'r+', encoding='utf-8') as f:
                content = f.read()
                # Ajuste regex para não remover espaços essenciais entre comandos SVG
                optimizations = [
                    (r'fill-opacity="[\d.]+"', ''),
                    (r'stroke="none"', ''),
                    (r'stroke-width="[\d.]+"', ''),
                    (r'<!--.*?-->', ''),
                    (r'\s{2,}', ' '),  # mantém espaços simples
                ]
                for pattern, replacement in optimizations:
                    content = re.sub(pattern, replacement, content)
                f.seek(0)
                f.write(content)
                f.truncate()
            info_print(f"[optimize_svg] otimizado: {os.path.getsize(svg_path)} bytes")
        except Exception as e:
            logging.warning(f"Otimização SVG falhou: {str(e)}")
            info_print("[optimize_svg] WARNING:", str(e))

    def process_chunk(self, chunk_data):
        curves, temp_path = chunk_data
        try:
            if not curves:
                info_print(f"[process_chunk] AVISO: chunk vazio {temp_path}")
                return (True, temp_path)
            compiler = Compiler(
                interface_class=interfaces.Gcode,
                movement_speed=3000,
                cutting_speed=1000,
                pass_depth=0,
                dwell_time=100
            )
            compiler.append_curves(curves)
            compiler.compile_to_file(temp_path)
            info_print(f"[process_chunk] escrito {temp_path}")
            return (True, temp_path)
        except Exception as e:
            logging.error(f"Falha no chunk: {str(e)}")
            info_print("[process_chunk] ERRO:", str(e))
            return (False, temp_path)

    def parallel_conversion(self, svg_path, output_path):
        try:
            start_time = time.time()
            info_print(f"[parallel_conversion] parse_file: {svg_path}")
            curves = parse_file(svg_path)
            info_print(f"[parallel_conversion] curvas parseadas: {len(curves)}")

            if len(curves) == 0:
                info_print("[parallel_conversion] Nenhuma curva encontrada -> abortando")
                return False

            if len(curves) > MAX_COMPLEXITY:
                step = len(curves) // MAX_COMPLEXITY + 1
                curves = curves[::step]
                info_print(f"[parallel_conversion] simplificado para {len(curves)} curvas (step {step})")

            results = []
        
            if self.use_multiprocessing and len(curves) > 1000:
                num_workers = min(4, multiprocessing.cpu_count())
                chunk_size = max(20, len(curves) // num_workers)
                info_print(f"[parallel_conversion] usando multiprocessing: workers={num_workers}, chunk_size={chunk_size}")
                pool = multiprocessing.Pool(num_workers)
                tasks = [(curves[i:i+chunk_size], f"{output_path}.part{i}") for i in range(0, len(curves), chunk_size)]
                results = pool.map(self.process_chunk, tasks)
                pool.close(); pool.join()
            else:
                info_print("[parallel_conversion] processamento sequencial")
                results.append(self.process_chunk((curves, output_path)))

            success = all(r[0] for r in results)
            if success:
                if self.use_multiprocessing and len(curves) > 1000:
                    with open(output_path, 'w', encoding='utf-8') as outfile:
                        for ok, part in results:
                            if not os.path.exists(part):
                                info_print("[parallel_conversion] parte ausente:", part)
                                continue
                            with open(part, 'r', encoding='utf-8') as infile:
                                outfile.write(infile.read())
                            try:
                                os.remove(part)
                            except Exception:
                                pass
                    info_print(f"[parallel_conversion] partes combinadas em {output_path}")

                elapsed = time.time() - start_time
                info_print(f"[parallel_conversion] sucesso em {elapsed:.2f}s")
                
                if os.path.exists(output_path):
                    info_print(f"[parallel_conversion] G-code existe: {output_path} size={os.path.getsize(output_path)}")
                else:
                    info_print(f"[parallel_conversion] AVISO: G-code não foi criado: {output_path}")
                    return False

                return True
            else:
                info_print("[parallel_conversion] Nem todos os chunks tiveram sucesso")
                return False
        except Exception as e:
            logging.error(f"Falha na conversão paralela: {str(e)}")
            info_print("[parallel_conversion] ERRO:", str(e))
            info_print(traceback.format_exc())
            return False

    def convert(self, input_png, output_gcode, quality=65, simplify=True):
        try:
            info_print(f"[convert] inicio. input={input_png} output={output_gcode}")
            if not os.path.exists(input_png):
                info_print("[convert] arquivo input nao existe")
                raise FileNotFoundError(f"Arquivo não encontrado: {input_png}")

            preprocessed = self.preprocess_image(input_png)
            if preprocessed != input_png:
                info_print(f"[convert] usando pré-processado: {preprocessed}")

            info_print("[convert] chamando converter.png_to_svg(...)")
            svg_content = converter.png_to_svg(preprocessed, keep_every_point=False, quality=quality, simplify=simplify)

            info_print(f"[convert] svg_content length: {len(svg_content) if svg_content else 0}")
            svg_path = os.path.splitext(output_gcode)[0] + ".svg"
            with open(svg_path, 'w', encoding='utf-8') as f:
                f.write(svg_content)
            info_print(f"[convert] SVG gravado em {svg_path} size={os.path.getsize(svg_path)}")

            self.optimize_svg(svg_path)

            ok = self.parallel_conversion(svg_path, output_gcode)

            if os.path.exists(svg_path):
                os.remove(svg_path)
            if os.path.exists(preprocessed) and preprocessed != input_png:
                os.remove(preprocessed)

            info_print(f"[convert] final. ok={ok}")
            return ok
        except Exception as e:
            logging.critical(f"Erro na conversão principal: {str(e)}\n{traceback.format_exc()}")
            info_print("[convert] EXCEPTION:", str(e))
            info_print(traceback.format_exc())
            return False

def main():
    try:
        if len(sys.argv) < 3:
            print("Uso: python pngToGcode.py entrada.png saida.gcode [qualidade=65] [simplificar=True] [multiprocessing=True]")
            sys.exit(1)

        quality = int(sys.argv[3]) if len(sys.argv) > 3 else 65
        simplify = sys.argv[4].lower() == 'true' if len(sys.argv) > 4 else True
        use_multiprocessing = sys.argv[5].lower() == 'true' if len(sys.argv) > 5 else True

        info_print(f"[main] quality={quality} simplify={simplify} multiprocessing={use_multiprocessing}")
        conv = GCodeConverter(use_multiprocessing=use_multiprocessing)
        success = conv.convert(sys.argv[1], sys.argv[2], quality, simplify)
        info_print(f"[main] success={success}")
        sys.exit(0 if success else 1)
    except Exception as e:
        info_print("[main] ERRO NO MAIN:", str(e))
        info_print(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()
