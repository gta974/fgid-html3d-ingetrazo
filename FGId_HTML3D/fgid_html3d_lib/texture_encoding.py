"""Encode HTML textures compactly without changing source assets or dimensions."""
from PySide6.QtCore import QByteArray, QBuffer, QIODevice
from PySide6.QtGui import QImage
import numpy as np


def encode_texture(data):
    image = QImage.fromData(data)
    if image.isNull():return None
    transparent = False
    if image.hasAlphaChannel():
        rgba = image.convertToFormat(QImage.Format_RGBA8888)
        pixels = np.frombuffer(rgba.constBits(), dtype=np.uint8).reshape(rgba.height(), rgba.bytesPerLine())
        transparent = bool(np.any(pixels[:,3:rgba.width()*4:4] < 255))
    def encode(fmt, quality=-1):
        array = QByteArray(); buffer = QBuffer(array)
        buffer.open(QIODevice.WriteOnly)
        ok = image.save(buffer, fmt, quality); buffer.close()
        return bytes(array) if ok else None
    if transparent:
        result = data if data.startswith(b'\x89PNG\r\n\x1a\n') else encode('PNG')
        return (result, 'image/png') if result else None
    if data.startswith(b'\xff\xd8'):
        return data, 'image/jpeg'  # Keep existing JPEG quality and bytes.
    jpeg = encode('JPEG', 85)
    png = data if data.startswith(b'\x89PNG\r\n\x1a\n') else encode('PNG')
    if jpeg and (not png or len(jpeg)<len(png)):return jpeg, 'image/jpeg'
    return (png, 'image/png') if png else None
