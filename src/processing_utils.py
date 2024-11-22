import re
from deep_translator import GoogleTranslator
from typing import List, Callable

# Configuración de patrones de spam que deben ser eliminados del texto.
SPAM_PATTERNS = [
    r"Subtitled by",
    r'-♪ <font color="green">online</font>-<font color="red">courses</font>.<font color="yellow">club</font> ♪-',
    "We compress knowledge for you!",
    r"https://t.me/joinchat/ailxpXoW3JVjYzQ1",
    r"Subtitled\s*by",
    r"https?://[^\s]+",
    r"♪",
    r"We\s*compress\s*knowledge\s*for\s*you!",
    r"online|courses|club",
    r"<font.*?>.*?<\/font>",
    r"\bjoinchat\b",
]


def eliminar_spam(texto: str) -> str:
    """Elimina cualquier contenido no deseado o spam del texto según los patrones definidos

    Args:
        texto (str): El texto a procesar.

    Returns:
        str: Texto limpio de cualquier patrón coincidente de spam.
    """
    for patron in SPAM_PATTERNS:
        texto = re.sub(patron, "", texto, flags=re.IGNORECASE)
    return texto


def traducir_texto(texto: str, idioma_destino: str, progress_callback: Callable = None) -> str:
    """Traduce un texto al idioma especificado utilizando Google Translator.

    Args:
        texto (str): Texto a traducir.
        idioma_destino (str): Código del idioma al que se desea traducir.
        progress_callback (Callable, opcional): Función de callback para informar progreso.

    Returns:
        str: Texto traducido.

    Raises:
        Exception: Si ocurre un error durante la traducción.
    """
    try:
        translator = GoogleTranslator(source="auto", target=idioma_destino)
        traduccion = translator.translate(texto)
        if progress_callback:
            progress_callback('traduccion', traduccion)
        return traduccion
    except Exception as e:
        if progress_callback:
            progress_callback('error', f"Error en traducción: {str(e)}")
        raise


def contar_subtitulos(texto: str) -> int:
    """Cuenta el número total de subtítulos en un archivo de subtítulos.

    Args:
        texto (str): El contenido del archivo de subtítulos.

    Returns:
        int: Número de subtítulos presentes.
    """
    return len([line for line in texto.split('\n') if line.strip().isdigit()])


def procesar_archivo_srt(archivo_srt: str, traducir: bool, idioma_destino: str,
                         progress_callback: Callable = None) -> str:
    """Procesa un archivo SRT, eliminando spam y traduciendo subtítulos si es necesario.

    Args:
        archivo_srt (str): Ruta del archivo SRT.
        traducir (bool): Indica si se debe traducir el contenido.
        idioma_destino (str): Código del idioma al que se desea traducir.
        progress_callback (Callable, opcional): Función para manejar actualizaciones de progreso.

    Returns:
        str: Contenido procesado del archivo SRT.

    Raises:
        Exception: Si ocurre un error durante el procesamiento.
    """
    try:
        # Leer contenido del archivo
        with open(archivo_srt, "r", encoding='UTF-8') as f:
            contenido = f.read()

        # Contar subtítulos para el seguimiento del progreso
        total_subtitulos = contar_subtitulos(contenido)
        if progress_callback:
            progress_callback('info', f"Total de subtítulos: {total_subtitulos}")

        lineas = contenido.split('\n')
        texto_procesado = []
        subtitulos_procesados = 0

        bloques = []
        bloque_actual = []

        for linea in lineas:
            # Eliminar contenido de spam
            linea = eliminar_spam(linea)

            if linea.strip():
                if linea.strip().isdigit() or '-->' in linea:
                    if bloque_actual:
                        bloques.append(bloque_actual)
                        bloque_actual = []
                bloque_actual.append(linea)

        if bloque_actual:
            bloques.append(bloque_actual)

        total_bloques = len(bloques)
        bloques_procesados = 0

        for bloque in bloques:
            bloque_texto = "\n".join(bloque)

            if traducir:
                try:
                    bloque_texto = traducir_texto(bloque_texto, idioma_destino)
                    bloque = bloque_texto.split('\n')
                except Exception as e:
                    if progress_callback:
                        progress_callback('error', f"Error traduciendo bloque: {str(e)}")
                    continue

            texto_procesado.extend(bloque)

            # Actualizar progreso
            bloques_procesados += 1
            if progress_callback:
                progress = (bloques_procesados / total_bloques) * 0.9  # 90% del progreso total
                progress_callback('progress', progress)

        # Agregar líneas vacías antes de los números de subtítulo
        texto_procesado_con_saltos = []
        for i, linea in enumerate(texto_procesado):
            if linea.strip().isdigit():
                texto_procesado_con_saltos.append("\n" + linea)
            else:
                texto_procesado_con_saltos.append(linea)

        if progress_callback:
            progress_callback('progress', 1.0)  # 100% completado

        return "\n".join(texto_procesado_con_saltos)

    except Exception as e:
        if progress_callback:
            progress_callback('error', str(e))
        raise


