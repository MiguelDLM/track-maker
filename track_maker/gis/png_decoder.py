"""Decodificador PNG ligero y puro en Python + NumPy sin dependencias externas (PIL/Pillow).

Especializado en la decodificación de mosaicos PNG RGB / RGBA de 8 bits por canal
empleados por AWS Terrarium y servicios cartográficos de elevación DEM.
"""

from __future__ import annotations
import struct
import zlib
import numpy as np

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def decode_png_rgb(png_bytes: bytes) -> np.ndarray:
    """Decodifica un archivo PNG de 8-bit RGB o RGBA a un array NumPy uint8 de dimensiones (H, W, 3)."""
    if not png_bytes.startswith(PNG_SIGNATURE):
        raise ValueError("Firma PNG no válida (no es un archivo PNG válido).")

    offset = 8
    width = 0
    height = 0
    bit_depth = 8
    color_type = 2
    idat_chunks = []

    while offset < len(png_bytes):
        if offset + 8 > len(png_bytes):
            break
        length, chunk_type = struct.unpack(">I4s", png_bytes[offset:offset + 8])
        offset += 8
        chunk_data = png_bytes[offset:offset + length]
        offset += length
        _crc = png_bytes[offset:offset + 4]
        offset += 4

        if chunk_type == b"IHDR":
            width, height, bit_depth, color_type, comp, filt, interlace = struct.unpack(
                ">IIBBBBB", chunk_data
            )
            if bit_depth != 8:
                raise NotImplementedError(f"Profundidad de bits no soportada: {bit_depth}")
            if color_type not in (2, 6):  # 2 = RGB, 6 = RGBA
                raise NotImplementedError(f"Tipo de color PNG no soportado: {color_type}")
            if interlace != 0:
                raise NotImplementedError("PNG entrelazado no soportado.")
        elif chunk_type == b"IDAT":
            idat_chunks.append(chunk_data)
        elif chunk_type == b"IEND":
            break

    raw_decompressed = zlib.decompress(b"".join(idat_chunks))
    channels = 3 if color_type == 2 else 4
    bpp = channels
    row_bytes = width * bpp
    stride = 1 + row_bytes

    if len(raw_decompressed) < height * stride:
        raise ValueError("El flujo PNG descomprimido es más corto de lo esperado.")

    raw = np.frombuffer(raw_decompressed, dtype=np.uint8, count=height * stride).reshape((height, stride))
    filters = raw[:, 0]
    scanlines = raw[:, 1:]
    recon = np.zeros((height, row_bytes), dtype=np.uint8)
    prev = np.zeros(row_bytes, dtype=np.uint8)

    for r in range(height):
        line = scanlines[r]
        filter_type = filters[r]
        if filter_type == 1:  # Sub
            recon[r] = np.cumsum(line.reshape((width, bpp)), axis=0, dtype=np.uint8).ravel()
        elif filter_type == 2:  # Up
            recon[r] = line + prev
        elif filter_type == 3:  # Average
            recon[r] = _unfilter_average(line.tobytes(), prev.tobytes(), bpp)
        elif filter_type == 4:  # Paeth
            recon[r] = _unfilter_paeth(line.tobytes(), prev.tobytes(), bpp)
        else:  # 0 = None
            recon[r] = line
        prev = recon[r]

    img_array = recon.reshape((height, width, channels))
    # Devolver RGB (descartando canal Alpha si existe)
    return img_array[:, :, :3]


def _unfilter_average(line: bytes, prev: bytes, bpp: int) -> bytearray:
    out = bytearray(len(line))
    for i in range(bpp):
        out[i] = (line[i] + (prev[i] >> 1)) & 0xFF
    for i in range(bpp, len(line)):
        out[i] = (line[i] + ((out[i - bpp] + prev[i]) >> 1)) & 0xFF
    return out


def _unfilter_paeth(line: bytes, prev: bytes, bpp: int) -> bytearray:
    out = bytearray(len(line))
    for i in range(bpp):
        out[i] = (line[i] + prev[i]) & 0xFF
    for i in range(bpp, len(line)):
        a = out[i - bpp]
        b = prev[i]
        c = prev[i - bpp]
        pa = b - c
        pb = a - c
        pc = pa + pb
        if pa < 0:
            pa = -pa
        if pb < 0:
            pb = -pb
        if pc < 0:
            pc = -pc
        if pa <= pb and pa <= pc:
            pred = a
        elif pb <= pc:
            pred = b
        else:
            pred = c
        out[i] = (line[i] + pred) & 0xFF
    return out
