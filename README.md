🎯 Conversor de PNG para G-code com Arduino (Plotter)


📌 Visão geral do projeto

- Este projeto tem como objetivo o desenvolvimento de um sistema completo de conversão de imagens PNG em arquivos G-code, voltado principalmente para plotters e máquinas controladas por Arduino para fins acadêmicos.

- A conversão não é feita de forma direta. Para preservar maior fidelidade visual e suavidade nos traços, o sistema realiza a seguinte sequência:

                                                                                       PNG → SVG → G-code

O uso do SVG como etapa intermediária permite trabalhar com vetores, possibilitando:

- curvas mais suaves

- redução de ruído visual

- maior controle sobre simplificação geométrica

🧠 Motivação técnica

Durante o desenvolvimento, observou-se que:

- imagens PNG grandes geravam arquivos SVG muito complexos

- SVGs com muitos pontos resultavam em G-code pesado, e isso aumentava significativamente o tempo de processamento e o tempo de execução na máquina

Dessa forma, o foco do projeto passou a ser:

- otimização do fluxo de conversão

- redução do tamanho dos arquivos

- simplificação das curvas, sem perda significativa de qualidade visual

🔄 Fluxo completo do sistema

O usuário envia uma imagem PNG pelo site. O PHP:

- salva a imagem

- realiza uma primeira otimização

- chama o script Python

O Python:

- pré-processa a imagem

- converte PNG → SVG

- otimiza e simplifica o SVG

- converte SVG → G-code

- O G-code final é retornado para download

🖼️ Processamento e otimização de imagens

Para lidar com problemas de tamanho e complexidade, foram implementadas diversas técnicas:

🔹 Redimensionamento: Imagens maiores que um limite máximo são automaticamente redimensionadas, mantendo a proporção.

🔹 Conversão para escala de cinza: A imagem é convertida para tons de cinza para facilitar a vetorização.

🔹 Binarização: Foi adicionada uma etapa de binarização, transformando a imagem em apenas preto e branco, reduzindo ruído e pontos desnecessários.

🔹 Quantização de cores: Testes com quantização de cores foram realizados, eliminando distinções entre cores semelhantes para simplificar a imagem sem comprometer fortemente a qualidade.

🔹 Compressão: Foram utilizados recursos das bibliotecas:

         - Pillow (PIL) – manipulação e redimensionamento

         - GD (PHP) – otimização inicial do PNG

✏️ Conversão PNG → SVG

A conversão para SVG é realizada com foco em:

- redução de nós

- simplificação de curvas

- eliminação de elementos desnecessários

Também foram realizados testes com ferramentas como:

- Potrace (pesquisada e testada durante o desenvolvimento)

- Além disso, arquivos intermediários desnecessários foram removidos para tornar o fluxo mais eficiente.

⚙️ Conversão SVG → G-code

A conversão final utiliza a biblioteca:

                                                                       svg_to_gcode

Nessa etapa:

- os caminhos vetoriais são interpretados

- as curvas são convertidas em comandos de movimento

- parâmetros como velocidade e avanço são definidos

- o G-code final é gerado de forma compatível com plotters e CNCs simples

🪵 Logs e depuração

Para facilitar o entendimento do fluxo e a identificação de erros, foi implementado um sistema de logging detalhado.

O arquivo:

                                                                             gcode_converter.log 
descreve passo a passo:

- abertura da imagem

- pré-processamento

- geração do SVG

- otimização

- conversão para G-code

- possíveis erros ou avisos

Isso tornou o processo de depuração mais claro e organizado, além de facilitar futuras melhorias.

📱 Versão mobile (WebView)

Este projeto foi desenvolvido inicialmente como uma aplicação web.

Embora seja possível transformá-lo em um aplicativo Android utilizando WebView, essa abordagem não foi implementada nesta versão porque:

- todo o processamento ocorre no servidor (PHP + Python)

- o app Android seria apenas um container da interface web

- a versão web já funciona corretamente em dispositivos móveis

🔮 Possível evolução

Uma versão Android pode ser criada futuramente sem alterações no backend, apenas carregando o site em uma WebView.

🔌 Envio do G-code para o Arduino

Após a geração do G-code, ele pode ser enviado ao Arduino de diversas formas:

🔹 Via USB (Serial)

Utilizando softwares como:

- Universal G-code Sender (UGS)

- CNCjs

- Pronterface

🔹 Via código próprio

É possível criar um script (em Python ou outro idioma) que:

- abra a porta serial

- envie linha por linha do G-code

- controle delays e respostas do Arduino

🔹 Firmware comum no Arduino

- GRBL

- Firmwares customizados para plotters

📊 Contexto acadêmico
- Esse projeto foi desenvolvido com o incentivo do Nightwind, do CTISM/UFSM

🔔 *Este projeto foi desenvolvido a partir de um fork do repositório SvgToGcode, do usuário PadLex, que serviu como base para a conversão de arquivos SVG em G-code. A partir dessa base, foram realizadas adaptações e extensões para permitir a conversão de imagens PNG, além de otimizações no fluxo de processamento.*
