<?php
// Configurações de segurança
ini_set('display_errors', 0);
error_reporting(0);

// Diretório seguro para downloads
define('GCODE_DIR', __DIR__ . '/gcode/');

// Verificar se o parâmetro foi enviado
if (!isset($_GET['file']) || empty($_GET['file'])) {
    header("HTTP/1.0 400 Bad Request");
    die("Parâmetro file não especificado");
}

// Sanitizar nome do arquivo
$filename = basename($_GET['file']);
$filepath = GCODE_DIR . $filename;

// Verificar se arquivo existe e é seguro
if (!file_exists($filepath) || !is_file($filepath)) {
    header("HTTP/1.0 404 Not Found");
    die("Arquivo não encontrado");
}

// Configurar headers para download
header('Content-Description: File Transfer');
header('Content-Type: application/octet-stream');
header('Content-Disposition: attachment; filename="' . $filename . '"');
header('Content-Length: ' . filesize($filepath));
header('Expires: 0');
header('Cache-Control: must-revalidate');
header('Pragma: public');

// Limpar buffer de saída e enviar arquivo
ob_clean();
flush();
readfile($filepath);
exit;
?>