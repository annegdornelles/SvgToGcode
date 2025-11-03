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
            <h2>ℹ️ Sobre o Conversor</h2>
            <p>
                Este sistema converte imagens PNG em arquivos <strong>G-code</strong> prontos para máquinas CNC, impressoras 3D e plotters.
                Ele faz a otimização automática da imagem, converte contornos em trajetórias e gera comandos precisos para máquinas automatizadas.
            </p>
        </div>
    </div>
</body>
</html>