def dividir_en_bloques(texto_procesado: str, progress_callback: Callable = None) -> List[List[str]]:
    """Divide el texto procesado en bloques basados en números de subtítulo.

    Args:
        texto_procesado (str): Texto que ya ha sido procesado.
        progress_callback (Callable, opcional): Función de callback para informar progreso.

    Returns:
        List[List[str]]: Lista de bloques de subtítulos.
    """
    try:
        bloques = []
        bloque_actual = []
        lineas = texto_procesado.split("\n")
        total_lineas = len(lineas)

        for i, linea in enumerate(lineas):
            if linea.strip().isdigit():
                if bloque_actual:
                    bloques.append(bloque_actual)
                bloque_actual = [linea]
            else:
                if linea.strip():
                    bloque_actual.append(linea)

            if progress_callback:
                progress = 0.6 + ((i / total_lineas) * 0.2)  # 60-80% del progreso
                progress_callback('progress', progress)

        if bloque_actual:
            bloques.append(bloque_actual)

        if progress_callback:
            progress_callback('progress', 0.8)

        return bloques
    except Exception as e:
        if progress_callback:
            progress_callback('error', str(e))
        raise


def procesar_bloques(bloques: List[List[str]], progress_callback: Callable = None) -> List[List[str]]:
    """Realiza ajustes adicionales en los bloques de subtítulos, como combinar bloques incompletos.

    Args:
        bloques (List[List[str]]): Lista de bloques a procesar.
        progress_callback (Callable, opcional): Función para manejar actualizaciones de progreso.

    Returns:
        List[List[str]]: Lista de bloques procesados.
    """
    try:
        total_bloques = len(bloques)
        for i, bloque in enumerate(bloques):
            if len(bloque) < 3 and i + 1 < len(bloques):
                bloque_sin_texto = bloque
                bloque_siguiente = bloques[i + 1]

                tiempo_completo = bloque_sin_texto[1].split("-->")[0] + "-->" + bloque_siguiente[1].split("-->")[1]
                bloque_siguiente[1] = tiempo_completo

                bloques.pop(i)

            if progress_callback:
                progress = 0.8 + ((i / total_bloques) * 0.1)  # 80-90% del progreso
                progress_callback('progress', progress)

        return bloques
    except Exception as e:
        if progress_callback:
            progress_callback('error', str(e))
        raise


def devolver_formato(bloques: List[List[str]], progress_callback: Callable = None) -> str:
    """Convierte los bloques de subtítulos procesados nuevamente en un formato de texto.

    Args:
        bloques (List[List[str]]): Lista de bloques de subtítulos.
        progress_callback (Callable, opcional): Función de callback para manejar el progreso.

    Returns:
        str: El texto formateado en su estructura original.
    """
    try:
        texto_final = ""
        total_bloques = len(bloques)

        for i, bloque in enumerate(bloques):
            for linea in bloque:
                texto_final += linea + "\n"
            texto_final += "\n"

            if progress_callback:
                progress = 0.9 + ((i / total_bloques) * 0.1)  # 90-100% del progreso
                progress_callback('progress', progress)

        if progress_callback:
            progress_callback('progress', 1.0)

        return texto_final.rstrip()
    except Exception as e:
        if progress_callback:
            progress_callback('error', str(e))
        raise
