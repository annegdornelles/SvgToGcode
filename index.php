<?php
set_time_limit(0);
ini_set('display_errors', 1);
error_reporting(E_ALL);

$BASE_DIR = __DIR__ . DIRECTORY_SEPARATOR;
$PYTHON = 'C:\\Users\\gabri\\AppData\\Local\\Programs\\Python\\Python313\\python.exe';
$SCRIPT = $BASE_DIR . 'pngToGcode.py';

$UPLOAD_DIR = $BASE_DIR . 'uploads' . DIRECTORY_SEPARATOR;
$GCODE_DIR = $BASE_DIR . 'gcode' . DIRECTORY_SEPARATOR;

// Cria as pastas se não existirem
foreach ([$UPLOAD_DIR, $GCODE_DIR] as $dir) {
    if (!is_dir($dir)) {
        mkdir($dir, 0777, true);
    }
}

/**
 * Otimiza um PNG redimensionando e preservando transparência.
 */
function otimizar_png($inputPath, $outputPath, $maxWidth = 800, $maxHeight = 800)
{
    list($width, $height) = getimagesize($inputPath);

    $scale = min($maxWidth / $width, $maxHeight / $height, 1);
    $newWidth = (int)($width * $scale);
    $newHeight = (int)($height * $scale);

    $img = imagecreatefrompng($inputPath);
    if (!$img) {
        throw new Exception("Falha ao carregar a imagem.");
    }

    $tmp = imagecreatetruecolor($newWidth, $newHeight);
    imagesavealpha($tmp, true);
    $transparent = imagecolorallocatealpha($tmp, 0, 0, 0, 127);
    imagefill($tmp, 0, 0, $transparent);

    imagecopyresampled($tmp, $img, 0, 0, 0, 0, $newWidth, $newHeight, $width, $height);

    $result = imagepng($tmp, $outputPath, 6);

    imagedestroy($img);
    imagedestroy($tmp);

    if (!$result) {
        throw new Exception("Falha ao salvar imagem otimizada.");
    }
}

if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_FILES['imagem'])) {
    try {
        if ($_FILES['imagem']['error'] !== UPLOAD_ERR_OK) {
            throw new Exception("Erro no upload: " . $_FILES['imagem']['error']);
        }

        // Gera um ID único para cada execução
        $file_id = uniqid('img_', true);

        $uploaded_original = $UPLOAD_DIR . $file_id . '_orig.png';
        $uploaded_optimized = $UPLOAD_DIR . $file_id . '_opt.png';
        $gcode_path = $GCODE_DIR . $file_id . '.gcode';

        // Move o arquivo enviado
        if (!move_uploaded_file($_FILES['imagem']['tmp_name'], $uploaded_original)) {
            throw new Exception("Falha ao salvar o arquivo original.");
        }

        // Otimiza o PNG
        otimizar_png($uploaded_original, $uploaded_optimized);

        // Monta o comando para o Python
        $command = "\"$PYTHON\" \"$SCRIPT\" \"$uploaded_optimized\" \"$gcode_path\" 65 true 2>&1";
        exec($command, $output, $return_code);
        $output_text = implode("\n", $output);

        // Exibe debug em caso de falha
        echo "<h3>Debug do Python</h3>";
        echo "<pre>Return code: $return_code\n\nOutput:\n" . htmlspecialchars($output_text) . "</pre>";

        // Verifica se o G-code foi gerado
        if ($return_code !== 0 || !file_exists($gcode_path)) {
            echo "<h4>⚠️ Arquivo G-code não encontrado!</h4>";
            echo "<h4>📁 Conteúdo da pasta gcode/:</h4><pre>";
            foreach (scandir($GCODE_DIR) as $f) {
                if ($f !== '.' && $f !== '..') {
                    $fp = $GCODE_DIR . $f;
                    echo htmlspecialchars($f) . " — " . (file_exists($fp) ? filesize($fp) . ' bytes' : 'não existe') . "\n";
                }
            }
            echo "</pre>";
            throw new Exception("Conversão falhou. Retorno do Python:\n" . $output_text);
        }

        // Se tudo deu certo, força o download
        header('Content-Type: application/octet-stream');
        header('Content-Disposition: attachment; filename="' . basename($gcode_path) . '"');
        header('Content-Length: ' . filesize($gcode_path));
        readfile($gcode_path);
        exit;
    } catch (Exception $e) {
        echo "<pre style='color: red; background: #fee; padding: 15px; border-radius: 5px;'>";
        echo "❌ Erro na conversão:\n" . htmlspecialchars($e->getMessage());
        echo "</pre>";
    }
}
?>

<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Conversor PNG para G-code</title>
    <link rel="stylesheet" href="css/style.css">
</head>
<body>
    <div class="container">
        <h1>🎯 Conversor PNG para G-code</h1>

        <form method="POST" enctype="multipart/form-data">
            <input type="file" name="imagem" accept=".png" required>
            <br>
            <button type="submit">🚀 Converter para G-code</button>
        </form>

        <div class="info-section">
            <h2>🔧 O que é G-code?</h2>
            <p>
                O <span class="tech-term">G-code</span> é a linguagem padrão para controle numérico computadorizado (CNC). 
                É um conjunto de comandos que instruem máquinas automatizadas sobre como se mover, quando ligar/desligar 
                ferramentas e como executar operações específicas. Cada linha de G-code contém instruções precisas para 
                coordenadas, velocidades e funções da máquina.
            </p>
        </div>

        <h2>🏭 Aplicações do G-code</h2>
        <div class="applications">
            <div class="application-card">
                <h3>🖨️ Impressão 3D</h3>
                <p>
                    Na impressão 3D, o G-code controla cada movimento da <span class="tech-term">hotend</span> 
                    (bico extrusor), determina a quantidade de filamento a ser extrudado, a temperatura da mesa 
                    aquecida e do bico, além da velocidade de impressão. Cada camada do objeto é definida por 
                    coordenadas XYZ precisas.
                </p>
                <ul>
                    <li><strong>G1:</strong> Movimento linear com extrusão</li>
                    <li><strong>G0:</strong> Movimento rápido sem extrusão</li>
                    <li><strong>M104:</strong> Define temperatura do hotend</li>
                    <li><strong>M140:</strong> Define temperatura da mesa</li>
                </ul>
            </div>

            <div class="application-card">
                <h3>✏️ Plotters & Desenho</h3>
                <p>
                    Plotters usam G-code para controlar canetas, marcadores ou outras ferramentas de desenho. 
                    O código define quando a ferramenta deve tocar o papel (pen down) e quando deve se mover 
                    sem desenhar (pen up), criando desenhos vetoriais precisos.
                </p>
                <ul>
                    <li><strong>M3:</strong> Abaixar a caneta (pen down)</li>
                    <li><strong>M5:</strong> Levantar a caneta (pen up)</li>
                    <li><strong>G1:</strong> Movimento linear com desenho</li>
                    <li><strong>G0:</strong> Movimento sem desenhar</li>
                </ul>
            </div>

            <div class="application-card">
                <h3>⚙️ Máquinas CNC</h3>
                <p>
                    Em fresadoras e tornos CNC, o G-code controla ferramentas de corte, brocas e outros 
                    implementos para usinagem de precisão. Define velocidades de corte, profundidades 
                    e trajetórias complexas para criar peças mecânicas.
                </p>
                <ul>
                    <li><strong>G2/G3:</strong> Movimentos circulares</li>
                    <li><strong>M6:</strong> Troca de ferramenta</li>
                    <li><strong>F:</strong> Velocidade de avanço</li>
                    <li><strong>S:</strong> Velocidade do spindle</li>
                </ul>
            </div>
        </div>

        <h2>🎨 Conversão de Imagem para G-code</h2>
        <p>
            A conversão de uma imagem PNG para G-code envolve várias etapas complexas que transformam pixels 
            em comandos de movimento precisos:
        </p>
        
        <h3>🔍 Processamento da Imagem</h3>
        <ul>
            <li><strong>Detecção de bordas:</strong> Algoritmos como Canny ou Sobel identificam contornos na imagem</li>
            <li><strong>Simplificação vetorial:</strong> Converte pixels em vetores geométricos suaves</li>
            <li><strong>Otimização de trajetória:</strong> Minimiza movimentos desnecessários da ferramenta</li>
            <li><strong>Escalonamento:</strong> Ajusta o tamanho da imagem para as dimensões da máquina</li>
        </ul>

        <h3>📐 Parâmetros de Conversão</h3>
        <ul>
            <li><strong>Resolução:</strong> Define a precisão do desenho final</li>
            <li><strong>Velocidade de movimento:</strong> Controla a rapidez da execução</li>
            <li><strong>Profundidade:</strong> Para máquinas CNC, define o corte</li>
            <li><strong>Tipo de ferramenta:</strong> Caneta, laser, fresa, etc.</li>
        </ul>

        <div class="info-section">
            <h2>⚡ Vantagens do G-code</h2>
            <p>
                O G-code oferece controle total sobre máquinas automatizadas, permitindo reprodutibilidade 
                perfeita, automação completa e integração com software CAD/CAM. É um padrão industrial 
                reconhecido mundialmente, garantindo compatibilidade entre diferentes fabricantes e 
                sistemas de controle.
            </p>
        </div>

        <h2>🎯 Casos de Uso Específicos</h2>
        <p>
            Este conversor é ideal para artistas digitais que desejam materializar suas criações, 
            prototipadores que precisam de desenhos técnicos precisos, educadores que ensinam 
            fabricação digital e makers que exploram a interseção entre arte e tecnologia.
        </p>

        <p>
            <strong>Dica profissional:</strong> Sempre teste seu G-code em simuladores antes de 
            executar em máquinas reais. Isso evita acidentes e desperdício de material!
        </p>
    </div>
</body>
</html>
